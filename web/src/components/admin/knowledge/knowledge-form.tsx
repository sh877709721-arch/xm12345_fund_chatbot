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

import type { KnowledgeEntry, KnowledgeType, KnowledgeStatus } from "@/utils/request/knowledge-entries";
import { createKnowledgeEntry, updateKnowledgeEntry } from "@/utils/request/knowledge-entries";
import type {
  KnowledgeCatalog,
  CatalogTreeNode,
} from "@/utils/request/knowledge-catalog";
import { toast } from "sonner";

import { Textarea } from "@/components/ai-elements/textarea";
import { CatalogTree } from "./catalog-tree";

export type DialogStateType = "add" | "edit" | "row_edit";

export function KnowledgeDialog({
  item,
  type,
  onSave,
  onUpdateLocal,
  catalogs,
  catalogTree,
}: {
  item?: KnowledgeEntry;
  type: DialogStateType;
  onSave?: () => void;
  onUpdateLocal?: (updatedEntry: KnowledgeEntry) => void;
  catalogs?: KnowledgeCatalog[];
  catalogTree?: Record<string, Record<string, CatalogTreeNode[]>>;
}) {
  const [open, setOpen] = React.useState(false);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [selectedCatalogId, setSelectedCatalogId] = React.useState<number | null>(
    item?.knowledge_catalog_id || null
  );

  // 阻止回车键提交，允许 Shift+Enter 换行
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
    }
  };

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
    <div className="flex items-center gap-2">
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          {type === "add" ? (
            <Button variant="default">
              <IconPlus className="h-4 w-4" />
              <span className="hidden lg:inline ml-2">新增知识</span>
            </Button>
          ) : (
            type === "edit" ? (
              <TriggerSpan
                className="inline-block max-w-full cursor-pointer hover:underline truncate"
                title={item?.name}>
                {item?.name}
              </TriggerSpan>
            ) : (
              <a type="button" className="w-full h-8 px-2 py-1 text-sm">编辑</a>
            )
          )}
        </DialogTrigger>

        <DialogContent
          className="sm:max-w-[1400px]"
          onKeyDown={handleKeyDown}
        >
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              setIsSubmitting(true);

              // 添加超时保护
              const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('请求超时，请检查网络连接')), 30000);
              });

              try {
                // 获取表单数据
                const formData = new FormData(e.target as HTMLFormElement);
                const name = formData.get('name') as string;
                const knowledgeType = formData.get('type') as KnowledgeType;
                const status = formData.get('status') as KnowledgeStatus;
                const content = formData.get('content') as string;
                const reference = formData.get('reference') as string;

                if (type === "add") {
                  // 创建新知识条目（带超时保护）
                  await Promise.race([
                    createKnowledgeEntry({
                      knowledge_type: knowledgeType,
                      knowledge_catalog_id: selectedCatalogId || 0,
                      name: name,
                      details: {
                        content: content,
                        role: "user", // 默认角色
                        status: status,
                        created_by: 1, // 默认创建者ID，实际应该从上下文中获取
                        version: 1,
                        reference: reference // 添加参考资料
                      },
                      created_by: 1 // 默认创建者ID
                    }),
                    timeoutPromise
                  ]);

                } else {
                  // 更新现有知识条目（带超时保护）
                  await Promise.race([
                    updateKnowledgeEntry(item!.id, {
                      knowledge_type: knowledgeType,
                      knowledge_catalog_id: selectedCatalogId || 0,
                      name: name,
                      details: {
                        content: content,
                        role: "user",
                        status: status,
                        created_by: item?.details?.created_by || 1,
                        version: (item?.details?.version || 0) + 1,
                        reference: reference // 添加参考资料
                      }
                    }),
                    timeoutPromise
                  ]);

                  // 编辑成功后立即更新本地数据，不刷新页面
                  if (onUpdateLocal) {
                    const updatedData: KnowledgeEntry = {
                      id: item!.id,
                      knowledge_type: knowledgeType,
                      knowledge_catalog_id: selectedCatalogId || 0,
                      name: name,
                      status: status,
                      created_at: item!.created_at,
                      updated_at: new Date().toISOString(),
                      details: {
                        content: content,
                        role: "user",
                        status: status,
                        created_by: item?.details?.created_by || 1,
                        version: (item?.details?.version || 0) + 1,
                        reference: reference
                      }
                    };
                    onUpdateLocal(updatedData);
                  }
                }

                // 保存成功（保持向后兼容）
                if (onSave) {
                  onSave();
                }
                setOpen(false);
              } catch (error: any) {
                console.error("保存知识条目失败:", error);

                // 用户友好的错误提示
                if (error.message === '请求超时，请检查网络连接') {
                  toast.error('请求超时，请检查网络连接后重试');
                } else if (error.response) {
                  const status = error.response.status;
                  const data = error.response.data;

                  if (status === 400) {
                    toast.error('请求参数错误，请检查填写内容');
                  } else if (status === 401) {
                    toast.error('未授权访问，请重新登录');
                  } else if (status === 403) {
                    toast.error('权限不足，无法操作');
                  } else if (status === 404) {
                    toast.error('请求的资源不存在');
                  } else if (status >= 500) {
                    toast.error('服务器错误，请稍后重试');
                  } else {
                    toast.error(data?.detail || data?.message || '请求失败');
                  }

                  console.error("API响应错误:", status, data);
                } else if (error.request) {
                  toast.error('网络连接失败，请检查网络设置');
                  console.error("网络请求错误:", error.message);
                } else {
                  toast.error('操作失败，请重试');
                  console.error("其他错误:", error.message);
                }
              } finally {
                setIsSubmitting(false);
              }
            }}>
            <DialogHeader>
              <DialogTitle>{type === "edit" ? `编辑: ${item?.id}` : "新增"}</DialogTitle>
              <DialogDescription>
              </DialogDescription>
            </DialogHeader>
            <div className="flex gap-4 h-[720px] p-0">
              {/* 头部区域 */}


              {/* 两栏布局 */}
              <div className="flex gap-4 flex-1 overflow-hidden px-4">
                {/* 左侧:知识目录树 */}
                <div className="w-[300px] flex-shrink-0 border-r pr-4 overflow-hidden flex flex-col">
                  <Label htmlFor="catalog" className="mb-2">知识目录</Label>
                  <div className="flex-1 overflow-auto border rounded-md">
                    <CatalogTree
                      catalogTree={catalogTree || {}}
                      catalogs={catalogs || []}
                      selectedCatalogId={selectedCatalogId}
                      onCatalogSelect={(catalog) => {
                        setSelectedCatalogId(catalog.id);
                      }}
                      loading={false}
                    />
                  </div>
                </div>

                {/* 右侧:表单字段 */}
                <div className="flex-1 flex flex-col gap-2 overflow-hidden">
                  {/* 名称字段 */}
                  <div className="flex-shrink-0">
                    <Label htmlFor="name" className="mb-2">名称</Label>
                    <Input
                      id="name"
                      name="name"
                      defaultValue={item?.name}
                      required
                      onKeyDown={handleKeyDown}
                    />
                  </div>

                  {/* 类型 & 状态选择区 (10%) */}
                  <div className="h-[10%] min-h-[60px] flex gap-2 flex-shrink-0">
                    <div className="flex-1 flex flex-col gap-2">
                      <Label htmlFor="type">类型</Label>
                      <Select name="type" defaultValue={item?.knowledge_type || "qa"}>
                        <SelectTrigger id="type" className="w-full">
                          <SelectValue placeholder="选择类型" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="qa">问答</SelectItem>
                          <SelectItem value="document">文档</SelectItem>
                          <SelectItem value="data_table">数据表</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="flex-1 flex flex-col gap-2">
                      <Label htmlFor="status">状态</Label>
                      <Select name="status" defaultValue={item?.status || "pending"}>
                        <SelectTrigger id="status" className="w-full">
                          <SelectValue placeholder="选择状态" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="active">已启用</SelectItem>
                          <SelectItem value="pending">待审核</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {/* 内容输入区 (75%) */}
                  <div className="h-[60%] flex flex-col flex-shrink-0">
                    <Label htmlFor="content" className="mb-2">内容</Label>
                    <div className="flex-1 min-h-0">
                      <Textarea
                        id="content"
                        name="content"
                        placeholder="请输入内容"
                        defaultValue={item?.details?.content}
                        className="h-full w-full resize-none"
                        required
                        onKeyDown={handleKeyDown}
                      />
                    </div>
                  </div>

                  {/* 参考资料区 (15%) */}
                  <div className="h-[15%] min-h-[80px] flex flex-col flex-shrink-0">
                    <Label htmlFor="reference" className="mb-2">参考资料</Label>
                    <div className="flex-1 min-h-0">
                      <Textarea
                        id="reference"
                        name="reference"
                        placeholder="请输入参考资料链接或标识"
                        defaultValue={item?.details?.reference || ""}
                        className="h-full w-full resize-none"
                        onKeyDown={handleKeyDown}
                      />
                    </div>
                  </div>
                </div>
              </div>


            </div>
            {/* 底部固定区域 */}
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