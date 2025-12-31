import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/context/auth-context";
import { toast } from "sonner";
import { User, Bell, Shield, Database } from "lucide-react";

export default function SettingsPage() {
  const { user, refreshUser } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  // 用户资料设置
  const [profileSettings, setProfileSettings] = useState({
    username: user?.username || "",
    email: user?.email || "",
    displayName: user?.username || "",
  });

  // 通知设置
  const [notificationSettings, setNotificationSettings] = useState({
    emailNotifications: true,
    pushNotifications: false,
    weeklyReport: true,
    systemAlerts: true,
  });

  // 安全设置
  const [securitySettings, setSecuritySettings] = useState({
    twoFactorAuth: false,
    sessionTimeout: true,
    loginAlerts: true,
  });

  const handleProfileSave = async () => {
    setIsLoading(true);
    try {
      // TODO: 调用更新用户资料API
      toast.success("个人资料已更新");
      await refreshUser();
    } catch (error) {
      toast.error("更新失败，请重试");
    } finally {
      setIsLoading(false);
    }
  };

  const handleNotificationSave = async () => {
    setIsLoading(true);
    try {
      // TODO: 调用更新通知设置API
      toast.success("通知设置已更新");
    } catch (error) {
      toast.error("更新失败，请重试");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSecuritySave = async () => {
    setIsLoading(true);
    try {
      // TODO: 调用更新安全设置API
      toast.success("安全设置已更新");
    } catch (error) {
      toast.error("更新失败，请重试");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">系统设置</h1>
          <p className="text-muted-foreground">
            管理您的账户设置和偏好配置
          </p>
        </div>
      </div>

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="profile" className="flex items-center gap-2">
            <User className="h-4 w-4" />
            个人资料
          </TabsTrigger>
          <TabsTrigger value="notifications" className="flex items-center gap-2">
            <Bell className="h-4 w-4" />
            通知设置
          </TabsTrigger>
          <TabsTrigger value="security" className="flex items-center gap-2">
            <Shield className="h-4 w-4" />
            安全设置
          </TabsTrigger>
          <TabsTrigger value="data" className="flex items-center gap-2">
            <Database className="h-4 w-4" />
            数据管理
          </TabsTrigger>
        </TabsList>

        <TabsContent value="profile">
          <Card>
            <CardHeader>
              <CardTitle>个人资料</CardTitle>
              <CardDescription>
                更新您的个人信息和联系方式
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="username">用户名</Label>
                  <Input
                    id="username"
                    value={profileSettings.username}
                    onChange={(e) =>
                      setProfileSettings((prev) => ({
                        ...prev,
                        username: e.target.value,
                      }))
                    }
                    placeholder="请输入用户名"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="displayName">显示名称</Label>
                  <Input
                    id="displayName"
                    value={profileSettings.displayName}
                    onChange={(e) =>
                      setProfileSettings((prev) => ({
                        ...prev,
                        displayName: e.target.value,
                      }))
                    }
                    placeholder="请输入显示名称"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">邮箱地址</Label>
                <Input
                  id="email"
                  type="email"
                  value={profileSettings.email}
                  onChange={(e) =>
                    setProfileSettings((prev) => ({
                      ...prev,
                      email: e.target.value,
                    }))
                  }
                  placeholder="请输入邮箱地址"
                />
              </div>

              <div className="space-y-2">
                <Label>账户状态</Label>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary" className="bg-green-100 text-green-800">
                    活跃用户
                  </Badge>
                  <span className="text-sm text-muted-foreground">
                    账户创建时间: {new Date().toLocaleDateString()}
                  </span>
                </div>
              </div>

              <Separator />

              <div className="flex justify-end">
                <Button
                  onClick={handleProfileSave}
                  disabled={isLoading}
                >
                  {isLoading ? "保存中..." : "保存更改"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications">
          <Card>
            <CardHeader>
              <CardTitle>通知设置</CardTitle>
              <CardDescription>
                配置您希望接收的通知类型
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between space-x-2">
                <div className="space-y-0.5">
                  <Label>邮件通知</Label>
                  <p className="text-sm text-muted-foreground">
                    通过邮件接收重要更新和提醒
                  </p>
                </div>
                <Checkbox
                  checked={notificationSettings.emailNotifications}
                  onCheckedChange={(checked) =>
                    setNotificationSettings((prev) => ({
                      ...prev,
                      emailNotifications: checked as boolean,
                    }))
                  }
                />
              </div>

              <div className="flex items-center justify-between space-x-2">
                <div className="space-y-0.5">
                  <Label>推送通知</Label>
                  <p className="text-sm text-muted-foreground">
                    在浏览器中接收实时通知
                  </p>
                </div>
                <Checkbox
                  checked={notificationSettings.pushNotifications}
                  onCheckedChange={(checked) =>
                    setNotificationSettings((prev) => ({
                      ...prev,
                      pushNotifications: checked as boolean,
                    }))
                  }
                />
              </div>

              <Separator />

              <div className="flex items-center justify-between space-x-2">
                <div className="space-y-0.5">
                  <Label>周报</Label>
                  <p className="text-sm text-muted-foreground">
                    每周接收活动摘要和统计报告
                  </p>
                </div>
                <Checkbox
                  checked={notificationSettings.weeklyReport}
                  onCheckedChange={(checked) =>
                    setNotificationSettings((prev) => ({
                      ...prev,
                      weeklyReport: checked as boolean,
                    }))
                  }
                />
              </div>

              <div className="flex items-center justify-between space-x-2">
                <div className="space-y-0.5">
                  <Label>系统警报</Label>
                  <p className="text-sm text-muted-foreground">
                    接收系统重要事件和警报通知
                  </p>
                </div>
                <Checkbox
                  checked={notificationSettings.systemAlerts}
                  onCheckedChange={(checked) =>
                    setNotificationSettings((prev) => ({
                      ...prev,
                      systemAlerts: checked as boolean,
                    }))
                  }
                />
              </div>

              <Separator />

              <div className="flex justify-end">
                <Button
                  onClick={handleNotificationSave}
                  disabled={isLoading}
                >
                  {isLoading ? "保存中..." : "保存设置"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security">
          <Card>
            <CardHeader>
              <CardTitle>安全设置</CardTitle>
              <CardDescription>
                管理您的账户安全和隐私设置
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between space-x-2">
                <div className="space-y-0.5">
                  <Label>双因素认证</Label>
                  <p className="text-sm text-muted-foreground">
                    为您的账户添加额外的安全层
                  </p>
                </div>
                <Checkbox
                  checked={securitySettings.twoFactorAuth}
                  onCheckedChange={(checked) =>
                    setSecuritySettings((prev) => ({
                      ...prev,
                      twoFactorAuth: checked as boolean,
                    }))
                  }
                />
              </div>

              <div className="flex items-center justify-between space-x-2">
                <div className="space-y-0.5">
                  <Label>会话超时</Label>
                  <p className="text-sm text-muted-foreground">
                    自动退出长时间不活跃的会话
                  </p>
                </div>
                <Checkbox
                  checked={securitySettings.sessionTimeout}
                  onCheckedChange={(checked) =>
                    setSecuritySettings((prev) => ({
                      ...prev,
                      sessionTimeout: checked as boolean,
                    }))
                  }
                />
              </div>

              <div className="flex items-center justify-between space-x-2">
                <div className="space-y-0.5">
                  <Label>登录提醒</Label>
                  <p className="text-sm text-muted-foreground">
                    新设备登录时发送通知
                  </p>
                </div>
                <Checkbox
                  checked={securitySettings.loginAlerts}
                  onCheckedChange={(checked) =>
                    setSecuritySettings((prev) => ({
                      ...prev,
                      loginAlerts: checked as boolean,
                    }))
                  }
                />
              </div>

              <Separator />

              <div className="space-y-4">
                <Label>密码重置</Label>
                <Button variant="outline" className="w-full justify-start">
                  更改密码
                </Button>
              </div>

              <Separator />

              <div className="flex justify-end">
                <Button
                  onClick={handleSecuritySave}
                  disabled={isLoading}
                >
                  {isLoading ? "保存中..." : "保存设置"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="data">
          <Card>
            <CardHeader>
              <CardTitle>数据管理</CardTitle>
              <CardDescription>
                管理您的数据和隐私设置
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <Label>数据导出</Label>
                <p className="text-sm text-muted-foreground">
                  下载您的所有数据副本
                </p>
                <Button variant="outline">
                  导出数据
                </Button>
              </div>

              <Separator />

              <div className="space-y-4">
                <Label>缓存清理</Label>
                <p className="text-sm text-muted-foreground">
                  清除本地缓存和临时文件
                </p>
                <Button variant="outline">
                  清理缓存
                </Button>
              </div>

              <Separator />

              <div className="space-y-4">
                <Label className="text-red-600">危险操作</Label>
                <p className="text-sm text-muted-foreground">
                  以下操作不可撤销，请谨慎操作
                </p>
                <Button variant="destructive">
                  删除账户
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
