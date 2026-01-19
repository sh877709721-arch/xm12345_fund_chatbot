import axios from "axios";
import { toast } from "sonner";

const instance = axios.create({
  baseURL: import.meta.env.VITE_BACKEND_URL || "", //"http://127.0.0.1:8000", // 生产环境用 ""
  timeout: 15000,
});
// 请求拦截器
instance.interceptors.request.use(
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

// 响应拦截器
instance.interceptors.response.use(
  (response) => {
    // 2xx 范围内的状态码都会触发该函数
    // 对响应数据做点什么
    return response.data;
  },
  (error) => {
    // 超出 2xx 范围的状态码都会触发该函数
    // 对响应错误做点什么
    console.log(error);

    // 处理特定的错误状态码
    if (error.response?.status === 401) {
      // 未授权，只清除本地token，不自动跳转
      localStorage.removeItem("access_token");
      // 让AuthContext和路由系统处理跳转，避免页面刷新
    } else if (error.response?.status === 403) {
      // 权限不足，显示提示并跳转到403页面
      const errorMessage = error.response?.data?.detail || "权限不足";

      // 显示错误提示
      toast.error(errorMessage);

      // 跳转到403页面
      window.location.href = "/znkfzs/403";

      // 返回已拒绝的 Promise，阻止后续处理
      return Promise.reject({
        ...error,
        handled: true, // 标记错误已处理
      });
    } else {
      toast.error(error.response?.data?.detail || error.message);
    }
    return Promise.reject(error);
  }
);

export default instance;
