import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { cva, type VariantProps } from "class-variance-authority";
import type { ComponentProps, HTMLAttributes } from "react";
import { MessageActions } from "./message-actions";
import { MarkdownContent } from "./markdown-content";
//import { ChainOfThoughtAuto } from "./chain-of-thought";
import { RecommendQuestions } from "./recommend-questions";
import type { RecommendQA, Message as MessageType, Source } from "@/hooks/use-qwen-chat";

export type MessageProps = HTMLAttributes<HTMLDivElement> & {
  from: MessageType["role"];
  messageId?: number;
  messageDbId?: number | null;  // 数据库中的真实ID，可能为null
  feedback?: 'good' | 'medium' | 'bad' | null;
  onFeedbackChange?: (messageId: number, feedback: 'good' | 'medium' | 'bad' | null) => void;
  onToggleChainOfThought?: (messageId: number) => void;
  // 新增 Chain-of-Thought 支持
  thoughtSteps?: any[];  // 使用 any 类型避免循环导入
  showChainOfThought?: boolean;
  hasChainOfThought?: boolean;
  chatStatus?: string;
  isStreaming?: boolean;
  recommendQa?: RecommendQA[] | null;
  isLast?: boolean;
  sources?: Source[];
};

export const Message = ({
  className,
  from,
  messageId,
  messageDbId,
  feedback,
  onFeedbackChange,
  onToggleChainOfThought,
  thoughtSteps,
  showChainOfThought = false,
  hasChainOfThought = false,
  chatStatus,
  isStreaming = false,
  recommendQa,
  isLast = false,
  sources,
  children,
  ...props
}: MessageProps) => (
  <div
    className={cn(
      "group flex w-full items-start gap-2 py-4",
      from === "user"
        ? "justify-end"
        : "justify-start",
      className
    )}
    {...props}
  >
    {/* Assistant 头像 */}
    {from === "assistant" && (
      <MessageAvatar src="./assets/12345.png" name="AI助手" />
    )}

    {/* 消息内容 */}
    <div className={cn(
      "flex flex-col max-w-[90%]",
      from === "user" && "items-end"
    )}>
      {/* Chain-of-Thought - 只在助手消息上显示 */}
      {/* {from === "assistant" && hasChainOfThought && thoughtSteps && thoughtSteps.length > 0 && (
        <ChainOfThoughtAuto
          thoughtSteps={thoughtSteps}
          defaultOpen={showChainOfThought}
          isStreaming={isStreaming}
          className="mb-3"
        />
      )} */}

      <div className={cn(
        "rounded-lg inline-block w-full",
        from === "user"
          ? "bg-primary text-primary-foreground"
          : "bg-secondary text-foreground"
      )}>
        {/* 等待返回中动画或消息内容 */}
        {isLast && (from === "assistant" && chatStatus === "submitted") ? (
          from === "assistant" && chatStatus === 'submitted' ? (
            <div className="flex items-center gap-2 px-3 py-2 rounded-md bg-muted/50 border border-border/50">
              <div className="flex items-center gap-1">
                <span className="inline-block w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                <span className="inline-block w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                <span className="inline-block w-2 h-2 bg-primary rounded-full animate-bounce"></span>
              </div>
              <p className="text-xs text-muted-foreground">等待返回中...</p>
            </div>
          ) : (
            children
          )
        ) : (
          children
        )}
      </div>


      {from === "assistant" &&
        ((messageId !== undefined)) &&
        (onFeedbackChange || onToggleChainOfThought) && (
          <div className="mt-2 space-y-2">
            <div className="flex items-center gap-2 px-3 py-2 rounded-md bg-muted/50 border border-border/50">
              <p className="text-xs text-muted-foreground leading-relaxed">
                以上信息仅供参考，医保政策解读及业务办理以现行政策和厦门市医保机构最终审核结果为准，试运行期间，若有不明请至窗口或拨打12345人工服务。
              </p>
            </div>
            <MessageActions
              messageId={messageId}
              feedback={feedback}
              onFeedbackChange={onFeedbackChange}
              onToggleChainOfThought={onToggleChainOfThought}
              showChainOfThought={showChainOfThought}
            />
          </div>
        )}


      {/* 消息操作 - 只在助手消息上显示 */}




      {from === "assistant" &&
        (isStreaming == false) &&
        (isLast == true) &&
        recommendQa && (
          <RecommendQuestions questions={recommendQa} />
        )}

    </div>
  </div>
);

const messageContentVariants = cva(
  "flex flex-col gap-1 overflow-hidden text-sm",
  {
    variants: {
      variant: {
        contained: [],
        flat: [],
      },
    },
    defaultVariants: {
      variant: "contained",
    },
  }
);

export type MessageContentProps = HTMLAttributes<HTMLDivElement> &
  VariantProps<typeof messageContentVariants>;

export const MessageContent = ({
  children,
  className,
  variant,
  messageId,
  isUser = false,
  sources,
  ...props
}: MessageContentProps & { messageId?: number, isUser?: boolean; sources?: Source[] }) => (
  <div
    className={cn("px-4 py-3", messageContentVariants({ variant, className }))}
    {...props}
  >
    {typeof children === 'string' ? (
      <MarkdownContent messageId={messageId} content={children} isUser={isUser} sources={sources} />
    ) : (
      children
    )}
  </div>
);

export type MessageAvatarProps = ComponentProps<typeof Avatar> & {
  src: string;
  name?: string;
};

export const MessageAvatar = ({
  src,
  name,
  className,
  ...props
}: MessageAvatarProps) => (
  <Avatar className={cn("size-8 ring-1 ring-border", className)} {...props}>
    <AvatarImage alt="" className="mt-0 mb-0" src={src} />
    <AvatarFallback>{name?.slice(0, 2) || "ME"}</AvatarFallback>
  </Avatar>
);
