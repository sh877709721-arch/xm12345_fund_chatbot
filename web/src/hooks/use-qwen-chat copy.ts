import { useCallback, useEffect, useState, useRef } from "react";

// 思考过程步骤类型
export type ThoughtStep = {
  id: string;
  type: 'thought' | 'action' | 'observation' | 'final';
  content: string;
  timestamp?: number;
  status?: 'pending' | 'complete' | 'error';
};

// Source引用类型
export type Source = {
  id?: string;
  title: string;
  url?: string;
  description?: string;
  snippet?: string;
};

export type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
  db_id?: number | null;  // 真实的数据库ID，初始时为undefined，接收到后更新
  temp_id?: number;       // 临时ID，用于标识消息
  feedback?: 'good' | 'medium' | 'bad' | null;  // 用户反馈：好/中/差/无反馈
  // 新增字段：思考过程
  thoughtSteps?: ThoughtStep[];  // 思考过程步骤
  showChainOfThought?: boolean;  // 是否显示思考过程
  hasChainOfThought?: boolean;   // 是否包含思考过程
  sources?: Source[];           // Source引用列表
};

export type ChatStatus = "submitted" | "streaming" | "ready" | "error";

export type ChatSession = {
  id: string;
  status?: string;
  title?: string | null;
  user_id?: string;
  created_at?: string;
  updated_at?: string;
};

export type ModelType = "default" | "boost";

export type RecommendQA = {
  id: number;
  question: string;
}

export function useQwenChat(
  /** 你的 SSE 接口地址，例如 /api/v1/chat/completions */
  api: string = "/v1/chat/completions",
  initMessages: Message[] = [],
  options?: { resetEndpoint?: string; storageKey?: string; initialModel?: ModelType }
) {
  const [messages, setMessages] = useState<Message[]>(initMessages);
  const [model, setModel] = useState<ModelType>(options?.initialModel ?? "default");
  const [status, setStatus] = useState<ChatStatus>("ready");
  const [session, setSession] = useState<ChatSession | null>(null);
  const [recommendQa, setRecommendQa] = useState<RecommendQA[]|null>([
      {"id": 2557,"question": "怎么打印厦门的医保参保凭证？"},
      {"id": 1872,"question": "厦门医保参保人在外地就医，怎么报销费用？"},
      {"id": 2151,"question": "怎么查我在思明区的医保缴费情况和金额？"}
    ])
  const tempIdRef = useRef(-1); // 用于生成临时ID

  /* ---------- 获取历史记录 ---------- */
  const storageKey = options?.storageKey ?? "qwen_chat_session";
  // use a fixed reset endpoint by default — the Vite proxy already forwards `/api` to your backend
  const resetEndpoint = options?.resetEndpoint ?? "/znkfzs/v1/chat/reset-chat-session";

  const resetChatSession = useCallback(async (force = false) => {
    // Try to reuse existing session from storage unless force is true
    try {
      if (!force) {
        const raw = localStorage.getItem(storageKey);
        if (raw) {
          const parsed = JSON.parse(raw) as ChatSession;
          if (parsed?.id) {
            setSession(parsed);
            // try to load recent messages for this chat id from server
            try {
              const res = await fetch(`/znkfzs/v1/chat/get_resent_messages?chat_id=${parsed.id}`, {
                method: "POST",
                headers: { accept: "application/json" },
                body: "",
              });
              if (res.ok) {
                const body = await res.json();
                const fetchedMessages: Message[] = Array.isArray(body)
                  ? body.map((m: any) => ({
                      id: m.id,
                      role: (m.role as Message['role']) ?? (m.from as Message['role']) ?? "assistant",
                      content: (m.content as string) ?? m.text ?? m.message ?? JSON.stringify(m),
                      db_id: m.id, // 从数据库加载的消息，其id就是数据库ID
                      temp_id: undefined,
                    }))
                  : [];

                  setMessages(fetchedMessages)
              } else {
                // fallback to initMessages if fetch failed
                setMessages(initMessages);
              }
            } catch (e) {
              // ignore fetch errors and fallback
              setMessages(initMessages);
            }

            setStatus("ready");
            return parsed;
          }
        }
      }

      setStatus("submitted");
      const res = await fetch(resetEndpoint, { method: "POST", headers: { accept: "application/json" } });
      if (!res.ok) throw new Error(`reset failed: ${res.status}`);
      const body = await res.json();
      const s: ChatSession = {
        id: body.id,
        status: body.status,
        title: body.title,
        user_id: body.user_id,
        created_at: body.created_at,
        updated_at: body.updated_at,
      };
      setSession(s);
      try {
        localStorage.setItem(storageKey, JSON.stringify(s));
      } catch {}
      setMessages(initMessages);
      setStatus("ready");
      return s;
    } catch (err) {
      setStatus("error");
      throw err;
    }
  }, [initMessages, resetEndpoint, storageKey]);


  /* ----------- STOP功能----------------- */
  const readerRef = useRef<ReadableStreamDefaultReader<Uint8Array> | null>(null);
  const messagesRef = useRef<Message[]>(messages);
  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  const stop = useCallback(() => {
    readerRef.current?.cancel(); // 1. 立即断流
    readerRef.current = null;
    setStatus("ready"); // 2. 重置状态
    /* 3. 可选：把最后一条没写完的 assistant 消息删掉 */
    setMessages((prev) => {
      const last = prev[prev.length - 1];
      return last?.role === "assistant" ? prev.slice(0, -1) : prev;
    });
  }, []);

  /* ---------- 辅助函数 ---------- */
  // 根据临时ID查找消息索引
  const findMessageIndexByTempId = (messages: Message[], role: "user" | "assistant"): number => {
    for (let i = messages.length - 1; i >= 0; i--) {
      const msg = messages[i];
      if (msg.role === role && msg.temp_id && msg.temp_id < 0) {
        return i;
      }
    }
    return -1;
  };


  // 更新消息反馈
  const updateMessageFeedback = useCallback((messageId: number, feedback: 'good' | 'medium' | 'bad' | null) => {
    console.log('updateMessageFeedback', messageId, feedback);
    
    setMessages((prev) =>
      prev.map((msg) => {
        // 同时匹配临时ID和数据库ID
        if (msg.id === messageId || msg.db_id === messageId) {
          return { ...msg, feedback };
        }
        return msg;
      })
    );
  }, []);

  // 将后端思考步骤数据转换为前端格式
  const convertThoughtStepFromBackend = useCallback((backendStep: any): ThoughtStep => {
    return {
      id: backendStep.id,
      type: backendStep.type,
      content: backendStep.content,
      timestamp: backendStep.timestamp,
      status: backendStep.status || 'complete'
    };
  }, []);

  const toggleChainOfThought = useCallback((messageId: number) => {
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === messageId
          ? { ...msg, showChainOfThought: !msg.showChainOfThought }
          : msg
      )
    );
  }, []);

  // 📝 CHANGE: 添加扩展截断消息的功能
  // 注意：这里只是基础框架，实际使用时需要根据你的后端 API 调整
  const expandTruncatedMessage = useCallback(async (messageId: number) => {
    // 实际应用中，这里应该调用 API 获取完整的消息内容
    // 例如：await fetch(`/api/v1/chat/expand-message/${messageId}`)

    setMessages((prev) =>
      prev.map((msg) => {
        if (msg.id === messageId && msg.content.includes('...')) {
          // 这里应该从 API 获取完整内容
          // 暂时只作为示例移除截断标记
          return {
            ...msg,
            content: msg.content.replace(/\.\.\.$/, '[完整内容待加载]'),
          };
        }
        return msg;
      })
    );
  }, []);

  /* ---------- 发送一条用户消息 ---------- */
  const sendMessage = useCallback(
    async (userContent: string) => {
      const tempUserMsgId = tempIdRef.current--;
      const tempAssistantMsgId = tempIdRef.current--;

      const userMsg: Message = {
        id: tempUserMsgId,
        role: "user",
        content: userContent,
        temp_id: tempUserMsgId,
        db_id: undefined,
      };

      // ensure we have the latest session id
      // IMPORTANT: React state updates (setSession) do not synchronously update the
      // `session` variable in the current function. Calling `resetChatSession()` will
      // set state, but `session` here would remain stale until the next render.
      // To avoid losing the chat_id because of that timing, capture the returned
      // session from resetChatSession() and prefer it when building the request body.
      let currentSession: ChatSession | null = session;
      if (!currentSession?.id) {
        try {
          // resetChatSession returns the new session when successful — use that
          // return value so we don't depend on state being updated synchronously.
          currentSession = await resetChatSession();
        } catch (e) {
          // If reset failed, proceed without chat_id (server may handle it), but
          // keep streaming UI consistent. The error state will be set inside
          // resetChatSession when appropriate.
          currentSession = null;
        }
      }

      // push user message and placeholder assistant message
      setMessages((prev) => {
        return [...prev, userMsg, {
          id: tempAssistantMsgId,
          role: "assistant",
          content: "",
          temp_id: tempAssistantMsgId,
          db_id: undefined,
          feedback: null,  // 初始化投票状态为null
        }];
      });
      setStatus("streaming");

      let assistantText = ""; // 累积 assistant 内容


      try {
        // always use the freshest messages via ref
        const convo = [...messagesRef.current, userMsg]; //[...messagesRef.current, userMsg];
        const body: any = { messages: convo, model };
        // use the freshest session reference (may be returned from resetChatSession)
        if (currentSession?.id) body.chat_id = currentSession.id;

        const res = await fetch(api, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        if (!res.ok || !res.body) throw new Error("Network error");

        readerRef.current = res.body.getReader(); // 保存引用
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const r = readerRef.current;
          if (!r) break;
          const { done, value } = await r.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          const lines = buffer.split("\n");
          buffer = lines.pop()!; // 最后一行可能不完整

          for (const line of lines) {
            const trim = line.trim();
            if (trim.startsWith("data:")) {
              const data = trim.slice(5).trim();
              if (data === "[DONE]") {
                // finished streaming
                readerRef.current = null;
                setStatus("ready");

                // 获取推荐问题
                (async () => {
                  try {
                    if (currentSession?.id) {
                      const recommendRes = await fetch(`/znkfzs/v1/chat/get_similary_qa?chat_id=${currentSession.id}`, {
                        method: 'POST',
                        headers: { 'accept': 'application/json' },
                        body: ''
                      });

                      if (recommendRes.ok) {
                        const recommendData = await recommendRes.json();
                        if (Array.isArray(recommendData)) {
                          setRecommendQa(recommendData);
                        }
                      }
                    }
                  } catch (error) {
                    console.error('Failed to fetch recommended questions:', error);
                  }
                })();

                break;
              }

              try {
                const chunk: any = JSON.parse(data);

                // 处理消息ID的特殊chunk
                if (chunk.object === "chat.completion.message_id" && chunk.message_id) {
                  setMessages((prev) => {
                    const copy = [...prev];

                    // 更新用户消息ID
                    if (chunk.message_id.user_message_id) {
                      const userMessageIndex = findMessageIndexByTempId(copy, "user");
                      if (userMessageIndex >= 0) {
                        copy[userMessageIndex] = {
                          ...copy[userMessageIndex],
                          id: chunk.message_id.user_message_id,
                          temp_id: undefined, // 清除临时ID
                        };
                      }
                    }

                    // 更新助手消息ID
                    if (chunk.message_id.assistant_message_id) {
                      const assistantMessageIndex = findMessageIndexByTempId(copy, "assistant");
                      if (assistantMessageIndex >= 0) {
                        copy[assistantMessageIndex] = {
                          ...copy[assistantMessageIndex],
                          id: chunk.message_id.assistant_message_id,
                          temp_id: undefined, // 清除临时ID
                        };
                      }
                    }

                    return copy;
                  });
                  continue;
                }

                // 处理sources chunk
                if (chunk.object === "chat.completion.sources" && chunk.sources) {
                  setMessages((prev) => {
                    const copy = [...prev];
                    const lastIndex = copy.length - 1;

                    copy[lastIndex] = {
                      ...copy[lastIndex],
                      sources: chunk.sources.map((source: any) => ({
                        id: source.id,
                        title: source.title,
                        url: source.url || source.href,
                        description: source.description,
                        snippet: source.snippet || source.content
                      }))
                    };
                    return copy;
                  });
                  continue;
                }

                // 处理思考步骤chunk (保持兼容性)
                if (chunk.object === "chat.completion.thought_step" && chunk.thought_step) {
                  setMessages((prev) => {
                    const copy = [...prev];
                    const lastIndex = copy.length - 1;
                    const currentThoughtSteps = copy[lastIndex].thoughtSteps || [];

                    // 转换后端格式到前端格式
                    const newThoughtStep = convertThoughtStepFromBackend(chunk.thought_step);

                    // 如果是最终答案，同时更新消息内容
                    let contentUpdate = {};
                    if (newThoughtStep.type === 'final') {
                      contentUpdate = {
                        content: newThoughtStep.content
                      };
                    }

                    copy[lastIndex] = {
                      ...copy[lastIndex],
                      ...contentUpdate,
                      thoughtSteps: [...currentThoughtSteps, newThoughtStep],
                      hasChainOfThought: true,
                      showChainOfThought: false, // 默认不展开
                    };
                    return copy;
                  });
                  continue;
                }

                const delta = chunk.choices?.[0]?.delta?.content;
                if (!delta) {
                  continue;
                }

                // 处理不同类型的消息
                if (chunk.object === "chat.completion.chunk") {
                  // 常规内容块 - 立即显示给用户
                  assistantText = delta //.split("**参考出处**")[0] //[0]

                  /* 更新最后一行 assistant 消息的内容 */
                  setMessages((prev) => {
                    const copy = [...prev];
                    const lastIndex = copy.length - 1;

                    copy[lastIndex] = {
                      ...copy[lastIndex],
                      content: assistantText, // 更新内容
                    };
                    return copy;
                  });

                  //处理参考来源 - 与历史消息加载逻辑保持一致
                  // const splitContent = delta.split("**参考出处**");
                  // const referenceText = splitContent[1];
                  // if (referenceText) {
                  //   // 按 \n\n 分割多条记录
                  //   const referenceItems = referenceText.split('\n\n').filter((item: string) => item.trim());

                  //   const extractedSources = referenceItems.map((item: string, index: number) => {
                  //     // 尝试提取标题和URL
                  //     const lines = item.trim().split('\n');
                  //     const title = lines[0]?.trim() || `参考来源 ${index + 1}`;

                  //     // 查找URL（如果存在）
                  //     let url = '';
                  //     const urlMatch = item.match(/https?:\/\/[^\s]+/);
                  //     if (urlMatch) {
                  //       url = urlMatch[0];
                  //       // 清除末尾的 ) 字符
                  //       if (url.endsWith(')')) {
                  //         url = url.slice(0, -1);
                  //       }
                  //     }

                  //     return {
                  //       title,
                  //       url: url || undefined,
                  //       id: `source-temp-${Date.now()}-${index}`
                  //     };
                  //   }).filter((source: Source) => source.title); // 过滤掉空的记录

                  //   // 如果提取到 sources，更新消息
                  //   if (extractedSources.length > 0) {
                  //     setMessages((prev) => {
                  //       const copy = [...prev];
                  //       const lastIndex = copy.length - 1;

                  //       copy[lastIndex] = {
                  //         ...copy[lastIndex],
                  //         sources: extractedSources
                  //       };
                  //       return copy;
                  //     });
                  //   }
                  // }
                  
                  

                } else if (chunk.object === "chat.completion.action") {
                  // Action 消息 - 替换当前action内容，避免累积重复
                  const actionContent = delta; // 直接使用当前delta内容

                  // 使用替换模式更新action内容
                  setMessages((prev) => {
                    const copy = [...prev];
                    const lastIndex = copy.length - 1;
                    const currentMessage = copy[lastIndex];

                    if (currentMessage.role === "assistant") {
                      const thoughtSteps = [...(currentMessage.thoughtSteps || [])];
                      const lastStepIndex = thoughtSteps.length - 1;

                      // 查找最后一个action步骤或创建新的
                      let actionStepIndex = -1;
                      for (let i = lastStepIndex; i >= 0; i--) {
                        if (thoughtSteps[i].type === 'action') {
                          actionStepIndex = i;
                          break;
                        }
                      }

                      const actionStep: ThoughtStep = {
                        id: actionStepIndex >= 0 ? thoughtSteps[actionStepIndex].id : `action-${Date.now()}`,
                        type: 'action',
                        content: actionContent,
                        timestamp: actionStepIndex >= 0 ? thoughtSteps[actionStepIndex].timestamp : Date.now(),
                        status: 'complete'
                      };

                      if (actionStepIndex >= 0) {
                        // 替换现有的action步骤
                        thoughtSteps[actionStepIndex] = actionStep;
                      } else {
                        // 添加新的action步骤
                        thoughtSteps.push(actionStep);
                      }

                      copy[lastIndex] = {
                        ...currentMessage,
                        thoughtSteps,
                        hasChainOfThought: true,
                        showChainOfThought: false //默认不展开 currentMessage.showChainOfThought ?? true
                      };
                    }

                    return copy;
                  });


                } else if (chunk.object === "chat.completion.observation") {
                  // Observation 消息 - 替换当前observation内容，避免累积重复
                  const observationContent = delta; // 直接使用当前delta内容

                  // 使用替换模式更新observation内容
                  setMessages((prev) => {
                    const copy = [...prev];
                    const lastIndex = copy.length - 1;
                    const currentMessage = copy[lastIndex];

                    if (currentMessage.role === "assistant") {
                      const thoughtSteps = [...(currentMessage.thoughtSteps || [])];
                      const lastStepIndex = thoughtSteps.length - 1;

                      // 查找最后一个observation步骤或创建新的
                      let observationStepIndex = -1;
                      for (let i = lastStepIndex; i >= 0; i--) {
                        if (thoughtSteps[i].type === 'observation') {
                          observationStepIndex = i;
                          break;
                        }
                      }

                      const observationStep: ThoughtStep = {
                        id: observationStepIndex >= 0 ? thoughtSteps[observationStepIndex].id : `observation-${Date.now()}`,
                        type: 'observation',
                        content: observationContent,
                        timestamp: observationStepIndex >= 0 ? thoughtSteps[observationStepIndex].timestamp : Date.now(),
                        status: 'complete'
                      };

                      if (observationStepIndex >= 0) {
                        // 替换现有的observation步骤
                        thoughtSteps[observationStepIndex] = observationStep;
                      } else {
                        // 添加新的observation步骤
                        thoughtSteps.push(observationStep);
                      }

                      copy[lastIndex] = {
                        ...currentMessage,
                        thoughtSteps,
                        hasChainOfThought: true,
                        showChainOfThought: false// 默认不展开 currentMessage.showChainOfThought ?? true
                      };
                    }

                    return copy;
                  });


                } else {
                  // 兼容旧格式：如果object字段不是这三种类型，作为常规chunk处理
                  assistantText = delta;

                  /* 更新最后一行 assistant 消息的内容 */
                  setMessages((prev) => {
                    const copy = [...prev];
                    const lastIndex = copy.length - 1;

                    copy[lastIndex] = {
                      ...copy[lastIndex],
                      content: assistantText,
                    };
                    return copy;
                  });
                }

              } catch (e) {
                /* 忽略解析失败 */
              }
            }
          }
        }
      } catch (err) {
        setStatus("error");
        throw err;
      } finally {
        readerRef.current = null;
        setStatus((s) => (s === "error" ? "error" : "ready"));
      }
    },
    [api, resetChatSession, session]
  );

  /* ---------- 重新生成最后一条 assistant 回复 ---------- */
  const regenerate = useCallback(() => {
    if (messages.length < 2) return;
    const lastUser = messages[messages.length - 2];
    setMessages((prev) => prev.slice(0, -2)); // 删除最后两条
    sendMessage(lastUser.content);
  }, [messages, sendMessage]);

  /* ----------- 获取最近4条消息 ------------ */
  const getRecentMessages = useCallback((count: number = 8) => {
    return messagesRef.current.slice(-count);
  }, []);

  /* ----------- 清空全部消息 ------------ */
  const clearMessages = useCallback(() => {
    setMessages(initMessages);
  }, []);

  // load session from storage on mount (non-forced)
  useEffect(() => {
    (async () => {
      try {
        const raw = localStorage.getItem(storageKey);
        if (raw) {
          const parsed = JSON.parse(raw) as ChatSession;
          if (parsed?.id) {
            setSession(parsed);
            // try to fetch recent messages for this session and initialize messages
            try {
              const res = await fetch(`/znkfzs/v1/chat/get_resent_messages?chat_id=${parsed.id}`, {
                method: "POST",
                headers: { accept: "application/json" },
                body: "",
              });
              if (res.ok) {
                const body = await res.json();
                const fetchedMessages: Message[] = Array.isArray(body)
                  ? body.map((m: any) => ({
                      id: m.id,
                      role: (m.role as Message['role']) ?? (m.from as Message['role']) ?? "assistant",
                      content: (m.content as string) ?? m.text ?? m.message ?? JSON.stringify(m),
                      //content: (m.content?.split("**参考出处**")[0] as string) ?? m.text?.split("**参考出处**")[0] ?? m.message?.split("**参考出处**")[0] ?? JSON.stringify(m),
                      db_id: m.id, // 从数据库加载的消息，其id就是数据库ID
                      temp_id: undefined,
                      sources: (() => {
                        const splitContent = m.content?.split("**参考出处**") || [];
                        const referenceText = splitContent[1];
                        if (!referenceText) return [];

                        // 按 \n\n 分割多条记录
                        const referenceItems = referenceText.split('\n\n').filter((item: string) => item.trim());

                        return referenceItems.map((item: string, index: number) => {
                          // 尝试提取标题和URL
                          const lines = item.trim().split('\n');
                          const title = lines[0]?.trim() || `参考来源 ${index + 1}`;

                          // 查找URL（如果存在）
                          let url = '';
                          const urlMatch = item.match(/https?:\/\/[^\s]+/);
                          if (urlMatch) {
                            url = urlMatch[0];
                            // 清除末尾的 ) 字符
                            if (url.endsWith(')')) {
                              url = url.slice(0, -1);
                            }
                          }

                          return {
                            title,
                            url: url || undefined,
                            id: `source-${m.id}-${index}`
                          };
                        }).filter((source: Source) => source.title); // 过滤掉空的记录
                      })()
                    }))
                  : [];

                setMessages(() => [...initMessages, ...fetchedMessages]);
              } else {
                setMessages(initMessages);
              }
            } catch (e) {
              setMessages(initMessages);
            }
          }else{
            resetChatSession()
          }
        }
      } catch {}
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    messages,
    sendMessage,
    status,
    regenerate,
    stop,
    clearMessages,
    session,
    resetChatSession,
    updateMessageFeedback,
    toggleChainOfThought,
    expandTruncatedMessage,
    getRecentMessages,
    model,
    setModel,
    recommendQa
  };
}
