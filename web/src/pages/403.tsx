import { Link } from "react-router-dom";
import { ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function Forbidden() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4 py-12">
      <Card className="w-full max-w-md text-center">
        <CardHeader className="space-y-4">
          {/* 图标 */}
          <div className="flex justify-center">
            <div className="rounded-full bg-destructive/10 p-6">
              <ShieldAlert className="h-16 w-16 text-destructive" />
            </div>
          </div>

          {/* 标题 */}
          <CardTitle className="text-3xl">
            权限不足
          </CardTitle>

          {/* 描述文本 */}
          <CardDescription className="text-base">
            抱歉，您没有权限访问此页面。<br />
            如果您认为这是一个错误，请联系管理员。
          </CardDescription>
        </CardHeader>

        {/* 操作按钮 */}
        <CardContent className="space-y-3">
          <div className="flex flex-col sm:flex-row gap-3">
            <Button asChild variant="default" className="flex-1">
              <Link to="/admin">
                返回控制台
              </Link>
            </Button>

            <Button
              asChild
              variant="outline"
              className="flex-1"
              onClick={() => window.history.back()}
            >
              <Link to="#">
                返回上一页
              </Link>
            </Button>
          </div>

          {/* 额外提示 */}
          <p className="text-xs text-muted-foreground mt-4">
            错误代码：403 Forbidden
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
