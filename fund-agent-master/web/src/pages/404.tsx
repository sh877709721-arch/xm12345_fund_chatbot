import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4 py-12">
      <Card className="w-full max-w-md text-center">
        <CardHeader className="space-y-4">
          {/* 大号 404 数字 */}
          <div className="text-[120px] font-bold text-primary leading-none">
            404
          </div>

          {/* 标题 */}
          <CardTitle className="text-3xl">
            页面未找到
          </CardTitle>

          {/* 描述文本 */}
          <CardDescription className="text-base">
            抱歉，您查找的页面不存在或已被移动。
          </CardDescription>
        </CardHeader>

        {/* 操作按钮 */}
        <CardContent className="space-y-3">
          <div className="flex flex-col sm:flex-row gap-3">
            <Button asChild variant="default" className="flex-1">
              <Link to="/">
                返回主页
              </Link>
            </Button>

            <Button asChild variant="outline" className="flex-1">
              <Link to="/admin">
                返回控制台
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
