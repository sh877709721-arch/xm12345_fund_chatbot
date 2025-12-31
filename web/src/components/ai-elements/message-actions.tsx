import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ThumbsUp, Minus, ThumbsDown } from "lucide-react";
import type { HTMLAttributes } from "react";
import { useVote } from "@/hooks/use-vote";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Textarea } from "@/components/ui/textarea";
import { useState } from "react";

export type MessageActionsProps = HTMLAttributes<HTMLDivElement> & {
  messageId: number;  // 修改为数字类型
  feedback?: 'good' | 'medium' | 'bad' | null;  // 修正投票类型
  onFeedbackChange?: (messageId: number, feedback: 'good' | 'medium' | 'bad' | null) => void;
  onToggleChainOfThought?: (messageId: number) => void;
  hasChainOfThought?: boolean;
  showChainOfThought?: boolean;
  disabled?: boolean;
};

export const MessageActions = ({
  messageId,
  feedback,
  onFeedbackChange,
  onToggleChainOfThought,
  showChainOfThought,
  disabled = false,
  className,
  ...props
}: MessageActionsProps) => {
  const [feedbackText, setFeedbackText] = useState("");
  const [isPopoverOpen, setIsPopoverOpen] = useState(false);

  const { toggleVote, loading } = useVote({
    onSuccess: (vote) => {
      // 投票成功后，更新本地状态
      console.log('onSuccess');
      if (vote && vote.vote_type) {
        const newFeedback =
          vote.vote_type === 'good' ? 'good' :
            vote.vote_type === 'medium' ? 'medium' : 'bad';
        console.log('更新反馈:', { messageId, feedback: newFeedback });
        onFeedbackChange?.(messageId, newFeedback);
        setFeedbackText("");
        setIsPopoverOpen(false);
      }
    },
    onError: (error) => {
      // 投票失败时的处理
      console.log('onError');
      console.error('投票失败:', error);
    }
  });
  const handleGood = async () => {
    const currentFeedback = feedback || null;
    const newFeedback = 'good';
    const success = await toggleVote(messageId, currentFeedback, newFeedback, null);
    // 如果 API 调用失败，仍然更新本地状态以保持响应性
    if (!success && !loading) {
      onFeedbackChange?.(messageId, newFeedback);
    }
  };

  const handleMedium = async () => {
    const currentFeedback = feedback || null;
    const newFeedback = 'medium';
    const success = await toggleVote(messageId, currentFeedback, newFeedback, null);
    // 如果 API 调用失败，仍然更新本地状态以保持响应性
    if (!success && !loading) {
      console.log('API调用失败，手动更新本地状态');
      onFeedbackChange?.(messageId, newFeedback);
    }
  };

  const handleBadClick = () => {
    if (feedback === 'bad') {
      // 如果已经是差评，取消选择
      onFeedbackChange?.(messageId, null);
    } else {
      // 打开Popover进行反馈
      setIsPopoverOpen(true);
    }
  };

  const handleBadSubmit = async () => {
    console.log('处理差投票:', { messageId, currentFeedback: feedback, feedbackText });
    const currentFeedback = feedback || null;
    const newFeedback = 'bad';
    const success = await toggleVote(messageId, currentFeedback, newFeedback, feedbackText);
    console.log('投票结果:', { success, newFeedback, loading });
    // 如果 API 调用失败，仍然更新本地状态以保持响应性
    if (!success && !loading) {
      console.log('API调用失败，手动更新本地状态');
      onFeedbackChange?.(messageId, newFeedback);
      setFeedbackText("");
      setIsPopoverOpen(false);
    }
  };

  const handleBadCancel = () => {
    setFeedbackText("");
    setIsPopoverOpen(false);
  };

  if (messageId === 0) {
    return <></>
  }

  return (
    <div
      className={cn(
        "flex items-center gap-1 transition-opacity duration-200",
        className
      )}
      {...props}
    >
      <Button
        variant="ghost"
        size="sm"
        onClick={handleGood}
        disabled={disabled || loading}
        className={cn(
          "h-8 w-8 p-0",
          feedback === 'good'
            ? "text-green-600 bg-green-50 hover:bg-green-100 font-semibold"
            : "text-muted-foreground hover:text-foreground"
        )}
        aria-label="好"
      >
        <ThumbsUp className="h-4 w-4" />
      </Button>

      <Button
        variant="ghost"
        size="sm"
        onClick={handleMedium}
        disabled={disabled || loading}
        className={cn(
          "h-8 w-8 p-0",
          feedback === 'medium'
            ? "text-yellow-600 bg-yellow-50 hover:bg-yellow-100 font-semibold"
            : "text-muted-foreground hover:text-foreground"
        )}
        aria-label="中"
      >
        <Minus className="h-4 w-4" />
      </Button>

      <Popover open={isPopoverOpen} onOpenChange={setIsPopoverOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleBadClick}
            disabled={disabled || loading}
            className={cn(
              "h-8 w-8 p-0",
              feedback === 'bad'
                ? "text-red-600 bg-red-50 hover:bg-red-100 font-semibold"
                : "text-muted-foreground hover:text-foreground"
            )}
            aria-label="差"
          >
            <ThumbsDown className="h-4 w-4" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-80" align="start" sideOffset={8}>
          <div className="space-y-3">
            <div className="text-sm font-medium">请提供您的反馈</div>
            <Textarea
              placeholder="请详细说明您的问题或建议..."
              value={feedbackText}
              onChange={(e) => setFeedbackText(e.target.value)}
              className="min-h-[80px] resize-none"
            />
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleBadCancel}
              >
                取消
              </Button>
              <Button
                variant="default"
                size="sm"
                onClick={handleBadSubmit}
                disabled={!feedbackText.trim() || loading}
              >
                确定
              </Button>
            </div>
          </div>
        </PopoverContent>
      </Popover>

    </div>
  );
};