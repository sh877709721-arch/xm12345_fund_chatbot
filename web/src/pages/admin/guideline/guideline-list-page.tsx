// import { useGuidelineData } from "@/hooks/use-guideline-data";
// import { GuidelineDialog } from "@/components/admin/guideline/guideline-form";
// import {
//   Table,
//   TableBody,
//   TableCell,
//   TableHead,
//   TableHeader,
//   TableRow,
// } from "@/components/ui/table";
// import { Button } from "@/components/ui/button";
// import { Input } from "@/components/ui/input";
// import {
//   Select,
//   SelectContent,
//   SelectItem,
//   SelectTrigger,
//   SelectValue,
// } from "@/components/ui/select";
// import { Badge } from "@/components/ui/badge";
// import { IconDotsVertical, IconSearch, IconRefresh } from "@tabler/icons-react";
// import {
//   DropdownMenu,
//   DropdownMenuContent,
//   DropdownMenuItem,
//   DropdownMenuSeparator,
//   DropdownMenuTrigger,
// } from "@/components/ui/dropdown-menu";
// import { ContentPreview } from "@/components/admin/guideline/content-preview";
// import { type GuidelineStatus } from "@/utils/request/guideline";

// export function GuidelineListPage() {
//   const {
//     guidelineData,
//     loading,
//     searchParams,
//     handleSearch,
//     handleReset,
//     handlePageChange,
//     handleRefresh,
//     updateLocalGuideline,
//     handleDelete,
//   } = useGuidelineData();

//   const [searchTitle, setSearchTitle] = React.useState("");
//   const [statusFilter, setStatusFilter] = React.useState<GuidelineStatus | "all">("all");

//   const handleSearchClick = () => {
//     handleSearch({ title: searchTitle, status: statusFilter });
//   };

//   const formatDate = (dateString: string) => {
//     return new Date(dateString).toLocaleString('zh-CN');
//   };

//   const getStatusConfig = (status: GuidelineStatus) => {
//     const statusMap = {
//       A: { label: "已启用", color: "text-green-500" },
//       I: { label: "已禁用", color: "text-gray-500" },
//       D: { label: "草稿", color: "text-yellow-500" },
//       X: { label: "已删除", color: "text-red-500" },
//     };
//     return statusMap[status] || statusMap.D;
//   };

//   return (
//     <div className="container mx-auto py-6">
//       <div className="mb-6">
//         <h1 className="text-3xl font-bold">行动指南管理</h1>
//         <p className="text-muted-foreground mt-2">
//           管理和配置系统行动指南，控制 AI 助手的行为响应
//         </p>
//       </div>

//       {/* 搜索栏 */}
//       <div className="flex items-center gap-2 py-4 mb-4 border rounded-lg p-4 bg-card">
//         <div className="relative flex-1 min-w-[200px]">
//           <IconSearch className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
//           <Input
//             placeholder="搜索标题..."
//             value={searchTitle}
//             onChange={(e) => setSearchTitle(e.target.value)}
//             onKeyDown={(e) => e.key === 'Enter' && handleSearchClick()}
//             className="pl-10"
//           />
//         </div>

//         <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as typeof statusFilter)}>
//           <SelectTrigger className="w-32">
//             <SelectValue placeholder="状态" />
//           </SelectTrigger>
//           <SelectContent>
//             <SelectItem value="all">全部状态</SelectItem>
//             <SelectItem value="A">已启用</SelectItem>
//             <SelectItem value="I">已禁用</SelectItem>
//             <SelectItem value="D">草稿</SelectItem>
//           </SelectContent>
//         </Select>

//         <Button onClick={handleSearchClick}>搜索</Button>
//         <Button variant="outline" onClick={handleReset}>重置</Button>
//         <Button variant="outline" onClick={handleRefresh}>
//           <IconRefresh className={cn("h-4 w-4 mr-1", loading && "animate-spin")} />
//           刷新
//         </Button>

//         <GuidelineDialog type="add" onSave={handleRefresh} />
//       </div>

//       {/* 表格 */}
//       <div className="border rounded-lg">
//         <Table>
//           <TableHeader>
//             <TableRow>
//               <TableHead className="w-[80px]">ID</TableHead>
//               <TableHead className="w-[300px]">标题</TableHead>
//               <TableHead className="w-[400px]">触发条件</TableHead>
//               <TableHead className="w-[400px]">行动内容</TableHead>
//               <TableHead className="w-[100px]">优先级</TableHead>
//               <TableHead className="w-[100px]">状态</TableHead>
//               <TableHead className="w-[180px]">创建时间</TableHead>
//               <TableHead className="w-[80px]">操作</TableHead>
//             </TableRow>
//           </TableHeader>
//           <TableBody>
//             {loading ? (
//               <TableRow>
//                 <TableCell colSpan={8} className="text-center py-8">
//                   加载中...
//                 </TableCell>
//               </TableRow>
//             ) : guidelineData.items.length === 0 ? (
//               <TableRow>
//                 <TableCell colSpan={8} className="text-center py-8">
//                   暂无数据
//                 </TableCell>
//               </TableRow>
//             ) : (
//               guidelineData.items.map((item) => {
//                 const statusConfig = getStatusConfig(item.status);
//                 return (
//                   <TableRow key={item.id}>
//                     <TableCell className="font-medium">{item.id}</TableCell>
//                     <TableCell>
//                       <GuidelineDialog
//                         item={item}
//                         type="edit"
//                         onUpdateLocal={updateLocalGuideline}
//                       />
//                     </TableCell>
//                     <TableCell>
//                       <ContentPreview content={item.condition} maxLength={80} />
//                     </TableCell>
//                     <TableCell>
//                       <ContentPreview content={item.action} maxLength={80} />
//                     </TableCell>
//                     <TableCell>{item.priority}</TableCell>
//                     <TableCell>
//                       <Badge variant="outline" className={statusConfig.color}>
//                         {statusConfig.label}
//                       </Badge>
//                     </TableCell>
//                     <TableCell>{formatDate(item.created_time)}</TableCell>
//                     <TableCell>
//                       <DropdownMenu>
//                         <DropdownMenuTrigger asChild>
//                           <Button variant="ghost" size="icon">
//                             <IconDotsVertical className="h-4 w-4" />
//                           </Button>
//                         </DropdownMenuTrigger>
//                         <DropdownMenuContent align="end">
//                           <GuidelineDialog item={item} type="row_edit" onUpdateLocal={updateLocalGuideline} />
//                           <DropdownMenuSeparator />
//                           <DropdownMenuItem
//                             className="text-destructive"
//                             onClick={() => {
//                               if (confirm(`确定要删除指南 "${item.title}" 吗？`)) {
//                                 handleDelete(item.id);
//                               }
//                             }}
//                           >
//                             删除
//                           </DropdownMenuItem>
//                         </DropdownMenuContent>
//                       </DropdownMenu>
//                     </TableCell>
//                   </TableRow>
//                 );
//               })
//             )}
//           </TableBody>
//         </Table>
//       </div>

//       {/* 分页 */}
//       <div className="flex items-center justify-between mt-4">
//         <div className="text-sm text-muted-foreground">
//           共 {guidelineData.total} 条记录，第 {guidelineData.page} / {Math.ceil(guidelineData.total / guidelineData.size)} 页
//         </div>
//         <div className="flex items-center gap-2">
//           <Button
//             variant="outline"
//             size="sm"
//             onClick={() => handlePageChange(guidelineData.page - 1)}
//             disabled={!guidelineData.has_prev || loading}
//           >
//             上一页
//           </Button>
//           <Button
//             variant="outline"
//             size="sm"
//             onClick={() => handlePageChange(guidelineData.page + 1)}
//             disabled={!guidelineData.has_next || loading}
//           >
//             下一页
//           </Button>
//         </div>
//       </div>
//     </div>
//   );
// }
