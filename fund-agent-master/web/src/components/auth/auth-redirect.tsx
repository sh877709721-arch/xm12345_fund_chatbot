import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/auth-context";

interface AuthRedirectProps {
  children: React.ReactNode;
}

export function AuthRedirect({ children }: AuthRedirectProps) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // 如果用户已登录，重定向到admin页面
  if (isAuthenticated) {
    return <Navigate to="/admin" replace />;
  }

  // 如果用户未登录，显示子组件（通常是登录页面）
  return <>{children}</>;
}