import * as React from "react";
import {
  IconChevronDown,
  IconEdit,
  IconFolder,
  IconFolderOpen,
  IconPlus,
  IconTrash,
} from "@tabler/icons-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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
import { toast } from "sonner";
import {
  getKnowledgeCatalogTree,
  getKnowledgeCatalogs,
  createKnowledgeCatalog,
  updateKnowledgeCatalog,
  deleteKnowledgeCatalog,
  type CatalogTreeNode,
  type KnowledgeCatalog,
} from "@/utils/request/knowledge-catalog";

interface CatalogFilterProps {
  onCatalogSelect: (
    catalog: { level1: string; level2: string; level3: string } | null
  ) => void;
}

export function CatalogFilter({ onCatalogSelect }: CatalogFilterProps) {
  const [treeData, setTreeData] = React.useState<
    Record<string, Record<string, CatalogTreeNode[]>>
  >({});
  const [open, setOpen] = React.useState(false);
  const [expandedNodes, setExpandedNodes] = React.useState<Set<string>>(
    new Set()
  );
  const [manageDialogOpen, setManageDialogOpen] = React.useState(false);
  const [catalogs, setCatalogs] = React.useState<KnowledgeCatalog[]>([]);
  const [editingCatalog, setEditingCatalog] =
    React.useState<KnowledgeCatalog | null>(null);
  const [newCatalog, setNewCatalog] = React.useState({
    name: "",
    catalog_level_1: "",
    catalog_level_2: "",
    catalog_level_3: "",
  });

  // 获取目录树数据
  const fetchCatalogTree = React.useCallback(async () => {
    try {
      const data = await getKnowledgeCatalogTree();
      if (data) {
        setTreeData(data);
      }
    } catch (error) {
      toast.error("获取目录树失败");
    }
  }, []);

  // 获取所有目录数据
  const fetchCatalogs = React.useCallback(async () => {
    try {
      const data = await getKnowledgeCatalogs();
      if (data) {
        setCatalogs(data);
      }
    } catch (error) {
      toast.error("获取目录列表失败");
    }
  }, []);

  React.useEffect(() => {
    fetchCatalogTree();
    fetchCatalogs();
  }, [fetchCatalogTree, fetchCatalogs]);

  // 切换节点展开/收起状态
  const toggleNode = (path: string) => {
    setExpandedNodes((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(path)) {
        newSet.delete(path);
      } else {
        newSet.add(path);
      }
      return newSet;
    });
  };

  // 处理目录选择
  const handleCatalogSelect = (
    level1: string,
    level2: string,
    level3: string
  ) => {
    onCatalogSelect({ level1, level2, level3 });
    setOpen(false);
  };

  // 重置筛选
  const handleResetFilter = () => {
    onCatalogSelect(null);
    setOpen(false);
  };

  // 渲染目录树节点
  const renderTreeNodes = (nodes: CatalogTreeNode[], path: string = "") => {
    return nodes.map((node) => {
      const currentPath = path ? `${path}-${node.id}` : `${node.id}`;
      const isExpanded = expandedNodes.has(currentPath);
      const hasChildren = node.children && node.children.length > 0;

      return (
        <div key={node.id} className="flex flex-col">
          <div className="flex items-center py-1 hover:bg-accent rounded-sm px-2 cursor-pointer">
            {hasChildren && (
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 mr-1"
                onClick={(e) => {
                  e.stopPropagation();
                  toggleNode(currentPath);
                }}>
                {isExpanded ? (
                  <IconChevronDown className="h-4 w-4" />
                ) : (
                  <IconChevronDown className="h-4 w-4 rotate-[-90deg]" />
                )}
              </Button>
            )}
            {!hasChildren && <div className="w-6 h-6 mr-1" />}
            {isExpanded && hasChildren ? (
              <IconFolderOpen className="h-4 w-4 mr-2 text-muted-foreground" />
            ) : (
              <IconFolder className="h-4 w-4 mr-2 text-muted-foreground" />
            )}
            <span
              className="flex-1 text-sm"
              onClick={(e) => {
                e.stopPropagation();
                // 这里可以处理点击节点的逻辑，暂时留空
              }}>
              {node.name}
            </span>
          </div>
          {isExpanded && hasChildren && (
            <div className="ml-4 pl-2 border-l">
              {renderTreeNodes(node.children || [], currentPath)}
            </div>
          )}
        </div>
      );
    });
  };

  // 渲染三级目录结构
  const renderCatalogTree = () => {
    return Object.entries(treeData).map(([level1, level2Data]) => (
      <div key={level1} className="flex flex-col">
        <div
          className="font-medium py-1 px-2 hover:bg-accent rounded-sm cursor-pointer"
          onClick={() => handleCatalogSelect(level1, "", "")}>
          {level1}
        </div>
        <div className="ml-2 pl-2 border-l">
          {Object.entries(level2Data).map(([level2, level3Data]) => (
            <div key={level2} className="flex flex-col">
              <div
                className="py-1 px-2 hover:bg-accent rounded-sm cursor-pointer"
                onClick={() => handleCatalogSelect(level1, level2, "")}>
                {level2}
              </div>
              <div className="ml-2 pl-2 border-l">
                {level3Data.map((node) => (
                  <div
                    key={node.id}
                    className="py-1 px-2 hover:bg-accent rounded-sm cursor-pointer"
                    onClick={() =>
                      handleCatalogSelect(level1, level2, node.name)
                    }>
                    {node.name}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    ));
  };

  // 打开编辑对话框
  const handleEditCatalog = (catalog: KnowledgeCatalog) => {
    setEditingCatalog(catalog);
    setNewCatalog({
      name: catalog.category_level_3,
      catalog_level_1: catalog.category_level_1,
      catalog_level_2: catalog.category_level_2,
      catalog_level_3: catalog.category_level_3,
    });
    setManageDialogOpen(true);
  };

  // 打开新增对话框
  const handleCreateCatalog = () => {
    setEditingCatalog(null);
    setNewCatalog({
      name: "",
      catalog_level_1: "",
      catalog_level_2: "",
      catalog_level_3: "",
    });
    setManageDialogOpen(true);
  };

  // 保存目录
  const handleSaveCatalog = async () => {
    try {
      if (editingCatalog) {
        // 更新目录
        const data = await updateKnowledgeCatalog(editingCatalog.id, {
          catalog_level_1: newCatalog.catalog_level_1,
          catalog_level_2: newCatalog.catalog_level_2,
          catalog_level_3: newCatalog.catalog_level_3,
        });
        if (data) {
          toast.success("目录更新成功");
          fetchCatalogTree();
          fetchCatalogs();
        }
      } else {
        // 创建新目录
        const data = await createKnowledgeCatalog({
          name: newCatalog.name,
          catalog_level_1: newCatalog.catalog_level_1,
          catalog_level_2: newCatalog.catalog_level_2,
          catalog_level_3: newCatalog.catalog_level_3,
        });
        if (data) {
          toast.success("目录创建成功");
          fetchCatalogTree();
          fetchCatalogs();
        }
      }
      setManageDialogOpen(false);
    } catch (error) {
      toast.error(editingCatalog ? "目录更新失败" : "目录创建失败");
    }
  };

  // 删除目录
  const handleDeleteCatalog = async (catalogId: number) => {
    try {
      const data = await deleteKnowledgeCatalog(catalogId);
      if (data) {
        toast.success("目录删除成功");
        fetchCatalogTree();
        fetchCatalogs();
      }
    } catch (error) {
      toast.error("目录删除失败");
    }
  };

  return (
    <>
      <div className="flex items-center gap-2">
        <DropdownMenu open={open} onOpenChange={setOpen}>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="gap-2">
              <IconFolder className="h-4 w-4" />
              目录筛选
              <IconChevronDown className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="start"
            className="w-64 max-h-96 overflow-y-auto">
            <DropdownMenuItem onClick={handleResetFilter}>
              全部目录
            </DropdownMenuItem>
            <div className="border-t my-1" />
            {renderCatalogTree()}
          </DropdownMenuContent>
        </DropdownMenu>

        <Dialog open={manageDialogOpen} onOpenChange={setManageDialogOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" size="icon" onClick={handleCreateCatalog}>
              <IconEdit className="h-4 w-4" />
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>
                {editingCatalog ? "编辑目录" : "新增目录"}
              </DialogTitle>
              <DialogDescription>
                {editingCatalog
                  ? "修改目录信息，点击保存更新目录"
                  : "填写目录信息，点击保存创建新目录"}
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="level1" className="text-right">
                  一级目录
                </Label>
                <Input
                  id="level1"
                  value={newCatalog.catalog_level_1}
                  onChange={(e) =>
                    setNewCatalog({
                      ...newCatalog,
                      catalog_level_1: e.target.value,
                    })
                  }
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="level2" className="text-right">
                  二级目录
                </Label>
                <Input
                  id="level2"
                  value={newCatalog.catalog_level_2}
                  onChange={(e) =>
                    setNewCatalog({
                      ...newCatalog,
                      catalog_level_2: e.target.value,
                    })
                  }
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="level3" className="text-right">
                  三级目录
                </Label>
                <Input
                  id="level3"
                  value={newCatalog.catalog_level_3}
                  onChange={(e) =>
                    setNewCatalog({
                      ...newCatalog,
                      catalog_level_3: e.target.value,
                    })
                  }
                  className="col-span-3"
                />
              </div>
            </div>
            <DialogFooter>
              <Button onClick={handleSaveCatalog}>保存</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* 管理目录对话框 */}
      <Dialog>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>管理目录</DialogTitle>
            <DialogDescription>
              管理所有知识库目录，可以新增、编辑或删除目录
            </DialogDescription>
          </DialogHeader>
          <div className="max-h-96 overflow-y-auto">
            <div className="grid grid-cols-4 gap-2 py-2 font-semibold border-b">
              <div>一级目录</div>
              <div>二级目录</div>
              <div>三级目录</div>
              <div className="text-right">操作</div>
            </div>
            {catalogs.map((catalog) => (
              <div
                key={catalog.id}
                className="grid grid-cols-4 gap-2 py-2 border-b">
                <div>{catalog.category_level_1}</div>
                <div>{catalog.category_level_2}</div>
                <div>{catalog.category_level_3}</div>
                <div className="flex justify-end gap-1">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleEditCatalog(catalog)}>
                    编辑
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => handleDeleteCatalog(catalog.id)}>
                    <IconTrash className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
            {catalogs.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                暂无目录数据
              </div>
            )}
          </div>
          <DialogFooter>
            <Button onClick={handleCreateCatalog}>
              <IconPlus className="h-4 w-4 mr-2" />
              新增目录
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
