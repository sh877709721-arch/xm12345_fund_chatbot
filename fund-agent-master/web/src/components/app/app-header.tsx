
import { ThemeToggleSimple } from "@/components/theme-toggle-simple";
import { useChat } from "@/context/chat-context";

import { RotateCcwIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
// import {
//   Select,
//   SelectContent,
//   SelectItem,
//   SelectTrigger,
//   SelectValue,
// } from "@/components/ui/select";
export function AppHeader() {
  //const { model, setModel, resetChatSession } = useChat();
  const { resetChatSession } = useChat();
  return (
    <header className="bg-background dark:bg-background sticky top-0 z-50 flex h-10 shrink-0 items-center gap-2 border-b transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-(--header-height)">
      <div className="flex w-full items-center gap-1 px-4 lg:gap-2 lg:px-6">
        <h1 className="text-base font-medium">智能客服</h1>

        {/* 模型选择器 - 暂时隐藏 */}
        {/* <div className="flex items-center gap-2 ml-2">
          <span className="text-xs text-muted-foreground">模型:</span>
          <Select value={model} onValueChange={(value: "default" | "boost") => setModel(value)}>
            <SelectTrigger size="sm" className="w-24">
              <SelectValue placeholder="选择模型">
                {model === "default" ? "默认" : "增强版"}
              </SelectValue>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="default">默认</SelectItem>
              <SelectItem value="boost">增强版</SelectItem>
            </SelectContent>
          </Select>
        </div> */}

        <div className="ml-auto flex items-center gap-2">
          <ThemeToggleSimple />

          <Button variant="ghost" onClick={() => resetChatSession(true)}>
            <RotateCcwIcon className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </header>
  );
}
