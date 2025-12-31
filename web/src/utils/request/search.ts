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
