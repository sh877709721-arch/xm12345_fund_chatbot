import type { VoteWithMessage, PaginatedResponse, VoteStatsQuery } from '@/utils/request/vote';

// 重新导出投票相关类型
export type {
  VoteType,
  VoteWithMessage,
  PaginatedResponse,
  VoteStatsQuery
} from '@/utils/request/vote';

// 投票统计数据摘要接口
export interface VoteStatsSummary {
  total: number;              // 总投票数
  good: number;               // 好评数
  medium: number;             // 中评数
  bad: number;                // 差评数
  goodRate: number;           // 好评率 (0-100)
  mediumRate: number;         // 中评率 (0-100)
  badRate: number;            // 差评率 (0-100)
}

// 投票统计Hook返回类型
export interface UseVoteStatsReturn {
  fetchVoteStats: (query?: VoteStatsQuery) => Promise<PaginatedResponse<VoteWithMessage> | null>;
  fetchGoodVotes: (page?: number, size?: number, startDate?: string, endDate?: string) => Promise<PaginatedResponse<VoteWithMessage> | null>;
  fetchMediumVotes: (page?: number, size?: number, startDate?: string, endDate?: string) => Promise<PaginatedResponse<VoteWithMessage> | null>;
  fetchBadVotes: (page?: number, size?: number, startDate?: string, endDate?: string) => Promise<PaginatedResponse<VoteWithMessage> | null>;
  fetchAllVotes: (page?: number, size?: number, startDate?: string, endDate?: string) => Promise<PaginatedResponse<VoteWithMessage> | null>;
  loading: boolean;
  error: string | null;
}

// 计算投票统计摘要的工具函数
export const calculateVoteStatsSummary = (data: VoteWithMessage[]): VoteStatsSummary => {
  const total = data.length;
  const good = data.filter(vote => vote.vote_type === 'good').length;
  const medium = data.filter(vote => vote.vote_type === 'medium').length;
  const bad = data.filter(vote => vote.vote_type === 'bad').length;

  return {
    total,
    good,
    medium,
    bad,
    goodRate: total > 0 ? Math.round((good / total) * 100) : 0,
    mediumRate: total > 0 ? Math.round((medium / total) * 100) : 0,
    badRate: total > 0 ? Math.round((bad / total) * 100) : 0
  };
};