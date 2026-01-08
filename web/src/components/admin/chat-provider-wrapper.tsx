import { ChatProvider } from "@/context/chat-context";
import { Outlet } from "react-router-dom";

/**
 * ChatProvider 包装器
 *
 * 为需要使用 useChat hook 的页面提供 ChatProvider
 * 不包含任何布局，仅提供 Context
 *
 * 用于在 DashboardLayout 中渲染 bot-chat 页面
 */
export function ChatProviderWrapper() {
  return (
    <ChatProvider>
      <Outlet />
    </ChatProvider>
  );
}
