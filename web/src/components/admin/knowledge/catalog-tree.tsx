import * as React from "react";
import {
  IconFolder,
  IconChevronDown,
  IconChevronRight,
} from "@tabler/icons-react";
import { Button } from "@/components/ui/button";
import type {
  CatalogTreeNode,
  KnowledgeCatalog,
} from "@/utils/request/knowledge-catalog";

interface CatalogTreeProps {
  catalogTree: Record<string, Record<string, CatalogTreeNode[]>>;
  catalogs: KnowledgeCatalog[]; // 用于ID反查
  selectedCatalogId?: number | null;
  onCatalogSelect?: (catalog: {
    id: number;
    level1: string;
    level2: string;
    level3: string;
    path: string;
  }) => void;
  loading?: boolean;
}

export const CatalogTree: React.FC<CatalogTreeProps> = ({
  catalogTree,
  catalogs,
  selectedCatalogId,
  onCatalogSelect,
  loading = false,
}) => {
  const [expandedNodes, setExpandedNodes] = React.useState<Set<string>>(
    new Set(["root"])
  );

  // 计算当前选中目录的路径（用于高亮）
  const selectedPath = React.useMemo(() => {
    if (!selectedCatalogId) return null;
    const catalog = catalogs.find((c) => c.id === selectedCatalogId);
    if (!catalog) return null;
    return `level3-${catalog.category_level_1}-${catalog.category_level_2}-${catalog.category_level_3}`;
  }, [selectedCatalogId, catalogs]);

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

  // 处理目录选择（仅限三级目录）
  const handleCatalogSelect = (
    level1: string,
    level2: string,
    node: CatalogTreeNode
  ) => {
    if (onCatalogSelect) {
      const path = `${level1}/${level2}/${node.name}`;
      onCatalogSelect({
        id: node.id,
        level1,
        level2,
        level3: node.name,
        path,
      });
    }
  };

  // 渲染三级目录树
  const renderCatalogTree = () => {
    if (loading) {
      return (
        <div className="py-8 text-center text-sm text-muted-foreground">
          加载中...
        </div>
      );
    }

    if (!catalogTree || typeof catalogTree !== "object") {
      return (
        <div className="py-8 text-center text-sm text-muted-foreground">
          暂无目录数据
        </div>
      );
    }

    return (
      <div className="space-y-1 p-2">
        {catalogTree &&
          catalogTree[0] &&
          Object.entries(catalogTree[0]).map(([level1, level2Data]) => {
            const level1Path = `level1-${level1}`;
            const isLevel1Expanded = expandedNodes.has(level1Path);

            return (
              <div key={level1} className="flex flex-col">
                {/* 一级目录 */}
                <div
                  className={`flex items-center py-2 px-3 rounded cursor-pointer transition-colors ${
                    false
                      ? "bg-primary text-primary-foreground"
                      : "hover:bg-accent"
                  }`}
                  onClick={() => toggleNode(level1Path)}>
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

                {/* 二级目录 */}
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
                              className={`flex items-center py-2 px-3 rounded cursor-pointer transition-colors ${
                                false
                                  ? "bg-primary text-primary-foreground"
                                  : "hover:bg-accent"
                              }`}
                              onClick={() => toggleNode(level2Path)}>
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
                              <IconFolder
                                className="h-4 w-4 mr-2 text-muted-foreground"
                              />
                              <span className="flex-1 truncate">{level2}</span>
                            </div>

                            {/* 三级目录（可选择） */}
                            {isLevel2Expanded &&
                              Array.isArray(level3Data) && (
                                <div className="ml-4">
                                  {level3Data.map((node) => {
                                    const level3Path = `level3-${level1}-${level2}-${node.name}`;
                                    const isSelected =
                                      selectedPath === level3Path;
                                    return (
                                      <div
                                        key={node.id}
                                        className={`flex items-center py-2 px-3 rounded cursor-pointer transition-colors ${
                                          isSelected
                                            ? "bg-primary text-primary-foreground"
                                            : "hover:bg-accent"
                                        }`}
                                        onClick={() =>
                                          handleCatalogSelect(
                                            level1,
                                            level2,
                                            node
                                          )
                                        }>
                                        <div className="w-5 h-5 mr-1" />
                                        <IconFolder
                                          className="h-4 w-4 mr-2 text-muted-foreground"
                                        />
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

  return (
    <div className="h-full overflow-y-auto">{renderCatalogTree()}</div>
  );
};

CatalogTree.displayName = "CatalogTree";
