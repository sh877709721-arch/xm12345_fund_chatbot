import instance from "./instance";
import { toast } from "sonner";

// 投票类型常量
export const VoteType = {
  GOOD: "good",      // 好评
  MEDIUM: "medium",  // 中评
  BAD: "bad"         // 差评
} as const;

export type VoteType = typeof VoteType[keyof typeof VoteType];

// 消息投票创建请求接口
export interface MessageVoteRequest {
  message_id: number;         // 消息ID (数字类型)
  vote_type: VoteType;        // 投票类型（好评/中评/差评）
}

// 投票更新请求接口
export interface VoteUpdateRequest {
  vote_type: VoteType;        // 更新投票类型
}

// 消息投票响应接口
export interface MessageVote {
  id: number;
  message_id: number;         // 消息ID (数字类型)
  vote_type: VoteType;        // 投票类型
  created_at: string;         // 创建时间
  updated_at: string;         // 更新时间
}

// 带消息内容的投票数据接口
export interface VoteWithMessage {
  vote_id: number;             // 投票ID
  message_id: number;          // 消息ID
  vote_type: VoteType;         // 投票类型
  feedback: string;
  created_at: string;          // 投票更新时间
  question: string;            // 用户问题
  answer: string;              // AI回答
  chat_id: string;             // 聊天会话ID
  client_type?: string;        // 请求来源（已转换的中文显示）
}

// 分页响应接口
export interface PaginatedResponse<T> {
  code: number;
  message: string;
  data: {
    items: T[];                // 数据列表
    total: number;             // 总数量
    page: number;              // 当前页码
    size: number;              // 每页数量
    pages: number;             // 总页数
  };
}

// API响应接口
export interface VoteResponse {
  code: number;
  message: string;
  data: MessageVote;
}

// 投票统计查询参数接口
export interface VoteStatsQuery {
  page?: number;               // 页码，默认1
  size?: number;               // 每页数量，默认10
  vote_type?: VoteType | null; // 投票类型过滤
  start_date?: string | null;  // 开始时间 (YYYY-MM-DD HH:MM:SS)
  end_date?: string | null;    // 结束时间 (YYYY-MM-DD HH:MM:SS)
  searchKeyword?: string | null; // 搜索关键词（搜索问题和回答）
  client_type?: string | null; // 请求来源过滤 (web/h5/miniprogram/mp/医保/rexian)
}

// 对assistant消息进行投票
export async function voteMessage(voteData: MessageVoteRequest): Promise<VoteResponse> {
  try {
    const response = await instance.post<VoteResponse>(
      "/v1/admin/vote/",
      voteData
    );
    toast.success("投票成功");
    return response.data;
  } catch (error: any) {
    toast.error(error.response?.data?.detail || error.message || "投票失败");
    throw error;
  }
}

// 更新消息投票
export async function updateVote(
  voteId: number,
  voteData: VoteUpdateRequest
): Promise<VoteResponse> {
  try {
    const response = await instance.put<VoteResponse>(
      `/v1/admin/vote/${voteId}`,
      voteData
    );
    toast.success("投票更新成功");
    return response.data;
  } catch (error: any) {
    toast.error(error.response?.data?.detail || error.message || "更新投票失败");
    throw error;
  }
}

// 取消消息投票
export async function cancelVote(voteId: number): Promise<VoteResponse> {
  try {
    const response = await instance.delete<VoteResponse>(
      `/v1/admin/vote/${voteId}`
    );
    toast.success("已取消投票");
    return response.data;
  } catch (error: any) {
    toast.error(error.response?.data?.detail || error.message || "取消投票失败");
    throw error;
  }
}

// 获取当前用户对某条消息的投票
export async function getMessageVote(messageId: number): Promise<VoteResponse | null> {
  try {
    const response = await instance.get<VoteResponse>(
      `/v1/admin/vote/message/${messageId}`
    );
    return response.data;
  } catch (error: any) {
    // 如果没有投票记录，不显示错误，返回null
    if (error.response?.status === 404) {
      console.log(`消息 ${messageId} 没有投票记录`);
      return null;
    }
    console.error('获取投票信息失败:', error);
    // 不显示toast，因为这是正常情况
    return null;
  }
}

// 创建或更新投票（如果已存在则更新）
export async function createOrUpdateVote(
  messageId: number,
  voteType: VoteType,
  feedbackContent: string | null,
): Promise<VoteResponse> {
  try {
    const response = await instance.post<VoteResponse>(
      "/v1/admin/vote/",
      {
        message_id: messageId,
        vote_type: voteType,
        feedback: feedbackContent
      }
    );
    toast.success("投票成功");
    return response.data;
  } catch (error: any) {
    toast.error(error.response?.data?.detail || error.message || "投票失败");
    throw error;
  }
}

// 获取带消息内容的投票列表（支持按类型和时间过滤）
export async function getVotesWithMessages(
  query: VoteStatsQuery = {}
): Promise<PaginatedResponse<VoteWithMessage>> {
  try {
    const params = new URLSearchParams();

    // 设置默认值
    params.append('page', (query.page || 1).toString());
    params.append('size', (query.size || 10).toString());

    // 添加过滤条件（如果存在）
    if (query.vote_type) {
      params.append('vote_type', query.vote_type);
    }
    if (query.start_date) {
      params.append('start_date', query.start_date);
    }
    if (query.end_date) {
      params.append('end_date', query.end_date);
    }
    if (query.searchKeyword) {
      params.append('searchKeyword', query.searchKeyword);
    }
    if (query.client_type) {
      params.append('client_type', query.client_type);
    }

    const response = await instance.get<PaginatedResponse<VoteWithMessage>>(
      `/v1/admin/vote/with_messages?${params.toString()}`
    );

    console.log('response',response)

    return response.data;
  } catch (error: any) {
    console.error('获取投票统计失败:', error);
    throw error;
  }
}

// 导出投票数据到Excel
export async function exportVotesToExcel(
  query: VoteStatsQuery = {}
): Promise<void> {
  try {
    const params = new URLSearchParams();

    // 添加过滤条件（如果存在）
    if (query.vote_type) {
      params.append('vote_type', query.vote_type);
    }
    if (query.start_date) {
      params.append('start_date', query.start_date);
    }
    if (query.end_date) {
      params.append('end_date', query.end_date);
    }
    if (query.searchKeyword) {
      params.append('searchKeyword', query.searchKeyword);
    }
    if (query.client_type) {
      params.append('client_type', query.client_type);
    }

    // 使用axios直接请求，避免响应拦截器处理blob
    const axios = (await import('axios')).default;
    const baseURL = import.meta.env.VITE_BACKEND_URL || '';
    const token = localStorage.getItem('access_token');
    
    const response = await axios.get(
      `${baseURL}/v1/admin/vote/export/excel?${params.toString()}`,
      {
        responseType: 'blob', // 重要：指定响应类型为blob
        headers: token ? {
          Authorization: `Bearer ${token}`
        } : {},
      }
    );

    // 从响应头获取文件名，如果没有则使用默认名称
    const contentDisposition = response.headers['content-disposition'];
    let filename = `问答数据_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.xlsx`;
    
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1].replace(/['"]/g, '');
        // 处理URL编码的文件名
        try {
          filename = decodeURIComponent(filename);
        } catch (e) {
          // 如果解码失败，使用原始文件名
        }
      }
    }

    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);

    toast.success('导出成功');
  } catch (error: any) {
    console.error('导出投票数据失败:', error);
    // 如果是blob错误响应，尝试解析错误信息
    if (error.response?.data instanceof Blob) {
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const errorText = JSON.parse(reader.result as string);
          toast.error(errorText.detail || '导出失败');
        } catch {
          toast.error('导出失败');
        }
      };
      reader.readAsText(error.response.data);
    } else {
      toast.error(error.response?.data?.detail || error.message || '导出失败');
    }
    throw error;
  }
}