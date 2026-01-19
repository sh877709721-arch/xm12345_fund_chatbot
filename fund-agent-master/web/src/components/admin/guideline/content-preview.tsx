import * as React from "react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

interface ContentPreviewProps {
  content: string;
  maxLength?: number;
  className?: string;
}

export function ContentPreview({ content, maxLength = 100, className = "" }: ContentPreviewProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);

  if (!content) {
    return <span className={className}>-</span>;
  }

  const shouldTruncate = content.length > maxLength;
  const displayContent = isExpanded || !shouldTruncate ? content : content.slice(0, maxLength) + "...";

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className={className}>
            <span className="whitespace-pre-wrap">{displayContent}</span>
            {shouldTruncate && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setIsExpanded(!isExpanded);
                }}
                className="ml-2 text-xs text-blue-500 hover:text-blue-700 underline"
              >
                {isExpanded ? "收起" : "展开"}
              </button>
            )}
          </div>
        </TooltipTrigger>
        <TooltipContent className="max-w-md">
          <p className="whitespace-pre-wrap text-sm">{content}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
