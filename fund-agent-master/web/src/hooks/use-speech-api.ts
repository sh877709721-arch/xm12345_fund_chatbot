/**
 * 讯飞语音识别 Hook
 * 提供录音和实时语音转文字功能
 * 使用 Web Audio API 直接获取 PCM 数据，避免格式转换
 */
import { useCallback, useEffect, useRef, useState } from "react";
import {
  SpeechWebSocketClient,
  arrayBufferToBase64,
  supportsGetUserMedia,
  type WebSocketOptions,
} from "@/utils/request/speech";


// ============================================================================
// 音频处理工具
// ============================================================================

/**
 * 将 Float32 音频数据转换为 Int16 PCM 格式
 * @param float32Array Float32Array (-1.0 到 1.0)
 * @returns Int16Array (-32768 到 32767)
 */
function float32ToInt16(float32Array: Float32Array): Int16Array {
  const int16Array = new Int16Array(float32Array.length);
  for (let i = 0; i < float32Array.length; i++) {
    const sample = Math.max(-1, Math.min(1, float32Array[i]));
    int16Array[i] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
  }
  return int16Array;
}

// ============================================================================
// 类型定义
// ============================================================================

/** 语音识别状态 */
export type SpeechStatus =
  | "idle"      // 空闲
  | "connecting"; // 连接中

/** 语音识别模式 */
export type SpeechMode = "xfyun" | "browser";

/** Hook 配置选项 */
export interface UseSpeechApiOptions {
  /** 语音识别模式 */
  mode?: SpeechMode;
  /** WebSocket 配置（仅 xfyun 模式） */
  websocketOptions?: WebSocketOptions;
  /** 识别结果回调 */
  onResult?: (text: string, isFinal: boolean) => void;
  /** 错误回调 */
  onError?: (error: string) => void;
  /** 连接状态变化回调 */
  onStatusChange?: (status: SpeechStatus) => void;
}

/** Hook 返回值 */
export interface UseSpeechApiReturn {
  /** 当前状态 */
  status: SpeechStatus;
  /** 是否正在录音 */
  isRecording: boolean;
  /** 是否已连接（WebSocket 模式） */
  isConnected: boolean;
  /** 当前识别的文本 */
  transcript: string;
  /** 错误信息 */
  error: string | null;
  /** 开始录音 */
  startRecording: () => Promise<void>;
  /** 停止录音 */
  stopRecording: () => void;
  /** 清除错误 */
  clearError: () => void;
  /** 重置状态 */
  reset: () => void;
}

// ============================================================================
// Hook 实现
// ============================================================================

/**
 * 讯飞语音识别 Hook
 *
 * @example
 * ```tsx
 * const { isRecording, transcript, startRecording, stopRecording } = useSpeechApi({
 *   mode: "xfyun",
 *   onResult: (text, isFinal) => {
 *     if (isFinal) {
 *       console.log("最终结果:", text);
 *     }
 *   }
 * });
 * ```
 */
export function useSpeechApi(
  options: UseSpeechApiOptions = {}
): UseSpeechApiReturn {
  const {
    mode = "xfyun",
    websocketOptions = {},
    onResult,
    onError,
    onStatusChange,
  } = options;

  // 状态
  const [status, setStatus] = useState<SpeechStatus>("idle");
  const [transcript, setTranscript] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  // Refs
  const wsClientRef = useRef<SpeechWebSocketClient | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const finalTranscriptRef = useRef<string>("");
  const isRecordingRef = useRef<boolean>(false);

  // 清除错误
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // 重置状态
  const reset = useCallback(() => {
    setTranscript("");
    finalTranscriptRef.current = "";
    clearError();
    setIsConnected(false);
  }, [clearError]);

  // 更新状态并通知
  const updateStatus = useCallback(
    (newStatus: SpeechStatus) => {
      setStatus(newStatus);
      onStatusChange?.(newStatus);
    },
    [onStatusChange]
  );

  // 初始化 WebSocket 客户端（xfyun 模式）
  const initWebSocket = useCallback(async () => {
    if (mode !== "xfyun") return;

    try {
      updateStatus("connecting");

      wsClientRef.current = new SpeechWebSocketClient({
        ...websocketOptions,
        onConnected: () => {
          console.log("[SpeechAPI] WebSocket 已连接");
          setIsConnected(true);
          updateStatus("idle");
        },
        onResult: (text, isFinal) => {
          console.log("[SpeechAPI] 识别结果:", text, "是否最终:", isFinal);

          if (isFinal) {
            // 最终结果，累加到完整文本
            finalTranscriptRef.current += (finalTranscriptRef.current ? " " : "") + text;
            setTranscript(finalTranscriptRef.current);
            onResult?.(finalTranscriptRef.current, true);
          } else {
            // 中间结果，临时显示
            const tempText = finalTranscriptRef.current + (finalTranscriptRef.current ? " " : "") + text;
            setTranscript(tempText);
            onResult?.(tempText, false);
          }
        },
        onError: (errorMsg) => {
          console.error("[SpeechAPI] 识别错误:", errorMsg);
          setError(errorMsg);
          onError?.(errorMsg);
          stopRecording();
        },
        onClosed: () => {
          console.log("[SpeechAPI] WebSocket 已关闭");
          setIsConnected(false);
          updateStatus("idle");
        },
      });

      await wsClientRef.current.connect();
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "连接失败";
      setError(errorMsg);
      onError?.(errorMsg);
      updateStatus("idle");
      throw err;
    }
  }, [mode, websocketOptions, onResult, onError, onStatusChange, updateStatus]);

  // 发送音频数据到 WebSocket
  const sendAudioToWebSocket = useCallback(async (pcmData: ArrayBuffer, isLast = false) => {
    if (mode !== "xfyun" || !wsClientRef.current) return;

    try {
      const base64 = arrayBufferToBase64(pcmData);
      wsClientRef.current.sendAudio(base64, isLast);
    } catch (err) {
      console.error("[SpeechAPI] 发送音频失败:", err);
      const errorMsg = err instanceof Error ? err.message : "发送音频失败";
      setError(errorMsg);
      onError?.(errorMsg);
    }
  }, [mode, onError]);

  // 开始录音
  const startRecording = useCallback(async () => {
    // 检查浏览器支持
    if (!supportsGetUserMedia()) {
      setError("浏览器不支持 getUserMedia");
      return;
    }

    try {
      // 获取麦克风权限
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,      // 讯飞推荐采样率
          channelCount: 1,        // 单声道
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      streamRef.current = stream;

      // xfyun 模式需要先连接 WebSocket
      if (mode === "xfyun" && !wsClientRef.current?.isConnected) {
        await initWebSocket();
      }

      // 初始化 AudioContext
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      const audioContext = new AudioContextClass({ sampleRate: 16000 });
      audioContextRef.current = audioContext;

      // 创建音频源
      const source = audioContext.createMediaStreamSource(stream);
      sourceRef.current = source;

      // 创建 ScriptProcessorNode 来获取原始 PCM 数据
      const bufferSize = 4096;
      const processor = audioContext.createScriptProcessor(bufferSize, 1, 1);
      processorRef.current = processor;

      let audioBuffer = new Int16Array(0);
      const TARGET_FRAME_SIZE = 1280; // 讯飞推荐帧大小：640 samples @ 16kHz = 1280 bytes

      processor.onaudioprocess = async (e) => {
        if (!isRecordingRef.current) return;

        // 获取 Float32 音频数据
        const inputData = e.inputBuffer.getChannelData(0);

        // 转换为 Int16 PCM
        const int16Data = float32ToInt16(inputData);

        // 缓存音频数据直到达到目标帧大小
        const tmpBuffer = new Int16Array(audioBuffer.length + int16Data.length);
        tmpBuffer.set(audioBuffer);
        tmpBuffer.set(int16Data, audioBuffer.length);
        audioBuffer = tmpBuffer;

        // 按帧大小发送数据
        while (audioBuffer.length >= TARGET_FRAME_SIZE) {
          const frame = audioBuffer.slice(0, TARGET_FRAME_SIZE);
          await sendAudioToWebSocket(frame.buffer);

          // 移除已发送的数据
          const remaining = audioBuffer.slice(TARGET_FRAME_SIZE);
          audioBuffer = remaining;
        }
      };

      // 连接音频节点
      source.connect(processor);
      processor.connect(audioContext.destination);

      isRecordingRef.current = true;
      console.log("[SpeechAPI] PCM 录音已开始");

    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "启动录音失败";
      setError(errorMsg);
      onError?.(errorMsg);
      throw err;
    }
  }, [mode, initWebSocket, sendAudioToWebSocket, onError]);

  // 停止录音
  const stopRecording = useCallback(() => {
    if (!isRecordingRef.current) return;

    console.log("[SpeechAPI] 停止录音");
    isRecordingRef.current = false;

    // 发送最后一帧（空数据）
    if (mode === "xfyun" && wsClientRef.current) {
      sendAudioToWebSocket(new ArrayBuffer(0), true);
    }

    // 关闭音频处理
    if (sourceRef.current) {
      sourceRef.current.disconnect();
      sourceRef.current = null;
    }

    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }

    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    // 停止麦克风流
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    // xfyun 模式：关闭 WebSocket
    if (mode === "xfyun" && wsClientRef.current) {
      wsClientRef.current.close();
      wsClientRef.current = null;
      setIsConnected(false);
    }
  }, [mode, sendAudioToWebSocket]);

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      stopRecording();
    };
  }, [stopRecording]);

  return {
    status,
    isRecording: isRecordingRef.current || false,
    isConnected,
    transcript,
    error,
    startRecording,
    stopRecording,
    clearError,
    reset,
  };
}
