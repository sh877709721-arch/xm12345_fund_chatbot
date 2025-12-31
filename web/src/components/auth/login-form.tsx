import React, { useState, useEffect } from "react";
import { login, getCurrentUser } from "@/utils/request/auth";
import { useNavigate, useLocation } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "@/context/auth-context";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
export function LoginForm({
  className,
}: //...props
  React.ComponentProps<"form">) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [lastSubmitTime, setLastSubmitTime] = useState(0);
  const navigate = useNavigate();
  const location = useLocation();
  const { login: authLogin } = useAuth();

  // 获取登录前要跳转的路径
  const from = location.state?.from?.pathname || "/admin";

  // 防止快速连续提交（最少间隔2秒）
  const [cooldownRemaining, setCooldownRemaining] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const canSubmit = cooldownRemaining === 0 && !loading && !isSubmitting;

  // 更新冷却时间
  useEffect(() => {
    if (lastSubmitTime === 0) {
      setCooldownRemaining(0);
      return;
    }

    const interval = setInterval(() => {
      const elapsed = Date.now() - lastSubmitTime;
      const remaining = Math.max(0, 2000 - elapsed); // 固定2秒冷却时间
      setCooldownRemaining(remaining);

      if (remaining <= 0) {
        clearInterval(interval);
        setCooldownRemaining(0);
      }
    }, 100);

    return () => clearInterval(interval);
  }, [lastSubmitTime]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // 防止快速重复提交
    if (!canSubmit) {
      const remainingSeconds = Math.ceil(cooldownRemaining / 1000);
      toast.error(`请等待${remainingSeconds}秒后再试，避免频繁操作`);
      return;
    }

    // 表单验证
    if (!username.trim() || !password.trim()) {
      toast.error("请输入邮箱和密码");
      return;
    }

    setLoading(true);
    setIsSubmitting(true);
    const submitTime = Date.now();
    setLastSubmitTime(submitTime);
    setCooldownRemaining(2000); // 设置2000ms冷却，与useEffect逻辑一致

    try {
      await login({ username, password });
      toast.success("登录成功");

      // 获取用户信息
      const user = await getCurrentUser();
      console.log("当前用户:", user);

      // 更新认证状态
      authLogin(user);

      // 跳转到之前尝试访问的页面，默认为/admin
      navigate(from, { replace: true });
    } catch (error: any) {
      console.error("登录错误:", error);

      // 更详细的错误处理
      let errorMessage = "登录失败";

      if (error.response?.status === 401) {
        errorMessage = "用户名或密码错误";
      } else if (error.response?.status === 429) {
        errorMessage = "请求过于频繁，请稍后再试";
      } else if (error.response?.status >= 500) {
        errorMessage = "服务器错误，请稍后再试";
      } else if (error.message) {
        errorMessage = error.message;
      }

      toast.error(errorMessage);
    } finally {
      setLoading(false);
      setIsSubmitting(false);
    }
  };

  return (
    <div className={cn("flex flex-col gap-6", className)}>
      <Card>
        <CardHeader className="text-center">
          <CardTitle className="text-3xl font-bold text-gray-900 dark:text-white">欢迎回来</CardTitle>
          <CardDescription className="text-gray-600 dark:text-gray-400">
            登录你的账号
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-gray-700 dark:text-gray-300 font-medium">邮箱</Label>
              <Input
                id="email"
                type="email"
                placeholder="m@example.com"
                onChange={(e) => setUsername(e.target.value)}
                value={username}
                required
                className="h-11 bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 focus:border-blue-500 focus:ring-blue-500 dark:focus:ring-blue-400"
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-gray-700 dark:text-gray-300 font-medium">密码</Label>
                {/* <a
                  href="#"
                  className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-500 dark:hover:text-blue-300"
                >
                  忘记密码？
                </a> */}
              </div>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="h-11 bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 focus:border-blue-500 focus:ring-blue-500 dark:focus:ring-blue-400"
              />
            </div>

            <Button
              type="submit"
              className="w-full h-11 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg shadow-md hover:shadow-lg transform hover:scale-[1.02] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={loading || !canSubmit}
            >
              {loading
                ? "登录中..."
                : !canSubmit && cooldownRemaining > 0
                  ? `请等待 ${Math.ceil(cooldownRemaining / 1000)}s`
                  : "登录"
              }
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
