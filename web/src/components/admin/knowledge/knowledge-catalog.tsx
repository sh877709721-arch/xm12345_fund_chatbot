import * as React from "react";
import {
  IconFolder,
  IconChevronDown,
  IconChevronRight,
  IconEdit,
  IconPlus,
  IconTrash,
} from "@tabler/icons-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import {
  type CatalogTreeNode,
  type KnowledgeCatalog,
  createKnowledgeCatalog,
  updateKnowledgeCatalog,
  deleteKnowledgeCatalog,
} from "@/utils/request/knowledge-catalog";
import { CardContent } from "@/components/ui/card";
import CatalogEditForm from "@/components/admin/knowledge/catalog-edit-form";

export type DialogStateType = "add" | "edit" | null;

interface KnowledgeCatalogProps {
  catalogTree: Record<string, Record<string, CatalogTreeNode[]>>;
  catalogs: KnowledgeCatalog[];
  loading: boolean;
  onCatalogSelect: (
    catalog: {
      level1: string;
      level2: string;
      level3: string;
    } | null
  ) => void;
  onCatalogRefresh?: () => Promise<void>;
}

const KnowledgeCatalogComp: React.FC<KnowledgeCatalogProps> = ({
  catalogTree,
  catalogs,
  loading,
  onCatalogSelect,
  onCatalogRefresh,
}) => {
  const [expandedNodes, setExpandedNodes] = React.useState<Set<string>>(
    new Set(["root"])
  );
  const [manageDialogOpen, setManageDialogOpen] = React.useState(false);

  const [formData, setFormData] = React.useState({
    id: 0,
    name: "",
    catalog_level_1: "",
    catalog_level_2: "",
    catalog_level_3: "",
  });
  const [dialogState, setDialogState] = React.useState<DialogStateType>(null);
  const [selectedPath, setSelectedPath] = React.useState<string | null>(null);

  // 切换节点展开/收起状态
  const toggleNode = (nodePath: string) => {
    setExpandedNodes((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(nodePath)) {
        newSet.delete(nodePath);
      } else {
        newSet.add(nodePath);
      }
      return newSet;
    });
  };

  // 处理目录选择
  const handleCatalogSelectInternal = (
    level1: string,
    level2: string,
    level3: string,
    path: string
  ) => {
    setSelectedPath(path);
    onCatalogSelect({ level1, level2, level3 });
  };

  // 重置筛选
  const handleResetFilter = () => {
    setSelectedPath(null);
    onCatalogSelect(null);
  };

  // 渲染三级目录结构
  const renderCatalogTree = () => {
    if (loading) {
      return (
        <div className="py-2 text-center text-sm text-muted-foreground">
          加载中...
        </div>
      );
    }

    if (!catalogTree || typeof catalogTree !== "object") {
      return (
        <div className="py-2 text-center text-sm text-muted-foreground">
          暂无目录数据
        </div>
      );
    }

    return (
      <div className="space-y-1 p-2">
        <div
          className={`flex items-center py-1 px-2 rounded cursor-pointer ${
            selectedPath === "all" ? "bg-primary/10" : "hover:bg-accent"
          }`}
          onClick={handleResetFilter}>
          <span className="ml-1">全部知识</span>
        </div>
        {catalogTree && catalogTree[0] && Object.entries(catalogTree[0]).map(([level1, level2Data]) => {
          const level1Path = `level1-${level1}`;
          const isLevel1Expanded = expandedNodes.has(level1Path);

          return (
            <div key={level1} className="flex flex-col">
              <div
                className={`flex items-center py-1 px-2 rounded cursor-pointer ${
                  selectedPath === level1Path
                    ? "bg-primary/10"
                    : "hover:bg-accent"
                }`}
                onClick={() => {
                  toggleNode(level1Path);
                  handleCatalogSelectInternal(level1, "", "", level1Path);
                }}>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-5 w-5 p-0 mr-1"
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleNode(level1Path);
                  }}>
                  {isLevel1Expanded ? (
                    <IconChevronDown className="h-4 w-4" />
                  ) : (
                    <IconChevronRight className="h-4 w-4" />
                  )}
                </Button>
                <IconFolder className="h-4 w-4 mr-2 text-muted-foreground" />
                <span className="flex-1 truncate">{level1}</span>
              </div>

              {isLevel1Expanded &&
                level2Data &&
                typeof level2Data === "object" && (
                  <div className="ml-4">
                    {Object.entries(level2Data).map(([level2, level3Data]) => {
                      const level2Path = `level2-${level1}-${level2}`;
                      const isLevel2Expanded = expandedNodes.has(level2Path);

                      return (
                        <div key={level2} className="flex flex-col">
                          <div
                            className={`flex items-center py-1 px-2 rounded cursor-pointer ${
                              selectedPath === level2Path
                                ? "bg-primary/10"
                                : "hover:bg-accent"
                            }`}
                            onClick={() => {
                              toggleNode(level2Path);
                              handleCatalogSelectInternal(
                                level1,
                                level2,
                                "",
                                level2Path
                              );
                            }}>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-5 w-5 p-0 mr-1"
                              onClick={(e) => {
                                e.stopPropagation();
                                toggleNode(level2Path);
                              }}>
                              {isLevel2Expanded ? (
                                <IconChevronDown className="h-4 w-4" />
                              ) : (
                                <IconChevronRight className="h-4 w-4" />
                              )}
                            </Button>
                            <IconFolder className="h-4 w-4 mr-2 text-muted-foreground" />
                            <span className="flex-1 truncate">{level2}</span>
                          </div>

                          {isLevel2Expanded && Array.isArray(level3Data) && (
                            <div className="ml-4">
                              {level3Data.map((node) => {
                                const level3Path = `level3-${level1}-${level2}-${node.name}`;
                                return (
                                  <div
                                    key={node.id}
                                    className={`flex items-center py-1 px-2 rounded cursor-pointer ${
                                      selectedPath === level3Path
                                        ? "bg-primary/10"
                                        : "hover:bg-accent"
                                    }`}
                                    onClick={() =>
                                      handleCatalogSelectInternal(
                                        level1,
                                        level2,
                                        node.name,
                                        level3Path
                                      )
                                    }>
                                    <div className="w-5 h-5 mr-1" />
                                    <IconFolder className="h-4 w-4 mr-2 text-muted-foreground" />
                                    <span className="flex-1 truncate">
                                      {node.name}
                                    </span>
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
            </div>
          );
        })}
      </div>
    );
  };

  // 打开编辑对话框
  const handleEditCatalog = (catalog: KnowledgeCatalog) => {
    setDialogState("edit");
    setFormData({
      id: catalog.id,
      name: catalog.category_level_3,
      catalog_level_1: catalog.category_level_1,
      catalog_level_2: catalog.category_level_2,
      catalog_level_3: catalog.category_level_3,
    });
    setManageDialogOpen(true);
  };

  // 打开新增对话框
  const handleCreateCatalog = () => {
    setFormData({
      id: -1,
      name: "",
      catalog_level_1: "",
      catalog_level_2: "",
      catalog_level_3: "",
    });
    setManageDialogOpen(true);
  };

  // 保存目录
  const handleSaveCatalog = async () => {
    if (
      !formData.catalog_level_1 ||
      !formData.catalog_level_2 ||
      !formData.catalog_level_3
    ) {
      toast.error("请填写完整的一级、二级和三级目录");
      return;
    }

    try {
      if (dialogState === "add") {
        await createKnowledgeCatalog(formData);
        toast.success("目录创建成功");
      } else if (dialogState === "edit") {
        await updateKnowledgeCatalog(formData.id, formData);
        toast.success("目录更新成功");
      }
    } catch (error) {
      toast.error("操作失败");
      return;
    }

    // 重新获取数据
    if (onCatalogRefresh) {
      await onCatalogRefresh();
    }

    setDialogState(null);
  };

  // 删除目录
  const handleDeleteCatalog = async () => {
    try {
      await deleteKnowledgeCatalog(formData.id);
      toast.success("目录删除成功");
    } catch (error) {
      toast.error("删除失败");
      return;
    }

    // 重新获取数据
    if (onCatalogRefresh) {
      await onCatalogRefresh();
    }

    setDialogState(null);
  };

  return (
    <div className="h-full flex flex-col border rounded-xl overflow-hidden">
      <div className="border-b px-4 py-2 flex items-center justify-between">
        <div className="w-full">
          {/* 顶部管理按钮 */}
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start"
            onClick={handleCreateCatalog}>
            <IconEdit className="h-4 w-4 mr-2" />
            管理目录
          </Button>
        </div>
      </div>
      <CardContent className="flex-1 p-0 overflow-auto">
        <div className="h-full flex flex-col">
          {/* 目录树 */}
          <div className="flex-1 overflow-y-auto">
            {renderCatalogTree()}
          </div>

          {/* 管理目录对话框 */}
          <Dialog open={manageDialogOpen} onOpenChange={setManageDialogOpen}>
            <DialogContent className="sm:max-w-[900px] p-8">
              <DialogHeader className="flex flex-row items-center justify-between">
                <div>
                  <DialogTitle>
                    {dialogState === "edit" ? "编辑目录" : "管理目录"}
                  </DialogTitle>
                  <DialogDescription>
                    {dialogState === "edit"
                      ? "修改目录信息，点击保存更新目录"
                      : "管理所有知识库目录，可以新增、编辑或删除目录"}
                  </DialogDescription>
                </div>
                {!dialogState ? (
                  <Button
                    variant="default"
                    size="sm"
                    onClick={() => {
                      // 设置为新建模式（清空正在编辑的对象）
                      //setEditingCatalog();
                      setDialogState("add");
                      setFormData({
                        id: -1,
                        name: "",
                        catalog_level_1: "",
                        catalog_level_2: "",
                        catalog_level_3: "",
                      });
                    }}>
                    <IconPlus className="h-4 w-4" />
                    <span className="hidden lg:inline ml-2">知识目录</span>
                  </Button>
                ) : null}
              </DialogHeader>

              {!dialogState ? (
                <div className="max-h-120">
                  <div className="grid grid-cols-4 gap-2 py-2 font-semibold border-b">
                    <div>一级目录</div>
                    <div>二级目录</div>
                    <div>三级目录</div>
                    <div className="text-right">操作</div>
                  </div>
                  <div className="max-h-96 overflow-y-auto">
                    {catalogs.map((catalog) => (
                      <div
                        key={catalog.id}
                        className="grid grid-cols-4 gap-2 py-2 border-b">
                        <div
                          className="truncate"
                          title={catalog.category_level_1}>
                          {catalog.category_level_1}
                        </div>
                        <div
                          className="truncate"
                          title={catalog.category_level_2}>
                          {catalog.category_level_2}
                        </div>
                        <div
                          className="truncate"
                          title={catalog.category_level_3}>
                          {catalog.category_level_3}
                        </div>
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
                            onClick={() => {
                              setFormData({
                                id: catalog.id,
                                name: catalog.category_level_3,
                                catalog_level_1: catalog.category_level_1,
                                catalog_level_2: catalog.category_level_2,
                                catalog_level_3: catalog.category_level_3,
                              });
                              handleDeleteCatalog();
                            }}>
                            <IconTrash className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>

                  {catalogs.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                      暂无目录数据
                    </div>
                  )}
                </div>
              ) : (
                <CatalogEditForm
                  dialogType={dialogState}
                  formData={formData}
                  onChange={setFormData}
                  onSave={handleSaveCatalog}
                  onCancel={() => setDialogState(null)}
                />
              )}
            </DialogContent>
          </Dialog>
        </div>
      </CardContent>
    </div>
  );
};

KnowledgeCatalogComp.displayName = "KnowledgeCatalogComp";

export { KnowledgeCatalogComp };
