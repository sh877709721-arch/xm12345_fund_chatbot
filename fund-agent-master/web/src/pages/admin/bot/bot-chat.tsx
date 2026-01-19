"use client";

import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import {
  Message,
  MessageContent
} from "@/components/ai-elements/message-admin";
import {
  PromptInput,
  PromptInputActionMenu,
  PromptInputBody,
  type PromptInputMessage,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputFooter,
  PromptInputTools,
} from "@/components/ai-elements/prompt-input";
import { PromptInputSpeechButton } from "@/components/ai-elements/prompt-input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { RotateCcwIcon } from "lucide-react";

import { useRef, useState, useEffect } from "react";

import { useChat } from "@/context/chat-context";

function format_content(content: string) {
  // return content.replace(/<a href="([^"]+)">([^<]+)<\/a>/g, '[$2]($1)')
  //   .replace(/\[来源: (?:\[doc_\d+\]\(doc_\d+\)(?:,\s*)?)+\]/g, '')
  //   .replace(/\[来源:(?:\[doc_\d+\]\(doc_\d+\)(?:,\s*)?)+\]/g, '')
  //   .replace(/\[来源:\s+doc_\d+\]/g, '')
  //   .replace(/\[来源:\[doc_\d+\]\]/g, '')
  //   .replace(/\[来源:(?:\[\d+\]\(\d+\)(?:,\s*)?)+\]/g, '')
  //   .replace(/\[来源: (?:\[\d+\]\(\d+\)(?:,\s*)?)+\]/g, '')
  //   .replace(/来源: (?:\d+\(\d+\)(?:,\s*)?)+\]/g, '')
  //   .replace(/\[来源:\[\d+\]\]/g, '')
  return content;
}

const ChatBotDemo = () => {
  const [input, setInput] = useState("");
  const { messages, sendMessage, status, stop, updateMessageFeedback, toggleChainOfThought, recommendQa, model, setModel, resetChatSession } = useChat();
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // 滚动到底部的函数
  const scrollToBottom = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
  };

  // 组件挂载时滚动到底部
  useEffect(() => {
    scrollToBottom();
  }, []);

  // 当有新消息时滚动到底部
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (message: PromptInputMessage) => {
    if (status === "streaming" || status === "submitted") {
      stop();
      return;
    }
    const hasText = Boolean(message.text);
    const hasAttachments = Boolean(message.files?.length);

    if (!(hasText || hasAttachments)) {
      return;
    }

    sendMessage(message.text || "");
    setInput("");
  };
  return (
    <div className="h-full flex flex-col min-h-0 px-4 sm:px-5 lg:px-6 relative">
      {/* 顶部反馈按钮区域 */}
      <div ref={scrollContainerRef} className="absolute bg-background top-[1px] bottom-[115px] left-0 right-0 overflow-y-auto">
        <Conversation className="flex-1 min-h-0 max-w-full sm:max-w-2xl lg:max-w-3xl mx-auto w-full">
          <ConversationContent>
            {messages.map(({ content, ...message }, index) => (
              <Message
                from={message.role}
                key={message.id}
                messageId={message.id}
                messageDbId={message.db_id}
                feedback={message.feedback}
                onFeedbackChange={updateMessageFeedback}
                onToggleChainOfThought={toggleChainOfThought}
                thoughtSteps={message.thoughtSteps}
                showChainOfThought={message.showChainOfThought}
                hasChainOfThought={message.hasChainOfThought}
                chatStatus={status}
                isStreaming={status === "streaming" && message.role === "assistant"}
                recommendQa={recommendQa}
                isLast={index === messages.length - 1}
                sources={message.sources}
              >
                <MessageContent messageId={message.id} isUser={message.role === "user"} sources={message.sources}>
                  {format_content(content)}
                </MessageContent>
              </Message>
            ))}
          </ConversationContent>
          <ConversationScrollButton />
        </Conversation>


      </div>

      <div className="bg-background absolute left-0 right-0 bottom-0 z-20 px-2 sm:px-4">
        <div className="max-w-full sm:max-w-2xl lg:max-w-3xl mx-auto">
          <PromptInput
            onSubmit={handleSubmit}
            className="mt-2"
            globalDrop
            multiple
          >
            <PromptInputBody>
              <PromptInputTextarea
                onChange={(e) => setInput(e.target.value)}
                ref={textareaRef}
                value={input}
              />
            </PromptInputBody>
            <PromptInputFooter>
              <PromptInputTools>
                <PromptInputActionMenu>

                  {/* 模型选择器 */}
                  <div className="flex items-center gap-2">
                    <Label htmlFor="model-select" className="text-sm text-muted-foreground">
                      模型:
                    </Label>
                    <Select value={model} onValueChange={setModel}>
                      <SelectTrigger id="model-select" className="w-40">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="default">
                          <div className="flex flex-col">
                            <span className="font-medium">默认</span>
                          </div>
                        </SelectItem>
                        <SelectItem value="boost">
                          <div className="flex flex-col">
                            <span className="font-medium">知识图谱</span>
                          </div>
                        </SelectItem>
                        <SelectItem value="guideline_bot">
                          <div className="flex flex-col">
                            <span className="font-medium">指南模式</span>
                          </div>
                        </SelectItem>
                        <SelectItem value="react_bot">
                          <div className="flex flex-col">
                            <span className="font-medium">思考模式</span>
                          </div>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </PromptInputActionMenu>
              </PromptInputTools>



              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => resetChatSession(true)}
                  title="重置会话"
                >
                  <RotateCcwIcon className="w-4 h-4" />
                </Button>
                <PromptInputSpeechButton
                  mode="xfyun"
                  onTranscriptionChange={setInput}
                  textareaRef={textareaRef}
                />
                <PromptInputSubmit
                  disabled={!input && !status}
                  status={status}
                />
              </div>
            </PromptInputFooter>
          </PromptInput>
          <div className="text-[9px] sm:text-[10px] text-gray-400 text-center mt-1 leading-tight px-2">
            生成式人工智能声明：内容由AI生成，请甄别使用
          </div>
        </div>
      </div>
    </div>

  );
};

export default ChatBotDemo;
