import * as React from "react";
import {
  IconChevronDown,
  IconEdit,
  IconFolder,
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

interface CatalogManagerProps {
  onCatalogSelect: (
    catalog: { level1: string; level2: string; level3: string } | null
  ) => void;
}

// 新增子组件：目录列表视图
function CatalogListView({
  catalogs,
  onEdit,
  onDelete,
}: {
  catalogs: KnowledgeCatalog[];
  onEdit: (catalog: KnowledgeCatalog) => void;
  onDelete: (catalogId: number, catalogName: string) => void;
  onCreate?: () => void;
}) {
  return (
    <div className="max-h-96">
      <div className="grid grid-cols-4 gap-2 py-2 font-semibold border-b">
        <div>一级目录</div>
        <div>二级目录</div>
        <div>三级目录</div>
        <div className="text-right">操作</div>
      </div>
      {catalogs.map((catalog) => (
        <div key={catalog.id} className="grid grid-cols-4 gap-2 py-2 border-b">
          <div>{catalog.category_level_1}</div>
          <div>{catalog.category_level_2}</div>
          <div>{catalog.category_level_3}</div>
          <div className="flex justify-end gap-1">
            <Button size="sm" variant="outline" onClick={() => onEdit(catalog)}>
              编辑
            </Button>
            <Button
              size="sm"
              variant="destructive"
              onClick={() =>
                onDelete(
                  catalog.id,
                  `${catalog.category_level_1}/${catalog.category_level_2}/${catalog.category_level_3}`
                )
              }>
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
  );
}

// 新增子组件：目录表单视图
function CatalogFormView({
  newCatalog,
  setNewCatalog,
}: {
  editingCatalog?: KnowledgeCatalog | null;
  newCatalog: {
    name: string;
    catalog_level_1: string;
    catalog_level_2: string;
    catalog_level_3: string;
  };
  setNewCatalog: React.Dispatch<
    React.SetStateAction<{
      name: string;
      catalog_level_1: string;
      catalog_level_2: string;
      catalog_level_3: string;
    }>
  >;
}) {
  return (
    <div className="grid gap-4 py-4">
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="level1" className="text-right">
          一级目录 *
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
          placeholder="请输入一级目录名称"
        />
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="level2" className="text-right">
          二级目录 *
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
          placeholder="请输入二级目录名称"
        />
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="level3" className="text-right">
          三级目录 *
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
          placeholder="请输入三级目录名称"
        />
      </div>
    </div>
  );
}

export function CatalogManager({ onCatalogSelect }: CatalogManagerProps) {
  const [treeData, setTreeData] = React.useState<
    Record<string, Record<string, CatalogTreeNode[]>>
  >({});
  const [open, setOpen] = React.useState(false);
  // const [expandedNodes, setExpandedNodes] = React.useState<Set<string>>(
  //   new Set()
  // );
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
      console.error("获取目录树失败:", error);
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
      console.error("获取目录列表失败:", error);
      toast.error("获取目录列表失败");
    }
  }, []);

  React.useEffect(() => {
    fetchCatalogTree();
    fetchCatalogs();
  }, [fetchCatalogTree, fetchCatalogs]);

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

  // 渲染三级目录结构
  const renderCatalogTree = () => {
    return Object.entries(treeData).map(([level1, level2Data]) => (
      <div key={level1} className="flex flex-col">
        <div
          className="font-medium py-1 px-2 hover:bg-accent rounded-sm cursor-pointer flex items-center"
          onClick={() => handleCatalogSelect(level1, "", "")}>
          <IconFolder className="h-4 w-4 mr-2 text-muted-foreground" />
          {level1}
        </div>
        <div className="ml-4 pl-2 border-l">
          {Object.entries(level2Data).map(([level2, level3Data]) => (
            <div key={level2} className="flex flex-col">
              <div
                className="py-1 px-2 hover:bg-accent rounded-sm cursor-pointer flex items-center"
                onClick={() => handleCatalogSelect(level1, level2, "")}>
                <IconFolder className="h-4 w-4 mr-2 text-muted-foreground" />
                {level2}
              </div>
              <div className="ml-4 pl-2 border-l">
                {level3Data.map((node) => (
                  <div
                    key={node.id}
                    className="py-1 px-2 hover:bg-accent rounded-sm cursor-pointer flex items-center"
                    onClick={() =>
                      handleCatalogSelect(level1, level2, node.name)
                    }>
                    <IconFolder className="h-4 w-4 mr-2 text-muted-foreground" />
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

  // 添加状态来跟踪当前视图
  const [currentView, setCurrentView] = React.useState<"list" | "form">("list");

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
    setOpen(false); // 关闭筛选下拉菜单
    setCurrentView("form"); // 切换到表单视图
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
    setOpen(false); // 关闭筛选下拉菜单
    setCurrentView("form"); // 切换到表单视图
  };

  // 返回列表视图
  const handleBackToList = () => {
    setCurrentView("list");
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
          setCurrentView("list"); // 保存后返回列表
        }
      } else {
        // 创建新目录
        const data = await createKnowledgeCatalog({
          //name: newCatalog.name,
          catalog_level_1: newCatalog.catalog_level_1,
          catalog_level_2: newCatalog.catalog_level_2,
          catalog_level_3: newCatalog.catalog_level_3,
        });
        if (data) {
          toast.success("目录创建成功");
          fetchCatalogTree();
          fetchCatalogs();
          setCurrentView("list"); // 保存后返回列表
        }
      }
    } catch (error) {
      console.error(editingCatalog ? "目录更新失败:" : "目录创建失败:", error);
      toast.error(editingCatalog ? "目录更新失败" : "目录创建失败");
    }
  };

  // 删除目录
  const handleDeleteCatalog = async (
    catalogId: number,
    catalogName: string
  ) => {
    try {
      // 确认删除
      if (!window.confirm(`确定要删除目录 "${catalogName}" 吗？`)) {
        return;
      }

      const data = await deleteKnowledgeCatalog(catalogId);
      if (data) {
        toast.success("目录删除成功");
        fetchCatalogTree();
        fetchCatalogs();
      }
    } catch (error) {
      console.error("目录删除失败:", error);
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
            {Object.keys(treeData).length > 0 ? (
              renderCatalogTree()
            ) : (
              <div className="py-2 text-center text-sm text-muted-foreground">
                暂无目录数据
              </div>
            )}
          </DropdownMenuContent>
        </DropdownMenu>

        <Button variant="outline" size="icon" onClick={handleCreateCatalog}>
          <IconEdit className="h-4 w-4" />
        </Button>
      </div>

      {/* 管理目录对话框 */}
      <Dialog open={manageDialogOpen} onOpenChange={setManageDialogOpen}>
        <DialogHeader>
          <DialogTitle>
            {currentView === "list"
              ? "目录管理"
              : editingCatalog
                ? "编辑目录"
                : "新增目录"}
          </DialogTitle>
          <DialogDescription>
            {currentView === "list"
              ? "管理现有目录，可以编辑或删除"
              : editingCatalog
                ? "修改目录信息，点击保存更新目录"
                : "填写目录信息，点击保存创建新目录"}
          </DialogDescription>
        </DialogHeader>

        <DialogContent className="sm:max-w-[600px] overflow-y-auto">
          {currentView === "list" ? (
            <CatalogListView
              catalogs={catalogs}
              onEdit={handleEditCatalog}
              onDelete={handleDeleteCatalog}
              onCreate={handleCreateCatalog}
            />
          ) : (
            <CatalogFormView
              editingCatalog={editingCatalog}
              newCatalog={newCatalog}
              setNewCatalog={setNewCatalog}
            />
          )}
        </DialogContent>

        <DialogFooter>
          {currentView === "list" ? (
            <Button onClick={handleCreateCatalog}>
              <IconPlus className="h-4 w-4 mr-2" />
              新增目录
            </Button>
          ) : (
            <div className="flex gap-2">
              <Button variant="outline" onClick={handleBackToList}>
                返回
              </Button>
              <Button onClick={handleSaveCatalog}>保存</Button>
            </div>
          )}
        </DialogFooter>
      </Dialog>
    </>
  );
}
