import instance from "./instance";
import { toast } from "sonner";

// 知识标注角色枚举
export type KnowledgeLabelRole = "system" | "user" | "assistant" | "admin";

// 知识条目状态枚举
export type KnowledgeStatus = "pending" | "active" | "deleted";

// 知识标注批次接口
export interface KnowledgeLabelBatch {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
}

// 知识标注条目接口
export interface KnowledgeLabel {
  id: number;
  batch_id: number;
  name: string;
  status: KnowledgeStatus;
  created_at: string;
  updated_at: string;
}

// 知识标注详情接口
export interface KnowledgeLabelWithDetail {
  batch_number: number;
  label_id: number;
  question: string;
  ai_content: string;
  user_content: string;
  is_passed: boolean;
  description: string;
  filled_by: string;
  create_at: string;
  update_at: string;
}

export interface KnowledgeLabelWithDetailPage {
  items: KnowledgeLabelWithDetail[];
  total: number;
  page: number;
  size: number;
  has_next: boolean;
  has_prev: boolean;
}

// 知识标注批次创建请求接口
export interface KnowledgeLabelBatchCreateRequest {
  name: string;
}
//知识标 更新请求接口
export interface KnowledgeLabelBatchUpdateRequest {
  name: string;
}

// 知识标注条目创建请求接口
export interface KnowledgeLabelCreateRequest {
  batch_id: number;
  name: string;
}

// 知识标注详情创建请求接口
export interface KnowledgeLabelDetailCreateRequest {
  label_id: number;
  content: string;
  role: KnowledgeLabelRole;
}

// 知识标注详情更新请求接口
export interface KnowledgeLabelDetailUpdateRequest {
  label_id: number;
  content: string;
  context: string;
  role: KnowledgeLabelRole;
  status: KnowledgeStatus;
  is_pass: boolean;
  description: string;
  filled_by: string;
}

// 知识标注批次响应接口
export interface KnowledgeLabelBatchResponse {
  code: number;
  message: string;
  data: KnowledgeLabelBatch;
}

// 知识标注条目响应接口
export interface KnowledgeLabelResponse {
  code: number;
  message: string;
  data: KnowledgeLabel;
}

// 知识标注详情响应接口
export interface KnowledgeLabelWithDetailResponse {
  code: number;
  message: string;
  data: KnowledgeLabelWithDetail[];
}

// 批量知识标注条目创建请求接口
export interface BatchKnowledgeLabelsCreateRequest {
  batch_id: number;
  names: string[];
}

export interface KnowledgeLabelsAndDetailsCreateRequest {
  name: string;
  ai_content: string;
  user_content: string;
  description?: string;
  is_passed?: boolean | null;
  filled_by?: string;
}

// 创建知识标注批次
export async function createKnowledgeLabelBatch(
  request: KnowledgeLabelBatchCreateRequest
): Promise<KnowledgeLabelBatch> {
  try {
    const response = await instance.post<KnowledgeLabelBatchResponse>(
      "/v1/admin/knowledge-label/batch",
      request
    );
    return response.data as unknown as KnowledgeLabelBatch;
  } catch (error: any) {
    toast.error(error.message || "Failed to create knowledge label batch");
    throw error;
  }
}

// 更新知识标注批次
export async function updateKnowledgeLabelBatch(
  id: number,
  request: KnowledgeLabelBatchUpdateRequest
): Promise<KnowledgeLabelBatchResponse> {
  try {
    const response = await instance.put<KnowledgeLabelBatchResponse>(
      `/v1/admin/knowledge-label/batch/${id}`,
      request
    );
    toast.success("知识标注批次更新成功");
    return response.data;
  } catch (error: any) {
    toast.error(error.message || "Failed to update knowledge label batch");
    throw error;
  }
}

// 删除知识标注批次
export async function deleteKnowledgeLabelBatch(
  batch_id: number
): Promise<KnowledgeLabelResponse> {
  try {
    const response = await instance.delete<KnowledgeLabelResponse>(
      `/v1/admin/knowledge-label/batch/${batch_id}`
    );
    toast.success("知识标注批次删除成功");
    return response.data;
  } catch (error: any) {
    toast.error(error.message || "Failed to delete knowledge label batch");
    throw error;
  }
}

// 获取知识标注批次
export async function getKnowledgeLabelBatch(
  batch_id: number
): Promise<KnowledgeLabelBatch[]> {
  try {
    const response = await instance.get<KnowledgeLabelBatch[]>(
      `/v1/admin/knowledge-label/batch/${batch_id}`
    );
    return response.data;
  } catch (error: any) {
    toast.error(error.message || "Failed to fetch knowledge label batch");
    throw error;
  }
}

export async function getKnowledgeLabelBatchs(): Promise<
  KnowledgeLabelBatch[]
> {
  try {
    const response = await instance.get<KnowledgeLabelBatch[]>(
      `/v1/admin/knowledge-label/batch`
    );
    return response.data;
  } catch (error: any) {
    toast.error(error.message || "Failed to fetch knowledge label batch");
    throw error;
  }
}

// 创建知识标注条目
export async function createKnowledgeLabel(
  batch_id: number,
  request: KnowledgeLabelsAndDetailsCreateRequest
): Promise<KnowledgeLabelResponse> {
  try {
    const response = await instance.post<KnowledgeLabelResponse>(
      `/v1/admin/knowledge-label/${batch_id}/label-detail`,
      request
    );
    toast.success("知识标注条目创建成功");
    return response.data;
  } catch (error: any) {
    toast.error(error.message || "Failed to create knowledge label");
    throw error;
  }
}

// 批量创建知识标注条目
export async function createKnowledgeLabels(
  request: BatchKnowledgeLabelsCreateRequest
): Promise<boolean> {
  try {
    const response = await instance.post<boolean>(
      `/v1/admin/knowledge-label/batch/${request.batch_id}/labels`,
      request.names
    );
    toast.success("知识标注条目批量创建成功");
    return response.data;
  } catch (error: any) {
    toast.error(error.message || "Failed to batch create knowledge labels");
    throw error;
  }
}

// 更新知识标注条目
export async function updateKnowledgeLabel(
  label_id: number,
  request: KnowledgeLabelsAndDetailsCreateRequest
): Promise<KnowledgeLabelResponse> {
  try {
    const response = await instance.put<KnowledgeLabelResponse>(
      `/v1/admin/knowledge-label/${label_id}/label-detail`,
      request
    );
    toast.success("知识标注条目更新成功");
    return response.data;
  } catch (error: any) {
    toast.error(error.message || "Failed to update knowledge label");
    throw error;
  }
}

// 获取知识标注条目
export async function getKnowledgeLabel(
  label_id: number
): Promise<KnowledgeLabel[]> {
  try {
    const response = await instance.get<KnowledgeLabel[]>(
      `/v1/admin/knowledge-label/${label_id}`
    );
    return response.data;
  } catch (error: any) {
    toast.error(error.message || "Failed to fetch knowledge label");
    throw error;
  }
}

// 分页获取知识标注条目

export interface KnowledgeLabelWithDetailRequest {
  batch_id: number;
  name?: string;
  pass_state?: "passed" | "unpassed" | "unchecked" | "all";
  filled_by?: string;
  page: number;
  size: number;
}

export async function getKnowledgeLabelsWithDetailsPaginationByBatchId(
  request: KnowledgeLabelWithDetailRequest
): Promise<KnowledgeLabelWithDetailPage> {
  try {
    const response = await instance.post<KnowledgeLabelWithDetailResponse>(
      "/v1/admin/knowledge-label/query",
      request
    );
    return response.data as unknown as KnowledgeLabelWithDetailPage;
  } catch (error: any) {
    toast.error(error.message || "Failed to fetch knowledge labels");
    throw error;
  }
}
