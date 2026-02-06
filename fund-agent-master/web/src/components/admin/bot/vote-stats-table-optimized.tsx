import * as React from "react";
import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  Search,
  RefreshCw,
  ThumbsUp,
  Minus,
  ThumbsDown,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Download,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DateTimePicker } from "@/components/ui/date-input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { VoteWithMessage } from "@/utils/request/vote";
import { exportVotesToExcel } from "@/utils/request/vote";
import { useVoteData } from "@/hooks/use-vote-data";
import { cn } from "@/lib/utils";

interface VoteStatsTableOptimizedProps {
  className?: string;
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const getVoteBadgeVariant = (voteType: string) => {
  switch (voteType) {
    case "good":
      return "default";
    case "medium":
      return "secondary";
    case "bad":
      return "destructive";
    default:
      return "outline";
  }
};

const getVoteIcon = (voteType: string, className?: string) => {
  switch (voteType) {
    case "good":
      return <ThumbsUp className={cn("h-4 w-4 text-green-600", className)} />;
    case "medium":
      return <Minus className={cn("h-4 w-4 text-yellow-600", className)} />;
    case "bad":
      return <ThumbsDown className={cn("h-4 w-4 text-red-600", className)} />;
    default:
      return null;
  }
};

const getVoteText = (voteType: string) => {
  switch (voteType) {
    case "good":
      return "好评";
    case "medium":
      return "中评";
    case "bad":
      return "差评";
    default:
      return "未知";
  }
};

// 内容预览组件
const ContentPreview = ({ content, maxLength = 100 }: { content: string; maxLength?: number }) => {
  const [isExpanded, setIsExpanded] = React.useState(false);

  // 非空保护：如果内容为空则不展示
  if (!content || content.trim() === '') {
    return null;
  }

  const shouldTruncate = content.length > maxLength;

  if (!shouldTruncate) {
    return (
      <div className="text-sm leading-relaxed whitespace-pre-wrap">
        {content}
      </div>
    );
  }

  const displayContent = isExpanded ? content : content.slice(0, maxLength) + "...";

  return (
    <div className="relative group">
      <div className="text-sm leading-relaxed whitespace-pre-wrap">
        {displayContent}
      </div>
      <div className="invisible group-hover:visible absolute z-50 max-w-md p-3 bg-popover border rounded-md shadow-lg">
        <div className="text-sm leading-relaxed whitespace-pre-wrap max-h-64 overflow-y-auto">
          {content}
        </div>
      </div>
      {shouldTruncate && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
          className="mt-1 h-6 px-2 text-xs"
        >
          {isExpanded ? "收起" : "展开"}
        </Button>
      )}
    </div>
  );
};

export function VoteStatsTableOptimized({ className }: VoteStatsTableOptimizedProps) {
  const {
    voteData,
    searchParams,
    loading,
    totalPages,
    hasNextPage,
    hasPrevPage,
    handleSearch,
    handleReset,
    handleVoteTypeChange,
    handleDateRangeChange,
    handleClientTypeChange,
    handlePageChange,
    handlePageSizeChange,
    handleRefresh,
  } = useVoteData();

  // 本地搜索状态
  const [localSearchKeyword, setLocalSearchKeyword] = React.useState(searchParams.searchKeyword || "");

  // 同步本地搜索关键词与 searchParams
  React.useEffect(() => {
    setLocalSearchKeyword(searchParams.searchKeyword || "");
  }, [searchParams.searchKeyword]);

  // 处理搜索输入变化（只更新本地状态，不触发搜索）
  const handleSearchInputChange = (value: string) => {
    setLocalSearchKeyword(value);
  };

  // 触发搜索
  const triggerSearch = () => {
    handleSearch(localSearchKeyword);
  };

  // 处理回车键
  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      event.preventDefault();
      triggerSearch();
    }
  };

  // 列定义
  const columns: ColumnDef<VoteWithMessage>[] = [
    {
      accessorKey: "vote_type",
      header: () => <div className="pl-6">投票类型</div>,
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          {getVoteIcon(row.original.vote_type) || <div className="w-4 h-4" />}
          <Badge variant={getVoteBadgeVariant(row.original.vote_type)}>
            {getVoteText(row.original.vote_type)}
          </Badge>
        </div>
      ),
      size: 120,
      enableSorting: true,
    },
    {
      accessorKey: "client_type",
      header: "请求来源",
      cell: ({ row }) => (
        <span className="text-sm text-muted-foreground">
          {row.original.client_type || "未知"}
        </span>
      ),
      size: 120,
      enableSorting: false,
    },
    {
      accessorKey: "message_id",
      header: "消息ID",
      cell: ({ row }) => (
        <span className="font-mono text-sm text-muted-foreground">
          {row.original.message_id}
        </span>
      ),
      size: 100,
      enableSorting: true,
    },
    {
      accessorKey: "question",
      header: "用户问题",
      cell: ({ row }) => (
        <div className="max-w-xs">
          <ContentPreview content={row.original.question} maxLength={80} />
        </div>
      ),
      size: 250,
      enableSorting: false,
    },
    {
      accessorKey: "answer",
      header: "AI回答",
      cell: ({ row }) => (
        <div className="max-w-md">
          <ContentPreview content={row.original.answer} maxLength={150} />
        </div>
      ),
      size: 400,
      enableSorting: false,
    },
    {
      accessorKey: "feedback",
      header: "反馈内容",
      cell: ({ row }) => (
        <div className="max-w-md">
          <ContentPreview content={row.original.feedback} maxLength={150} />
        </div>
      ),
      size: 180,
      enableSorting: false,
    },
    {
      accessorKey: "updated_at",
      header: "消息时间",
      cell: ({ row }) => (
        <span className="text-sm text-muted-foreground">
          {formatDate(row.original.created_at)}
        </span>
      ),
      size: 150,
      enableSorting: true,
    },
  ];

  // 表格实例
  const table = useReactTable({
    data: voteData.items,
    columns,
    enableRowSelection: false,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    manualPagination: true,
    manualSorting: false,
    pageCount: totalPages,
  });

  // 处理分页变化
  const handlePageChangeInternal = (page: number) => {
    handlePageChange(page);
  };

  // 处理页面大小变化
  const handlePageSizeChangeInternal = (size: string) => {
    handlePageSizeChange(Number(size));
  };

  // 处理导出Excel
  const handleExportExcel = async () => {
    try {
      const query = {
        vote_type: searchParams.vote_type === "all" ? undefined : searchParams.vote_type,
        start_date: searchParams.start_date || undefined,
        end_date: searchParams.end_date || undefined,
        searchKeyword: searchParams.searchKeyword || undefined,
        client_type: searchParams.client_type || undefined,
      };
      await exportVotesToExcel(query);
    } catch (error) {
      console.error("导出失败:", error);
    }
  };

  return (
    <div className={cn("w-full h-full flex flex-col", className)}>
      {/* 搜索栏和操作按钮 */}
      <div className="py-2 flex-shrink-0">
        <div className="flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="搜索问题或回答..."
              value={localSearchKeyword}
              onChange={(event) => {
                handleSearchInputChange(event.target.value);
              }}
              onKeyDown={handleKeyDown}
              onBlur={triggerSearch}
              className="pl-8 h-8"
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground whitespace-nowrap">投票类型：</span>
            <Select value={searchParams.vote_type} onValueChange={handleVoteTypeChange}>
              <SelectTrigger className="w-28 h-8">
                <SelectValue placeholder="投票类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部</SelectItem>
                <SelectItem value="good">好评</SelectItem>
                <SelectItem value="medium">中评</SelectItem>
                <SelectItem value="bad">差评</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground whitespace-nowrap">请求来源：</span>
            <Select 
              value={searchParams.client_type || "all"} 
              onValueChange={handleClientTypeChange}
            >
              <SelectTrigger className="w-28 h-8">
                <SelectValue placeholder="请求来源" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部</SelectItem>
                <SelectItem value="web">网页</SelectItem>
                <SelectItem value="h5">H5</SelectItem>
                <SelectItem value="miniprogram">小程序</SelectItem>
                <SelectItem value="mp">公众号</SelectItem>
                <SelectItem value="公积金">公积金</SelectItem>
                <SelectItem value="rexian">热线</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground whitespace-nowrap">开始日期时间：</span>
            <DateTimePicker
              value={searchParams.start_date}
              onChange={(value) => handleDateRangeChange(value || "", searchParams.end_date)}
              placeholder="开始日期时间"
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground whitespace-nowrap">结束日期时间：</span>
            <DateTimePicker
              value={searchParams.end_date}
              onChange={(value) => handleDateRangeChange(searchParams.start_date, value || "")}
              placeholder="结束日期时间"
            />
          </div>

          <div className="flex items-center gap-2">
            <Button onClick={handleRefresh} disabled={loading} className="h-8">
              <RefreshCw className={cn("h-3 w-3 mr-1", loading && "animate-spin")} />
              刷新
            </Button>

            <Button variant="secondary" onClick={handleReset} className="h-8">
              重置
            </Button>

            <Button 
              onClick={handleExportExcel} 
              disabled={loading} 
              variant="outline"
              className="h-8"
            >
              <Download className="h-3 w-3 mr-1" />
              导出Excel
            </Button>
          </div>
        </div>
      </div>

      {/* 表格区域 */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="h-full rounded-lg border flex flex-col min-h-0">
          {/* 表头：固定 */}
          <div className="flex-shrink-0">
            <Table className="w-full table-fixed">
              <colgroup>
                {columns.map((c, i) => (
                  <col key={i} style={{ width: c.size }} />
                ))}
              </colgroup>
              <TableHeader className="bg-muted">
                {table.getHeaderGroups().map((hg) => (
                  <TableRow key={hg.id}>
                    {hg.headers.map((h) => (
                      <TableHead
                        key={h.id}
                        colSpan={h.colSpan}
                        className="align-middle"
                      >
                        {h.isPlaceholder ? null : flexRender(h.column.columnDef.header, h.getContext())}
                      </TableHead>
                    ))}
                  </TableRow>
                ))}
              </TableHeader>
            </Table>
          </div>

          {/* 表体：滚动 */}
          <div className="overflow-auto flex-1">
            <Table className="w-full table-fixed">
              <colgroup>
                {columns.map((c, i) => (
                  <col key={i} style={{ width: c.size }} />
                ))}
              </colgroup>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={columns.length} className="h-24 text-center">
                      加载中...
                    </TableCell>
                  </TableRow>
                ) : table.getRowModel().rows.length ? (
                  table.getRowModel().rows.map((row) => (
                    <TableRow
                      key={row.id}
                      data-state={row.getIsSelected() && "selected"}
                    >
                      {row.getVisibleCells().map((cell) => (
                        <TableCell key={cell.id} className="align-middle py-2">
                          {flexRender(cell.column.columnDef.cell, cell.getContext())}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={columns.length} className="h-24 text-center">
                      无数据
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>

          {/* 分页：固定在表格底部 */}
          <div className="flex items-center justify-between px-4 py-2 border-t flex-shrink-0">
            <div className="text-muted-foreground hidden flex-1 text-sm lg:flex">
              共 {voteData.total} 条数据
            </div>
            <div className="flex w-full items-center gap-8 lg:w-fit">
              <div className="hidden items-center gap-2 lg:flex">
                <span className="text-sm font-medium">每页行数</span>
                <Select
                  value={`${searchParams.size}`}
                  onValueChange={handlePageSizeChangeInternal}
                >
                  <SelectTrigger className="w-20" size="sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent side="top">
                    {[10, 20, 30, 40, 50, 100, 500, 1000].map((s) => (
                      <SelectItem key={s} value={`${s}`}>
                        {s}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="text-sm font-medium">
                第 {voteData.page} 页，共 {totalPages} 页
              </div>

              <div className="ml-auto flex items-center gap-2 lg:ml-0">
                <Button
                  variant="outline"
                  className="hidden lg:flex size-8"
                  size="icon"
                  onClick={() => handlePageChangeInternal(1)}
                  disabled={voteData.page <= 1}
                >
                  <ChevronsLeft className="size-4" />
                </Button>
                <Button
                  variant="outline"
                  className="size-8"
                  size="icon"
                  onClick={() => handlePageChangeInternal(voteData.page - 1)}
                  disabled={!hasPrevPage}
                >
                  <ChevronLeft className="size-4" />
                </Button>
                <Button
                  variant="outline"
                  className="size-8"
                  size="icon"
                  onClick={() => handlePageChangeInternal(voteData.page + 1)}
                  disabled={!hasNextPage}
                >
                  <ChevronRight className="size-4" />
                </Button>
                <Button
                  variant="outline"
                  className="hidden lg:flex size-8"
                  size="icon"
                  onClick={() => handlePageChangeInternal(totalPages)}
                  disabled={!hasNextPage || voteData.page >= totalPages}
                >
                  <ChevronsRight className="size-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}