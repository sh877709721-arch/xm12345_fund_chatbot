"use client";

import type React from "react";

import { useState, type ReactNode, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import type { KnowledgeLabelBatch } from "@/utils/request/knowledge-label";

type DialogType = "add" | "edit";

type BatchDialogProps = {
  type: DialogType;
  item?: KnowledgeLabelBatch;
  onSave: (batch: KnowledgeLabelBatch, isNew: boolean) => void;
  trigger: ReactNode;
};

export function BatchDialog({ type, item, onSave, trigger }: BatchDialogProps) {
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState<Partial<KnowledgeLabelBatch>>(
    item || {
      name: "",
      created_at: new Date().toISOString().split("T")[0],
    }
  );

  useEffect(() => {
    if (open) {
      setFormData(
        item || {
          name: "",
          created_at: new Date().toISOString().split("T")[0],
        }
      );
    }
  }, [open, item]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData as KnowledgeLabelBatch, type === "add");
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>
              {type === "add" ? "新增批次" : "编辑批次"}
            </DialogTitle>
            <DialogDescription>
              {type === "add" ? "创建新的标注批次" : "修改批次信息"}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">批次名称</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                placeholder="输入批次名称"
                required
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}>
              取消
            </Button>
            <Button type="submit">{type === "add" ? "创建" : "保存"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}