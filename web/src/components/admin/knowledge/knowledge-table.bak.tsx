// "use client";
// import * as React from "react";
// import {
//   IconChevronLeft,
//   IconChevronRight,
//   IconChevronsLeft,
//   IconChevronsRight,
//   IconCircleCheckFilled,
//   IconDotsVertical,
//   IconLoader,
//   IconPlus,
//   IconSearch,
// } from "@tabler/icons-react";
// import {
//   type ColumnDef,
//   flexRender,
//   getCoreRowModel,
//   getFilteredRowModel,
//   getPaginationRowModel,
//   getSortedRowModel,
//   useReactTable,
// } from "@tanstack/react-table";
// import { toast } from "sonner";

// import { useIsMobile } from "@/hooks/use-mobile";
// import { Badge } from "@/components/ui/badge";
// import { Button } from "@/components/ui/button";
// import { Checkbox } from "@/components/ui/checkbox";
// import {
//   Drawer,
//   DrawerClose,
//   DrawerContent,
//   DrawerDescription,
//   DrawerFooter,
//   DrawerHeader,
//   DrawerTitle,
//   DrawerTrigger,
// } from "@/components/ui/drawer";
// import {
//   DropdownMenu,
//   DropdownMenuContent,
//   DropdownMenuItem,
//   DropdownMenuSeparator,
//   DropdownMenuTrigger,
// } from "@/components/ui/dropdown-menu";
// import { Input } from "@/components/ui/input";
// import { Label } from "@/components/ui/label";
// import {
//   Select,
//   SelectContent,
//   SelectItem,
//   SelectTrigger,
//   SelectValue,
// } from "@/components/ui/select";
// import { Separator } from "@/components/ui/separator";
// import {
//   Table,
//   TableBody,
//   TableCell,
//   TableHead,
//   TableHeader,
//   TableRow,
// } from "@/components/ui/table";
// import {
//   type KnowledgeEntry,
//   type KnowledgeType,
// } from "@/utils/request/knowledge-entries";

// const columns: ColumnDef<KnowledgeEntry>[] = [
//   {
//     id: "select",
//     header: () => <div className="text-muted-foreground">ID</div>,
//     cell: ({ row }) => (
//       <div className="max-w-xs lg:max-w-sm xl:max-w-md 2xl:max-w-lg truncate whitespace-normal break-words leading-tight">
//         {row.original.id}
//       </div>
//     ),
//     enableSorting: false,
//     enableHiding: false,
//     size: 60,
//   },
//   {
//     accessorKey: "name",
//     header: "知识名称",
//     cell: ({ row }) => {
//       return <TableCellViewer item={row.original} />;
//     },
//     enableHiding: false,
//     size: 100,
//   },
//   {
//     accessorKey: "knowledge_type",
//     header: "类型",
//     cell: ({ row }) => (
//       <div className="w-20 leading-tight">
//         <Badge variant="outline" className="text-muted-foreground px-1.5">
//           {row.original.knowledge_type === "qa"
//             ? "问答"
//             : row.original.knowledge_type === "document"
//             ? "文档"
//             : "数据表"}
//         </Badge>
//       </div>
//     ),
//     size: 80,
//   },
//   {
//     accessorKey: "details",
//     header: "内容",
//     cell: ({ row }) => (
//       <div className="max-w-xs lg:max-w-sm xl:max-w-md 2xl:max-w-lg truncate whitespace-normal break-words leading-tight">
//         {row.original.details?.content ? (
//           <ContentPreview content={row.original.details.content} />
//         ) : (
//           "暂无内容"
//         )}
//       </div>
//     ),
//     size: 600,
//   },
//   {
//     accessorKey: "status",
//     header: "状态",
//     cell: ({ row }) => (
//       <div className="leading-tight">
//         <Badge variant="outline" className="text-muted-foreground px-1.5">
//           {row.original.status === "active" ? (
//             <IconCircleCheckFilled className="fill-green-500 dark:fill-green-400 inline" />
//           ) : row.original.status === "pending" ? (
//             <IconLoader className="inline" />
//           ) : null}
//           <span className="ml-1">
//             {row.original.status === "active"
//               ? "已启用"
//               : row.original.status === "pending"
//               ? "待审核"
//               : "已删除"}
//           </span>
//         </Badge>
//       </div>
//     ),
//     size: 80,
//   },
//   {
//     accessorKey: "created_at",
//     header: "创建时间",
//     cell: ({ row }) => {
//       const date = new Date(row.original.created_at);
//       return (
//         <div className="text-muted-foreground leading-tight">
//           {date.toLocaleDateString("zh-CN")}
//         </div>
//       );
//     },
//     size: 60,
//   },
//   {
//     id: "actions",
//     cell: ({ row }) => (
//       <div className="leading-tight">
//         <DropdownMenu>
//           <DropdownMenuTrigger asChild>
//             <Button
//               variant="ghost"
//               className="data-[state=open]:bg-muted text-muted-foreground flex size-8"
//               size="icon">
//               <IconDotsVertical />
//               <span className="sr-only">Open menu</span>
//             </Button>
//           </DropdownMenuTrigger>
//           <DropdownMenuContent align="end" className="w-32">
//             <DropdownMenuItem>编辑</DropdownMenuItem>
//             <DropdownMenuItem>复制</DropdownMenuItem>
//             <DropdownMenuItem>收藏</DropdownMenuItem>
//             <DropdownMenuSeparator />
//             <DropdownMenuItem variant="destructive">删除</DropdownMenuItem>
//           </DropdownMenuContent>
//         </DropdownMenu>
//       </div>
//     ),
//     size: 60,
//   },
// ];

// export function DataTable({
//   data,
//   pagination,
//   selectedCatalog,
//   loading,
//   searchParams,
//   onSearch,
//   onReset,
//   onPageChange,
//   onPageSizeChange,
// }: {
//   data: KnowledgeEntry[];
//   pagination: {
//     total: number;
//     page: number;
//     size: number;
//     hasNext: boolean;
//     hasPrev: boolean;
//   };
//   selectedCatalog: any;
//   loading: boolean;
//   searchParams: {
//     name: string;
//     knowledge_type: KnowledgeType | "all";
//     page: number;
//     size: number;
//   };
//   onSearch: (name: string) => void; // 修改onSearch函数签名以接受搜索名称参数
//   onReset: () => void;
//   onPageChange: (page: number) => void;
//   onPageSizeChange: (size: number) => void;
// }) {
//   const [rowSelection, setRowSelection] = React.useState({});
//   const [searchName, setSearchName] = React.useState(searchParams.name);
//   const [knowledgeType, setKnowledgeType] = React.useState<
//     KnowledgeType | "all"
//   >(searchParams.knowledge_type);

//   const table = useReactTable({
//     data,
//     columns,
//     state: {
//       rowSelection,
//     },

//     enableRowSelection: true,
//     onRowSelectionChange: setRowSelection,
//     getCoreRowModel: getCoreRowModel(),
//     getFilteredRowModel: getFilteredRowModel(),
//     getPaginationRowModel: getPaginationRowModel(),
//     getSortedRowModel: getSortedRowModel(),
//     columnResizeMode: "onChange",
//   });

//   // 更新搜索参数
//   React.useEffect(() => {
//     setSearchName(searchParams.name);
//     setKnowledgeType(searchParams.knowledge_type);
//   }, [searchParams]);

//   const handleLocalSearch = () => {
//     // 直接调用onSearch函数并将当前搜索名称传递给父组件
//     onSearch(searchName);
//   };

//   const handleKeyDown = (e: React.KeyboardEvent) => {
//     if (e.key === "Enter") {
//       handleLocalSearch();
//     }
//   };

//   const totalPages = Math.ceil(pagination.total / pagination.size);

//   return (
//     <div className="w-full flex-col justify-start gap-6 h-full flex">
//       <div className="flex items-center justify-between px-4 lg:px-6 py-2">
//         <div className="flex-1">
//           {selectedCatalog ? (
//             <div className="text-sm text-muted-foreground">
//               {selectedCatalog.level1}
//               {selectedCatalog.level2 && ` / ${selectedCatalog.level2}`}
//               {selectedCatalog.level3 && ` / ${selectedCatalog.level3}`}
//             </div>
//           ) : (
//             "全部知识"
//           )}
//         </div>
//         <div className="w-2/3 flex items-center gap-2">
//           {/* 搜索栏 */}
//           <div className="px-4 lg:px-6 w-full">
//             <div className="flex gap-4 mb-4">
//               <div className="flex-1">
//                 <div className="relative">
//                   <IconSearch className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
//                   <Input
//                     placeholder="搜索知识名称..."
//                     className="pl-10"
//                     value={searchName}
//                     onChange={(e) => setSearchName(e.target.value)}
//                     onKeyDown={handleKeyDown}
//                   />
//                 </div>
//               </div>

//               <Select
//                 value={knowledgeType}
//                 onValueChange={(value: KnowledgeType | "all") =>
//                   setKnowledgeType(value)
//                 }>
//                 <SelectTrigger className="w-32">
//                   <SelectValue placeholder="类型" />
//                 </SelectTrigger>
//                 <SelectContent>
//                   <SelectItem value="all">全部类型</SelectItem>
//                   <SelectItem value="qa">问答</SelectItem>
//                   <SelectItem value="document">文档</SelectItem>
//                   <SelectItem value="data_table">数据表</SelectItem>
//                 </SelectContent>
//               </Select>

//               <Button onClick={handleLocalSearch}>搜索</Button>
//               <Button variant="outline" onClick={onReset}>
//                 重置
//               </Button>
//               <Button
//                 variant="default"
//                 size="sm"
//                 onClick={() => console.log("新建知识条目")}>
//                 <IconPlus className="h-4 w-4" />
//                 <span className="hidden lg:inline ml-2">新增知识</span>
//               </Button>
//             </div>
//           </div>
//         </div>
//       </div>

//       <div className="flex-1 flex flex-col overflow-hidden px-4 lg:px-6">
//         <div className="overflow-hidden rounded-lg border flex-1 flex flex-col">
//           <div className="overflow-auto flex-1">
//             <Table className="w-full">
//               <TableHeader className="bg-muted sticky top-0 z-10">
//                 {table.getHeaderGroups().map((headerGroup) => (
//                   <TableRow key={headerGroup.id}>
//                     {headerGroup.headers.map((header) => {
//                       return (
//                         <TableHead
//                           key={header.id}
//                           colSpan={header.colSpan}
//                           className="align-middle">
//                           {header.isPlaceholder
//                             ? null
//                             : flexRender(
//                                 header.column.columnDef.header,
//                                 header.getContext()
//                               )}
//                         </TableHead>
//                       );
//                     })}
//                   </TableRow>
//                 ))}
//               </TableHeader>
//               <TableBody>
//                 {loading ? (
//                   <TableRow>
//                     <TableCell
//                       colSpan={columns.length}
//                       className="h-24 text-center">
//                       加载中...
//                     </TableCell>
//                   </TableRow>
//                 ) : table.getRowModel().rows?.length ? (
//                   table.getRowModel().rows.map((row) => (
//                     <TableRow
//                       key={row.id}
//                       data-state={row.getIsSelected() && "selected"}
//                       className="align-middle">
//                       {row.getVisibleCells().map((cell) => (
//                         <TableCell key={cell.id} className="align-middle py-2">
//                           {flexRender(
//                             cell.column.columnDef.cell,
//                             cell.getContext()
//                           )}
//                         </TableCell>
//                       ))}
//                     </TableRow>
//                   ))
//                 ) : (
//                   <TableRow>
//                     <TableCell
//                       colSpan={columns.length}
//                       className="h-24 text-center">
//                       无数据
//                     </TableCell>
//                   </TableRow>
//                 )}
//               </TableBody>
//             </Table>
//           </div>
//           <div className="flex items-center justify-between px-4 py-2 border-t">
//             <div className="text-muted-foreground hidden flex-1 text-sm lg:flex">
//               共 {pagination.total} 条数据
//             </div>
//             <div className="flex w-full items-center gap-8 lg:w-fit">
//               <div className="hidden items-center gap-2 lg:flex">
//                 <Label htmlFor="rows-per-page" className="text-sm font-medium">
//                   每页行数
//                 </Label>
//                 <Select
//                   value={`${searchParams.size}`}
//                   onValueChange={(value) => {
//                     onPageSizeChange(Number(value));
//                     table.setPageSize(Number(value));
//                   }}>
//                   <SelectTrigger size="sm" className="w-20" id="rows-per-page">
//                     <SelectValue placeholder={searchParams.size} />
//                   </SelectTrigger>
//                   <SelectContent side="top">
//                     {[10, 20, 30, 40, 50].map((pageSize) => (
//                       <SelectItem key={pageSize} value={`${pageSize}`}>
//                         {pageSize}
//                       </SelectItem>
//                     ))}
//                   </SelectContent>
//                 </Select>
//               </div>
//               <div className="flex w-fit items-center justify-center text-sm font-medium">
//                 第 {pagination.page} 页，共 {totalPages} 页
//               </div>
//               <div className="ml-auto flex items-center gap-2 lg:ml-0">
//                 <Button
//                   variant="outline"
//                   className="hidden h-8 w-8 p-0 lg:flex"
//                   onClick={() => onPageChange(1)}
//                   disabled={pagination.page <= 1}>
//                   <span className="sr-only">首页</span>
//                   <IconChevronsLeft className="h-4 w-4" />
//                 </Button>
//                 <Button
//                   variant="outline"
//                   className="size-8"
//                   size="icon"
//                   onClick={() => onPageChange(pagination.page - 1)}
//                   disabled={pagination.page <= 1}>
//                   <span className="sr-only">上一页</span>
//                   <IconChevronLeft className="h-4 w-4" />
//                 </Button>
//                 <Button
//                   variant="outline"
//                   className="size-8"
//                   size="icon"
//                   onClick={() => onPageChange(pagination.page + 1)}
//                   disabled={!pagination.hasNext}>
//                   <span className="sr-only">下一页</span>
//                   <IconChevronRight className="h-4 w-4" />
//                 </Button>
//                 <Button
//                   variant="outline"
//                   className="hidden size-8 lg:flex"
//                   size="icon"
//                   onClick={() => onPageChange(totalPages)}
//                   disabled={
//                     !pagination.hasNext || pagination.page >= totalPages
//                   }>
//                   <span className="sr-only">末页</span>
//                   <IconChevronsRight className="h-4 w-4" />
//                 </Button>
//               </div>
//             </div>
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// }

// function TableCellViewer({ item }: { item: KnowledgeEntry }) {
//   const isMobile = useIsMobile();

//   return (
//     <Drawer direction={isMobile ? "bottom" : "right"}>
//       <DrawerTrigger asChild>
//         <Button variant="link" className="text-foreground w-fit px-0 text-left">
//           {item.name}
//         </Button>
//       </DrawerTrigger>
//       <DrawerContent>
//         <DrawerHeader className="gap-1">
//           <DrawerTitle>{item.name}</DrawerTitle>
//           <DrawerDescription>
//             类型:{" "}
//             {item.knowledge_type === "qa"
//               ? "问答"
//               : item.knowledge_type === "document"
//               ? "文档"
//               : "数据表"}
//           </DrawerDescription>
//         </DrawerHeader>
//         <div className="flex flex-col gap-4 overflow-y-auto px-4 text-sm">
//           <div className="grid gap-2">
//             <div className="font-medium">内容:</div>
//             <div className="text-muted-foreground whitespace-pre-wrap">
//               {item.details?.content || "暂无内容"}
//             </div>
//           </div>
//           <Separator />
//           <form className="flex flex-col gap-4">
//             <div className="flex flex-col gap-3">
//               <Label htmlFor="name">知识名称</Label>
//               <Input id="name" defaultValue={item.name} />
//             </div>
//             <div className="grid grid-cols-2 gap-4">
//               <div className="flex flex-col gap-3">
//                 <Label htmlFor="type">类型</Label>
//                 <Select defaultValue={item.knowledge_type}>
//                   <SelectTrigger id="type" className="w-full">
//                     <SelectValue placeholder="选择类型" />
//                   </SelectTrigger>
//                   <SelectContent>
//                     <SelectItem value="qa">问答</SelectItem>
//                     <SelectItem value="document">文档</SelectItem>
//                     <SelectItem value="data_table">数据表</SelectItem>
//                   </SelectContent>
//                 </Select>
//               </div>
//               <div className="flex flex-col gap-3">
//                 <Label htmlFor="status">状态</Label>
//                 <Select defaultValue={item.status}>
//                   <SelectTrigger id="status" className="w-full">
//                     <SelectValue placeholder="选择状态" />
//                   </SelectTrigger>
//                   <SelectContent>
//                     <SelectItem value="active">已启用</SelectItem>
//                     <SelectItem value="pending">待审核</SelectItem>
//                     <SelectItem value="deleted">已删除</SelectItem>
//                   </SelectContent>
//                 </Select>
//               </div>
//             </div>
//           </form>
//         </div>
//         <DrawerFooter>
//           <Button>保存</Button>
//           <DrawerClose asChild>
//             <Button variant="outline">关闭</Button>
//           </DrawerClose>
//         </DrawerFooter>
//       </DrawerContent>
//     </Drawer>
//   );
// }

// interface ContentPreviewProps {
//   content: string;
// }

// function ContentPreview({ content }: ContentPreviewProps) {
//   const [isOpen, setIsOpen] = React.useState(false);
//   const isMobile = useIsMobile();

//   // 移除多余的空白字符并限制长度
//   const truncatedContent = React.useMemo(() => {
//     const trimmed = content.trim();
//     // 在桌面端显示更多字符
//     const maxLength = isMobile ? 50 : 100;
//     return trimmed.length > maxLength
//       ? `${trimmed.substring(0, maxLength)}...`
//       : trimmed;
//   }, [content, isMobile]);

//   return (
//     <>
//       <div
//         className="cursor-pointer hover:underline"
//         onClick={() => setIsOpen(true)}
//         title={content}>
//         {truncatedContent || "暂无内容"}
//       </div>

//       <Drawer
//         direction={isMobile ? "bottom" : "right"}
//         open={isOpen}
//         onOpenChange={setIsOpen}>
//         <DrawerContent>
//           <DrawerHeader>
//             <DrawerTitle>内容详情</DrawerTitle>
//           </DrawerHeader>
//           <div className="px-4 pb-4 flex-1 overflow-y-auto">
//             <pre className="whitespace-pre-wrap break-words font-sans">
//               {content}
//             </pre>
//           </div>
//           <DrawerFooter>
//             <DrawerClose asChild>
//               <Button variant="outline">关闭</Button>
//             </DrawerClose>
//           </DrawerFooter>
//         </DrawerContent>
//       </Drawer>
//     </>
//   );
// }
