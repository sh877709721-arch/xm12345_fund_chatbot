import instance from "./instance";
import { toast } from "sonner";

// ==================== 类型定义 ====================

export type GuidelineStatus = 'A' | 'I' | 'D' | 'X';

export interface GuidelineItem {
  id: number;
  title: string;
  condition: string;
  action: string;
  prompt_template?: string;
  priority: number;
  status: GuidelineStatus;
  created_time: string;
  updated_time: string;
}

export interface GuidelineCreateRequest {
  title: string;
  condition: string;
  action: string;
  prompt_template?: string;
  priority: number;
  status: GuidelineStatus;
}

export interface GuidelineUpdateRequest {
  title?: string;
  condition?: string;
  action?: string;
  prompt_template?: string;
  priority?: number;
  status?: GuidelineStatus;
}

export interface GuidelineSearchParams {
  title?: string;
  condition?: string;
  action?: string;
  status?: GuidelineStatus | 'all';
  priority_min?: number;
  priority_max?: number;
  orderby?: 'id' | 'created_time' | 'priority';
  order?: 'asc' | 'desc';
  page: number;
  size: number;
}

export interface GuidelineListResponse {
  items: GuidelineItem[];
  total: number;
  page: number;
  size: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface GuidelineMatchRequest {
  context: string;
  candidate_top_k?: number;
  vector_top_k?: number;
  bm25_top_k?: number;
  similarity_threshold?: number;
  use_llm_refinement?: boolean;
}

export interface GuidelineMatchResult {
  guideline_id: number;
  title: string;
  condition: string;
  action: string;
  prompt_template?: string;
  priority: number;
  match_score?: number;
  match_method: 'llm' | 'rrf' | 'rrf_fallback';
  confidence?: number;
}

// ==================== API 函数 ====================

// 获取所有指南
export async function getGuidelines(): Promise<GuidelineItem[]> {
  try {
    const response = await instance.get<GuidelineItem[]>("/v1/admin/guidelines");
    return response.data;
  } catch (error: any) {
    toast.error("获取指南列表失败");
    throw error;
  }
}

// 搜索指南（分页 + 多条件）
export async function searchGuidelines(
  params: GuidelineSearchParams
): Promise<GuidelineListResponse> {
  try {
    const response = await instance.post<GuidelineListResponse>(
      "/v1/admin/guidelines/search",
      params
    );
    return response.data;
  } catch (error: any) {
    console.error("搜索指南失败:", error);
    throw error;
  }
}

// 获取单个指南
export async function getGuideline(id: number): Promise<GuidelineItem> {
  try {
    const response = await instance.get<GuidelineItem>(
      `/v1/admin/guidelines/${id}`
    );
    return response.data;
  } catch (error: any) {
    toast.error("获取指南失败");
    throw error;
  }
}

// 创建指南
export async function createGuideline(
  data: GuidelineCreateRequest
): Promise<GuidelineItem> {
  try {
    const response = await instance.post<GuidelineItem>(
      "/v1/admin/guidelines",
      data
    );
    toast.success("指南创建成功");
    return response.data;
  } catch (error: any) {
    toast.error(error.response?.data?.detail || "创建指南失败");
    throw error;
  }
}

// 更新指南
export async function updateGuideline(
  id: number,
  data: GuidelineUpdateRequest
): Promise<GuidelineItem> {
  try {
    const response = await instance.put<GuidelineItem>(
      `/v1/admin/guidelines/${id}`,
      data
    );
    toast.success("指南更新成功");
    return response.data;
  } catch (error: any) {
    toast.error(error.response?.data?.detail || "更新指南失败");
    throw error;
  }
}

// 删除指南（软删除）
export async function deleteGuideline(id: number): Promise<void> {
  try {
    await instance.delete(`/v1/admin/guidelines/${id}`);
    toast.success("指南已删除");
  } catch (error: any) {
    toast.error("删除指南失败");
    throw error;
  }
}

// 智能匹配测试
export async function matchGuideline(
  request: GuidelineMatchRequest
): Promise<GuidelineMatchResult | null> {
  try {
    const response = await instance.post<{ data: GuidelineMatchResult | null }>(
      "/v1/admin/guidelines/match",
      request
    );
    return response.data.data;
  } catch (error: any) {
    toast.error("匹配测试失败");
    throw error;
  }
}
