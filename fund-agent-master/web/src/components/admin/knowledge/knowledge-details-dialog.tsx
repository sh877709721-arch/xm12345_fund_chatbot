import React from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
//import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2, Edit } from "lucide-react";
import { Textarea } from "@/components/ai-elements/textarea";
import { getKnowledgeDetails } from "@/utils/request/search";
import type { KnowledgeDetail } from "@/utils/request/search";
import { toast } from "sonner";
import { updateKnowledgeEntry } from "@/utils/request/knowledge-entries";
import type { UpdateKnowledgeRequest } from "@/utils/request/knowledge-entries";
import type { KnowledgeType } from "@/utils/request/knowledge-entries";
import { useAuth } from "@/context/auth-context";
import { canEditKnowledge } from "@/utils/permission";

interface KnowledgeDetailsDialogProps {
  knowledgeId: number;
  title: string;
  type: "qa" | "doc";
  onSave?: () => void;
  trigger?: React.ReactNode;
}

export function KnowledgeDetailsDialog({
  knowledgeId,
  title,
  type,
  onSave,
  trigger,
}: KnowledgeDetailsDialogProps) {
  const { user } = useAuth();
  const canEdit = canEditKnowledge(user);

  const [open, setOpen] = React.useState(false);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [details, setDetails] = React.useState<KnowledgeDetail | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [isEditing, setIsEditing] = React.useState(false);

  // 表单状态
  const [content, setContent] = React.useState("");
  const [reference, setReference] = React.useState("");
  const [status, setStatus] = React.useState("active");
  const [knowledgeType, setKnowledgeType] = React.useState<KnowledgeType>("qa");

  // 加载知识详情
  const loadDetails = React.useCallback(async () => {
    if (!knowledgeId) return;

    setLoading(true);
    try {
      const data: any = await getKnowledgeDetails(knowledgeId);
      if (data.length > 0) {
        const detail = data[0];
        setDetails(detail);
        setContent(detail.content);
        setReference(detail.reference);
        setStatus(detail.status);
        // 根据搜索结果类型设置知识类型
        setKnowledgeType(type === "qa" ? "qa" : "document");
      }
    } catch (error: any) {
      console.error("加载知识详情失败:", error);
      toast.error("加载知识详情失败");
    } finally {
      setLoading(false);
    }
  }, [knowledgeId, type]);

  // 当对话框打开时加载详情
  React.useEffect(() => {
    if (open) {
      loadDetails();
      // 如果用户没有编辑权限，确保不在编辑模式
      if (!canEdit) {
        setIsEditing(false);
      }
    }
  }, [open, loadDetails, canEdit]);

  // 保存编辑
  const handleSave = async () => {
    if (!details || !knowledgeId) return;

    setIsSubmitting(true);
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error('请求超时，请检查网络连接')), 30000);
    });

    try {
      await Promise.race([
        updateKnowledgeEntry(knowledgeId, {
          knowledge_type: knowledgeType,
          knowledge_catalog_id: 0, // 默认目录ID
          name: title,
          details: {
            content: content,
            role: details.role,
            status: status as any,
            version: details.version + 1,
            reference: reference
          }
        } as UpdateKnowledgeRequest),
        timeoutPromise
      ]);

      toast.success('知识条目已更新');
      setIsEditing(false);
      // 重新加载详情
      await loadDetails();
      onSave?.();
    } catch (error: any) {
      console.error("更新知识条目失败:", error);

      if (error.message === '请求超时，请检查网络连接') {
        toast.error('请求超时，请检查网络连接后重试');
      } else if (error.response) {
        const status = error.response.status;
        const data = error.response.data;

        if (status === 400) {
          toast.error('请求参数错误');
        } else if (status === 401) {
          toast.error('未授权访问，请重新登录');
        } else if (status === 403) {
          toast.error('权限不足，无法操作');
        } else if (status === 404) {
          toast.error('请求的资源不存在');
        } else if (status >= 500) {
          toast.error('服务器错误，请稍后重试');
        } else {
          toast.error(data?.detail || data?.message || '更新失败');
        }
      } else if (error.request) {
        toast.error('网络连接失败，请检查网络设置');
      } else {
        toast.error('更新失败，请重试');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const TriggerSpan = React.forwardRef<
    HTMLSpanElement,
    React.HTMLAttributes<HTMLSpanElement>
  >(({ children, ...props }, ref) => (
    <span
      ref={ref}
      {...props}
      className="inline-block max-w-full cursor-pointer hover:underline truncate"
    >
      {children}
    </span>
  ));
  TriggerSpan.displayName = "TriggerSpan";

  // 阻止回车键提交
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <TriggerSpan title={title}>
            {knowledgeId}:{title}
          </TriggerSpan>
        )}
      </DialogTrigger>

      <DialogContent
        className="sm:max-w-[700px]"
        onKeyDown={handleKeyDown}
      >
        <div className="flex flex-col h-[600px]">
          {/* 头部区域 */}
          <DialogHeader className="px-6 pt-6 pb-4 border-b">
            <DialogTitle className="flex items-center justify-between">
              <span>{title}</span>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs">
                  ID: {knowledgeId}
                </Badge>
                <Badge variant="secondary" className="text-xs">
                  {type === "qa" ? "问答" : "文档"}
                </Badge>
              </div>
            </DialogTitle>
            <DialogDescription>
              知识详情内容查看和编辑
            </DialogDescription>
          </DialogHeader>

          {/* 内容区域 */}
          <div className="flex-1 overflow-hidden px-6 py-4">
            {loading ? (
              <div className="flex items-center justify-center h-full">
                <Loader2 className="w-6 h-6 animate-spin" />
                <span className="ml-2">加载中...</span>
              </div>
            ) : details ? (
              <div className="flex flex-col gap-4 h-full">
                {/* 控制栏 */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <Label htmlFor="status">状态:</Label>
                      <Select
                        value={status}
                        onValueChange={setStatus}
                        disabled={!isEditing}
                      >
                        <SelectTrigger className="w-32" id="status">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="active">已启用</SelectItem>
                          <SelectItem value="pending">待审核</SelectItem>
                          <SelectItem value="deleted">已删除</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="flex items-center gap-2">
                      <Label htmlFor="type">类型:</Label>
                      <Select
                        value={knowledgeType}
                        onValueChange={(v: KnowledgeType) => setKnowledgeType(v)}
                        disabled={!isEditing}
                      >
                        <SelectTrigger className="w-32" id="type">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="qa">问答</SelectItem>
                          <SelectItem value="document">文档</SelectItem>
                          <SelectItem value="data_table">数据表</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  {canEdit && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        if (isEditing) {
                          // 取消编辑，恢复原始数据
                          setContent(details.content);
                          setReference(details.reference);
                          setStatus(details.status);
                          setIsEditing(false);
                        } else {
                          setIsEditing(true);
                        }
                      }}
                    >
                      {isEditing ? "取消" : <Edit className="w-4 h-4" />}
                    </Button>
                  )}
                </div>

                {/* 内容区域 */}
                <div className="flex-1 flex flex-col gap-4 min-h-0 overflow-auto">
                  <div className="flex-1 flex flex-col gap-2">
                    <Label htmlFor="content">内容</Label>
                    <div className="flex-1 min-h-0">
                      <Textarea
                        id="content"
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                        disabled={!isEditing}
                        className="h-full w-full resize-none"
                        placeholder="请输入内容"
                        onKeyDown={handleKeyDown}
                      />
                    </div>
                  </div>
                </div>
                <div className="flex-1 flex flex-col gap-4 min-h-0 overflow-auto">
                  {/* 参考资料区域 */}
                  <div className="flex flex-col gap-2">
                    <Label htmlFor="reference">参考资料</Label>
                    <Textarea
                      id="reference"
                      value={reference}
                      onChange={(e) => setReference(e.target.value)}
                      disabled={!isEditing}
                      placeholder="请输入参考资料链接或标识"
                      onKeyDown={handleKeyDown}
                    />
                  </div>

                  {/* 元数据信息 */}
                  <div className="grid grid-cols-2 gap-4 text-sm text-muted-foreground">
                    <div>
                      <span className="font-medium">版本:</span> {details.version}
                    </div>
                    <div>
                      <span className="font-medium">创建时间:</span> {new Date(details.created_at).toLocaleString('zh-CN')}
                    </div>
                    <div>
                      <span className="font-medium">更新时间:</span> {new Date(details.updated_at).toLocaleString('zh-CN')}
                    </div>
                    <div>
                      <span className="font-medium">角色:</span> {details.role}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                无法加载知识详情
              </div>
            )}
          </div>

          {/* 底部操作区域 */}
          <DialogFooter className="px-6 py-4 border-t">
            <div className="flex justify-end gap-3 w-full">
              {!isEditing && (
                <DialogClose asChild>
                  <Button variant="outline">关闭</Button>
                </DialogClose>
              )}
              {canEdit && isEditing && details && (
                <>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setContent(details.content);
                      setReference(details.reference);
                      setStatus(details.status);
                      setIsEditing(false);
                    }}
                  >
                    取消
                  </Button>
                  <Button
                    onClick={handleSave}
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? "保存中..." : "保存"}
                  </Button>
                </>
              )}
            </div>
          </DialogFooter>
        </div>
      </DialogContent>
    </Dialog>
  );
}