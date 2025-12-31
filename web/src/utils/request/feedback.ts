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
      "/v1/feedback/upload-image",
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
      "/v1/feedback/",
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