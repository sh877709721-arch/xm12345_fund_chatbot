import * as React from "react";
import { toast } from "sonner";
import {
  searchGuidelines,
  deleteGuideline,
  type GuidelineItem,
  type GuidelineSearchParams,
  //type GuidelineStatus,
} from "@/utils/request/guideline";

interface SearchParams extends GuidelineSearchParams {}

interface GuidelineData {
  items: GuidelineItem[];
  total: number;
  page: number;
  size: number;
  has_next: boolean;
  has_prev: boolean;
}

export function useGuidelineData() {
  // 状态管理
  const [loading, setLoading] = React.useState(false);

  const [guidelineData, setGuidelineData] = React.useState<GuidelineData>({
    items: [],
    total: 0,
    page: 1,
    size: 10,
    has_next: false,
    has_prev: false,
  });

  const [searchParams, setSearchParams] = React.useState<SearchParams>({
    title: "",
    condition: "",
    action: "",
    status: "all",
    priority_min: undefined,
    priority_max: undefined,
    orderby: "id",
    order: "desc",
    page: 1,
    size: 10,
  });

  // 获取指南数据
  const fetchGuidelines = React.useCallback(async () => {
    setLoading(true);
    try {
      const data = await searchGuidelines({
        title: searchParams.title || undefined,
        condition: searchParams.condition || undefined,
        action: searchParams.action || undefined,
        status: searchParams.status !== "all" ? searchParams.status : undefined,
        priority_min: searchParams.priority_min,
        priority_max: searchParams.priority_max,
        orderby: searchParams.orderby,
        order: searchParams.order,
        page: searchParams.page,
        size: searchParams.size,
      });

      setGuidelineData(data);
    } catch (error) {
      console.error("获取指南失败:", error);
      toast.error("获取指南失败");
      setGuidelineData({
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
  }, [searchParams]);

  // 处理搜索
  const handleSearch = React.useCallback(
    (params?: Partial<SearchParams>) => {
      setSearchParams((prev) => ({
        ...prev,
        ...params,
        page: 1, // 搜索时重置到第一页
      }));
    },
    []
  );

  // 重置搜索
  const handleReset = React.useCallback(() => {
    setSearchParams({
      title: "",
      condition: "",
      action: "",
      status: "all",
      priority_min: undefined,
      priority_max: undefined,
      orderby: "id",
      order: "desc",
      page: 1,
      size: 10,
    });
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
      page: 1,
      size,
    }));
  }, []);

  // 刷新数据
  const handleRefresh = React.useCallback(() => {
    fetchGuidelines();
  }, [fetchGuidelines]);

  // 本地更新方法（避免刷新）
  const updateLocalGuideline = React.useCallback(
    (updatedItem: GuidelineItem) => {
      setGuidelineData((prev) => ({
        ...prev,
        items: prev.items.map((item) =>
          item.id === updatedItem.id ? { ...item, ...updatedItem } : item
        ),
      }));
    },
    []
  );

  // 删除指南
  const handleDelete = React.useCallback(async (id: number) => {
    try {
      await deleteGuideline(id);
      // 重新获取数据
      fetchGuidelines();
    } catch (error) {
      console.error("删除指南失败:", error);
    }
  }, [fetchGuidelines]);

  // 当搜索参数改变时获取数据
  React.useEffect(() => {
    fetchGuidelines();
  }, [fetchGuidelines]);

  return {
    // 数据
    guidelineData,
    searchParams,

    // 状态
    loading,

    // 方法
    handleSearch,
    handleReset,
    handlePageChange,
    handlePageSizeChange,
    handleRefresh,
    updateLocalGuideline,
    handleDelete,
  };
}
