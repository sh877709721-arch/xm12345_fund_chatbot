"use client";

import { useControllableState } from "@radix-ui/react-use-controllable-state";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { cn } from "@/lib/utils";
import {
  BrainIcon,
  ChevronDownIcon,
  DotIcon,
  SearchIcon,
  EyeIcon,
  CheckCircleIcon,
  type LucideIcon,
} from "lucide-react";
import type { ComponentProps } from "react";
import { createContext, memo, useContext, useMemo } from "react";
import type { ThoughtStep } from "@/hooks/use-qwen-chat";
import { MarkdownContent } from "./markdown-content";

type ChainOfThoughtContextValue = {
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
};

const ChainOfThoughtContext = createContext<ChainOfThoughtContextValue | null>(
  null
);

const useChainOfThought = () => {
  const context = useContext(ChainOfThoughtContext);
  if (!context) {
    throw new Error(
      "ChainOfThought components must be used within ChainOfThought"
    );
  }
  return context;
};

export type ChainOfThoughtProps = ComponentProps<"div"> & {
  open?: boolean;
  defaultOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
};

export const ChainOfThought = memo(
  ({
    className,
    open,
    defaultOpen = false,
    onOpenChange,
    children,
    ...props
  }: ChainOfThoughtProps) => {
    const [isOpen, setIsOpen] = useControllableState({
      prop: open,
      defaultProp: defaultOpen,
      onChange: onOpenChange,
    });

    const chainOfThoughtContext = useMemo(
      () => ({ isOpen, setIsOpen }),
      [isOpen, setIsOpen]
    );

    return (
      <ChainOfThoughtContext.Provider value={chainOfThoughtContext}>
        <div
          className={cn("not-prose max-w-prose space-y-4", className)}
          {...props}
        >
          {children}
        </div>
      </ChainOfThoughtContext.Provider>
    );
  }
);

export type ChainOfThoughtHeaderProps = ComponentProps<
  typeof CollapsibleTrigger
>;

export const ChainOfThoughtHeader = memo(
  ({ className, children, ...props }: ChainOfThoughtHeaderProps) => {
    const { isOpen } = useChainOfThought();

    return (
      <CollapsibleTrigger
        className={cn(
          "flex w-full items-center gap-2 text-muted-foreground text-sm transition-colors hover:text-foreground",
          className
        )}
        {...props}
      >
        <BrainIcon className="size-4" />
        <span className="flex-1 text-left">
          {children ?? "Chain of Thought"}
        </span>
        <ChevronDownIcon
          className={cn(
            "size-4 transition-transform",
            isOpen ? "rotate-180" : "rotate-0"
          )}
        />
      </CollapsibleTrigger>
    );
  }
);

export type ChainOfThoughtStepProps = ComponentProps<"div"> & {
  icon?: LucideIcon;
  label: string;
  description?: string;
  status?: "complete" | "active" | "pending";
};

export const ChainOfThoughtStep = memo(
  ({
    className,
    icon: Icon = DotIcon,
    label,
    description,
    status = "complete",
    children,
    ...props
  }: ChainOfThoughtStepProps) => {
    const statusStyles = {
      complete: "text-muted-foreground",
      active: "text-foreground",
      pending: "text-muted-foreground/50",
    };

    return (
      <div
        className={cn(
          "flex gap-2 text-sm",
          statusStyles[status],
          "fade-in-0 slide-in-from-top-2 animate-in",
          className
        )}
        {...props}
      >
        <div className="relative mt-0.5">
          <Icon className="size-4" />
          <div className="-mx-px absolute top-7 bottom-0 left-1/2 w-px bg-border" />
        </div>
        <div className="flex-1 space-y-2">
          <div>{label}</div>
          {description && (
            <div className="text-muted-foreground text-xs">{description}</div>
          )}
          {children}
        </div>
      </div>
    );
  }
);

export type ChainOfThoughtSearchResultsProps = ComponentProps<"div">;

export const ChainOfThoughtSearchResults = memo(
  ({ className, ...props }: ChainOfThoughtSearchResultsProps) => (
    <div className={cn("flex items-center gap-2", className)} {...props} />
  )
);

export type ChainOfThoughtSearchResultProps = ComponentProps<typeof Badge>;

export const ChainOfThoughtSearchResult = memo(
  ({ className, children, ...props }: ChainOfThoughtSearchResultProps) => (
    <Badge
      className={cn("gap-1 px-2 py-0.5 font-normal text-xs", className)}
      variant="secondary"
      {...props}
    >
      {children}
    </Badge>
  )
);

export type ChainOfThoughtContentProps = ComponentProps<
  typeof CollapsibleContent
>;

export const ChainOfThoughtContent = memo(
  ({ className, children, ...props }: ChainOfThoughtContentProps) => {
    return (
      <CollapsibleContent
        className={cn(
          "mt-2 space-y-3",
          "data-[state=closed]:fade-out-0 data-[state=closed]:slide-out-to-top-2 data-[state=open]:slide-in-from-top-2 text-popover-foreground outline-none data-[state=closed]:animate-out data-[state=open]:animate-in",
          className
        )}
        {...props}
      >
        {children}
      </CollapsibleContent>
    );
  }
);

// 新增：直接使用 ThoughtStep 数据的便捷组件
export type ChainOfThoughtAutoProps = ComponentProps<"div"> & {
  thoughtSteps: ThoughtStep[];
  open?: boolean;
  defaultOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
  isStreaming?: boolean;
};

export const ChainOfThoughtAuto = memo(
  ({
    className,
    thoughtSteps,
    open,
    defaultOpen = false,
    onOpenChange,
    isStreaming = false,
    ...props
  }: ChainOfThoughtAutoProps) => {
    const [isOpen, setIsOpen] = useControllableState({
      prop: open,
      defaultProp: defaultOpen,
      onChange: onOpenChange,
    });

    // 工具函数：根据步骤类型获取图标
    const getStepIcon = (type: ThoughtStep['type']): LucideIcon => {
      switch (type) {
        case 'thought':
          return BrainIcon;
        case 'action':
          return SearchIcon;
        case 'observation':
          return EyeIcon;
        case 'final':
          return CheckCircleIcon;
        default:
          return DotIcon;
      }
    };

    // 工具函数：根据步骤类型获取标签
    const getStepLabel = (type: ThoughtStep['type']): string => {
      switch (type) {
        case 'thought':
          return '思考';
        case 'action':
          return '行动';
        case 'observation':
          return '观察';
        case 'final':
          return '最终答案';
        default:
          return '未知';
      }
    };

    // 工具函数：根据状态获取状态样式
    const getStatus = (status?: ThoughtStep['status']): "complete" | "active" | "pending" => {
      switch (status) {
        case 'complete':
          return 'complete';
        case 'error':
          return 'pending';
        case 'pending':
          return 'active';
        default:
          return 'complete';
      }
    };

    if (!thoughtSteps || thoughtSteps.length === 0) {
      return null;
    }

    return (
      <div className={cn("not-prose max-w-prose space-y-4", className)} {...props}>
        <Collapsible open={isOpen} onOpenChange={setIsOpen}>
          <CollapsibleTrigger
            className="flex w-full items-center gap-2 text-muted-foreground text-sm transition-colors hover:text-foreground"
          >
            <BrainIcon className="size-4" />
            <span className="flex-1 text-left">思考过程</span>
            <div className="flex items-center gap-2">
              {thoughtSteps.length > 0 && (
                <span className="bg-muted text-muted-foreground px-2 py-0.5 rounded-full text-xs">
                  {thoughtSteps.length}
                </span>
              )}
              {isStreaming && (
                <span className="text-xs text-muted-foreground animate-pulse">
                  (进行中...)
                </span>
              )}
              <ChevronDownIcon
                className={cn(
                  "size-4 transition-transform",
                  isOpen ? "rotate-180" : "rotate-0"
                )}
              />
            </div>
          </CollapsibleTrigger>

          <CollapsibleContent
            className={cn(
              "mt-2 space-y-3",
              "data-[state=closed]:fade-out-0 data-[state=closed]:slide-out-to-top-2 data-[state=open]:slide-in-from-top-2 text-popover-foreground outline-none data-[state=closed]:animate-out data-[state=open]:animate-in"
            )}
          >
            {thoughtSteps.map((step, index) => {
              const isLastStep = index === thoughtSteps.length - 1;
              const isFinalAnswer = step.type === 'final' && isLastStep;

              return (
                <ChainOfThoughtStep
                  key={step.id || index}
                  icon={getStepIcon(step.type)}
                  label={getStepLabel(step.type)}
                  status={getStatus(step.status)}
                  className={isFinalAnswer ? "border-l-4 border-l-green-500 bg-green-50 dark:bg-green-950/20 -ml-1 pl-5" : ""}
                >
                  <div className={cn(
                    "prose prose-sm max-w-none break-words",
                    step.type === 'final' && "text-foreground font-medium",
                    step.type === 'action' && "text-blue-600 dark:text-blue-400",
                    step.type === 'observation' && "text-orange-600 dark:text-orange-400",
                    step.type === 'thought' && "text-muted-foreground",
                    isFinalAnswer && "text-base font-semibold text-green-700 dark:text-green-300"
                  )}>
                    {/* 对于action类型，如果内容包含工具调用信息，特殊处理 */}
                    {step.type === 'action' && step.content.includes('使用工具:') ? (
                      <div className="space-y-1">
                        <div className="font-medium">{step.content.split('\n')[0]}</div>
                        {step.content.includes('\n参数:') && (
                          <div className="text-xs bg-muted p-2 rounded border-l-2 border-blue-400">
                            <div className="font-mono">
                              {step.content.split('\n参数:')[1]}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div>
                        {isFinalAnswer && (
                          <div className="mb-2 text-sm font-medium text-green-600 dark:text-green-400">
                            💡 最终答案：
                          </div>
                        )}
                        <MarkdownContent content={step.content} />
                      </div>
                    )}
                  </div>
                </ChainOfThoughtStep>
              );
            })}

            {/* 流式加载指示器 */}
            {isStreaming && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground animate-pulse py-2">
                <div className="flex items-center gap-1">
                  <DotIcon className="size-4" />
                  <DotIcon className="size-4" />
                  <DotIcon className="size-4" />
                </div>
                <span>正在思考...</span>
              </div>
            )}
          </CollapsibleContent>
        </Collapsible>
      </div>
    );
  }
);

export type ChainOfThoughtImageProps = ComponentProps<"div"> & {
  caption?: string;
};

export const ChainOfThoughtImage = memo(
  ({ className, children, caption, ...props }: ChainOfThoughtImageProps) => (
    <div className={cn("mt-2 space-y-2", className)} {...props}>
      <div className="relative flex max-h-[22rem] items-center justify-center overflow-hidden rounded-lg bg-muted p-3">
        {children}
      </div>
      {caption && <p className="text-muted-foreground text-xs">{caption}</p>}
    </div>
  )
);

ChainOfThought.displayName = "ChainOfThought";
ChainOfThoughtHeader.displayName = "ChainOfThoughtHeader";
ChainOfThoughtStep.displayName = "ChainOfThoughtStep";
ChainOfThoughtSearchResults.displayName = "ChainOfThoughtSearchResults";
ChainOfThoughtSearchResult.displayName = "ChainOfThoughtSearchResult";
ChainOfThoughtContent.displayName = "ChainOfThoughtContent";
ChainOfThoughtImage.displayName = "ChainOfThoughtImage";
ChainOfThoughtAuto.displayName = "ChainOfThoughtAuto";
