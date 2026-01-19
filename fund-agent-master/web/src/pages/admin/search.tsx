// import { useState } from "react";
// import { searchKnowledge } from "@/utils/request/search";
// import type { SearchRequest, SearchResponse } from "@/utils/request/search";
// import { Input } from "@/components/ui/input";
// import { Button } from "@/components/ui/button";
// import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
// import { Badge } from "@/components/ui/badge";
// import { Loader2, Search } from "lucide-react";

// export default function SearchPage() {
//   const [query, setQuery] = useState("");
//   const [results, setResults] = useState<SearchResponse | null>(null);
//   const [loading, setLoading] = useState(false);
//   const [error, setError] = useState<string | null>(null);

//   const handleSearch = async () => {
//     if (!query.trim()) return;

//     setLoading(true);
//     setError(null);

//     try {
//       const params: SearchRequest = { query: query.trim() };
//       const response = await searchKnowledge(params);
//       setResults(response);
//     } catch (err) {
//       setError("搜索失败，请重试");
//     } finally {
//       setLoading(false);
//     }
//   };

//   const handleKeyPress = (e: React.KeyboardEvent) => {
//     if (e.key === "Enter") {
//       handleSearch();
//     }
//   };

//   const ResultCard = ({
//     title,
//     content,
//     score,
//     type
//   }: {
//     title: string;
//     content: string;
//     score: string;
//     type: "qa" | "doc";
//   }) => (
//     <Card className="h-full">
//       <CardHeader className="pb-3">
//         <div className="flex items-start justify-between">
//           <CardTitle className="text-lg font-medium leading-tight">
//             {title}
//           </CardTitle>
//           <Badge variant="secondary" className="text-xs">
//             {type === "qa" ? "问答" : "文档"}
//           </Badge>
//         </div>
//       </CardHeader>
//       <CardContent className="pt-0">
//         <p className="text-sm text-muted-foreground leading-relaxed">
//           {content}
//         </p>
//         <div className="mt-3 flex items-center justify-between">
//           <Badge variant="outline" className="text-xs">
//             匹配度: {parseFloat(score).toFixed(2)}
//           </Badge>
//         </div>
//       </CardContent>
//     </Card>
//   );

//   return (
//     <div className="container mx-auto p-6 space-y-6">
//       {/* 搜索框 */}
//       <div className="flex gap-2">
//         <Input
//           placeholder="请输入搜索关键词..."
//           value={query}
//           onChange={(e) => setQuery(e.target.value)}
//           onKeyPress={handleKeyPress}
//           className="flex-1"
//         />
//         <Button
//           onClick={handleSearch}
//           disabled={loading || !query.trim()}
//           className="px-6"
//         >
//           {loading ? (
//             <Loader2 className="w-4 h-4 animate-spin" />
//           ) : (
//             <Search className="w-4 h-4" />
//           )}
//           <span className="ml-2">搜索</span>
//         </Button>
//       </div>

//       {/* 错误提示 */}
//       {error && (
//         <div className="bg-red-50 border border-red-200 rounded-lg p-4">
//           <p className="text-red-600 text-sm">{error}</p>
//         </div>
//       )}

//       {/* 搜索结果 */}
//       {results && (
//         <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
//           {/* 第一列：QA结果 */}
//           <div className="space-y-4">
//             <div className="flex items-center gap-2">
//               <h3 className="text-lg font-semibold">精确匹配</h3>
//               <Badge variant="outline">{results.data.qa.length} 个结果</Badge>
//             </div>
//             {results.data.qa.length > 0 ? (
//               results.data.qa.map((item) => (
//                 <ResultCard
//                   key={item.id}
//                   title={item.question}
//                   content={item.answer}
//                   score={item.hybrid_score}
//                   type="qa"
//                 />
//               ))
//             ) : (
//               <div className="text-center py-8 text-muted-foreground">
//                 没有找到精确匹配的结果
//               </div>
//             )}
//           </div>

//           {/* 第二列：QA混合结果 */}
//           <div className="space-y-4">
//             <div className="flex items-center gap-2">
//               <h3 className="text-lg font-semibold">问答推荐</h3>
//               <Badge variant="outline">{results.data.qa_hybrid.length} 个结果</Badge>
//             </div>
//             {results.data.qa_hybrid.length > 0 ? (
//               results.data.qa_hybrid.map((item) => (
//                 <ResultCard
//                   key={item.id}
//                   title={item.question}
//                   content={item.answer}
//                   score={item.hybrid_score}
//                   type="qa"
//                 />
//               ))
//             ) : (
//               <div className="text-center py-8 text-muted-foreground">
//                 没有找到问答推荐结果
//               </div>
//             )}
//           </div>

//           {/* 第三列：文档混合结果 */}
//           <div className="space-y-4">
//             <div className="flex items-center gap-2">
//               <h3 className="text-lg font-semibold">文档推荐(FTS)</h3>
//               <Badge variant="outline">{results.data.doc_hybrid_rff.length} 个结果</Badge>
//             </div>
//             {results.data.doc_hybrid_rff.length > 0 ? (
//               results.data.doc_hybrid_rff.map((item) => (
//                 <ResultCard
//                   key={item.id}
//                   title={item.title}
//                   content={item.answer}
//                   score={item.hybrid_score}
//                   type="doc"
//                 />
//               ))
//             ) : (
//               <div className="text-center py-8 text-muted-foreground">
//                 没有找到文档推荐结果
//               </div>
//             )}
//           </div>
//           {/* 第三列：文档混合结果 */}
//           <div className="space-y-4">
//             <div className="flex items-center gap-2">
//               <h3 className="text-lg font-semibold">文档推荐(BM25)</h3>
//               <Badge variant="outline">{results.data.doc_hybrid_bm25.length} 个结果</Badge>
//             </div>
//             {results.data.doc_hybrid_bm25.length > 0 ? (
//               results.data.doc_hybrid_bm25.map((item) => (
//                 <ResultCard
//                   key={item.id}
//                   title={item.title}
//                   content={item.answer}
//                   score={item.hybrid_score}
//                   type="doc"
//                 />
//               ))
//             ) : (
//               <div className="text-center py-8 text-muted-foreground">
//                 没有找到文档推荐结果
//               </div>
//             )}
//           </div>
//         </div>
//       )}

//       {/* 无结果提示 */}
//       {results && !loading && (
//         <div className="text-center py-12 text-muted-foreground">
//           {results.data.qa.length === 0 &&
//             results.data.qa_hybrid.length === 0 &&
//             results.data.doc_hybrid_rff.length === 0 &&
//             results.data.doc_hybrid_bm25.length === 0 && (
//               <div>
//                 <p className="text-lg mb-2">没有找到相关结果</p>
//                 <p className="text-sm">请尝试使用不同的关键词进行搜索</p>
//               </div>
//             )}
//         </div>
//       )}
//     </div>
//   );
// }
