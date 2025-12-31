import * as React from "react";
import { Input } from "@/components/ui/input";
//import { Label } from "@/components/ui/label";
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
import { IconFolder } from "@tabler/icons-react";
import type {
  KnowledgeCatalog,
  CatalogTreeNode,
} from "@/utils/request/knowledge-catalog";
import { CatalogTree } from "./catalog-tree";

interface CatalogSelectorProps {
  catalogs: KnowledgeCatalog[];
  catalogTree: Record<string, Record<string, CatalogTreeNode[]>>;
  selectedCatalogId?: number | null;
  onConfirm: (catalogId: number, catalogPath: string) => void;
  loading?: boolean;
}

export const CatalogSelector: React.FC<CatalogSelectorProps> = ({
  catalogs,
  catalogTree,
  selectedCatalogId,
  onConfirm,
  loading = false,
}) => {
  const [open, setOpen] = React.useState(false);
  const [tempSelectedId, setTempSelectedId] = React.useState<number | null>(
    null
  );

  // 根据ID查找目录信息
  const selectedCatalog = React.useMemo(() => {
    if (!selectedCatalogId) return null;
    const catalog = catalogs.find((c) => c.id === selectedCatalogId);
    if (!catalog) return null;
    return {
      id: catalog.id,
      level1: catalog.category_level_1,
      level2: catalog.category_level_2,
      level3: catalog.category_level_3,
      path: `${catalog.category_level_1}/${catalog.category_level_2}/${catalog.category_level_3}`,
    };
  }, [selectedCatalogId, catalogs]);

  // 处理目录选择
  const handleCatalogSelect = (catalog: {
    id: number;
    level1: string;
    level2: string;
    level3: string;
    path: string;
  }) => {
    setTempSelectedId(catalog.id);
  };

  // 处理确认
  const handleConfirm = () => {
    const finalId = tempSelectedId || selectedCatalogId;
    if (finalId) {
      const catalog = catalogs.find((c) => c.id === finalId);
      if (catalog) {
        const path = `${catalog.category_level_1}/${catalog.category_level_2}/${catalog.category_level_3}`;
        onConfirm(finalId, path);
      }
    }
    setOpen(false);
    setTempSelectedId(null);
  };

  // 处理取消
  const handleCancel = () => {
    setOpen(false);
    setTempSelectedId(null);
  };

  return (
    <div className="flex items-center gap-2">
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          <div className="flex-1 flex items-center gap-2">
            <Input
              value={selectedCatalog?.path || ""}
              placeholder="请选择知识目录"
              readOnly
              className="cursor-pointer flex-1"
            />
            <Button
              type="button"
              variant="outline"
              size="icon"
              onClick={() => setOpen(true)}>
              <IconFolder className="h-4 w-4" />
            </Button>
          </div>
        </DialogTrigger>

        <DialogContent className="sm:max-w-[500px] h-[500px] flex flex-col">
          <DialogHeader>
            <DialogTitle>选择知识目录</DialogTitle>
            <DialogDescription>
              请选择知识所属的三级目录
            </DialogDescription>
          </DialogHeader>

          <div className="flex-1 overflow-hidden border rounded-md">
            <CatalogTree
              catalogTree={catalogTree}
              catalogs={catalogs}
              selectedCatalogId={tempSelectedId || selectedCatalogId}
              onCatalogSelect={handleCatalogSelect}
              loading={loading}
            />
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={handleCancel}>
              取消
            </Button>
            <Button onClick={handleConfirm}>确认</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

CatalogSelector.displayName = "CatalogSelector";
