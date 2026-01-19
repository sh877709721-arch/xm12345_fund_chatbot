import { AppHeader } from "@/components/app/app-header";
import { Outlet } from "react-router-dom";
import { ChatProvider } from "@/context/chat-context";
export function AppLayout() {
  return (
    <ChatProvider>
      <div className="flex flex-col h-screen">
        <AppHeader />
        <div className="flex flex-1 flex-col">
          <div className="@container/main flex flex-1 flex-col gap-1 w-full">
            <div className="h-full flex flex-col gap-1 py-1.5 px-2 md:gap-2 md:py-2">
              <Outlet />
            </div>
          </div>
        </div>
      </div>
    </ChatProvider>
  );
}
