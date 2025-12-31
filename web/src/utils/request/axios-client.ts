import axios from "axios";
import { toast } from "sonner";

// ============================================================
// 20251230 重构：统一响应类型定义
// ============================================================

/** 后端标准响应结构 */
export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
}

/** 分页数据结构 */
export interface PaginatedData<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages?: number;
  has_next?: boolean;
  has_prev?: boolean;
}

/** 后端分页响应结构 */
export type ApiPaginatedResponse<T> = ApiResponse<PaginatedData<T>>;

// ============================================================
// Axios 客户端配置
// ============================================================

const client = axios.create({
  baseURL: import.meta.env.VITE_BACKEND_URL || "", //"http://127.0.0.1:8000\", // 生产环境用 ""
  timeout: 15000,
});

// 请求拦截器
client.interceptors.request.use(
  (config) => {
    // 在发送请求之前做些什么
    //const access_token ="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZXZAZXhhbXBsZS5jb20iLCJleHAiOjE3NTY0Mzg0NzB9.cnF26suaqzWh96T7aRdGNkiTnEXJ2c3BmwLRsMRVibQ";
    const token = localStorage.getItem("access_token"); // access_token; //

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    // 对请求错误做些什么
    return Promise.reject(error);
  }
);

// ============================================================
// 20251230 重构：响应拦截器 - 统一解包逻辑
// ============================================================

client.interceptors.response.use(
  (response) => {
    // 2xx 范围内的状态码都会触发该函数

    // ============================================================
    // 20251230 重构：自动检测并解包后端标准响应格式
    // ============================================================

    const data = response.data;

    // 检查是否为标准 ApiResponse 结构（包含 code 字段）
    if (data && typeof data === 'object' && 'code' in data) {
      const apiResponse = data as ApiResponse<any>;

      // 检查业务状态码（假设 200 表示成功，根据实际后端调整）
      if (apiResponse.code !== 200) {
        const errorMsg = apiResponse.message || '请求失败';
        toast.error(errorMsg);
        return Promise.reject(new Error(errorMsg));
      }

      // ✅ 自动解包，只返回 data 字段
      return apiResponse.data;
    }

    // 如果不是标准响应格式（如 OAuth token 等），直接返回原数据
    return response.data;
  },
  (error) => {
    // 超出 2xx 范围内的状态码都会触发该函数
    // 对响应错误做点什么
    console.log(error);
    // 处理特定的错误状态码
    if (error.response?.status === 401) {
      // 未授权，只清除本地token，不自动跳转
      localStorage.removeItem("access_token");
      // 让AuthContext和路由系统处理跳转，避免页面刷新
    } else {
      toast.error(error.response?.data?.detail || error.message);
    }
    return Promise.reject(error);
  }
);

export default client;
