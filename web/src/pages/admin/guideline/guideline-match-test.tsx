// import * as React from "react";
// import { Button } from "@/components/ui/button";
// import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
// import { Label } from "@/components/ui/label";
// import { Textarea } from "@/components/ui/textarea";
// import { toast } from "sonner";
// import { matchGuideline, type GuidelineMatchResult } from "@/utils/request/guideline";

// export function GuidelineMatchTestPage() {
//   const [context, setContext] = React.useState("");
//   const [loading, setLoading] = React.useState(false);
//   const [result, setResult] = React.useState<GuidelineMatchResult | null>(null);

//   const handleTest = async () => {
//     if (!context.trim()) {
//       toast.error("请输入测试上下文");
//       return;
//     }

//     setLoading(true);
//     setResult(null);

//     try {
//       const matchResult = await matchGuideline({
//         context,
//         candidate_top_k: 5,
//         use_llm_refinement: true,
//       });

//       if (matchResult) {
//         setResult(matchResult);
//         toast.success("匹配成功");
//       } else {
//         toast.info("未找到匹配的指南");
//       }
//     } catch (error) {
//       console.error("匹配测试失败:", error);
//     } finally {
//       setLoading(false);
//     }
//   };

//   // const formatDate = (dateString: string) => {
//   //   return new Date(dateString).toLocaleString('zh-CN');
//   // };

//   return (
//     <div className="container mx-auto py-6 max-w-4xl">
//       <div className="mb-6">
//         <h1 className="text-3xl font-bold">Guideline 匹配测试</h1>
//         <p className="text-muted-foreground mt-2">
//           输入对话上下文，测试系统智能匹配行动指南的能力
//         </p>
//       </div>

//       <div className="space-y-4">
//         {/* 输入区域 */}
//         <Card>
//           <CardHeader>
//             <CardTitle>测试上下文</CardTitle>
//           </CardHeader>
//           <CardContent>
//             <Textarea
//               value={context}
//               onChange={(e) => setContext(e.target.value)}
//               placeholder="输入对话上下文或用户查询，例如：患者被诊断为高血压，需要饮食建议"
//               rows={6}
//               className="resize-none"
//             />
//             <Button
//               onClick={handleTest}
//               disabled={loading || !context.trim()}
//               className="mt-4"
//             >
//               {loading ? "匹配中..." : "开始匹配"}
//             </Button>
//           </CardContent>
//         </Card>

//         {/* 结果展示 */}
//         {result && (
//           <Card>
//             <CardHeader>
//               <CardTitle>匹配结果</CardTitle>
//             </CardHeader>
//             <CardContent>
//               <div className="space-y-4">
//                 <div className="grid grid-cols-2 gap-4">
//                   <div>
//                     <Label className="text-muted-foreground">匹配 ID</Label>
//                     <p className="font-medium text-lg">{result.guideline_id}</p>
//                   </div>
//                   <div>
//                     <Label className="text-muted-foreground">置信度</Label>
//                     <p className="font-medium text-lg">
//                       {result.confidence ? `${(result.confidence * 100).toFixed(1)}%` : "N/A"}
//                     </p>
//                   </div>
//                 </div>

//                 <div>
//                   <Label className="text-muted-foreground">标题</Label>
//                   <p className="font-medium text-lg">{result.title}</p>
//                 </div>

//                 <div>
//                   <Label className="text-muted-foreground">触发条件</Label>
//                   <p className="text-sm whitespace-pre-wrap bg-muted p-3 rounded-md mt-1">
//                     {result.condition}
//                   </p>
//                 </div>

//                 <div>
//                   <Label className="text-muted-foreground">行动内容</Label>
//                   <p className="text-sm whitespace-pre-wrap bg-muted p-3 rounded-md mt-1">
//                     {result.action}
//                   </p>
//                 </div>

//                 {result.prompt_template && (
//                   <div>
//                     <Label className="text-muted-foreground">Prompt 模板</Label>
//                     <p className="text-sm whitespace-pre-wrap bg-muted p-3 rounded-md mt-1">
//                       {result.prompt_template}
//                     </p>
//                   </div>
//                 )}

//                 <div className="grid grid-cols-3 gap-4">
//                   <div>
//                     <Label className="text-muted-foreground">匹配得分</Label>
//                     <p className="font-medium">
//                       {result.match_score?.toFixed(3) || "N/A"}
//                     </p>
//                   </div>
//                   <div>
//                     <Label className="text-muted-foreground">匹配方式</Label>
//                     <p className="font-medium">{result.match_method}</p>
//                   </div>
//                   <div>
//                     <Label className="text-muted-foreground">优先级</Label>
//                     <p className="font-medium">{result.priority}</p>
//                   </div>
//                 </div>
//               </div>
//             </CardContent>
//           </Card>
//         )}
//       </div>
//     </div>
//   );
// }
