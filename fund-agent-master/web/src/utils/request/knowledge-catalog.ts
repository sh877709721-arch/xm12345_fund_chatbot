import instance from "./instance";
import { toast } from "sonner";

// 知识库目录树节点接口
export interface CatalogTreeNode {
  id: number;
  name: string;
  children?: CatalogTreeNode[];
}

// 知识库目录树响应接口
export interface CatalogTreeResponse {
  code: number;
  message: string;
  data: Record<string, Record<string, CatalogTreeNode[]>>;
}

// 知识目录接口
export interface KnowledgeCatalog {
  id: number;
  category_level_1: string;
  category_level_2: string;
  category_level_3: string;
  status: string;
  created_at: string;
  updated_at: string;
}

// 知识目录创建请求接口
export interface KnowledgeCatalogCreate {
  name?: string;
  catalog_level_1: string;
  catalog_level_2: string;
  catalog_level_3: string;
}

// 知识目录更新请求接口
export interface KnowledgeCatalogUpdate {
  name?: string;
  catalog_level_1?: string;
  catalog_level_2?: string;
  catalog_level_3?: string;
}

// 知识目录响应接口
export interface KnowledgeCatalogsResponse {
  code: number;
  message: string;
  data: KnowledgeCatalog[];
}

// 单个知识目录响应接口
export interface KnowledgeCatalogResponse {
  code: number;
  message: string;
  data: KnowledgeCatalog;
}

// 获取知识库目录树
export async function getKnowledgeCatalogTree(): Promise<Record<string, Record<string, CatalogTreeNode[]>>> {
  try {
    const response = await instance.get<Record<string, Record<string, CatalogTreeNode[]>>>(
      "/v1/admin/knowledge/catalog-tree"
    );
    return response.data;
  } catch (error: any) {
    toast.error(error.message || "Failed to fetch knowledge catalog tree");
    throw error;
  }
}

// 获取所有知识目录
export async function getKnowledgeCatalogs(): Promise<KnowledgeCatalog[]> {
  try {
    const response = await instance.get<KnowledgeCatalog[]>(
      "/v1/admin/knowledge/catalogs"
    );
    return response.data;
  } catch (error: any) {
    toast.error(error.message || "Failed to fetch knowledge catalogs");
    throw error;
  }
}

// 创建知识目录
export async function createKnowledgeCatalog(
  catalog: KnowledgeCatalogCreate
): Promise<KnowledgeCatalog> {
  try {
    const response = await instance.post<KnowledgeCatalog>(
      "/v1/admin/knowledge/catalogs",
      catalog
    );
    toast.success("保存成功");
    return response.data;
  } catch (error: any) {
    toast.error(error.message || "Failed to create knowledge catalog");
    throw error;
  }
}

// 更新知识目录
export async function updateKnowledgeCatalog(
  catalogId: number,
  catalog: KnowledgeCatalogUpdate
): Promise<KnowledgeCatalog> {
  try {
    const response = await instance.put<KnowledgeCatalog>(
      `/v1/admin/knowledge/catalogs/${catalogId}`,
      catalog
    );
    toast.success("Knowledge catalog updated successfully");
    return response.data;
  } catch (error: any) {
    toast.error(error.message || "Failed to update knowledge catalog");
    throw error;
  }
}

// 删除知识目录（软删除）
export async function deleteKnowledgeCatalog(
  catalogId: number
): Promise<KnowledgeCatalog> {
  try {
    const response = await instance.delete<KnowledgeCatalog>(
      `/v1/admin/knowledge/catalogs/${catalogId}`
    );
    toast.success("Knowledge catalog deleted successfully");
    return response.data;
  } catch (error: any) {
    toast.error(error.message || "Failed to delete knowledge catalog");
    throw error;
  }
}

