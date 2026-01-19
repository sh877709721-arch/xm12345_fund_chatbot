import * as React from "react";
import {
  IconDashboard,
  IconHelp,
  IconInnerShadowTop,
  IconListDetails,
  IconSearch,
  IconSettings,
  IconRobot,
} from "@tabler/icons-react";
import {
  MessageCircle
} from 'lucide-react'
import { NavMain } from "@/components/admin/nav-main";
//import { NavSecondary } from "@/components/admin/nav-secondary";
import { NavUser } from "@/components/admin/nav-user";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { useAuth } from "@/context/auth-context";

export const data = {
  navMain: [
    {
      title: "控制台",
      url: "/admin",
      icon: IconDashboard,
    },
    {
      title: "知识库",
      url: "/admin/knowledge",
      icon: IconListDetails,
      items: [
        {
          title: "知识库管理",
          url: "/admin/knowledge-list",
        },
        {
          title: "文本查询",
          url: "/admin/knowledge-search",
        },
        {
          title: "表格查询",
          url: "/admin/knowledge-data-search",
        },
      ],
    },
    {
      title: "消息查询",
      url: "#",
      icon: MessageCircle,
      items: [
        {
          title: "问答查询",
          url: "/admin/vote-messages",
        },
        {
          title: "留言反馈",
          url: "/admin/feedback",
        },
      ],
    },
    {
      title: "指令微调",
      url: "#",
      icon: IconRobot,
      items: [
        {
          title: "Guideline 管理",
          url: "/admin/bot-instruction",
        },
        {
          title: "匹配测试",
          url: "/admin/guideline-match-test",
        },
        {
          title: "问答",
          url: "/admin/bot-chat?from=admin",
        },
      ],
    },
    // {
    //   title: "可视化大屏",
    //   url: "/admin/qa-dashboard",
    //   icon: IconDashboard,
    // },
    {
      title: "关于",
      url: "/admin/about",
      icon: IconHelp,
    },
  ],
  navSecondary: [
    {
      title: "设置",
      url: "/admin/settings",
      icon: IconSettings,
    },
    {
      title: "帮助",
      url: "#",
      icon: IconHelp,
    },
    {
      title: "搜索",
      url: "#",
      icon: IconSearch,
    },
  ],
};

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const { user } = useAuth();

  // 根据用户角色过滤菜单项
  const getFilteredNavItems = () => {
    // 如果没有用户信息或角色，返回所有菜单（兜底）
    if (!user || !user.user_role) {
      return data.navMain;
    }

    // normal_user 只能看见：控制台、消息查询、关于
    if (user.user_role === 'normal_user') {
      return data.navMain.filter(item => {
        const title = item.title;
        return title === '控制台' || title === '消息查询' || title === '知识库' || title === '关于';
      });
    }

    // superadmin 和 engineer 可以看见所有菜单
    return data.navMain;
  };

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              asChild
              className="data-[slot=sidebar-menu-button]:!p-1.5">
              <a href="#">
                <IconInnerShadowTop className="!size-5" />
                <span className="text-base font-semibold"> 智能客服.</span>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={getFilteredNavItems()} />
        {/* <NavSecondary items={data.navSecondary} className="mt-auto" /> */}
      </SidebarContent>
      <SidebarFooter>
        {user && <NavUser user={{
          name: user.username || user.email,
          email: user.email,
          avatar: ""
        }} />}
      </SidebarFooter>
    </Sidebar>
  );
}
