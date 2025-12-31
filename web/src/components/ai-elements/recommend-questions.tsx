import { useChat } from "@/context/chat-context";
import type { RecommendQA } from "@/hooks/use-qwen-chat";
import { cn } from "@/lib/utils";

interface RecommendQuestionsProps {
  questions: RecommendQA[] | null;
  className?: string;
}

export function RecommendQuestions({ questions, className }: RecommendQuestionsProps) {
  const { sendMessage } = useChat();

  if (!questions || questions.length === 0) {
    return null;
  }

  const handleQuestionClick = (question: string) => {
    // 立即发送消息
    sendMessage(question);
  };

  return (
    <div className={cn("mt-3 space-y-2", className)}>
      <div className="flex items-center gap-1.5 mb-2">
        <div className="w-1 h-3.5 rounded-full bg-gradient-to-b from-[#60A5FA] to-[#2563EB]"></div>
        <div className="text-[10px] font-medium text-[#4B5563] dark:text-[#D1D5DB] leading-tight sm:text-xs sm:font-semibold">
          以下是推荐问题，点击提问
        </div>
      </div>
      <div className="grid gap-1.5">
        {questions.map((qa) => (
          <div
            key={qa.id}
            onClick={() => handleQuestionClick(qa.question)}
            className="group cursor-pointer px-2.5 py-2 bg-gradient-to-r from-[#F9FAFB]/90 to-[#F3F4F6]/90 dark:from-[#1F2937]/50 dark:to-[#111827]/50 hover:from-[#EFF6FF]/90 hover:to-[#DBEAFE]/90 dark:hover:from-[#1E3A8A]/40 dark:hover:to-[#1E40AF]/40 border border-[#E5E7EB]/60 dark:border-[#374151]/60 hover:border-[#BFDBFE]/70 dark:hover:border-[#2563EB]/70 rounded-lg transition-all duration-200 shadow-sm hover:shadow-md hover:scale-[1.01] active:scale-[0.99] select-none"
          >
            <div className="flex items-start gap-1.5 w-full">
              <span className="line-clamp-2 text-[11px] text-[#374151] dark:text-[#E5E7EB] group-hover:text-[#111827] dark:group-hover:text-[#F9FAFB] leading-tight sm:text-xs sm:leading-snug">
                {qa.question}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}