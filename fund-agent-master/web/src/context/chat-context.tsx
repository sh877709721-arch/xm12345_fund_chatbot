// src/context/chat-context.tsx
import React, { createContext, useContext } from "react";
import { useQwenChat, type ModelType } from "@/hooks/use-qwen-chat";

import { type Message } from "@/hooks/use-qwen-chat";

interface ChatContextType {
  messages: Message[];
  sendMessage: ReturnType<typeof useQwenChat>["sendMessage"];
  status: ReturnType<typeof useQwenChat>["status"];
  clearMessages: ReturnType<typeof useQwenChat>["clearMessages"];
  stop: ReturnType<typeof useQwenChat>["stop"];
  regenerate: ReturnType<typeof useQwenChat>["regenerate"];
  resetChatSession: ReturnType<typeof useQwenChat>["resetChatSession"];
  updateMessageFeedback: ReturnType<typeof useQwenChat>["updateMessageFeedback"];
  toggleChainOfThought: ReturnType<typeof useQwenChat>["toggleChainOfThought"];
  expandTruncatedMessage: ReturnType<typeof useQwenChat>["expandTruncatedMessage"];
  model: ModelType;
  setModel: (model: ModelType) => void;
  recommendQa: ReturnType<typeof useQwenChat>["recommendQa"]
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

//import.meta.env.VITE_BACKEND_URL +
export function ChatProvider({ children }: { children: React.ReactNode }) {
  const chatHookData = useQwenChat([
    {
      id: 0,
      role: "assistant",
      content:
        "您好！我是你的医保服务小助手，你可以叫我小E。我熟悉医保各类政策法规、办事流程和便民服务信息，随时准备为你提供准确、及时的帮助。",
    },
  ]);

  return (
    <ChatContext.Provider value={chatHookData}>{children}</ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
}
