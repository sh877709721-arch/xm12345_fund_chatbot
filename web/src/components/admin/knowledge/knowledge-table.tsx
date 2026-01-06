/* knowledge-table.tsx */
"use client";

import * as React from "react";
import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
} from "@tanstack/react-table";
import {
  IconChevronLeft,
  IconChevronRight,
  IconChevronsLeft,
  IconChevronsRight,
  IconCircleCheckFilled,
  IconDotsVertical,
  IconLoader,
  IconSearch,
  IconChevronUp,
  IconChevronDown,
} from "@tabler/icons-react";

import type { UpdateKnowledgeRequest } from "@/utils/request/knowledge-entries";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { updateKnowledgeEntry } from "@/utils/request/knowledge-entries";
import { toast } from "sonner";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { KnowledgeDialog } from "@/components/admin/knowledge/knowledge-form";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ContentPreview } from "@/components/admin/knowledge/content-preview";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type {
  KnowledgeEntry,
  KnowledgeType,
} from "@/utils/request/knowledge-entries";
import {
  getKnowledgeCatalogs,
  getKnowledgeCatalogTree,
} from "@/utils/request/knowledge-catalog";
import type {
  KnowledgeCatalog,
  CatalogTreeNode,
} from "@/utils/request/knowledge-catalog";
import { type SearchParams } from "@/hooks/use-knowledge-data";

export type DialogStateType = "add" | "edit";

/* ---------- 常量 / 工具 ---------- */
const KNOWLEDGE_TYPE_MAP: Record<KnowledgeType, string> = {
  qa: "问答",
  document: "文档",
  data_table: "数据表",
};
const STATUS_MAP = {
  active: {
    label: "已启用",
    icon: IconCircleCheckFilled,
    color: "text-green-500",
  },
  pending: { label: "待审核", icon: IconLoader, color: "text-yellow-500" },
  deleted: { label: "已删除", icon: null, color: "text-gray-400" },
} as const;

const formatDate = (d: string | Date) =>
  new Date(d).toLocaleDateString("zh-CN");


/* ---------- 列定义 ---------- */

/* ---------- 组件接口（与旧版完全一致） ---------- */
export function DataTable({
  data,
  pagination,
  selectedCatalog,
  loading,
  searchParams,
  onSearch,
  onReset,
  onPageChange,
  onPageSizeChange,
  onUpdateLocal,
}: {
  data: KnowledgeEntry[];
  pagination: {
    total: number;
    page: number;
    size: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
  selectedCatalog: any;
  loading: boolean;
  searchParams: SearchParams;
  onSearch: (
    name?: string,
    knowledgeType?: KnowledgeType | "all",
    status?: string,
    orderby?: 'id' | 'created_at' | 'updated_at',
    order?: 'asc' | 'desc'
  ) => void;
  onReset: () => void;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  onUpdateLocal?: (updatedEntry: KnowledgeEntry) => void;
}) {
  const [catalogs, setCatalogs] = React.useState<KnowledgeCatalog[]>([]);
  const [catalogTree, setCatalogTree] = React.useState<
    Record<string, Record<string, CatalogTreeNode[]>>
  >({});

  // 加载目录数据
  React.useEffect(() => {
    const loadCatalogData = async () => {

      try {
        const [catalogsRes, treeRes] = await Promise.all([
          getKnowledgeCatalogs(),
          getKnowledgeCatalogTree(),
        ]);
        setCatalogs(catalogsRes);
        setCatalogTree(treeRes);
      } catch (error) {
        console.error("加载目录数据失败:", error);
      }
    };

    loadCatalogData();
  }, []);

  const columns: ColumnDef<KnowledgeEntry>[] = [
    {
      id: "select",
      header: ({ table }) => (
        <input
          type="checkbox"
          checked={table.getIsAllPageRowsSelected()}
          onChange={(e) => table.toggleAllPageRowsSelected(!!e.target.checked)}
          aria-label="Select all"
        />
      ),
      cell: ({ row }) => (
        <input
          type="checkbox"
          checked={row.getIsSelected()}
          onChange={(e) => row.toggleSelected(!!e.target.checked)}
          aria-label="Select row"
        />
      ),
      enableSorting: false,
      enableHiding: false,
      size: 50,
    },
    {
      id: "id",
      accessorKey: "id",
      header: ({ column }) => {
        const isSorted = column.getIsSorted();
        return (
          <div className="flex items-center gap-1 cursor-pointer select-none"
            onClick={() => column.toggleSorting()}>
            <span className="text-muted-foreground">ID</span>
            {isSorted === 'asc' && <IconChevronUp className="size-3" />}
            {isSorted === 'desc' && <IconChevronDown className="size-3" />}
          </div>
        );
      },
      cell: ({ row }) => (
        <div className="truncate break-words leading-tight">
          {row.original.id}
        </div>
      ),
      enableSorting: true,
      enableHiding: false,
      size: 80,
    },
    {
      accessorKey: "name",
      header: "知识名称",
      cell: ({ row }) => (
        <KnowledgeDialog
          item={row.original}
          type="edit"
          catalogs={catalogs}
          catalogTree={catalogTree}
          onUpdateLocal={onUpdateLocal}
        />
      ),
      enableHiding: true,
      size: 300,
    },
    {
      accessorKey: "knowledge_type",
      header: "类型",
      cell: ({ row }) => (
        <Badge variant="outline" className="px-1.5 text-muted-foreground">
          {KNOWLEDGE_TYPE_MAP[row.original.knowledge_type] ?? "-"}
        </Badge>
      ),
      size: 60,
    },
    {
      accessorKey: "details",
      header: "内容",
      cell: ({ row }) =>
        row.original.details?.content ? (
          <ContentPreview content={row.original.details.content} />
        ) : (
          <span className="text-muted-foreground">暂无内容</span>
        ),
      size: 400,
    },
    {
      accessorKey: "status",
      header: "状态",
      cell: ({ row }) => {
        const cfg = STATUS_MAP[row.original.status] ?? STATUS_MAP.deleted;
        const Icon = cfg.icon;
        return (
          <Badge
            variant="outline"
            className="gap-1 px-1.5 text-muted-foreground">
            {Icon && <Icon className={`size-3 ${cfg.color}`} />}
            <span>{cfg.label}</span>
          </Badge>
        );
      },
      size: 60,
    },
    {
      accessorKey: "created_at",
      header: ({ column }) => {
        const isSorted = column.getIsSorted();
        return (
          <div className="flex items-center gap-1 cursor-pointer select-none"
            onClick={() => column.toggleSorting()}>
            <span>创建时间</span>
            {isSorted === 'asc' && <IconChevronUp className="size-3" />}
            {isSorted === 'desc' && <IconChevronDown className="size-3" />}
          </div>
        );
      },
      cell: ({ row }) => (
        <span className="text-muted-foreground">
          {formatDate(row.original.created_at)}
        </span>
      ),
      sortingFn: "datetime",
      enableSorting: true,
      size: 100,
    },
    {
      accessorKey: "updated_at",
      header: ({ column }) => {
        const isSorted = column.getIsSorted();
        return (
          <div className="flex items-center gap-1 cursor-pointer select-none"
            onClick={() => column.toggleSorting()}>
            <span>更新时间</span>
            {isSorted === 'asc' && <IconChevronUp className="size-3" />}
            {isSorted === 'desc' && <IconChevronDown className="size-3" />}
          </div>
        );
      },
      cell: ({ row }) => (
        <span className="text-muted-foreground">
          {formatDate(row.original.updated_at)}
        </span>
      ),
      sortingFn: "datetime",
      enableSorting: true,
      size: 100,
    },
    {
      id: "actions",
      cell: ({ row }) => (
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
            <KnowledgeDialog
              item={row.original}
              type="row_edit"
              catalogs={catalogs}
              catalogTree={catalogTree}
              onUpdateLocal={onUpdateLocal}
            />
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="text-destructive text-center"
              onClick={() => handleDelete(row.original)}
            >
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
  const [knowledgeType, setKnowledgeType] = React.useState<
    KnowledgeType | "all"
  >(searchParams.knowledge_type);
  const [status, setStatus] = React.useState<string>(searchParams.status || "all");

  React.useEffect(() => {
    setSearchName(searchParams.name);
    setKnowledgeType(searchParams.knowledge_type);
    setStatus(searchParams.status || "all");
  }, [searchParams]);

  /* ---------------- table 实例 ---------------- */
  const [rowSelection, setRowSelection] = React.useState({});
  const [sorting, setSorting] = React.useState<SortingState>([
    { id: "id", desc: true }  // 初始状态：按 ID 降序
  ]);
  const table = useReactTable({
    data,
    columns,
    state: {
      rowSelection,
      sorting  // 新增排序状态
    },
    enableRowSelection: true,
    onRowSelectionChange: setRowSelection,
    onSortingChange: (updater) => {  // 新增排序处理
      const newSorting = typeof updater === 'function' ? updater(sorting) : updater;
      setSorting(newSorting);

      // 将排序状态转换为 API 参数并触发搜索
      if (newSorting && newSorting.length > 0) {
        const { id, desc } = newSorting[0];
        const orderby = id as 'id' | 'created_at' | 'updated_at';
        const order = desc ? 'desc' : 'asc';
        onSearch(
          searchParams.name,
          searchParams.knowledge_type,
          searchParams.status,
          orderby,
          order
        );
      } else {
        // 取消排序时，恢复默认排序
        onSearch(
          searchParams.name,
          searchParams.knowledge_type,
          searchParams.status,
          'id',
          'desc'
        );
      }
    },
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  /* ---------------- 事件 ---------------- */
  const handleSearch = () => onSearch(searchName, knowledgeType, status);
  const handleKeyDown = (e: React.KeyboardEvent) =>
    e.key === "Enter" && handleSearch();

  const handleDelete = async (item: KnowledgeEntry) => {
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error('请求超时，请检查网络连接')), 30000);
    });

    try {
      // 后端请求
      await Promise.race([
        updateKnowledgeEntry(item.id, {
          knowledge_type: item.knowledge_type,
          knowledge_catalog_id: item.knowledge_catalog_id,
          name: item.name,
          details: {
            ...item.details,
            status: "deleted" as const,
          }
        } as UpdateKnowledgeRequest),
        timeoutPromise
      ]);

      toast.success('知识条目已删除');
    } catch (error: any) {
      console.error("删除知识条目失败:", error);

      // 如果乐观更新失败，回滚状态需要通过重新获取数据来实现
      // 这里可以调用 onReset 来重新获取数据
      if (onReset) {
        onReset();
      }

      if (error.message === '请求超时，请检查网络连接') {
        toast.error('请求超时，请检查网络连接后重试');
      } else if (error.response) {
        const status = error.response.status;
        const data = error.response.data;

        if (status === 400) {
          toast.error('请求参数错误');
        } else if (status === 401) {
          toast.error('未授权访问，请重新登录');
        } else if (status === 403) {
          toast.error('权限不足，无法操作');
        } else if (status === 404) {
          toast.error('请求的资源不存在');
        } else if (status >= 500) {
          toast.error('服务器错误，请稍后重试');
        } else {
          toast.error(data?.detail || data?.message || '删除失败');
        }
      } else if (error.request) {
        toast.error('网络连接失败，请检查网络设置');
      } else {
        toast.error('删除失败，请重试');
      }
    }
  };

  const totalPages = Math.ceil(pagination.total / pagination.size);

  /* ---------------- UI ---------------- */
  return (
    <div className="w-full h-full flex flex-col gap-6">
      {/* 顶部工具栏 */}
      <div className="flex items-center justify-between px-4 lg:px-6 py-2">
        <div className="text-sm text-muted-foreground">
          {selectedCatalog
            ? [
              selectedCatalog.level1,
              selectedCatalog.level2,
              selectedCatalog.level3,
            ]
              .filter(Boolean)
              .join(" / ")
            : "全部知识"}
        </div>

        <div className="w-2/3 flex items-center gap-2">
          <div className="relative flex-1">
            <IconSearch className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="搜索知识名称..."
              className="pl-10"
              value={searchName}
              onChange={(e) => setSearchName(e.target.value)}
              onKeyDown={handleKeyDown}
            />
          </div>
          <Select
            value={knowledgeType}
            onValueChange={(v: KnowledgeType | "all") => {
              setKnowledgeType(v);
              // 当类型改变时自动触发搜索
              onSearch(searchName, v, status);
            }}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="类型" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部类型</SelectItem>
              <SelectItem value="qa">问答</SelectItem>
              <SelectItem value="document">文档</SelectItem>
              <SelectItem value="data_table">数据表</SelectItem>
            </SelectContent>
          </Select>
          <Select
            value={status}
            onValueChange={(v: string) => {
              setStatus(v);
              // 当状态改变时自动触发搜索
              onSearch(searchName, knowledgeType, v);
            }}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="状态" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部状态</SelectItem>
              <SelectItem value="active">已启用</SelectItem>
              <SelectItem value="pending">待审核</SelectItem>
              <SelectItem value="deleted">已删除</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={handleSearch}>搜索</Button>
          <Button variant="outline" onClick={onReset}>
            重置
          </Button>
          <KnowledgeDialog
            type="add"
            catalogs={catalogs}
            catalogTree={catalogTree}
            item={
              {
                name: "",
              } as KnowledgeEntry
            }
            onSave={onReset}
          // 如果需要传递其他属性，如默认值等
          />
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
                    {[10, 20, 30, 40, 50, 100, 500, 1000].map((s) => (
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
