"use client";

import type React from "react";

import { useState } from "react";
import { cn } from "@/lib/utils";
import {
  CheckCircle2,
  Clock,
  AlertCircle,
  Plus,
  Edit,
  Trash2,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { BatchDialog } from "@/components/admin/bot/batch-dialog";
import {
  createKnowledgeLabelBatch,
  updateKnowledgeLabelBatch,
  deleteKnowledgeLabelBatch,
} from "@/utils/request/knowledge-label";
import type { KnowledgeLabelBatch } from "@/utils/request/knowledge-label";

export type BatchListProps = {
  loading: boolean;
  batchList: KnowledgeLabelBatch[];
  setBatchList: (batch: KnowledgeLabelBatch[] | any) => void;
  selectedBatchId: number | null;
  onSelectBatch: (id: number | null) => void;
  itemCount: number;
  completedCount: number;
  onDeleteSuccess?: () => void;
};

const statusConfig = {
  pending: {
    label: "待处理",
    icon: AlertCircle,
    color: "text-muted-foreground",
    bgColor: "bg-muted",
  },
  active: {
    label: "进行中",
    icon: Clock,
    color: "text-blue-500",
    bgColor: "bg-blue-500/10",
  },
  deleted: {
    label: "已删除",
    icon: CheckCircle2,
    color: "text-red-500",
    bgColor: "bg-red-500/10",
  },
};

export function BatchList({
  loading,
  batchList,
  setBatchList,
  selectedBatchId,
  onSelectBatch,
  itemCount,
  completedCount,
  onDeleteSuccess,
}: BatchListProps) {
  const [hoveredId, setHoveredId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm("确定要删除这个批次吗？")) {
      try {
        await deleteKnowledgeLabelBatch(id);
        setBatchList(batchList.filter((b) => b.id !== id));
        if (selectedBatchId === id) {
          onSelectBatch(null);
        }
        // 调用删除成功回调，通知父组件重新获取数据
        onDeleteSuccess?.();
      } catch (error) {
        console.error("删除批次失败:", error);
      }
    }
  };

  const handleSave = async (batch: KnowledgeLabelBatch, isNew: boolean) => {
    try {
      if (isNew) {
        // 创建新批次
        const data: KnowledgeLabelBatch = await createKnowledgeLabelBatch({
          name: batch.name,
        });

        // 更新本地状态
        const newBatch: KnowledgeLabelBatch = {
          ...batch,
          id: data.id,
          created_at: data.created_at.split("T")[0],
          //status:
        };
        setBatchList((prevBatchList: KnowledgeLabelBatch[]) => [
          ...prevBatchList,
          newBatch,
        ]);
      } else {
        // 更新现有批次
        const data = await updateKnowledgeLabelBatch(batch.id, {
          name: batch.name,
        });

        // 更新本地状态
        const updatedBatch: KnowledgeLabelBatch = {
          ...batch,
          name: batch.name,
          created_at: (data as unknown as KnowledgeLabelBatch).created_at.split(
            "T"
          )[0],
        };

        setBatchList((prevBatchList: KnowledgeLabelBatch[]) =>
          prevBatchList.map((b) => (b.id === batch.id ? updatedBatch : b))
        );
      }
    } catch (error) {
      console.error(`${isNew ? "创建" : "更新"}批次失败:`, error);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col h-full">
        <div className="p-2 border-b flex-shrink-0">
          <Button className="w-full" size="sm" disabled>
            <Plus className="w-4 h-4 mr-2" />
            新增批次
          </Button>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <p>加载中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-2 border-b flex-shrink-0">
        <BatchDialog
          type="add"
          onSave={handleSave}
          trigger={
            <Button className="w-full" size="sm">
              <Plus className="w-4 h-4 mr-2" />
              新增批次
            </Button>
          }
        />
      </div>

      <ScrollArea className="flex-1 min-h-0">
        <div className="p-2">
          {batchList?.map((batch) => {
            const isSelected = batch.id === selectedBatchId;
            const isHovered = batch.id === hoveredId;
            const progress =
              itemCount > 0 ? (completedCount / itemCount) * 100 : 0;
            const status = progress === 100 ? "active" : "pending";
            const config =
              progress === 100 ? statusConfig.active : statusConfig.pending;
            const StatusIcon = config.icon;

            return (
              <div
                key={batch.id}
                onMouseEnter={() => setHoveredId(batch.id)}
                onMouseLeave={() => setHoveredId(null)}
                className={cn(
                  "relative group w-full text-left p-3 rounded-lg mb-2 transition-colors cursor-pointer",
                  "hover:bg-accent/50",
                  isSelected && "bg-accent"
                )}
                onClick={() => onSelectBatch(batch.id)}>
                <div className="flex items-start justify-between mb-2">
                  <h3
                    className={cn(
                      "font-medium text-sm leading-relaxed line-clamp-1 flex-1 pr-2",
                      isSelected ? "text-foreground" : "text-foreground/90"
                    )}>
                    {batch.id}:{batch.name}
                  </h3>

                  <div className="flex items-center gap-1">
                    <StatusIcon
                      className={cn("w-4 h-4 flex-shrink-0", config.color)}
                    />
                    {(isHovered || editingId === batch.id) && (
                      <div className="flex gap-0.5 ml-1">
                        <BatchDialog
                          type="edit"
                          item={batch}
                          onSave={(batchData, isNew) => {
                            handleSave(batchData, isNew);
                            setEditingId(null);
                          }}
                          trigger={
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-6 w-6 p-0 hover:bg-primary/10"
                              onClick={(e) => {
                                e.stopPropagation();
                                setEditingId(batch.id);
                              }}>
                              <Edit className="w-3 h-3" />
                            </Button>
                          }
                        />
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-6 w-6 p-0 hover:bg-destructive/10 hover:text-destructive"
                          onClick={(e) => handleDelete(batch.id, e)}>
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-center justify-between text-xs mb-2">
                  <span className="text-muted-foreground">
                    {completedCount}/{itemCount} 已完成
                  </span>
                  <Badge
                    variant="secondary"
                    className={cn("text-xs", config.bgColor, config.color)}>
                    {config.label}
                  </Badge>
                </div>

                <div className="w-full h-1 bg-secondary rounded-full overflow-hidden">
                  <div
                    className={cn(
                      "h-full transition-all duration-300",
                      status === "active" ? "bg-blue-500" : "bg-gray-300"
                    )}
                    style={{ width: `${progress}%` }}
                  />
                </div>

                <div className="text-xs text-muted-foreground mt-2">
                  创建于 {batch.created_at.split("T")[0]}
                </div>
              </div>
            );
          })}
        </div>
      </ScrollArea>
    </div>
  );
}
