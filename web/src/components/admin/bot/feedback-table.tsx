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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { FeedbackItem } from "@/utils/request/feedback";
import { exportFeedbacksToExcel } from "@/utils/request/feedback";
import { useFeedbackData } from "@/hooks/use-feedback-data";
import { cn } from "@/lib/utils";

interface FeedbackTableProps {
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

export function FeedbackTable({ className }: FeedbackTableProps) {
  const {
    feedbackData,
    searchParams,
    loading,
    totalPages,
    hasNextPage,
    hasPrevPage,
    handleSearch,
    handleReset,
    handleDateRangeChange,
    handlePageChange,
    handlePageSizeChange,
    handleRefresh,
  } = useFeedbackData();

  const [localContent, setLocalContent] = React.useState(searchParams.content || "");
  const [localPhone, setLocalPhone] = React.useState(searchParams.phone || "");
  const debounceTimerRef = React.useRef<NodeJS.Timeout | null>(null);

  React.useEffect(() => {
    setLocalContent(searchParams.content || "");
    setLocalPhone(searchParams.phone || "");
  }, [searchParams.content, searchParams.phone]);

  const triggerSearch = (params: { content?: string; phone?: string }) => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    debounceTimerRef.current = setTimeout(() => {
      handleSearch(params);
    }, 300);
  };

  React.useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  const columns: ColumnDef<FeedbackItem>[] = [
    {
      accessorKey: "id",
      header: "ID",
      cell: ({ row }) => (
        <span className="font-mono text-sm text-muted-foreground">
          {row.original.id}
        </span>
      ),
      size: 80,
      enableSorting: true,
    },
    {
      accessorKey: "content",
      header: "反馈内容",
      cell: ({ row }) => (
        <div className="max-w-xl">
          <ContentPreview content={row.original.content} maxLength={200} />
        </div>
      ),
      size: 500,
      enableSorting: false,
    },
    {
      accessorKey: "phone",
      header: "手机号",
      cell: ({ row }) => (
        <span className="text-sm text-muted-foreground">{row.original.phone || "-"}</span>
      ),
      size: 150,
      enableSorting: false,
    },
    {
      accessorKey: "status",
      header: "状态",
      cell: ({ row }) => (
        <Badge variant="outline">{row.original.status || "-"}</Badge>
      ),
      size: 100,
      enableSorting: false,
    },
    {
      accessorKey: "created_time",
      header: "创建时间",
      cell: ({ row }) => (
        <span className="text-sm text-muted-foreground">
          {formatDate(row.original.created_time)}
        </span>
      ),
      size: 180,
      enableSorting: true,
    },
    {
      accessorKey: "updated_time",
      header: "更新时间",
      cell: ({ row }) => (
        <span className="text-sm text-muted-foreground">
          {formatDate(row.original.updated_time)}
        </span>
      ),
      size: 180,
      enableSorting: true,
    },
  ];

  // 表格实例
  const table = useReactTable({
    data: feedbackData.items,
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

  const handlePageSizeChangeInternal = (size: string) => {
    handlePageSizeChange(Number(size));
  };

  const handleExportExcel = async () => {
    try {
      const query = {
        content: searchParams.content || undefined,
        phone: searchParams.phone || undefined,
        start_date: searchParams.start_date || undefined,
        end_date: searchParams.end_date || undefined,
      };
      await exportFeedbacksToExcel(query);
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
              placeholder="请输入反馈内容"
              value={localContent}
              onChange={(event) => {
                setLocalContent(event.target.value);
                triggerSearch({ content: event.target.value });
              }}
              className="pl-8 h-8"
            />
          </div>

          <div className="flex items-center gap-2">
            <Input
              placeholder="请输入手机号"
              value={localPhone}
              onChange={(event) => {
                setLocalPhone(event.target.value);
                triggerSearch({ phone: event.target.value });
              }}
              className="h-8"
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground whitespace-nowrap">开始时间：</span>
            <DateTimePicker
              value={searchParams.start_date}
              onChange={(value) => handleDateRangeChange(value || "", searchParams.end_date)}
              placeholder="开始时间"
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground whitespace-nowrap">结束时间：</span>
            <DateTimePicker
              value={searchParams.end_date}
              onChange={(value) => handleDateRangeChange(searchParams.start_date, value || "")}
              placeholder="结束时间"
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
              共 {feedbackData.total} 条数据
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
                第 {feedbackData.page} 页，共 {totalPages} 页
              </div>

              <div className="ml-auto flex items-center gap-2 lg:ml-0">
                <Button
                  variant="outline"
                  className="hidden lg:flex size-8"
                  size="icon"
                  onClick={() => handlePageChangeInternal(1)}
                  disabled={feedbackData.page <= 1}
                >
                  <ChevronsLeft className="size-4" />
                </Button>
                <Button
                  variant="outline"
                  className="size-8"
                  size="icon"
                  onClick={() => handlePageChangeInternal(feedbackData.page - 1)}
                  disabled={!hasPrevPage}
                >
                  <ChevronLeft className="size-4" />
                </Button>
                <Button
                  variant="outline"
                  className="size-8"
                  size="icon"
                  onClick={() => handlePageChangeInternal(feedbackData.page + 1)}
                  disabled={!hasNextPage}
                >
                  <ChevronRight className="size-4" />
                </Button>
                <Button
                  variant="outline"
                  className="hidden lg:flex size-8"
                  size="icon"
                  onClick={() => handlePageChangeInternal(totalPages)}
                  disabled={!hasNextPage || feedbackData.page >= totalPages}
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