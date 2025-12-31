import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { HomeIcon } from "lucide-react";
import { ThemeToggleSimple } from "@/components/theme-toggle-simple";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { useLocation } from "react-router-dom";
import { data } from "@/components/admin/app-sidebar";

export function SiteHeader() {
  const location = useLocation();

  // 根据路径生成面包屑
  const pathSnippets = location.pathname.split("/").filter((i) => i);

  // 创建路由到标题的映射
  const breadcrumbNameMap: Record<string, string> = {
    chat: "首页",
    admin: "管理",
  };

  // 从导航数据中提取映射关系
  data.navMain.forEach((item) => {
    const urlParts = item.url.split("/").filter((i) => i);
    if (urlParts.length > 0) {
      const key = urlParts[urlParts.length - 1];
      breadcrumbNameMap[key] = item.title;

      // 处理子菜单项
      if (item.items) {
        item.items.forEach((subItem) => {
          const subUrlParts = subItem.url.split("/").filter((i) => i);
          if (subUrlParts.length > 0) {
            const subKey = subUrlParts[subUrlParts.length - 1];
            breadcrumbNameMap[subKey] = subItem.title;
          }
        });
      }
    }
  });

  // 添加二级导航项
  data.navSecondary.forEach((item) => {
    const urlParts = item.url.split("/").filter((i) => i);
    if (urlParts.length > 0) {
      const key = urlParts[urlParts.length - 1];
      breadcrumbNameMap[key] = item.title;
    }
  });

  // 只获取最后一个路径片段作为页面标题
  const lastPathSegment = pathSnippets[pathSnippets.length - 1];
  const pageTitle = lastPathSegment
    ? (breadcrumbNameMap[lastPathSegment] || lastPathSegment)
    : "首页";

  return (
    <header className="sticky top-0 z-10 bg-background flex h-(--header-height) shrink-0 items-center gap-2 border-b transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-(--header-height)">
      <div className="flex w-full items-center gap-1 px-4 lg:gap-2 lg:px-6">
        <SidebarTrigger className="-ml-1" />
        <Separator
          orientation="vertical"
          className="mx-2 data-[orientation=vertical]:h-4"
        />

        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink href="/znkfzs/admin">首页</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage>{pageTitle}</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>

        <div className="ml-auto flex items-center gap-2">
          <ThemeToggleSimple />
          <Button variant="ghost" asChild size="sm" className="hidden sm:flex">
            <a href="/znkfzs" target="_blank" className="dark:text-foreground">
              <HomeIcon className="h-4 w-4" />
            </a>
          </Button>
        </div>
      </div>
    </header>
  );
}