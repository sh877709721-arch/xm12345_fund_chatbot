import { useChat } from "@/context/chat-context";
import { RotateCcwIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Outlet } from "react-router-dom";
import { ChatProvider } from "@/context/chat-context";

export function BotHeader() {
  const { resetChatSession } = useChat();
  return (
    <header className="bg-background dark:bg-background sticky top-0 z-50 flex h-12 shrink-0 items-center gap-2 border-b ">
      <div className="flex w-full items-center gap-1 px-4 lg:gap-2 lg:px-6">
        <div className="ml-auto flex items-center gap-2">
          <Button variant="ghost" onClick={() => resetChatSession(true)}>
            <RotateCcwIcon className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </header>
  );
}

export function BotLayout() {
  return (
    <ChatProvider>
      <div className="flex flex-col h-full">
        <BotHeader />
        <div className="flex-1 flex flex-col bg-background">
          <Outlet />
        </div>
      </div>
    </ChatProvider>
  );
}
