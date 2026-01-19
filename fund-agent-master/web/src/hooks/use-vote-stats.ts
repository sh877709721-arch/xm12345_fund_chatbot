import { useState, useCallback } from 'react';
import { getVotesWithMessages } from '@/utils/request/vote';
import type { VoteStatsQuery, VoteWithMessage, PaginatedResponse } from '@/utils/request/vote';

export const useVoteStats = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 获取投票统计数据
  const fetchVoteStats = useCallback(async (
    query: VoteStatsQuery = {}
  ): Promise<PaginatedResponse<VoteWithMessage>> => {
    setLoading(true);
    setError(null);

    try {
      const result = await getVotesWithMessages(query);
      return result;
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || error.message || '获取投票统计失败';
      setError(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  // 获取好评列表
  const fetchGoodVotes = useCallback(async (
    page = 1,
    size = 10,
    startDate?: string,
    endDate?: string
  ) => {
    return fetchVoteStats({
      page,
      size,
      vote_type: 'good',
      start_date: startDate,
      end_date: endDate
    });
  }, [fetchVoteStats]);

  // 获取中评列表
  const fetchMediumVotes = useCallback(async (
    page = 1,
    size = 10,
    startDate?: string,
    endDate?: string
  ) => {
    return fetchVoteStats({
      page,
      size,
      vote_type: 'medium',
      start_date: startDate,
      end_date: endDate
    });
  }, [fetchVoteStats]);

  // 获取差评列表
  const fetchBadVotes = useCallback(async (
    page = 1,
    size = 10,
    startDate?: string,
    endDate?: string
  ) => {
    return fetchVoteStats({
      page,
      size,
      vote_type: 'bad',
      start_date: startDate,
      end_date: endDate
    });
  }, [fetchVoteStats]);

  // 获取所有投票列表
  const fetchAllVotes = useCallback(async (
    page = 1,
    size = 10,
    startDate?: string,
    endDate?: string
  ) => {
    return fetchVoteStats({
      page,
      size,
      start_date: startDate,
      end_date: endDate
    });
  }, [fetchVoteStats]);

  return {
    fetchVoteStats,
    fetchGoodVotes,
    fetchMediumVotes,
    fetchBadVotes,
    fetchAllVotes,
    loading,
    error
  };
};