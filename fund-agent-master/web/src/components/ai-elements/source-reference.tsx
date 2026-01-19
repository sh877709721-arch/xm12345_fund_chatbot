"use client";

import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { ExternalLinkIcon, FileTextIcon } from "lucide-react";
import type { ComponentProps } from "react";
import type { Source } from "@/hooks/use-qwen-chat";

export type SourceReferenceProps = ComponentProps<typeof Badge> & {
  source: Source;
};

export const SourceReference = ({
  source,
  className,
  ...props
}: SourceReferenceProps) => {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Badge
          className={cn(
            "ml-1 cursor-pointer rounded-full bg-blue-50 text-blue-700 hover:bg-blue-100 border-blue-200",
            className
          )}
          variant="secondary"
          {...props}
        >
          <FileTextIcon className="h-3 w-3 mr-1" />
          {source.title}
        </Badge>
      </DialogTrigger>

      <DialogContent className="max-w-[calc(100%-1rem)] sm:max-w-xl md:max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileTextIcon className="h-5 w-5" />
            {source.title}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {source.url && (
            <a
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-blue-600 hover:text-blue-800 text-xs sm:text-sm break-all"
            >
              <ExternalLinkIcon className="h-4 w-4" />
              {source.url}
            </a>
          )}

          {source.description && (
            <div>
              <h4 className="font-medium mb-2">描述</h4>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {source.description}
              </p>
            </div>
          )}

          {source.snippet && (
            <div>
              <h4 className="font-medium mb-2">引用内容</h4>
              <blockquote className="border-l-4 border-border pl-4 py-2 bg-muted/30 rounded-r-md">
                <p className="text-sm text-muted-foreground italic leading-relaxed">
                  {source.snippet}
                </p>
              </blockquote>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export type SourceListProps = ComponentProps<"div"> & {
  sources: Source[];
};

export const SourceList = ({ sources, className, ...props }: SourceListProps) => {
  if (!sources || sources.length === 0) return null;

  return (
    <div className={cn("flex flex-wrap gap-2 mt-2", className)} {...props}>
      {sources.map((source, index) => (
        <SourceReference
          key={source.id || index}
          source={source}
        />
      ))}
    </div>
  );
};