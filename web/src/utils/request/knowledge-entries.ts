import instance from "./instance";
import { toast } from "sonner";

// 知识条目类型枚举
export type KnowledgeType = "qa" | "document" | "data_table";

// 知识条目状态枚举
export type KnowledgeStatus = "pending" | "active" | "deleted";

// 知识条目详情接口
export interface KnowledgeDetails {
  content: string;
  role: string;
  status: KnowledgeStatus;
  created_by: number;
  version: number;
  reference?: string; // 参考资料链接或标识
}

// 知识条目请求接口
export interface KnowledgeRequest {
  knowledge_type: KnowledgeType;
  knowledge_catalog_id: number;
  name: string;
  details: KnowledgeDetails;
  created_by: number;
}

// 更新知识条目请求接口 (部分字段可选)
export interface UpdateKnowledgeRequest {
  knowledge_type?: KnowledgeType;
  knowledge_catalog_id?: number;
  name?: string;
  details?: KnowledgeDetails;
  created_by?: number;
}

// 知识条目接口
export interface KnowledgeEntry {
  id: number;
  knowledge_type: KnowledgeType;
  name: string;
  knowledge_catalog_id: number;
  status: KnowledgeStatus;
  created_at: string;
  updated_at: string;
  details?: KnowledgeDetails | null; // 添加details字段，可选且可能为null
}

// 知识条目创建响应接口
export interface KnowledgeEntryResponse {
  code: number;
  message: string;
  data: KnowledgeEntry;
}

// 多个知识条目响应接口
export interface KnowledgeEntriesResponse {
  code: number;
  message: string;
  data: KnowledgeEntry[];
}

// 分页知识条目响应接口
export interface PaginatedKnowledgeEntriesResponse {
  items: KnowledgeEntry[];
  total: number;
  page: number;
  size: number;
  has_next: boolean;
  has_prev: boolean;
}

// 修改搜索参数接口以支持新参数
export interface SearchKnowledgeEntriesParams {
  page?: number;
  size?: number;
  knowledge_type?: KnowledgeType;
  name?: string;
  catalog_level_1?: string;
  catalog_level_2?: string;
  catalog_level_3?: string;
  status?: string;
  orderby?: 'id' | 'created_at' | 'updated_at';  // 新增
  order?: 'asc' | 'desc';  // 新增
}

// 创建知识条目
export async function createKnowledgeEntry(
  knowledge: KnowledgeRequest
): Promise<KnowledgeEntryResponse> {
  try {
    const response = await instance.post<KnowledgeEntryResponse>(
      "/v1/admin/knowledge/entries",
      knowledge
    );
    return response.data;
  } catch (error: any) {
    toast.error(error.response?.data?.detail || error.message || "知识条目创建失败");
    throw error;
  }
}

// 更新知识条目
export async function updateKnowledgeEntry(
  id: number,
  knowledge: UpdateKnowledgeRequest
): Promise<KnowledgeEntryResponse> {
  try {
    const response = await instance.put<KnowledgeEntryResponse>(
      `/v1/admin/knowledge/entries/${id}`,
      knowledge
    );
    return response.data;
  } catch (error: any) {
    toast.error(error.response?.data?.detail || error.message || "知识条目更新失败");
    throw error;
  }
}

// 获取知识条目列表
export async function searchKnowledgeEntries(
  params: SearchKnowledgeEntriesParams = {}
): Promise<PaginatedKnowledgeEntriesResponse> {
  try {
    const { page, size, knowledge_type, name, catalog_level_1, catalog_level_2, catalog_level_3, status, orderby, order } = params;

    const requestParams: Record<string, any> = {
      page,
      size,
    };

    // 添加新的目录层级参数
    if (catalog_level_1 !== undefined) {
      requestParams.catalog_level_1 = catalog_level_1;
    }

    if (catalog_level_2 !== undefined) {
      requestParams.catalog_level_2 = catalog_level_2;
    }

    if (catalog_level_3 !== undefined) {
      requestParams.catalog_level_3 = catalog_level_3;
    }

    if (knowledge_type !== undefined) {
      requestParams.knowledge_type = knowledge_type;
    }

    if (name !== undefined) {
      requestParams.name = name;
    }

    if (status !== undefined) {
      requestParams.status = status;
    }

    // 新增：传递排序参数
    if (orderby !== undefined) {
      requestParams.orderby = orderby;
    }

    if (order !== undefined) {
      requestParams.order = order;
    }

    const response = await instance.post<PaginatedKnowledgeEntriesResponse>(
      "/v1/admin/knowledge/entries/search",
      requestParams
    );
    return response.data;
  } catch (error: any) {
    toast.error(error.response?.data?.detail || error.message || "获取知识条目列表失败");
    throw error;
  }
}

// Excel 上传响应接口
export interface ExcelUploadResponse {
  status: string;
  knowledge_data_id: number;
  rows_processed: number;
  columns: number;
  message: string;
}

// 上传 Excel 文件
export async function uploadKnowledgeExcel(
  knowledgeId: number,
  file: File
): Promise<{ data: ExcelUploadResponse }> {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await instance.post<{ data: ExcelUploadResponse }>(
      `/v1/admin/knowledge/upload-excel?knowledge_id=${knowledgeId}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  } catch (error: any) {
    toast.error(error.response?.data?.detail || error.message || "Excel 上传失败");
    throw error;
  }
}

// 知识数据搜索响应接口
export interface KnowledgeDataSearchResult {
  row: Record<string, any>;
  score: number;
  knowledge_data_id: number;
}

export interface KnowledgeDataSearchResponse {
  results: KnowledgeDataSearchResult[];
  count: number;
}

// 搜索知识数据
export async function searchKnowledgeData(
  knowledgeId: number,
  query: string,
  topN: number = 10
): Promise<KnowledgeDataSearchResponse> {
  try {
    const response = await instance.post<{ data: KnowledgeDataSearchResponse }>(
      "/v1/admin/knowledge/search-data",
      {
        knowledge_id: knowledgeId,
        query: query,
        top_n: topN,
      }
    );
    return response.data.data;
  } catch (error: any) {
    toast.error(error.response?.data?.detail || error.message || "搜索知识数据失败");
    throw error;
  }
}