import instance from "./instance";

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  user_role?: string; // 用户角色：superadmin | engineer | normal_user
  full_name?: string;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

// 登录
export async function login(credentials: LoginRequest): Promise<TokenResponse> {
  const params = new URLSearchParams();
  params.append("username", credentials.username);
  params.append("password", credentials.password);

  const response = await instance.post<TokenResponse>(
    "/v1/auth/front_token",
    params.toString(), // 确保 URLSearchParams 被正确序列化为字符串
    {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    }
  );
  // 保存token到localStorage
  if (response.data.access_token) {
    localStorage.setItem("access_token", response.data.access_token);
  }

  return response.data;
}

// 获取当前用户信息
export async function getCurrentUser(): Promise<User> {
  const response = await instance.get<User>("/v1/auth/me");
  return response.data;
}

// 登出
export function logout(): void {
  localStorage.removeItem("access_token");
}

// 检查是否已登录
export function isAuthenticated(): boolean {
  return !!localStorage.getItem("access_token");
}
