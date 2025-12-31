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
  IconChevronLeft,
  IconChevronRight,
  IconChevronsLeft,
  IconChevronsRight,
  IconCircleCheckFilled,
  IconSearch,
} from "@tabler/icons-react";

import { ContentPreview } from "./content-preview";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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

import type { KnowledgeLabelWithDetail } from "@/utils/request/knowledge-label";
import { AnnotationDialog } from "./annotation-dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { IconDotsVertical } from "@tabler/icons-react";

export type DialogStateType = "add" | "edit";

// 知识条目类型枚举
export type KnowledgeLabelType = "passed" | "unpassed" | "unchecked";

const formatDate = (d: string | Date) =>
  new Date(d).toLocaleDateString("zh-CN");

/* ---------- 组件接口（与旧版完全一致） ---------- */

interface DataTableProps {
  batchId: number | null;
  data: KnowledgeLabelWithDetail[];
  pagination: {
    total: number;
    page: number;
    size: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
  loading?: boolean;
  searchParams: {
    batch_id?: number;
    name?: string;
    pass_state?: KnowledgeLabelType | "all";
    filled_by?: string;
    page: number;
    size: number;
  };
  onSearch: (name?: string, pass_state?: KnowledgeLabelType | "all") => void;
  onReset: () => void;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
}

export function DataTable({
  batchId,
  data,
  pagination,
  loading = false,
  searchParams,
  onSearch,
  onReset,
  onPageChange,
  onPageSizeChange,
}: DataTableProps) {
  /* ---------------表头定义-------------- */
  const columns: ColumnDef<KnowledgeLabelWithDetail>[] = [
    {
      accessorKey: "label_id",
      header: () => <span className="text-muted-foreground">ID</span>,
      cell: ({ row }) => (
        <div className="truncate break-words leading-tight">
          {row.original.label_id}
        </div>
      ),
      enableSorting: true,
      enableHiding: false,
      size: 80,
    },
    {
      accessorKey: "question",
      header: "问题",
      cell: ({ row }) => (
        <div className="text-xs text-muted-foreground">
          <AnnotationDialog
            batchId={batchId}
            item={row.original}
            type="edit"
            onSave={onReset}
          />
        </div>
      ),
      enableHiding: true,
      size: 320,
    },
    {
      accessorKey: "ai_content",
      header: "AI 内容",
      cell: ({ row }) =>
        row.original.ai_content ? (
          <ContentPreview content={row.original.ai_content} />
        ) : (
          <span className="text-muted-foreground">暂无内容</span>
        ),
      size: 320,
    },
    {
      accessorKey: "user_content",
      header: "人工标注",
      cell: ({ row }) =>
        row.original.user_content ? (
          <ContentPreview content={row.original.user_content} />
        ) : (
          <span className="text-muted-foreground">无</span>
        ),
      size: 320,
    },
    {
      accessorKey: "is_passed",
      header: "审核状态",
      cell: ({ row }) => {
        const status = row.original.is_passed;
        if (status === true) {
          return (
            <Badge variant="outline" className="text-muted-foreground px-1.5">
              <IconCircleCheckFilled className="fill-green-500 dark:fill-green-400" />
              已通过
            </Badge>
          );
        } else if (status === false) {
          return (
            <Badge variant="outline" className="text-muted-foreground px-1.5">
              <IconCircleCheckFilled className="fill-red-500 dark:fill-red-400" />
              未通过
            </Badge>
          );
        } else {
          return (
            <Badge variant="outline" className="text-muted-foreground px-1.5">
              待审核
            </Badge>
          );
        }
      },
      size: 80,
    },
    {
      accessorKey: "filled_by",
      header: "填写人",
      cell: ({ row }) => (
        <span className="text-muted-foreground">
          {row.original.filled_by || "-"}
        </span>
      ),
      size: 100,
    },
    {
      accessorKey: "create_at",
      header: "创建时间",
      cell: ({ row }) => (
        <span className="text-muted-foreground">
          {formatDate(row.original.create_at)}
        </span>
      ),
      sortingFn: "datetime",
      size: 60,
    },
    {
      id: "actions",
      cell: ({ }) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="size-8 text-muted-foreground">
              <IconDotsVertical />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-32">
            <DropdownMenuItem>编辑</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-destructive">
              删除
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
      size: 60,
    },
  ];

  /* ---------------- 搜索状态 ---------------- */
  const [searchName, setSearchName] = React.useState(searchParams.name);

  /* ---------------- 表格实例 ---------------- */
  const [rowSelection, setRowSelection] = React.useState({});
  const table = useReactTable({
    data,
    columns,
    state: { rowSelection },
    enableRowSelection: true,
    onRowSelectionChange: setRowSelection,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  /* ---------------- 事件 ---------------- */
  const handleSearch = () => onSearch(searchName, searchParams.pass_state);

  const handleKeyDown = (e: React.KeyboardEvent) =>
    e.key === "Enter" && handleSearch();
  const totalPages = Math.ceil(pagination.total / pagination.size);
  /* ---------------- 渲染 ---------------- */
  return (
    <div className="w-full h-full flex flex-col gap-6">
      {/* 搜索栏和新增按钮 */}
      <div className="flex items-center justify-between px-4 lg:px-6 py-2">
        <div className="text-sm text-muted-foreground"></div>
        <div className="w-2/3 flex items-center gap-2">
          <div className="relative flex-1">
            <IconSearch className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="搜索..."
              value={searchName}
              onChange={(event) => setSearchName(event.target.value)}
              onKeyDown={handleKeyDown}
              className="pl-8"
            />
          </div>

          <Select
            value={searchParams.pass_state}
            onValueChange={(v: KnowledgeLabelType) => {
              // 当类型改变时自动触发搜索
              onSearch(searchName, v);
            }}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="类型" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部</SelectItem>
              <SelectItem value="passed">通过</SelectItem>
              <SelectItem value="unpassed">未通过</SelectItem>
              <SelectItem value="unchecked">待审核</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={handleSearch}>搜索</Button>
          <Button
            variant="secondary"
            onClick={() => {
              setSearchName("");
              onReset();
            }}>
            重置
          </Button>
          {/* 新增按钮 */}
          <AnnotationDialog batchId={batchId} type="add" onSave={onReset} />
        </div>
      </div>
      {/* 表格区域 */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="overflow-hidden rounded-lg border flex-1 flex flex-col">
          {/* 表头：固定 */}
          <div className="overflow-hidden">
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
                        className="align-middle">
                        {h.isPlaceholder
                          ? null
                          : flexRender(
                            h.column.columnDef.header,
                            h.getContext()
                          )}
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
                    <TableCell
                      colSpan={columns.length}
                      className="h-24 text-center">
                      加载中...
                    </TableCell>
                  </TableRow>
                ) : table.getRowModel().rows.length ? (
                  table.getRowModel().rows.map((row) => (
                    <TableRow
                      key={row.id}
                      data-state={row.getIsSelected() && "selected"}>
                      {row.getVisibleCells().map((cell) => (
                        <TableCell key={cell.id} className="align-middle py-2">
                          {flexRender(
                            cell.column.columnDef.cell,
                            cell.getContext()
                          )}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell
                      colSpan={columns.length}
                      className="h-24 text-center">
                      无数据
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>

          {/* 分页：固定 */}
          <div className="flex items-center justify-between px-4 py-2 border-t shrink-0">
            <div className="text-muted-foreground hidden flex-1 text-sm lg:flex">
              共 {pagination.total} 条数据
            </div>
            <div className="flex w-full items-center gap-8 lg:w-fit">
              <div className="hidden items-center gap-2 lg:flex">
                <Label htmlFor="rows-per-page" className="text-sm font-medium">
                  每页行数
                </Label>
                <Select
                  value={`${searchParams.size}`}
                  onValueChange={(v) => {
                    onPageSizeChange(Number(v));
                    table.setPageSize(Number(v));
                  }}>
                  <SelectTrigger className="w-20" size="sm" id="rows-per-page">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent side="top">
                    {[10, 20, 30, 40, 50].map((s) => (
                      <SelectItem key={s} value={`${s}`}>
                        {s}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="text-sm font-medium">
                第 {pagination.page} 页，共 {totalPages} 页
              </div>

              <div className="ml-auto flex items-center gap-2 lg:ml-0">
                <Button
                  variant="outline"
                  className="hidden lg:flex size-8"
                  size="icon"
                  onClick={() => onPageChange(1)}
                  disabled={pagination.page <= 1}>
                  <IconChevronsLeft className="size-4" />
                </Button>
                <Button
                  variant="outline"
                  className="size-8"
                  size="icon"
                  onClick={() => onPageChange(pagination.page - 1)}
                  disabled={pagination.page <= 1}>
                  <IconChevronLeft className="size-4" />
                </Button>
                <Button
                  variant="outline"
                  className="size-8"
                  size="icon"
                  onClick={() => onPageChange(pagination.page + 1)}
                  disabled={!pagination.hasNext}>
                  <IconChevronRight className="size-4" />
                </Button>
                <Button
                  variant="outline"
                  className="hidden lg:flex size-8"
                  size="icon"
                  onClick={() => onPageChange(totalPages)}
                  disabled={
                    !pagination.hasNext || pagination.page >= totalPages
                  }>
                  <IconChevronsRight className="size-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
