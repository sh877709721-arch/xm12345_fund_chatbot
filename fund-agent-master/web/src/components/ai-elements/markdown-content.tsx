import { cn } from "@/lib/utils";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { type HTMLAttributes, forwardRef, useState } from "react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Source } from "@/hooks/use-qwen-chat";
import { GetReference, type ChatRefRequest } from "@/utils/request/chat";
import { toast } from "sonner";
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { X, Info } from "lucide-react"
export type MarkdownContentProps = HTMLAttributes<HTMLDivElement> & {
  content: string;
  messageId?: number;
  isUser?: boolean;
  sources?: Source[];
};

export type ReferenceDialogProps = HTMLAttributes<HTMLDivElement> & {
  messageId?: number;
  href?: string;
}

// 网页链接检测函数
const isWebUrl = (url?: string): boolean => {
  if (!url) return false;
  try {
    const urlObj = new URL(url);
    return ['http:', 'https:'].includes(urlObj.protocol);
  } catch {
    return false;
  }
};


const ReferenceDialog = forwardRef<HTMLButtonElement, ReferenceDialogProps & { messageId?: number, href?: string; }>(
  ({ children, messageId, href }, ref) => {
    const [referenceData, setReferenceData] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [isOpen, setIsOpen] = useState(false);

    const fetchReferenceData = async () => {
      if (!messageId || !href) return;

      setIsLoading(true);
      try {
        const referId = href; // 从 URL 提取 refer_id
        const query: ChatRefRequest = {
          message_id: messageId,
          refer_id: referId
        };
        const data = await GetReference(query);
        // 如果数据是错误对象，转换为可显示的格式
        if (data && typeof data === 'object' && data.type && data.msg) {
          // 这是错误数据，转换为错误消息
          setReferenceData({
            title: '获取引用失败',
            content: `错误信息: ${data.msg || '未知错误'}`,
            error: true
          });
        } else {
          setReferenceData(data);
        }
      } catch (error) {
        console.error('获取引用数据失败:', error);
        toast.error('获取引用数据失败');
        setReferenceData({
          title: '获取引用失败',
          content: `网络错误: ${error instanceof Error ? error.message : '未知错误'}`,
          error: true
        });
      } finally {
        setIsLoading(false);
      }
    };

    const handleOpenChange = (open: boolean) => {
      setIsOpen(open);
      if (open && !referenceData) {
        fetchReferenceData();
      }
    };

    return (
      <AlertDialog open={isOpen} onOpenChange={handleOpenChange}>
        <AlertDialogTrigger asChild>
          <button
            ref={ref}
            className="inline-flex items-center justify-center text-muted-foreground hover:text-primary transition-colors"
            title="查看引用来源"
          >
            {children}
          </button>
        </AlertDialogTrigger>
        <AlertDialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <div className="flex items-start justify-between">
            <AlertDialogHeader className="flex-1">
              <AlertDialogTitle>引用来源</AlertDialogTitle>
              <AlertDialogDescription>
                原文链接: {href}
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogCancel className="w-8 h-8 p-0">
              <X className="w-4 h-4" />
            </AlertDialogCancel>
          </div>

          <div className="mt-4">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                <span className="ml-2 text-sm text-muted-foreground">加载中...</span>
              </div>
            ) : (
              <div className="whitespace-pre-wrap">
                {referenceData}
              </div>
            )}
          </div>
        </AlertDialogContent>
      </AlertDialog>
    );
  }
);

ReferenceDialog.displayName = 'ReferenceDialog';


export const MarkdownContent = ({
  content,
  messageId,
  isUser = false,
  sources,
  className,
  ...props
}: MarkdownContentProps) => {
  // 对于用户消息，直接显示纯文本，不需要 Markdown 解析
  if (isUser) {
    return (
      <div className={cn(
        "whitespace-pre-wrap break-words overflow-x-hidden",
        "text-xs sm:text-sm",
        className
      )} {...props}>
        {content}
      </div>
    );
  }

  // 对于助手消息，使用 Markdown 解析
  return (
    <div className={cn(
      "prose prose-xs sm:prose-sm max-w-none",
      "prose-p:break-words prose-a:break-words prose-li:break-words",
      "prose-code:break-words prose-pre:overflow-x-auto",
      className
    )} {...props}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // 处理代码块
          code: ({
            className,
            children,
            ...props
          }: {
            className?: string;
            children?: React.ReactNode;
            [key: string]: any;
          }) => {
            const match = /language-(\w+)/.exec(className || '');
            const language = match?.[1];

            // 如果是内联代码
            if (!language) {
              return (
                <code
                  className={cn(
                    "rounded-md bg-muted px-1 py-0.5 font-mono text-xs sm:text-sm",
                    "break-all whitespace-pre-wrap",
                    className
                  )}
                  {...props}
                >
                  {children}
                </code>
              );
            }

            // 如果是代码块
            return (
              <div className="relative rounded-md overflow-hidden">
                <SyntaxHighlighter
                  style={oneDark}
                  language={language}
                  PreTag="div"
                  customStyle={{
                    margin: 0,
                    borderRadius: '0.375rem',
                    fontSize: '0.75rem',
                    overflowX: 'auto',
                    maxWidth: '100%',
                  }}
                  wrapLines={true}
                  lineProps={{ style: { wordBreak: 'break-all' } }}
                  {...props}
                >
                  {String(children).replace(/\n$/, '')}
                </SyntaxHighlighter>
              </div>
            );
          },

          // 处理段落
          p: ({ children, ...props }: { children?: React.ReactNode;[key: string]: any }) => {
            return (
              <p className="mb-2 last:mb-0" {...props}>
                {children}
              </p>
            );
          },

          // 处理标题
          h1: ({ children, ...props }: { children?: React.ReactNode;[key: string]: any }) => (
            <h1 className="text-2xl font-bold mb-2 mt-3 first:mt-0" {...props}>
              {children}
            </h1>
          ),

          h2: ({ children, ...props }: { children?: React.ReactNode;[key: string]: any }) => (
            <h2 className="text-xl font-bold mb-2 mt-3 first:mt-0" {...props}>
              {children}
            </h2>
          ),

          h3: ({ children, ...props }: { children?: React.ReactNode;[key: string]: any }) => (
            <h3 className="text-lg font-bold mb-2 mt-2 first:mt-0" {...props}>
              {children}
            </h3>
          ),

          // 处理列表
          ul: ({ children, ...props }: { children?: React.ReactNode;[key: string]: any }) => (
            <ul className="list-disc pl-6 mb-2 space-y-1" {...props}>
              {children}
            </ul>
          ),

          ol: ({ children, ...props }: { children?: React.ReactNode;[key: string]: any }) => (
            <ol className="list-decimal pl-6 mb-2 space-y-1" {...props}>
              {children}
            </ol>
          ),

          li: ({ children, ...props }: { children?: React.ReactNode;[key: string]: any }) => (
            <li className="leading-relaxed" {...props}>
              {children}
            </li>
          ),

          // 处理引用
          blockquote: ({ children, ...props }: { children?: React.ReactNode;[key: string]: any }) => (
            <blockquote className="border-l-4 border-border pl-4 my-2 italic text-muted-foreground" {...props}>
              {children}
            </blockquote>
          ),

          // 处理链接
          a: ({ href }: { href?: string; children?: React.ReactNode; }) => {
            const isUrl = isWebUrl(href);

            return (
              <span className="items-center gap-1">
                {/* 保留原有的 children 显示 */}
                {/* {children || JSON.stringify(href)} */}

                {isUrl && (
                  <a
                    href={href}
                    target={isUrl ? "_blank" : undefined}
                    rel={isUrl ? "noopener noreferrer" : undefined}
                    className="text-primary hover:underline ml-1 break-all underline-offset-2"
                  >
                    访问链接
                  </a>
                )}

                {/* 只有非网页链接才显示引用对话框 */}
                {!isUrl && messageId && (
                  <ReferenceDialog href={href} messageId={messageId} className="ml-1 inline-flex">
                    <Info size={12} strokeWidth={1} />
                  </ReferenceDialog>
                )}
              </span>
            );
          },

          // 处理表格
          table: ({ children, ...props }: { children?: React.ReactNode;[key: string]: any }) => (
            <div className="overflow-x-auto my-4 -mx-2 sm:mx-0 px-2 sm:px-0">
              <table className="w-full border-collapse border border-border rounded-lg overflow-hidden min-w-[300px]" {...props}>
                {children}
              </table>
            </div>
          ),

          thead: ({ children, ...props }: { children?: React.ReactNode;[key: string]: any }) => (
            <thead className="bg-muted/50" {...props}>
              {children}
            </thead>
          ),

          tbody: ({ children, ...props }: { children?: React.ReactNode;[key: string]: any }) => (
            <tbody className="divide-y divide-border" {...props}>
              {children}
            </tbody>
          ),

          tr: ({ children, ...props }: { children?: React.ReactNode;[key: string]: any }) => (
            <tr className="hover:bg-muted/30 transition-colors" {...props}>
              {children}
            </tr>
          ),

          th: ({ children, ...props }: { children?: React.ReactNode;[key: string]: any }) => (
            <th className="border border-border px-2 py-2 sm:px-4 sm:py-3 text-left font-semibold text-xs sm:text-sm bg-muted/50" {...props}>
              {children}
            </th>
          ),

          td: ({ children, ...props }: { children?: React.ReactNode;[key: string]: any }) => (
            <td className="border border-border px-2 py-2 sm:px-4 sm:py-3 text-xs sm:text-sm align-top break-words" {...props}>
              {children}
            </td>
          ),

          // 处理分隔线
          hr: ({ ...props }) => (
            <hr className="my-3 border-border" {...props} />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};