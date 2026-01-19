import instance from "./instance";
import { toast } from "sonner";

// 搜索请求接口
export interface SearchRequest {
  query: string;
}

// QA搜索结果接口
export interface QAResult {
  id: number;
  question: string;
  answer: string;
  hybrid_score: string;
}

// 文档搜索结果接口
export interface DocResult {
  id: number;
  title: string;
  answer: string;
  hybrid_score: string;
}

export interface SearchResult{
    qa: QAResult[];
    qa_hybrid: QAResult[];
    doc_hybrid_rff: QAResult[];
    doc_hybrid_bm25: QAResult[];
}

// 搜索响应接口
export interface SearchResponse {
  code: number;
  message: string;
  data: SearchResult;
}




// 知识详情接口
export interface KnowledgeDetail {
  id: number;
  knowledge_id: number;
  content: string;
  role: string;
  reference: string;
  status: string;
  version: number;
  created_at: string;
  updated_at: string;
}

// 知识详情响应接口
export interface KnowledgeDetailResponse {
  code: number;
  message: string;
  data: KnowledgeDetail[];
}

// 执行搜索
export async function searchKnowledge(
  params: SearchRequest
): Promise<SearchResponse> {
  try {
    const response = await instance.post<SearchResponse>(
      "/v1/admin/knowledge-search/",
      params
    );
    return response.data;
  } catch (error: any) {
    toast.error(error.message || "搜索失败");
    throw error;
  }
}

// 获取知识详情
export async function getKnowledgeDetails(
  knowledgeId: number
): Promise<KnowledgeDetailResponse> {
  try {
    const response = await instance.get<KnowledgeDetailResponse>(
      `/v1/admin/knowledge/details/${knowledgeId}`
    );
    return response.data;
  } catch (error: any) {
    toast.error(error.message || "获取知识详情失败");
    throw error;
  }
}

// ========== 表格数据搜索相关类型 ==========

/** 表格行数据结果 */
export interface DataTableRowResult {
  row: Record<string, any>;
  score: number;
  knowledge_data_id: number;
}

/** 知识库详情信息 */
export interface KnowledgeDetailInfo {
  knowledge_id: number;
  content: string | null;
  reference: string | null;
  version: number | null;
}

/** 完整搜索结果（表格数据 + 知识详情） */
export interface DataTableSearchResult {
  table_data: DataTableRowResult;
  knowledge_detail: KnowledgeDetailInfo;
}

/** 表格搜索请求 */
export interface DataTableSearchRequest {
  query: string;
  top_n?: number;
  threshold?: number;
}

/** 表格搜索响应 */
export interface DataTableSearchResponse {
  results: DataTableSearchResult[];
  count: number;
}

/** API 响应包装 */
export interface DataTableAPIResponse {
  code: number;
  message: string;
  data: DataTableSearchResponse;
}

/**
 * 搜索数据表格（返回表格记录 + 知识库详情）
 */
export async function searchDataTable(
  params: DataTableSearchRequest
): Promise<DataTableSearchResponse> {
  try {
    const response = await instance.post<DataTableSearchResponse>(
      "/v1/admin/knowledge/search-knowledge-data",
      params
    );
    return response.data;
  } catch (error: any) {
    toast.error(error.message || "搜索数据表格失败");
    throw error;
  }
}

