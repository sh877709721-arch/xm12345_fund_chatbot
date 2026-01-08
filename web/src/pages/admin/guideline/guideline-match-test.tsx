import * as React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { matchGuideline, type GuidelineMatchResult } from "@/utils/request/guideline";

export function GuidelineMatchTestPage() {
  const [context, setContext] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [result, setResult] = React.useState<GuidelineMatchResult | null>(null);

  const handleTest = async () => {
    if (!context.trim()) {
      toast.error("请输入测试上下文");
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const matchResult = await matchGuideline({
        context,
        candidate_top_k: 5,
        use_llm_refinement: true,
      });

      if (matchResult) {
        setResult(matchResult);
        toast.success("匹配成功");
      } else {
        toast.info("未找到匹配的指南");
      }
    } catch (error: any) {
      console.error("匹配测试失败:", error);

      if (error.message === '请求超时，请检查网络连接') {
        toast.error('请求超时，请检查网络连接后重试');
      } else if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('匹配失败，请重试');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full h-full flex flex-col gap-6">
      {/* 顶部标题 */}
      <div className="px-4 lg:px-6 py-2">
        <h1 className="text-3xl font-bold">Guideline 匹配测试</h1>
        <p className="text-muted-foreground mt-2">
          输入对话上下文，测试系统智能匹配行动指南的能力
        </p>
      </div>
      {/* 主要内容区域 */}
      <div className="flex-1 overflow-auto px-4 lg:px-6">
        <div className="max-w-4xl mx-auto space-y-6 pb-6">
          {/* 输入区域 */}
          <Card>
            <CardHeader>
              <CardTitle>测试上下文</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                value={context}
                onChange={(e) => setContext(e.target.value)}
                placeholder="输入对话上下文或用户查询，例如：为什么今年医保缴费变多了"
                rows={8}
                className="resize-none"
              />
              <Button
                onClick={handleTest}
                disabled={loading || !context.trim()}
                className="w-full sm:w-auto"
              >
                {loading ? "匹配中..." : "开始匹配"}
              </Button>
            </CardContent>
          </Card>

          {/* 结果展示 */}
          {result && (
            <Card>
              <CardHeader>
                <CardTitle>匹配结果</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {/* 匹配信息 */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <Label className="text-muted-foreground">匹配 ID</Label>
                      <p className="font-medium text-lg">{result.guideline_id}</p>
                    </div>
                    <div>
                      <Label className="text-muted-foreground">置信度</Label>
                      <p className="font-medium text-lg">
                        {result.confidence ? `${(result.confidence * 100).toFixed(1)}%` : "N/A"}
                      </p>
                    </div>
                  </div>

                  {/* 标题 */}
                  <div>
                    <Label className="text-muted-foreground">标题</Label>
                    <p className="font-medium text-lg">{result.title}</p>
                  </div>

                  {/* 触发条件 */}
                  <div>
                    <Label className="text-muted-foreground">触发条件</Label>
                    <p className="text-sm whitespace-pre-wrap bg-muted p-3 rounded-md mt-1">
                      {result.condition}
                    </p>
                  </div>

                  {/* 行动内容 */}
                  <div>
                    <Label className="text-muted-foreground">行动内容</Label>
                    <p className="text-sm whitespace-pre-wrap bg-muted p-3 rounded-md mt-1">
                      {result.action}
                    </p>
                  </div>

                  {/* Prompt 模板（可选） */}
                  {result.prompt_template && (
                    <div>
                      <Label className="text-muted-foreground">Prompt 模板</Label>
                      <p className="text-sm whitespace-pre-wrap bg-muted p-3 rounded-md mt-1">
                        {result.prompt_template}
                      </p>
                    </div>
                  )}

                  {/* 匹配详情 */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div>
                      <Label className="text-muted-foreground">匹配得分</Label>
                      <p className="font-medium">
                        {result.match_score?.toFixed(3) || "N/A"}
                      </p>
                    </div>
                    <div>
                      <Label className="text-muted-foreground">匹配方式</Label>
                      <p className="font-medium">{result.match_method}</p>
                    </div>
                    <div>
                      <Label className="text-muted-foreground">优先级</Label>
                      <p className="font-medium">{result.priority}</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

// 默认导出
export default GuidelineMatchTestPage;
