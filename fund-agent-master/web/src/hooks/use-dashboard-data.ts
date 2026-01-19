import { useState, useEffect, useCallback } from "react";
import { getFullDashboard } from "@/utils/request/dashboard";
import type {
  DashboardData,
  KpiStats,
  TrendStats,
  TimeSlotStats,
  SourceStats,
  TopQuestionsStats,
} from "@/utils/request/dashboard";

/**
 * 获取完整大屏数据的 Hook
 * @param startDate 开始日期（可选）
 * @param endDate 结束日期（可选）
 */
export function useDashboardData(startDate?: string, endDate?: string) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getFullDashboard(startDate, endDate);
      setData(result);
    } catch (err: any) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

/**
 * 获取 KPI 统计的 Hook
 * @param startDate 开始日期（可选）
 * @param endDate 结束日期（可选）
 */
export function useKpiStats(startDate?: string, endDate?: string) {
  const [data, setData] = useState<KpiStats | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await getFullDashboard(startDate, endDate);
        setData(result.kpi);
      } catch (err: any) {
        setError(err);
        console.error("获取KPI统计失败:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [startDate, endDate]);

  return { data, loading, error };
}

/**
 * 获取问答趋势统计的 Hook
 * @param startDate 开始日期（可选）
 * @param endDate 结束日期（可选）
 */
export function useTrendStats(startDate?: string, endDate?: string) {
  const [data, setData] = useState<TrendStats | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await getFullDashboard(startDate, endDate);
        setData(result.trend);
      } catch (err: any) {
        setError(err);
        console.error("获取趋势统计失败:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [startDate, endDate]);

  return { data, loading, error };
}

/**
 * 获取时段分布统计的 Hook
 * @param startDate 开始日期（可选）
 * @param endDate 结束日期（可选）
 */
export function useTimeSlotStats(startDate?: string, endDate?: string) {
  const [data, setData] = useState<TimeSlotStats | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await getFullDashboard(startDate, endDate);
        setData(result.time_slot);
      } catch (err: any) {
        setError(err);
        console.error("获取时段分布统计失败:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [startDate, endDate]);

  return { data, loading, error };
}

/**
 * 获取来源分布统计的 Hook
 * @param startDate 开始日期（可选）
 * @param endDate 结束日期（可选）
 */
export function useSourceStats(startDate?: string, endDate?: string) {
  const [data, setData] = useState<SourceStats | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await getFullDashboard(startDate, endDate);
        setData(result.source);
      } catch (err: any) {
        setError(err);
        console.error("获取来源分布统计失败:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [startDate, endDate]);

  return { data, loading, error };
}

/**
 * 获取高频问答 TOP5 的 Hook
 * @param startDate 开始日期（可选）
 * @param endDate 结束日期（可选）
 */
export function useTopQuestions(startDate?: string, endDate?: string) {
  const [data, setData] = useState<TopQuestionsStats | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await getFullDashboard(startDate, endDate);
        setData(result.top_questions);
      } catch (err: any) {
        setError(err);
        console.error("获取高频问答失败:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [startDate, endDate]);

  return { data, loading, error };
}
