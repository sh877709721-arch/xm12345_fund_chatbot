import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
} from "@/components/ui/drawer";
import * as React from "react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";

export function ContentPreview({ content }: { content: string }) {
  const [open, setOpen] = React.useState(false);
  return (
    <>
      {/* 单行省略展示 */}
      {/* <span
        className="inline-block max-w-full cursor-pointer hover:underline truncate"
        onClick={() => setOpen(true)}
        title={content}>
        {content}
      </span> */}

      <div className="text-xs text-muted-foreground">
        <Tooltip>
          <TooltipTrigger asChild>
            <a className="text-md line-clamp-3 leading-relaxed whitespace-normal break-words cursor-help text-xs text-muted-foreground">
              {content}
            </a>
          </TooltipTrigger>
          <TooltipContent side="top" className="max-w-sm">
            <span className="text-xl leading-relaxed whitespace-pre-wrap">
              {content}
            </span>
          </TooltipContent>
        </Tooltip>
      </div>

      {/* 点击查看完整内容 */}
      <Drawer direction={"right"} open={open} onOpenChange={setOpen}>
        <DrawerContent>
          <DrawerHeader>
            <DrawerTitle>内容详情</DrawerTitle>
          </DrawerHeader>
          <div className="flex-1 overflow-y-auto p-4">
            <pre className="whitespace-pre-wrap break-words font-sans">
              {content}
            </pre>
          </div>
          <DrawerFooter>
            <DrawerClose asChild>
              <Button variant="outline">关闭</Button>
            </DrawerClose>
          </DrawerFooter>
        </DrawerContent>
      </Drawer>
    </>
  );
}
