import * as React from "react";
import type { VariantProps } from "class-variance-authority";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
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
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import {
  createGuideline,
  updateGuideline,
  type GuidelineItem,
  type GuidelineStatus,
} from "@/utils/request/guideline";

export type DialogStateType = "add" | "edit" | "row_edit";

interface GuidelineFormProps {
  item?: GuidelineItem;
  type: DialogStateType;
  onSave?: () => void;
  onUpdateLocal?: (updatedItem: GuidelineItem) => void;
}

export function GuidelineDialog({ item, type, onSave, onUpdateLocal }: GuidelineFormProps) {
  const [open, setOpen] = React.useState(false);
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  // 阻止回车键提交
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
    }
  };

  const TriggerButton = React.forwardRef<
    HTMLButtonElement,
    React.ComponentProps<"button"> &
    VariantProps<typeof buttonVariants>
  >(({ className, variant, size, children, ...props }, ref) => (
    <Button
      ref={ref}
      className={className}
      variant={variant}
      size={size}
      {...props}
    >
      {children}
    </Button>
  ));
  TriggerButton.displayName = "TriggerButton";

  const TriggerSpan = React.forwardRef<
    HTMLSpanElement,
    React.HTMLAttributes<HTMLSpanElement>
  >(({ children, ...props }, ref) => (
    <span ref={ref} {...props}>
      {children}
    </span>
  ));
  TriggerSpan.displayName = "TriggerSpan";

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {type === "add" ? (
          <TriggerButton variant="default">
            <IconPlus className="h-4 w-4" />
            <span className="hidden lg:inline ml-2">新增指南</span>
          </TriggerButton>
        ) : type === "edit" ? (
          <TriggerSpan
            className="inline-block max-w-full cursor-pointer hover:underline truncate"
            title={item?.title}
          >
            {item?.title}
          </TriggerSpan>
        ) : (
          <button type="button" className="w-full h-8 px-2 py-1 text-sm">
            编辑
          </button>
        )}
      </DialogTrigger>

      <DialogContent className="sm:max-w-[800px]" onKeyDown={handleKeyDown}>
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            setIsSubmitting(true);

            const timeoutPromise = new Promise((_, reject) => {
              setTimeout(() => reject(new Error('请求超时，请检查网络连接')), 30000);
            });

            try {
              const formData = new FormData(e.target as HTMLFormElement);
              const title = formData.get('title') as string;
              const condition = formData.get('condition') as string;
              const action = formData.get('action') as string;
              const prompt_template = formData.get('prompt_template') as string;
              const priority = parseInt(formData.get('priority') as string);
              const status = formData.get('status') as GuidelineStatus;

              if (!title || !condition || !action) {
                toast.error("请填写所有必填字段");
                return;
              }

              if (type === "add") {
                await Promise.race([
                  createGuideline({
                    title,
                    condition,
                    action,
                    prompt_template: prompt_template || undefined,
                    priority,
                    status,
                  }),
                  timeoutPromise
                ]);

                if (onSave) {
                  onSave();
                }
              } else {
                const updated = await Promise.race<GuidelineItem>([
                  updateGuideline(item!.id, {
                    title,
                    condition,
                    action,
                    prompt_template: prompt_template || undefined,
                    priority,
                    status,
                  }),
                  timeoutPromise as Promise<GuidelineItem>
                ]);

                if (onUpdateLocal) {
                  onUpdateLocal({
                    ...item!,
                    ...updated,
                  });
                }
              }

              setOpen(false);
            } catch (error: any) {
              console.error("保存指南失败:", error);

              if (error.message === '请求超时，请检查网络连接') {
                toast.error('请求超时，请检查网络连接后重试');
              } else if (error.response?.data?.detail) {
                toast.error(error.response.data.detail);
              } else {
                toast.error('操作失败，请重试');
              }
            } finally {
              setIsSubmitting(false);
            }
          }}
        >
          <DialogHeader>
            <DialogTitle>
              {type === "edit" ? `编辑指南: ${item?.id}` : "新增指南"}
            </DialogTitle>
          </DialogHeader>

          <div className="flex flex-col gap-4 py-4">
            {/* 标题 */}
            <div>
              <Label htmlFor="title">标题 *</Label>
              <Input
                id="title"
                name="title"
                defaultValue={item?.title}
                placeholder="请输入指南标题"
                required
              />
            </div>

            {/* 触发条件 */}
            <div>
              <Label htmlFor="condition">触发条件 *</Label>
              <Textarea
                id="condition"
                name="condition"
                defaultValue={item?.condition}
                placeholder="描述触发此指南的条件,例如:用户提问 为什么保费变多了"
                required
                rows={3}
              />
            </div>

            {/* 行动内容 */}
            <div>
              <Label htmlFor="action">行动内容 *</Label>
              <Textarea
                id="action"
                name="action"
                defaultValue={item?.action}
                placeholder="描述采取的行动,例如:为什么保费变多了"
                required
                rows={3}
              />
            </div>

            {/* Prompt 模板（可选） */}
            <div>
              <Label htmlFor="prompt_template">Prompt 模板（可选）</Label>
              <Textarea
                id="prompt_template"
                name="prompt_template"
                defaultValue={item?.prompt_template}
                placeholder="自定义 Prompt 模板，留空使用默认模板"
                rows={4}
              />
              <p className="text-sm text-muted-foreground mt-1">
                如果填写，将覆盖默认的行动指南格式
              </p>
            </div>

            {/* 优先级 & 状态 */}
            <div className="flex gap-4">
              <div className="flex-1">
                <Label htmlFor="priority">优先级 *</Label>
                <Input
                  id="priority"
                  name="priority"
                  type="number"
                  min="1"
                  max="10"
                  defaultValue={item?.priority || 5}
                  required
                />
                <p className="text-xs text-muted-foreground mt-1">
                  1-10，数字越大优先级越高
                </p>
              </div>
              <div className="flex-1">
                <Label htmlFor="status">状态 *</Label>
                <Select name="status" defaultValue={item?.status || "D"}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="A">已启用</SelectItem>
                    <SelectItem value="I">已禁用</SelectItem>
                    <SelectItem value="D">草稿</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          <DialogFooter>
            <DialogClose asChild>
              <Button type="button" variant="outline">取消</Button>
            </DialogClose>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "保存中..." : "保存"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
