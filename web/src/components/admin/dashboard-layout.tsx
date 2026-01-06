import { AppSidebar } from "@/components/admin/app-sidebar";
import { SiteHeader } from "@/components/admin/site-header";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { Outlet, Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/context/auth-context";

export function DashboardLayout() {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  // 如果正在加载认证状态，显示加载动画
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // 如果未认证，重定向到登录页面，并保存当前路径以便登录后跳转
  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        state={{ from: location }}
        replace
      />
    );
  }

  return (
    <SidebarProvider
      style={
        {
          "--sidebar-width": "calc(var(--spacing) * 72)",
          "--header-height": "calc(var(--spacing) * 12)",
        } as React.CSSProperties
      }>
      <AppSidebar variant="sidebar" />
      <SidebarInset>
        <div className="h-screen flex flex-col">
          <SiteHeader />
          <div className="flex-1 overflow-hidden">
            <div className="flex flex-col gap-2 py-2 px-2 md:gap-4 md:py-4 h-full">
              <Outlet />
            </div>
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}