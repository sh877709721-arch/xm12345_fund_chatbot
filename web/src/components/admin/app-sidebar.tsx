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
          title: "检索测试",
          url: "/admin/knowledge-search",
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
        <NavMain items={data.navMain} />
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
