import * as React from "react";
import { toast } from "sonner";
import {
  searchKnowledgeEntries,
  type KnowledgeEntry,
  type KnowledgeType,
} from "@/utils/request/knowledge-entries";
import {
  getKnowledgeCatalogs,
  getKnowledgeCatalogTree,
  type KnowledgeCatalog,
  type CatalogTreeNode,
} from "@/utils/request/knowledge-catalog";

export interface SearchParams {
  name: string;
  knowledge_type: KnowledgeType | "all";
  status?:string | null;
  page: number;
  size: number;
}

interface SelectedCatalog {
  level1: string;
  level2: string;
  level3: string;
}

interface KnowledgeData {
  items: KnowledgeEntry[];
  total: number;
  page: number;
  size: number;
  has_next: boolean;
  has_prev: boolean;
}

export function useKnowledgeData() {
  // 状态管理
  const [loading, setLoading] = React.useState(false);
  const [catalogsLoading, setCatalogsLoading] = React.useState(false);

  const [knowledgeData, setKnowledgeData] = React.useState<KnowledgeData>({
    items: [],
    total: 0,
    page: 1,
    size: 10,
    has_next: false,
    has_prev: false,
  });

  const [searchParams, setSearchParams] = React.useState<SearchParams>({
    name: "",
    knowledge_type: "qa",
    status: "all",
    page: 1,
    size: 10,
  });

  const [selectedCatalog, setSelectedCatalog] = React.useState<SelectedCatalog | null>(null);

  // 缓存目录数据
  const [catalogs, setCatalogs] = React.useState<KnowledgeCatalog[]>([]);
  const [catalogTree, setCatalogTree] = React.useState<Record<string, Record<string, CatalogTreeNode[]>>>({});

  // 获取目录数据（带缓存）
  const fetchCatalogs = React.useCallback(async (force = false) => {
    if (!force && catalogs.length > 0) {
      return catalogs; // 返回缓存数据
    }

    setCatalogsLoading(true);
    try {
      const [catalogsData, treeData] = await Promise.all([
        getKnowledgeCatalogs(),
        getKnowledgeCatalogTree(),
      ]);

      setCatalogs(catalogsData as unknown as KnowledgeCatalog[]);
      setCatalogTree(treeData as unknown as Record<string, Record<string, CatalogTreeNode[]>>);
      return catalogsData;
    } catch (error) {
      console.error("获取目录数据失败:", error);
      toast.error("获取目录数据失败");
      return [];
    } finally {
      setCatalogsLoading(false);
    }
  }, [catalogs.length]);

  // 获取知识条目数据
  const fetchKnowledgeEntries = React.useCallback(async () => {
    setLoading(true);
    try {
      const data = await searchKnowledgeEntries({
        page: searchParams.page,
        size: searchParams.size,
        catalog_level_1: selectedCatalog?.level1 || undefined,
        catalog_level_2: selectedCatalog?.level2 || undefined,
        catalog_level_3: selectedCatalog?.level3 || undefined,
        knowledge_type: searchParams.knowledge_type !== "all" ? searchParams.knowledge_type : undefined,
        name: searchParams.name || undefined,
        status: searchParams.status && searchParams.status !== "all" ? searchParams.status : undefined,
      });

      setKnowledgeData(data as KnowledgeData);
    } catch (error) {
      console.error("获取知识条目失败:", error);
      toast.error("获取知识条目失败");
      setKnowledgeData({
        items: [],
        total: 0,
        page: 1,
        size: 10,
        has_next: false,
        has_prev: false,
      });
    } finally {
      setLoading(false);
    }
  }, [searchParams, selectedCatalog]);

  // 处理目录选择
  const handleCatalogSelect = React.useCallback((catalog: SelectedCatalog | null) => {
    setSelectedCatalog(catalog);
    setSearchParams((prev) => ({
      ...prev,
      page: 1, // 切换目录时回到第一页
    }));
  }, []);

  // 处理搜索
  const handleSearch = React.useCallback((name?: string, knowledgeType?: KnowledgeType | "all", status?: string) => {
    setSearchParams((prev) => ({
      ...prev,
      name: name !== undefined ? name : prev.name,
      knowledge_type: knowledgeType !== undefined ? knowledgeType : prev.knowledge_type,
      status: status !== undefined ? status : prev.status,
      page: 1, // 搜索时重置到第一页
    }));
  }, []);

  // 重置搜索
  const handleReset = React.useCallback(() => {
    setSearchParams({
      name: "",
      knowledge_type: "all",
      status: "all",
      page: 1,
      size: 10,
    });
    setSelectedCatalog(null);
  }, []);

  // 处理分页变化
  const handlePageChange = React.useCallback((page: number) => {
    setSearchParams((prev) => ({
      ...prev,
      page,
    }));
  }, []);

  // 处理页面大小变化
  const handlePageSizeChange = React.useCallback((size: number) => {
    setSearchParams((prev) => ({
      ...prev,
      page: 1, // 页面大小变化时回到第一页
      size,
    }));
  }, []);

  // 初始化时获取目录数据
  React.useEffect(() => {
    fetchCatalogs();
  }, []);

  // 当搜索参数或选中目录改变时获取知识条目
  React.useEffect(() => {
    fetchKnowledgeEntries();
  }, [fetchKnowledgeEntries]);

  // 刷新目录数据（用于CRUD操作后）
  const refreshCatalogs = React.useCallback(async () => {
    await fetchCatalogs(true); // 强制刷新
  }, [fetchCatalogs]);

  // 简单的本地更新方法 - 更新本地数据而不重新请求
  const updateLocalKnowledgeEntry = React.useCallback((updatedEntry: KnowledgeEntry) => {
    if (!updatedEntry || !updatedEntry.id) {
      return;
    }

    setKnowledgeData((prev) => ({
      ...prev,
      items: prev.items.map((item) =>
        item.id === updatedEntry.id ? { ...item, ...updatedEntry } : item
      ),
    }));
  }, []);

  return {
    // 数据
    knowledgeData,
    catalogs,
    catalogTree,
    selectedCatalog,
    searchParams,

    // 状态
    loading,
    catalogsLoading,

    // 方法
    handleCatalogSelect,
    handleSearch,
    handleReset,
    handlePageChange,
    handlePageSizeChange,
    refreshCatalogs,

    // 本地更新方法
    updateLocalKnowledgeEntry,
  };
}