import * as React from "react";
import { toast } from "sonner";
import {
  getVotesWithMessages,
  type VoteStatsQuery,
  type VoteWithMessage,
  type PaginatedResponse,
} from "@/utils/request/vote";

interface VoteData {
  items: VoteWithMessage[];
  total: number;
  page: number;
  size: number;
  has_next: boolean;
  has_prev: boolean;
}

interface SearchParams {
  vote_type: "good" | "medium" | "bad" | "all";
  page: number;
  size: number;
  start_date?: string;
  end_date?: string;
  searchKeyword?: string;
  client_type?: string;
}

export function useVoteData() {
  // 状态管理
  const [loading, setLoading] = React.useState(false);
  const [voteData, setVoteData] = React.useState<VoteData>({
    items: [],
    total: 0,
    page: 1,
    size: 10,
    has_next: false,
    has_prev: false,
  });

  const [searchParams, setSearchParams] = React.useState<SearchParams>({
    vote_type: "all",
    page: 1,
    size: 10,
    start_date: new Date().toISOString().split('T')[0],
    end_date: "",
    searchKeyword: "",
    client_type: "",
  });

  // 缓存数据，避免重复请求
  const [cachedQueries, setCachedQueries] = React.useState<Map<string, PaginatedResponse<VoteWithMessage>>>(new Map());

  // 生成查询缓存键
  const getQueryCacheKey = React.useCallback((params: SearchParams) => {
    return JSON.stringify({
      vote_type: params.vote_type,
      page: params.page,
      size: params.size,
      start_date: params.start_date,
      end_date: params.end_date,
      searchKeyword: params.searchKeyword,
      client_type: params.client_type,
    });
  }, []);

  // 获取投票数据（带缓存）
  const fetchVoteData = React.useCallback(async (force = false) => {
    const cacheKey = getQueryCacheKey(searchParams);

    // 检查缓存（除非强制刷新）
    if (!force && cachedQueries.has(cacheKey)) {
      const cachedData: any = cachedQueries.get(cacheKey)!;
      setVoteData({
        items: cachedData.items,
        total: cachedData.total,
        page: searchParams.page,
        size: searchParams.size,
        has_next: searchParams.page < Math.ceil(cachedData.total / searchParams.size),
        has_prev: searchParams.page > 1,
      });
      return cachedData;
    }

    setLoading(true);
    try {
      const query: VoteStatsQuery = {
        page: searchParams.page,
        size: searchParams.size,
        vote_type: searchParams.vote_type === "all" ? undefined : searchParams.vote_type,
        start_date: searchParams.start_date || undefined,
        end_date: searchParams.end_date || undefined,
        searchKeyword: searchParams.searchKeyword || undefined,
        client_type: searchParams.client_type || undefined,
      };

      const result: any = await getVotesWithMessages(query);

      // 更新缓存
      setCachedQueries((prev) => new Map(prev).set(cacheKey, result));

      setVoteData({
        items: result.items,
        total: result.total,
        page: searchParams.page,
        size: searchParams.size,
        has_next: searchParams.page < Math.ceil(result.total / searchParams.size),
        has_prev: searchParams.page > 1,
      });

      return result;
    } catch (error) {
      console.error("获取投票数据失败:", error);
      toast.error("获取投票数据失败");
      setVoteData({
        items: [],
        total: 0,
        page: 1,
        size: 10,
        has_next: false,
        has_prev: false,
      });
      throw error;
    } finally {
      setLoading(false);
    }
  }, [searchParams, getQueryCacheKey, cachedQueries]);

  // 处理搜索
  const handleSearch = React.useCallback((searchKeyword?: string) => {
    setSearchParams((prev) => ({
      ...prev,
      searchKeyword: searchKeyword !== undefined ? searchKeyword : prev.searchKeyword,
      page: 1, // 搜索时重置到第一页
    }));
  }, []);

  // 处理重置
  const handleReset = React.useCallback(() => {
    setSearchParams({
      vote_type: "all",
      page: 1,
      size: 10,
      start_date: new Date().toISOString().split('T')[0], // 直接计算当前日期
      end_date: "",
      searchKeyword: "",
      client_type: "",
    });
  }, []);

  // 处理投票类型变化
  const handleVoteTypeChange = React.useCallback((voteType: "good" | "medium" | "bad" | "all") => {
    setSearchParams((prev) => ({
      ...prev,
      vote_type: voteType,
      page: 1, // 类型变化时重置到第一页
    }));
  }, []);

  // 处理日期变化
  const handleDateRangeChange = React.useCallback((startDate?: string, endDate?: string) => {
    setSearchParams((prev) => ({
      ...prev,
      start_date: startDate,
      end_date: endDate,
      page: 1, // 日期变化时重置到第一页
    }));
  }, []);

  // 处理请求来源变化
  const handleClientTypeChange = React.useCallback((clientType: string) => {
    setSearchParams((prev) => ({
      ...prev,
      client_type: clientType === "all" ? "" : clientType,
      page: 1, // 请求来源变化时重置到第一页
    }));
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
      page: 1, // 页面大小变化时重置到第一页
      size,
    }));
  }, []);

  // 处理刷新
  const handleRefresh = React.useCallback(() => {
    return fetchVoteData(true); // 强制刷新
  }, [fetchVoteData]);

  // 初始化时获取数据
  React.useEffect(() => {
    fetchVoteData();
  }, [fetchVoteData]);

  // 计算分页信息
  const totalPages = Math.ceil(voteData.total / voteData.size);
  const hasNextPage = voteData.page < totalPages;
  const hasPrevPage = voteData.page > 1;

  return {
    // 数据
    voteData,
    searchParams,

    // 状态
    loading,

    // 分页信息
    totalPages,
    hasNextPage,
    hasPrevPage,

    // 方法
    handleSearch,
    handleReset,
    handleVoteTypeChange,
    handleDateRangeChange,
    handleClientTypeChange,
    handlePageChange,
    handlePageSizeChange,
    handleRefresh,
  };
}