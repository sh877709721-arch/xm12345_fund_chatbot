/**
 * 讯飞语音识别 API 请求封装
 * 提供 HTTP 文件上传和 WebSocket 流式识别两种方式
 */
import instance from "./instance";

// ============================================================================
// 类型定义
// ============================================================================

/** 语音识别响应 */
export interface SpeechRecognitionResponse {
  code: number;
  message: string;
  data: {
    text: string;
  } | null;
}

/** WebSocket 消息类型 */
export type WSMessageType = "connected" | "result" | "error" | "close";

/** WebSocket 消息基础结构 */
export interface WSMessageBase {
  type: WSMessageType;
}

/** WebSocket 连接成功消息 */
export interface WSConnectedMessage extends WSMessageBase {
  type: "connected";
  message: string;
}

/** WebSocket 识别结果消息 */
export interface WSResultMessage extends WSMessageBase {
  type: "result";
  text: string;
  is_final: boolean;
  status: number; // 0: 首帧, 1: 中间, 2: 结束
  sid: string;
}

/** WebSocket 错误消息 */
export interface WSErrorMessage extends WSMessageBase {
  type: "error";
  code?: number;
  message: string;
}

/** WebSocket 所有消息类型 */
export type WSMessage = WSConnectedMessage | WSResultMessage | WSErrorMessage;

/** WebSocket 配置选项 */
export interface WebSocketOptions {
  /** WebSocket 服务器地址 */
  url?: string;
  /** 连接建立回调 */
  onConnected?: () => void;
  /** 接收识别结果回调 */
  onResult?: (text: string, isFinal: boolean) => void;
  /** 接收错误回调 */
  onError?: (error: string) => void;
  /** 连接关闭回调 */
  onClosed?: () => void;
}

// ============================================================================
// HTTP 文件上传识别
// ============================================================================

/**
 * 上传音频文件进行语音识别
 * @param audioFile 音频文件
 * @returns 识别结果
 */
export async function recognizeAudioFile(audioFile: File): Promise<string> {
  const formData = new FormData();
  formData.append("audio_file", audioFile);

  // axios 拦截器已配置返回 response.data
  const response = await instance.post<SpeechRecognitionResponse>(
    "/v1/speech/recognize",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );

  // instance 拦截器返回 response.data，所以 response 就是 SpeechRecognitionResponse
  const data = response as unknown as SpeechRecognitionResponse;

  if (data.code !== 200) {
    throw new Error(data.message || "语音识别失败");
  }

  return data.data?.text || "";
}

/**
 * 检查语音识别服务健康状态
 */
export async function checkSpeechHealth(): Promise<{
  status: string;
  message: string;
  configured: boolean;
}> {
  return await instance.get("/v1/speech/health");
}

/**
 * 获取语音识别配置信息
 */
export async function getSpeechConfig(): Promise<{
  app_id: string;
  configured: boolean;
  language: string;
  accent: string;
  domain: string;
}> {
  return await instance.get("/v1/speech/config/info");
}

// ============================================================================
// WebSocket 流式识别
// ============================================================================

/**
 * 讯飞语音识别 WebSocket 客户端
 */
export class SpeechWebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;

  // 回调函数
  private onConnectedCallback: () => void;
  private onResultCallback: (text: string, isFinal: boolean) => void;
  private onErrorCallback: (error: string) => void;
  private onClosedCallback: () => void;

  constructor(options: WebSocketOptions = {}) {
    const baseURL = import.meta.env.VITE_BACKEND_URL || "";
    // 将 http/https 替换为 ws/wss
    const wsUrl = baseURL.replace(/^http/, "ws");
    this.url = options.url || `${wsUrl}/v1/speech/stream`;

    this.onConnectedCallback = options.onConnected || (() => {});
    this.onResultCallback = options.onResult || (() => {});
    this.onErrorCallback = options.onError || (() => {});
    this.onClosedCallback = options.onClosed || (() => {});
  }

  /**
   * 连接 WebSocket
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log("[SpeechWS] 连接已建立");
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WSMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error("[SpeechWS] 消息解析失败:", error);
          }
        };

        this.ws.onerror = (event) => {
          console.error("[SpeechWS] WebSocket 错误:", event);
          reject(new Error("WebSocket 连接失败"));
        };

        this.ws.onclose = () => {
          console.log("[SpeechWS] 连接已关闭");
          this.onClosedCallback();
        };

        // 等待连接建立
        this.ws.addEventListener("open", () => {
          resolve();
        }, { once: true });
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * 处理接收到的消息
   */
  private handleMessage(message: WSMessage): void {
    switch (message.type) {
      case "connected":
        console.log("[SpeechWS]", (message as WSConnectedMessage).message);
        this.onConnectedCallback();
        break;

      case "result":
        this.onResultCallback(
          (message as WSResultMessage).text,
          (message as WSResultMessage).is_final
        );
        break;

      case "error":
        this.onErrorCallback((message as WSErrorMessage).message);
        break;

      default:
        console.warn("[SpeechWS] 未知消息类型:", message);
    }
  }

  /**
   * 发送音频数据
   * @param base64Audio base64 编码的音频数据
   * @param isLast 是否是最后一帧
   */
  sendAudio(base64Audio: string, isLast = false): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error("WebSocket 未连接");
    }

    const message = {
      type: "audio",
      data: base64Audio,
      is_last: isLast,
    };

    this.ws.send(JSON.stringify(message));
  }

  /**
   * 关闭连接
   */
  close(): void {
    if (this.ws) {
      // 发送关闭消息
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: "close" }));
      }
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * 获取连接状态
   */
  get readyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }

  /**
   * 是否已连接
   */
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// ============================================================================
// 音频处理工具
// ============================================================================

/**
 * 将 Blob 转换为 Base64
 */
export function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const result = reader.result as string;
      // 移除 data:image/wav;base64, 前缀
      const base64 = result.split(",")[1];
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

/**
 * 将 ArrayBuffer 转换为 Base64
 */
export function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

/**
 * 检查浏览器是否支持 MediaRecorder
 */
export function supportsMediaRecorder(): boolean {
  return typeof MediaRecorder !== "undefined";
}

/**
 * 检查浏览器是否支持 getUserMedia
 */
export function supportsGetUserMedia(): boolean {
  return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
}
