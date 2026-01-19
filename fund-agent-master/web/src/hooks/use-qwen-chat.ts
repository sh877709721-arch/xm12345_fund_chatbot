import { useCallback, useEffect, useState, useRef } from "react";
import {
  resetChatSession as apiResetSession,
  getRecentMessages as apiGetRecentMessages,
  getSimilarQA as apiGetSimilarQA,
  streamChatCompletionV2,
  type ChatSession,
  type Message,
  type RecommendQA,
  type Source,
  type ThoughtStep,
} from "@/utils/request/chat";
import { getTrafficSource } from "@/utils/traffic-source";

// 重新导出类型，保持向后兼容
export type { ChatSession, Message, RecommendQA, Source, ThoughtStep };

export type ChatStatus = "submitted" | "streaming" | "ready" | "error";

export type ModelType = "default" | "boost" | "guideline_bot";

export function useQwenChat(
  initMessages: Message[] = [],
  options?: { storageKey?: string; initialModel?: ModelType }
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
              const response = await apiGetRecentMessages(parsed.id);
              console.log('🔍 [resetChatSession] API Response:', response);

              const messages: Message[] = Array.isArray(response)
                ? response.map((m: any) => ({
                    id: m.id,
                    role: (m.role as Message['role']) ?? (m.from as Message['role']) ?? "assistant",
                    content: (m.content as string) ?? m.text ?? m.message ?? JSON.stringify(m),
                    db_id: m.id, // 从数据库加载的消息，其id就是数据库ID
                    temp_id: undefined,
                  }))
                : [];

              console.log('🔍 [resetChatSession] Setting messages:', messages);
              setMessages(messages);
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
      const s = await apiResetSession();
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
  }, [initMessages, storageKey]);


  /* ----------- STOP功能----------------- */
  const controllerRef = useRef<AbortController | null>(null);
  const messagesRef = useRef<Message[]>(messages);
  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  const stop = useCallback(() => {
    controllerRef.current?.abort(); // 使用 AbortController 取消请求
    controllerRef.current = null;
    setStatus("ready"); // 重置状态
    /* 可选：把最后一条没写完的 assistant 消息删掉 */
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
      let currentSession: ChatSession | null = session;
      if (!currentSession?.id) {
        try {
          currentSession = await resetChatSession();
        } catch (e) {
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
          feedback: null,
        }];
      });
      setStatus("submitted");

      try {
        // always use the freshest messages via ref
        const convo = [...messagesRef.current, userMsg];
        const body: any = {
          messages: convo,
          model,
          from_source: getTrafficSource()
        };
        if (currentSession?.id) body.chat_id = currentSession.id;

        // 使用封装好的流式 API
        
        const { controller } = await streamChatCompletionV2(body, {
          onMessageId: (data) => {
            setMessages((prev) => {
              const copy = [...prev];
              if (data.user_message_id) {
                const userMessageIndex = findMessageIndexByTempId(copy, "user");
                if (userMessageIndex >= 0) {
                  copy[userMessageIndex] = {
                    ...copy[userMessageIndex],
                    id: data.user_message_id,
                    temp_id: undefined,
                  };
                }
              }

              if (data.assistant_message_id) {
                const assistantMessageIndex = findMessageIndexByTempId(copy, "assistant");
                if (assistantMessageIndex >= 0) {
                  copy[assistantMessageIndex] = {
                    ...copy[assistantMessageIndex],
                    id: data.assistant_message_id,
                    temp_id: undefined,
                  };
                }
              }

              return copy;
            });
          },

          onSources: (sources) => {
            setMessages((prev) => {
              const copy = [...prev];
              const lastIndex = copy.length - 1;

              copy[lastIndex] = {
                ...copy[lastIndex],
                sources: sources.map((source: any) => ({
                  id: source.id,
                  title: source.title,
                  url: source.url || source.href,
                  description: source.description,
                  snippet: source.snippet || source.content
                }))
              };
              return copy;
            });
          },

          onThoughtStep: (step) => {
            setMessages((prev) => {
              const copy = [...prev];
              const lastIndex = copy.length - 1;
              const currentThoughtSteps = copy[lastIndex].thoughtSteps || [];

              const newThoughtStep = convertThoughtStepFromBackend(step);

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
                showChainOfThought: false,
              };
              return copy;
            });
          },

          onContentChunk: (content) => {
            setStatus("streaming");
            setMessages((prev) => {
              const copy = [...prev];
              const lastIndex = copy.length - 1;

              copy[lastIndex] = {
                ...copy[lastIndex],
                content: content,
              };
              return copy;
            });
          },

          onActionChunk: (content) => {
            setMessages((prev) => {
              const copy = [...prev];
              const lastIndex = copy.length - 1;
              const currentMessage = copy[lastIndex];

              if (currentMessage.role === "assistant") {
                const thoughtSteps = [...(currentMessage.thoughtSteps || [])];
                const lastStepIndex = thoughtSteps.length - 1;

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
                  content: content,
                  timestamp: actionStepIndex >= 0 ? thoughtSteps[actionStepIndex].timestamp : Date.now(),
                  status: 'complete'
                };

                if (actionStepIndex >= 0) {
                  thoughtSteps[actionStepIndex] = actionStep;
                } else {
                  thoughtSteps.push(actionStep);
                }

                copy[lastIndex] = {
                  ...currentMessage,
                  thoughtSteps,
                  hasChainOfThought: true,
                  showChainOfThought: false
                };
              }

              return copy;
            });
          },

          onObservationChunk: (content) => {
            setMessages((prev) => {
              const copy = [...prev];
              const lastIndex = copy.length - 1;
              const currentMessage = copy[lastIndex];

              if (currentMessage.role === "assistant") {
                const thoughtSteps = [...(currentMessage.thoughtSteps || [])];
                const lastStepIndex = thoughtSteps.length - 1;

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
                  content: content,
                  timestamp: observationStepIndex >= 0 ? thoughtSteps[observationStepIndex].timestamp : Date.now(),
                  status: 'complete'
                };

                if (observationStepIndex >= 0) {
                  thoughtSteps[observationStepIndex] = observationStep;
                } else {
                  thoughtSteps.push(observationStep);
                }

                copy[lastIndex] = {
                  ...currentMessage,
                  thoughtSteps,
                  hasChainOfThought: true,
                  showChainOfThought: false
                };
              }

              return copy;
            });
          },

          onComplete: async () => {
            setStatus("ready");

            // 获取推荐问题
            if (currentSession?.id) {
              try {
                const qa = await apiGetSimilarQA(currentSession.id);
                if (qa.length > 0) {
                  setRecommendQa(qa);
                }
              } catch (error) {
                console.error('Failed to fetch recommended questions:', error);
              }
            }
          },

          onError: (error) => {
            setStatus("error");
            throw error;
          },
        });

        // 保存 controller 用于 stop 功能
        controllerRef.current = controller;
        
      } catch (err) {
        setStatus("error");
        throw err;
      }
    },
    [resetChatSession, session, findMessageIndexByTempId, convertThoughtStepFromBackend]
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
              const data = await apiGetRecentMessages(parsed.id);
              const messages: Message[] = Array.isArray(data)? data.map((m: any) => ({
                    id: m.id,
                    role: (m.role as Message['role']) ?? (m.from as Message['role']) ?? "assistant",
                    content: (m.content as string) ?? m.text ?? m.message ?? JSON.stringify(m),
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


              setMessages(() => [...initMessages, ...messages]);
            } catch (e) {
              console.log(e)
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
