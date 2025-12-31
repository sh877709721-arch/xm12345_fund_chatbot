import React from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { IconPlus } from "@tabler/icons-react";

import { Textarea } from "@/components/ai-elements/textarea";
import type { KnowledgeLabelWithDetail } from "@/utils/request/knowledge-label";
import {
  createKnowledgeLabel,
  updateKnowledgeLabel,
} from "@/utils/request/knowledge-label";

export type DialogStateType = "add" | "edit";

interface AnnotationDialogProps {
  batchId: number | null;
  item?: KnowledgeLabelWithDetail;
  type: DialogStateType;
  onSave: () => void;
}

export function AnnotationDialog({
  batchId,
  item,
  type,
  onSave,
}: AnnotationDialogProps) {
  const [open, setOpen] = React.useState(false);
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const TriggerSpan = React.forwardRef<
    HTMLSpanElement,
    React.HTMLAttributes<HTMLSpanElement>
  >(({ children, ...props }, ref) => (
    <span ref={ref} {...props}>
      {children}
    </span>
  ));
  TriggerSpan.displayName = "TriggerSpan";

  // 根据类型确定触发器内容
  const renderTrigger = () => {
    if (type === "add") {
      return (
        <Button variant="default" onClick={() => setOpen(true)}>
          <IconPlus className="h-4 w-4" />
          <span className="hidden lg:inline ml-2">新增标注</span>
        </Button>
      );
    } else {
      return (
        <TriggerSpan
          className="inline-block max-w-full cursor-pointer hover:underline truncate"
          title={item?.question}>
          {item?.question}
        </TriggerSpan>
      );
    }
  };

  // 转换状态值以匹配后端API期望的格式
  const convertIsPassedValue = (value: string): boolean | null => {
    switch (value) {
      case "通过":
        return true;
      case "未通过":
        return false;
      default:
        return null; // "未审核" 或其他情况
    }
  };

  // 将后端值转换为前端显示值
  const getDisplayValue = (value: boolean | null): string => {
    if (value === true) return "通过";
    if (value === false) return "未通过";
    return "未审核";
  };

  return (
    <div className="flex items-center gap-2">
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>{renderTrigger()}</DialogTrigger>

        <DialogContent className="sm:max-w-[600px]">
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              setIsSubmitting(true);
              try {
                // 获取表单数据
                const formData = new FormData(e.target as HTMLFormElement);
                const question = formData.get("question") as string;
                const aiContent = formData.get("ai_content") as string;
                const userContent = formData.get("user_content") as string;
                const isPassed = formData.get("is_passed") as string;
                const description = formData.get("description") as string;
                const filledBy = formData.get("filled_by") as string;

                // 转换状态值
                const isPassedValue = convertIsPassedValue(isPassed);

                if (type === "add") {
                  // 创建新标注 - 使用新的API接口
                  await createKnowledgeLabel(batchId || 0, {
                    name: question,
                    ai_content: aiContent,
                    user_content: userContent,
                    description: description,
                    is_passed: isPassedValue,
                    filled_by: filledBy,
                  });
                } else {
                  // 更新现有标注
                  await updateKnowledgeLabel(item!.label_id, {
                    name: question,
                    ai_content: aiContent,
                    user_content: userContent,
                    description: description,
                    is_passed: isPassedValue,
                    filled_by: filledBy,
                  });
                }

                // 保存成功
                onSave();
                setOpen(false);
              } catch (error) {
                console.error("保存标注失败:", error);
                // 可以添加错误提示
              } finally {
                setIsSubmitting(false);
              }
            }}>
            <DialogHeader className="px-4 pt-4 pb-2">
              <DialogTitle>
                {type === "edit"
                  ? `编辑标注: ${item?.label_id}`
                  : `批次号${batchId}：新增标注`}
              </DialogTitle>
            </DialogHeader>

            <div className="px-4 pb-4 grid grid-cols-1 md:grid-cols-2 gap-4 max-h-[70vh] overflow-y-auto">
              {/* 问题 */}
              <div className="md:col-span-2 flex flex-col gap-2">
                <Label htmlFor="question">问题</Label>
                <Textarea
                  id="question"
                  name="question"
                  placeholder="请输入问题"
                  defaultValue={item?.question}
                  className="min-h-[80px]"
                  required
                />
              </div>

              {/* AI 内容 */}
              <div className="md:col-span-2 flex flex-col gap-2">
                <Label htmlFor="ai_content">AI 生成的答案</Label>
                <Textarea
                  id="ai_content"
                  name="ai_content"
                  placeholder="AI 生成的内容"
                  defaultValue={item?.ai_content}
                  className="min-h-[100px]"
                  required
                />
              </div>

              {/* 用户的标注 */}
              <div className="md:col-span-2 flex flex-col gap-2">
                <Label htmlFor="user_content">用户的标注</Label>
                <Textarea
                  id="user_content"
                  name="user_content"
                  placeholder="请输入用户的标注内容"
                  defaultValue={item?.user_content}
                  className="min-h-[100px]"
                  required
                />
              </div>

              {/* 描述 */}
              <div className="md:col-span-2 flex flex-col gap-2">
                <Label htmlFor="description">描述</Label>
                <Textarea
                  id="description"
                  name="description"
                  placeholder="请输入描述信息"
                  defaultValue={item?.description}
                  className="min-h-[80px]"
                />
              </div>

              {/* 是否通过 */}
              <div className="flex flex-col gap-2">
                <Label htmlFor="is_passed">是否通过</Label>
                <Select
                  name="is_passed"
                  defaultValue={
                    item?.is_passed !== undefined
                      ? getDisplayValue(item.is_passed)
                      : ""
                  }>
                  <SelectTrigger id="is_passed">
                    <SelectValue placeholder="请选择是否通过" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="通过">通过</SelectItem>
                    <SelectItem value="未通过">未通过</SelectItem>
                    <SelectItem value="未审核">未审核</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* 填表人 */}
              <div className="flex flex-col gap-2">
                <Label htmlFor="filled_by">填表人</Label>
                <Input
                  id="filled_by"
                  name="filled_by"
                  placeholder="请输入填表人"
                  defaultValue={item?.filled_by}
                />
              </div>
            </div>

            <DialogFooter className="px-4 py-4 border-t">
              <div className="flex justify-end gap-4 w-full">
                <div className="w-24">
                  <DialogClose asChild>
                    <Button variant="outline" className="w-full" type="button">
                      取消
                    </Button>
                  </DialogClose>
                </div>
                <div className="w-24">
                  <Button
                    type="submit"
                    className="w-full"
                    disabled={isSubmitting}>
                    {isSubmitting ? "保存中..." : "保存"}
                  </Button>
                </div>
              </div>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
