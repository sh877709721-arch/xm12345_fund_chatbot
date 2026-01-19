import * as React from "react";
import { toast } from "sonner";
import {
  getFeedbacks,
  type FeedbackItem,
  type FeedbackQuery,
} from "@/utils/request/feedback";

const getTodayStartISO = () => {
  const now = new Date();
  const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0, 0);
  return startOfDay.toISOString();
};

interface FeedbackDataState {
  items: FeedbackItem[];
  total: number;
  page: number;
  size: number;
  has_next: boolean;
  has_prev: boolean;
}

interface SearchParams {
  page: number;
  size: number;
  content?: string;
  phone?: string;
  start_date?: string;
  end_date?: string;
}

export function useFeedbackData() {
  const [loading, setLoading] = React.useState(false);
  const [feedbackData, setFeedbackData] = React.useState<FeedbackDataState>({
    items: [],
    total: 0,
    page: 1,
    size: 10,
    has_next: false,
    has_prev: false,
  });

  const [searchParams, setSearchParams] = React.useState<SearchParams>({
    page: 1,
    size: 10,
    content: "",
    phone: "",
    start_date: getTodayStartISO(),
    end_date: "",
  });

  const fetchFeedbackData = React.useCallback(async () => {
    setLoading(true);
    try {
      const query: FeedbackQuery = {
        page: searchParams.page,
        size: searchParams.size,
        content: searchParams.content || undefined,
        phone: searchParams.phone || undefined,
        start_date: searchParams.start_date || undefined,
        end_date: searchParams.end_date || undefined,
      };

      const result = await getFeedbacks(query);
      setFeedbackData({
        items: result.items,
        total: result.total,
        page: searchParams.page,
        size: searchParams.size,
        has_next: result.has_next,
        has_prev: result.has_prev,
      });
      return result;
    } catch (error) {
      console.error("获取反馈数据失败:", error);
      toast.error("获取反馈数据失败");
      setFeedbackData({
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
  }, [searchParams]);

  const handleSearch = React.useCallback((params: { content?: string; phone?: string }) => {
    setSearchParams((prev) => ({
      ...prev,
      content: params.content !== undefined ? params.content : prev.content,
      phone: params.phone !== undefined ? params.phone : prev.phone,
      page: 1,
    }));
  }, []);

  const handleReset = React.useCallback(() => {
    setSearchParams({
      page: 1,
      size: 10,
      content: "",
      phone: "",
      start_date: getTodayStartISO(),
      end_date: "",
    });
  }, []);

  const handleDateRangeChange = React.useCallback((startDate?: string, endDate?: string) => {
    setSearchParams((prev) => ({
      ...prev,
      start_date: startDate,
      end_date: endDate,
      page: 1,
    }));
  }, []);

  const handlePageChange = React.useCallback((page: number) => {
    setSearchParams((prev) => ({
      ...prev,
      page,
    }));
  }, []);

  const handlePageSizeChange = React.useCallback((size: number) => {
    setSearchParams((prev) => ({
      ...prev,
      page: 1,
      size,
    }));
  }, []);

  const handleRefresh = React.useCallback(() => {
    return fetchFeedbackData();
  }, [fetchFeedbackData]);

  React.useEffect(() => {
    fetchFeedbackData();
  }, [fetchFeedbackData]);

  const totalPages = Math.ceil(feedbackData.total / feedbackData.size || 1);
  const hasNextPage = feedbackData.has_next ?? feedbackData.page < totalPages;
  const hasPrevPage = feedbackData.has_prev ?? feedbackData.page > 1;

  return {
    feedbackData,
    searchParams,
    loading,
    totalPages,
    hasNextPage,
    hasPrevPage,
    handleSearch,
    handleReset,
    handleDateRangeChange,
    handlePageChange,
    handlePageSizeChange,
    handleRefresh,
  };
}

