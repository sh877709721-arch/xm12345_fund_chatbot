import instance from "./instance";

// ============================================================
// Dashboard 数据类型定义
// ============================================================

/** 趋势数据点 */
export interface TrendDataPoint {
  date: string;  // 日期（格式：MM-DD）
  value: number; // 数值
}

/** 时段数据点 */
export interface TimeSlotDataPoint {
  time: string;  // 时段（00-06, 06-12, 12-18, 18-24）
  value: number; // 数值
}

/** 来源数据点 */
export interface SourceDataPoint {
  name: string;  // 来源名称
  value: number; // 数量
}

/** 高频问题 */
export interface TopQuestion {
  question: string; // 问题内容
  count: number;    // 出现次数
}

/** 核心 KPI 统计 */
export interface KpiStats {
  total_qa: number;       // 总问答数
  avg_daily_qa: number;   // 平均每日问答数
  total_votes: number;    // 总投票数
  good_rate: number;      // 好评率（百分比）
}

/** 问答趋势统计 */
export interface TrendStats {
  series: TrendDataPoint[]; // 趋势数据序列
}

/** 问答时段分布统计 */
export interface TimeSlotStats {
  series: TimeSlotDataPoint[]; // 时段数据序列
}

/** 问答来源分布统计 */
export interface SourceStats {
  distribution: SourceDataPoint[]; // 来源分布数据
}

/** 高频问答TOP5统计 */
export interface TopQuestionsStats {
  questions: TopQuestion[]; // 高频问题列表
}

/** 投票类型统计 */
export interface VoteTypeStats {
  good_count: number;   // 好评数
  medium_count: number; // 中评数
  bad_count: number;    // 差评数
  total_count: number;  // 总投票数
}

/** 完整大屏数据 */
export interface DashboardData {
  kpi: KpiStats;
  trend: TrendStats;
  time_slot: TimeSlotStats;
  source: SourceStats;
  top_questions: TopQuestionsStats;
  vote_stats: VoteTypeStats;
}

// ============================================================
// Dashboard API 请求函数
// ============================================================

/**
 * 获取核心KPI统计
 * @param startDate 开始日期（可选）
 * @param endDate 结束日期（可选）
 */
export async function getKpiStats(
  startDate?: string,
  endDate?: string
): Promise<KpiStats> {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);

  const response = await instance.get<any>(
    `/v1/admin/dashboard/kpi${params.toString() ? `?${params.toString()}` : ''}`
  );
  return response as unknown as KpiStats;
}

/**
 * 获取问答趋势统计
 * @param startDate 开始日期（可选）
 * @param endDate 结束日期（可选）
 */
export async function getTrendStats(
  startDate?: string,
  endDate?: string
): Promise<TrendStats> {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);

  const response = await instance.get<any>(
    `/v1/admin/dashboard/trend${params.toString() ? `?${params.toString()}` : ''}`
  );
  return response as unknown as TrendStats;
}

/**
 * 获取问答时段分布统计
 * @param startDate 开始日期（可选）
 * @param endDate 结束日期（可选）
 */
export async function getTimeSlotStats(
  startDate?: string,
  endDate?: string
): Promise<TimeSlotStats> {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);

  const response = await instance.get<any>(
    `/v1/admin/dashboard/time-slot${params.toString() ? `?${params.toString()}` : ''}`
  );
  return response as unknown as TimeSlotStats;
}

/**
 * 获取问答来源分布统计
 * @param startDate 开始日期（可选）
 * @param endDate 结束日期（可选）
 */
export async function getSourceStats(
  startDate?: string,
  endDate?: string
): Promise<SourceStats> {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);

  const response = await instance.get<any>(
    `/v1/admin/dashboard/source${params.toString() ? `?${params.toString()}` : ''}`
  );
  return response as unknown as SourceStats;
}

/**
 * 获取高频问答TOP5
 * @param startDate 开始日期（可选）
 * @param endDate 结束日期（可选）
 * @param limit 返回数量（默认5）
 */
export async function getTopQuestions(
  startDate?: string,
  endDate?: string,
  limit: number = 5
): Promise<TopQuestionsStats> {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  params.append('limit', limit.toString());

  const response = await instance.get<any>(
    `/v1/admin/dashboard/top-questions?${params.toString()}`
  );
  return response as unknown as TopQuestionsStats;
}

/**
 * 获取投票类型统计
 * @param startDate 开始日期（可选）
 * @param endDate 结束日期（可选）
 */
export async function getVoteStats(
  startDate?: string,
  endDate?: string
): Promise<VoteTypeStats> {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);

  const response = await instance.get<any>(
    `/v1/admin/dashboard/vote-stats${params.toString() ? `?${params.toString()}` : ''}`
  );
  return response as unknown as VoteTypeStats;
}

/**
 * 获取完整的大屏数据（一次调用返回所有统计数据）
 * @param startDate 开始日期（可选）
 * @param endDate 结束日期（可选）
 */
export async function getFullDashboard(
  startDate?: string,
  endDate?: string
): Promise<DashboardData> {

  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);

  const url = `/v1/admin/dashboard/full${params.toString() ? `?${params.toString()}` : ''}`;

  try {
    const response = await instance.get<any>(url);
    return response as unknown as DashboardData;
  } catch (error) {
    throw error;
  }
}
