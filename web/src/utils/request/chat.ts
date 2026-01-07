import instance from "./instance";
import { toast } from "sonner";

// ==================== 类型定义 ====================

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

// 消息类型
export type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
  db_id?: number | null;
  temp_id?: number;
  feedback?: 'good' | 'medium' | 'bad' | null;
  thoughtSteps?: ThoughtStep[];
  showChainOfThought?: boolean;
  hasChainOfThought?: boolean;
  sources?: Source[];
};

// 会话类型
export type ChatSession = {
  id: string;
  status?: string;
  title?: string | null;
  user_id?: string;
  created_at?: string;
  updated_at?: string;
};

// 推荐问题类型
export type RecommendQA = {
  id: number;
  question: string;
};

// ==================== 请求类型 ====================

export interface ChatCompletionRequest {
  messages: Array<{ role: string; content: string }>;
  model?: string;
  chat_id?: string;
  stream?: boolean;
  from_source?: string; // 流量来源参数
}

export interface ChatRefRequest {
  message_id: number;
  refer_id: string;
}

// ==================== 流式请求回调类型 ====================

export interface StreamChatCallbacks {
  onComplete?: () => void;
  onError?: (error: Error) => void;
  onMessageId?: (data: { user_message_id: number; assistant_message_id: number }) => void;
  onSources?: (sources: Source[]) => void;
  onThoughtStep?: (step: ThoughtStep) => void;
  onContentChunk?: (content: string) => void;
  onActionChunk?: (content: string) => void;
  onObservationChunk?: (content: string) => void;
}

// ==================== 普通 API 函数 ====================

/**
 * 重置聊天会话
 */
export async function resetChatSession(): Promise<ChatSession> {
  try {
    const response = await instance.post("/v1/chat/reset-chat-session") as unknown as ChatSession;
    return response;
  } catch (error: any) {
    toast.error(error.message || "重置会话失败");
    throw error;
  }
}

/**
 * 获取历史消息
 * 注意：由于 axios 响应拦截器已返回 response.data，
 * 且后端返回结构为 {code, message, data: Message[]}，
 * 所以这里再次访问 .data 得到的是 Message[] 数组
 */
export async function getRecentMessages(chatId: string): Promise<Message[]> {
  try {
    const response = await instance.post(
      `/v1/chat/get_resent_messages?chat_id=${chatId}`,""
    );

    return response.data;
  } catch (error: any) {
    toast.error(error.message || "获取历史消息失败");
    throw error;
  }
}

/**
 * 获取推荐问题
 */
export async function getSimilarQA(chatId: string): Promise<RecommendQA[]> {
  try {
    const response = await instance.post(
      `/v1/chat/get_similary_qa?chat_id=${chatId}`,
      ""
    ) as unknown as RecommendQA[];
    return response;
  } catch (error: any) {
    console.error("获取推荐问题失败:", error);
    // 推荐问题失败不影响主流程，不弹 toast
    return [];
  }
}

// ==================== 流式 API 函数 ====================

/**
 * 流式聊天完成请求（使用 Axios）
 * 完全封装 SSE 流处理逻辑
 * 注意：使用 XMLHttpRequest 实现真正的流式读取
 */
export async function streamChatCompletionV2(
  request: ChatCompletionRequest,
  callbacks: StreamChatCallbacks
): Promise<{
  controller: AbortController;
}> {
  const controller = new AbortController();
  let buffer = "";
  let lastPosition = 0;
  let isComplete = false;

  return new Promise((resolve, reject) => {
    // 获取配置的 baseURL 和 headers
    const token = localStorage.getItem("access_token");
    const baseURL = import.meta.env.VITE_BACKEND_URL || "";
    const url = `${baseURL}/v1/chat/completions`;

    // 创建 XMLHttpRequest
    const xhr = new XMLHttpRequest();

    // 监听 abort 信号
    controller.signal.addEventListener('abort', () => {
      xhr.abort();
      reject(new Error('Request aborted'));
    });

    // 监听 readyState 变化
    xhr.onreadystatechange = () => {
      if (xhr.readyState >= XMLHttpRequest.LOADING) {
        const responseText = xhr.responseText;

        // 提取新增的部分
        const newText = responseText.slice(lastPosition);
        lastPosition = responseText.length;

        // 处理新增的数据
        buffer += newText;
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trim = line.trim();
          if (!trim.startsWith("data:")) continue;

          const data = trim.slice(5).trim();
          if (data === "[DONE]") {
            if (!isComplete) {
              isComplete = true;
              callbacks.onComplete?.();
            }
            return;
          }

          try {
            const chunk: any = JSON.parse(data);

            // 根据不同的 chunk 类型调用对应的 callback
            if (chunk.object === "chat.completion.message_id" && chunk.message_id) {
              callbacks.onMessageId?.(chunk.message_id);
            } else if (chunk.object === "chat.completion.sources" && chunk.sources) {
              callbacks.onSources?.(chunk.sources);
            } else if (chunk.object === "chat.completion.thought_step" && chunk.thought_step) {
              callbacks.onThoughtStep?.(chunk.thought_step);
            } else if (chunk.object === "chat.completion.chunk") {
              const delta = chunk.choices?.[0]?.delta?.content;
              if (delta) callbacks.onContentChunk?.(delta);
            } else if (chunk.object === "chat.completion.action") {
              const delta = chunk.choices?.[0]?.delta?.content;
              if (delta) callbacks.onActionChunk?.(delta);
            } else if (chunk.object === "chat.completion.observation") {
              const delta = chunk.choices?.[0]?.delta?.content;
              if (delta) callbacks.onObservationChunk?.(delta);
            }
          } catch (parseError) {
            // 忽略解析失败的 chunk
            console.warn("Failed to parse chunk:", parseError);
          }
        }
      }

      // 请求完成
      if (xhr.readyState === XMLHttpRequest.DONE) {
        if (xhr.status >= 200 && xhr.status < 300) {
          if (!isComplete) {
            isComplete = true;
            callbacks.onComplete?.();
          }
          resolve({ controller });
        } else {
          const error = new Error(`Request failed with status ${xhr.status}`);
          callbacks.onError?.(error);
          reject(error);
        }
      }
    };

    // 错误处理
    xhr.onerror = () => {
      const error = new Error('Network error');
      callbacks.onError?.(error);
      reject(error);
    };

    // 设置请求头并发送
    xhr.open('POST', url);
    xhr.setRequestHeader('Content-Type', 'application/json');
    if (token) {
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    }
    xhr.send(JSON.stringify(request));
  });
}

/**
 * 流式聊天完成请求（使用 Fetch）
 * 完全封装 SSE 流处理逻辑
 */
export async function streamChatCompletion(
  request: ChatCompletionRequest,
  callbacks: StreamChatCallbacks
): Promise<{
  reader: ReadableStreamDefaultReader<Uint8Array>;
  controller: AbortController;
}> {
  const controller = new AbortController();
  const token = localStorage.getItem("access_token");

  try {
    const response = await fetch("/znkfzs/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      body: JSON.stringify(request),
      signal: controller.signal,
    });

    if (!response.ok || !response.body) {
      throw new Error(`Network error: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    // 启动流处理（异步，不阻塞）
    processStream(reader, decoder, buffer, callbacks);

    return { reader, controller };
  } catch (error) {
    callbacks.onError?.(error as Error);
    throw error;
  }
}

/**
 * 内部函数：处理 SSE 流
 */
async function processStream(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  decoder: TextDecoder,
  buffer: string,
  callbacks: StreamChatCallbacks
) {
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop()!;

      for (const line of lines) {
        const trim = line.trim();
        if (!trim.startsWith("data:")) continue;

        const data = trim.slice(5).trim();
        if (data === "[DONE]") {
          callbacks.onComplete?.();
          return;
        }

        try {
          const chunk: any = JSON.parse(data);

          // 根据不同的 chunk 类型调用对应的 callback
          if (chunk.object === "chat.completion.message_id" && chunk.message_id) {
            callbacks.onMessageId?.(chunk.message_id);
          } else if (chunk.object === "chat.completion.sources" && chunk.sources) {
            callbacks.onSources?.(chunk.sources);
          } else if (chunk.object === "chat.completion.thought_step" && chunk.thought_step) {
            callbacks.onThoughtStep?.(chunk.thought_step);
          } else if (chunk.object === "chat.completion.chunk") {
            const delta = chunk.choices?.[0]?.delta?.content;
            if (delta) callbacks.onContentChunk?.(delta);
          } else if (chunk.object === "chat.completion.action") {
            const delta = chunk.choices?.[0]?.delta?.content;
            if (delta) callbacks.onActionChunk?.(delta);
          } else if (chunk.object === "chat.completion.observation") {
            const delta = chunk.choices?.[0]?.delta?.content;
            if (delta) callbacks.onObservationChunk?.(delta);
          }
        } catch (parseError) {
          // 忽略解析失败的 chunk
          console.warn("Failed to parse chunk:", parseError);
        }
      }
    }
  } catch (error) {
    callbacks.onError?.(error as Error);
  }
}

// ==================== 旧 API 函数（待删除） ====================

// 连接类型枚举
export interface QueryRequest {
  model: string;
  messages: Array<{ role: string; content: string }>;
  stream?: boolean;
  max_tokens?: number;
  temperature?: number;
}

export interface AssistantResponse {
  from_: string;
  versions?: Array<{ id: string; content: string }>;
  sources?: Array<{ href: string; title: string }>;
  tools?: Array<{
    name: string;
    description: string;
    status: string;
    parameters: any;
    result: string;
    error: string;
  }>;
  reasoning?: { content: string; duration: number };
  avatar: string;
  name: string;
}

// 测试数据连接
export async function ChatQuery(query: QueryRequest) {
  try {
    const resp = await instance.post<AssistantResponse>(
      "/v1/chat/completions",
      query
    );
    console.log(resp);
    // Return the actual data payload to the caller
    return resp.data;
  } catch (error: any) {
    toast.error(error.message || "Failed to test connection");
    throw error;
  }
}

export async function GetReference(query: ChatRefRequest) {
  try {
    const resp = await instance.post(
      "/v1/chat/get_reference_content",
      query
    );
    return resp.data;
  } catch (error: any) {
    toast.error(error.message || "无法获取来源");
    throw error;
  }
}
