import * as React from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Loader2, Search } from "lucide-react";
import { toast } from "sonner";
import { matchGuideline, type GuidelineMatchResult } from "@/utils/request/guideline";

export function GuidelineMatchTestPage() {
  const [context, setContext] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [result, setResult] = React.useState<GuidelineMatchResult | null>(null);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleTest();
    }
  };

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

      <div className="px-4 lg:px-6 py-4 border-b">
        <div className="flex flex-col lg:flex-row gap-4 lg:gap-6 items-start">
          {/* 左侧标题区域 */}
          <div className="flex-1 space-y-2">
            <h4 className="text-2xl font-bold tracking-tight">Guideline 匹配测试</h4>
          </div>
          {/* 右侧搜索输入区域 */}
          <div className="flex-4 max-w-6xl">
            <div className="flex gap-2">
              <Input
                placeholder="输入对话上下文或用户查询，例如：为什么今年医保缴费变多了"
                value={context}
                onChange={(e) => setContext(e.target.value)}
                onKeyDown={handleKeyPress}
                className="flex-1"
              />
              <Button
                onClick={handleTest}
                disabled={loading || !context.trim()}
                className="px-6">
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Search className="w-4 h-4" />
                )}
                <span className="ml-2">匹配测试</span>
              </Button>
            </div>
            <p className="text-muted-foreground text-sm">
              根据对话上下文匹配，获取AI的行动指南
            </p>
          </div>
        </div>
      </div>
      {/* 主要内容区域 */}
      <div className="flex-1 overflow-auto px-4 lg:px-6">
        <div className="max-w-4xl mx-auto space-y-6 pb-6">


          {/* 结果展示 */}
          {result && (
            <div className="space-y-6">
              <div className="border-b pb-2">
                <h2 className="text-xl font-semibold">匹配结果</h2>
              </div>
              <div className="space-y-6">
                {/* 匹配信息 */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <Label className="text-sm text-muted-foreground font-medium">匹配 ID</Label>
                    <p className="font-semibold text-lg">{result.guideline_id}</p>
                  </div>
                  <div className="space-y-1">
                    <Label className="text-sm text-muted-foreground font-medium">置信度</Label>
                    <p className="font-semibold text-lg">
                      {result.confidence ? `${(result.confidence * 100).toFixed(1)}%` : "N/A"}
                    </p>
                  </div>
                </div>

                {/* 标题 */}
                <div className="space-y-1">
                  <Label className="text-sm text-muted-foreground font-medium">标题</Label>
                  <p className="font-semibold text-lg">{result.title}</p>
                </div>

                {/* 触发条件 */}
                <div className="space-y-1">
                  <Label className="text-sm text-muted-foreground font-medium">触发条件</Label>
                  <div className="bg-muted/50 p-4 rounded-lg border">
                    <p className="text-sm whitespace-pre-wrap leading-relaxed">
                      {result.condition}
                    </p>
                  </div>
                </div>

                {/* 行动内容 */}
                <div className="space-y-1">
                  <Label className="text-sm text-muted-foreground font-medium">行动内容</Label>
                  <div className="bg-muted/50 p-4 rounded-lg border">
                    <p className="text-sm whitespace-pre-wrap leading-relaxed">
                      {result.action}
                    </p>
                  </div>
                </div>

                {/* Prompt 模板（可选） */}
                {result.prompt_template && (
                  <div className="space-y-1">
                    <Label className="text-sm text-muted-foreground font-medium">Prompt 模板</Label>
                    <div className="bg-muted/50 p-4 rounded-lg border">
                      <p className="text-sm whitespace-pre-wrap leading-relaxed font-mono">
                        {result.prompt_template}
                      </p>
                    </div>
                  </div>
                )}

                {/* 匹配详情 */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="space-y-1">
                    <Label className="text-sm text-muted-foreground font-medium">匹配得分</Label>
                    <p className="font-semibold">
                      {result.match_score?.toFixed(3) || "N/A"}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <Label className="text-sm text-muted-foreground font-medium">匹配方式</Label>
                    <p className="font-semibold">{result.match_method}</p>
                  </div>
                  <div className="space-y-1">
                    <Label className="text-sm text-muted-foreground font-medium">优先级</Label>
                    <p className="font-semibold">{result.priority}</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// 默认导出
export default GuidelineMatchTestPage;
