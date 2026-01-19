import instance from "./instance";
import { toast } from "sonner";

// 反馈图片上传响应接口
export interface FeedbackImageUploadResponse {
  code: number;
  message: string;
  data: {
    url: string;
  };
}

// 反馈图片信息接口
export interface FeedbackImage {
  url: string;
  filename: string;
  size: number;
  content_type: string;
  path: string;
}

// 反馈提交请求接口
export interface FeedbackRequest {
  content: string;
  phone?: string;
  images?: FeedbackImage[];
}

// 反馈提交响应接口
export interface FeedbackResponse {
  code: number;
  message: string;
  data: {
    id: number;
    content: string;
    phone?: string;
    images: FeedbackImage[];
    created_at: string;
  };
}

// 上传反馈图片
export async function uploadFeedbackImage(file: File): Promise<FeedbackImageUploadResponse> {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await instance.post<FeedbackImageUploadResponse>(
      "/v1/admin/feedback/upload-image",
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || error.message || "上传图片失败";
    toast.error(errorMessage);
    throw error;
  }
}

// 提交反馈
export async function submitFeedback(feedbackData: FeedbackRequest): Promise<FeedbackResponse> {
  try {
    const response = await instance.post<FeedbackResponse>(
      "/v1/admin/feedback/",
      feedbackData
    );

    toast.success("反馈提交成功，感谢您的宝贵意见！");
    return response.data;
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || error.message || "提交反馈失败";
    toast.error(errorMessage);
    throw error;
  }
}

// 反馈列表数据结构
export interface FeedbackItem {
  id: number;
  content: string;
  phone?: string;
  status: string;
  images?: FeedbackImage[];
  created_time: string;
  updated_time: string;
}

export interface FeedbackListResponse<T = FeedbackItem> {
  items: T[];          // 数据列表
  total: number;       // 总数量
  page: number;        // 当前页码
  size: number;        // 每页数量
  pages: number;      // 总页数（可选，后端未返回时不强制）
  has_next: boolean;  // 是否有下一页
  has_prev: boolean;  // 是否有上一页
}

export interface FeedbackQuery {
  page?: number;
  size?: number;
  content?: string;
  phone?: string;
  start_date?: string;
  end_date?: string;
}

// 获取反馈列表（分页 + 条件）
export async function getFeedbacks(
  query: FeedbackQuery = {}
): Promise<FeedbackListResponse<FeedbackItem>> {
  const params = new URLSearchParams();
  params.append("page", (query.page || 1).toString());
  params.append("size", (query.size || 10).toString());

  if (query.content) {
    params.append("content", query.content);
  }
  if (query.phone) {
    params.append("phone", query.phone);
  }
  if (query.start_date) {
    params.append("start_date", query.start_date);
  }
  if (query.end_date) {
    params.append("end_date", query.end_date);
  }

  try {
    const response = await instance.get<FeedbackListResponse<FeedbackItem>>(
      `/v1/admin/feedback/?${params.toString()}`
    );
    return response.data;
  } catch (error: any) {
    console.error("获取反馈列表失败:", error);
    throw error;
  }
}

// 导出反馈数据到Excel
export async function exportFeedbacksToExcel(query: FeedbackQuery = {}): Promise<void> {
  const params = new URLSearchParams();

  if (query.content) {
    params.append("content", query.content);
  }
  if (query.phone) {
    params.append("phone", query.phone);
  }
  if (query.start_date) {
    params.append("start_date", query.start_date);
  }
  if (query.end_date) {
    params.append("end_date", query.end_date);
  }

  try {
    const axios = (await import("axios")).default;
    const baseURL = import.meta.env.VITE_BACKEND_URL || "";
    const token = localStorage.getItem("access_token");

    const response = await axios.get(
      `${baseURL}/v1/admin/feedback/export/excel?${params.toString()}`,
      {
        responseType: "blob",
        headers: token
          ? {
            Authorization: `Bearer ${token}`,
          }
          : {},
      }
    );

    const contentDisposition = response.headers["content-disposition"];
    let filename = `feedback_${new Date().toISOString().slice(0, 19).replace(/:/g, "-")}.xlsx`;

    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1].replace(/['"]/g, "");
        try {
          filename = decodeURIComponent(filename);
        } catch {
          // ignore decode errors
        }
      }
    }

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
    toast.success("导出成功");
  } catch (error: any) {
    console.error("导出反馈数据失败:", error);
    if (error.response?.data instanceof Blob) {
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const errorText = JSON.parse(reader.result as string);
          toast.error(errorText.detail || "导出失败");
        } catch {
          toast.error("导出失败");
        }
      };
      reader.readAsText(error.response.data);
    } else {
      toast.error(error.response?.data?.detail || error.message || "导出失败");
    }
    throw error;
  }
}