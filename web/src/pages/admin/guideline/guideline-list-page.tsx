import { useState } from "react";
import { useGuidelineData } from "@/hooks/use-guideline-data";
import { GuidelineDialog } from "@/components/admin/guideline/guideline-form";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
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
import { Badge } from "@/components/ui/badge";
import { IconDotsVertical, IconSearch, IconRefresh, IconChevronsLeft, IconChevronLeft, IconChevronRight, IconChevronsRight } from "@tabler/icons-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ContentPreview } from "@/components/admin/guideline/content-preview";
import { type GuidelineStatus } from "@/utils/request/guideline";
import { cn } from "@/lib/utils";
export default function GuidelineListPage() {
  const {
    guidelineData,
    loading,
    handleSearch,
    handleReset,
    handlePageChange,
    handleRefresh,
    updateLocalGuideline,
    handleDelete,
  } = useGuidelineData();

  const [searchTitle, setSearchTitle] = useState("");
  const [statusFilter, setStatusFilter] = useState<GuidelineStatus | "all">("all");
  const [pageSize, setPageSize] = useState(guidelineData.size);

  const handleSearchClick = () => {
    handleSearch({ title: searchTitle, status: statusFilter });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN');
  };

  const getStatusConfig = (status: GuidelineStatus) => {
    const statusMap = {
      A: { label: "已启用", color: "text-green-500" },
      I: { label: "已禁用", color: "text-gray-500" },
      D: { label: "草稿", color: "text-yellow-500" },
      X: { label: "已删除", color: "text-red-500" },
    };
    return statusMap[status] || statusMap.D;
  };

  const totalPages = Math.ceil(guidelineData.total / guidelineData.size);

  const handlePageSizeChange = (newSize: number) => {
    setPageSize(newSize);
    handleSearch({ title: searchTitle, status: statusFilter, size: newSize });
  };

  return (
    <div className="w-full h-full flex flex-col gap-6">
      {/* 顶部工具栏 */}
      <div className="flex items-center justify-between px-4 lg:px-6 py-2">
        <div className="text-sm text-muted-foreground">
          行动指南管理
        </div>

        <div className="w-2/3 flex items-center gap-2">
          <div className="relative flex-1">
            <IconSearch className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="搜索标题..."
              className="pl-10"
              value={searchTitle}
              onChange={(e) => setSearchTitle(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearchClick()}
            />
          </div>

          <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as typeof statusFilter)}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="状态" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部状态</SelectItem>
              <SelectItem value="A">已启用</SelectItem>
              <SelectItem value="I">已禁用</SelectItem>
              <SelectItem value="D">草稿</SelectItem>
            </SelectContent>
          </Select>

          <Button onClick={handleSearchClick}>搜索</Button>
          <Button variant="outline" onClick={handleReset}>重置</Button>
          <Button variant="outline" onClick={handleRefresh}>
            <IconRefresh className={cn("h-4 w-4 mr-1", loading && "animate-spin")} />
            刷新
          </Button>

          <GuidelineDialog type="add" onSave={handleRefresh} />
        </div>
      </div>

      {/* 表格区域 */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="overflow-hidden rounded-lg border flex-1 flex flex-col">
          {/* 表头：固定 */}
          <div className="overflow-hidden">
            <Table>
              <TableHeader className="bg-muted">
                <TableRow>
                  <TableHead className="w-[80px]">ID</TableHead>
                  <TableHead className="w-[300px]">标题</TableHead>
                  <TableHead className="w-[400px]">触发条件</TableHead>
                  <TableHead className="w-[400px]">行动内容</TableHead>
                  <TableHead className="w-[100px]">优先级</TableHead>
                  <TableHead className="w-[100px]">状态</TableHead>
                  <TableHead className="w-[180px]">创建时间</TableHead>
                  <TableHead className="w-[80px]">操作</TableHead>
                </TableRow>
              </TableHeader>
            </Table>
          </div>

          {/* 表体：滚动 */}
          <div className="overflow-auto flex-1">
            <Table>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8">
                      加载中...
                    </TableCell>
                  </TableRow>
                ) : guidelineData.items.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8">
                      暂无数据
                    </TableCell>
                  </TableRow>
                ) : (
                  guidelineData.items.map((item) => {
                    const statusConfig = getStatusConfig(item.status);
                    return (
                      <TableRow key={item.id}>
                        <TableCell className="font-medium">{item.id}</TableCell>
                        <TableCell>
                          <GuidelineDialog
                            item={item}
                            type="edit"
                            onUpdateLocal={updateLocalGuideline}
                          />
                        </TableCell>
                        <TableCell>
                          <ContentPreview content={item.condition} maxLength={80} />
                        </TableCell>
                        <TableCell>
                          <ContentPreview content={item.action} maxLength={80} />
                        </TableCell>
                        <TableCell>{item.priority}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className={statusConfig.color}>
                            {statusConfig.label}
                          </Badge>
                        </TableCell>
                        <TableCell>{formatDate(item.created_time)}</TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon">
                                <IconDotsVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <GuidelineDialog item={item} type="row_edit" onUpdateLocal={updateLocalGuideline} />
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                className="text-destructive"
                                onClick={() => {
                                  if (confirm(`确定要删除指南 "${item.title}" 吗？`)) {
                                    handleDelete(item.id);
                                  }
                                }}
                              >
                                删除
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </div>

          {/* 分页：固定 */}
          <div className="flex items-center justify-between px-4 py-2 border-t shrink-0">
            <div className="text-muted-foreground hidden flex-1 text-sm lg:flex">
              共 {guidelineData.total} 条数据
            </div>
            <div className="flex w-full items-center gap-8 lg:w-fit">
              <div className="hidden items-center gap-2 lg:flex">
                <Label htmlFor="rows-per-page" className="text-sm font-medium">
                  每页行数
                </Label>
                <Select
                  value={`${pageSize}`}
                  onValueChange={(v) => handlePageSizeChange(Number(v))}>
                  <SelectTrigger className="w-20" size="sm" id="rows-per-page">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent side="top">
                    {[10, 20, 30, 40, 50, 100].map((s) => (
                      <SelectItem key={s} value={`${s}`}>
                        {s}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="text-sm font-medium">
                第 {guidelineData.page} 页，共 {totalPages} 页
              </div>

              <div className="ml-auto flex items-center gap-2 lg:ml-0">
                <Button
                  variant="outline"
                  className="hidden lg:flex size-8"
                  size="icon"
                  onClick={() => handlePageChange(1)}
                  disabled={guidelineData.page <= 1}>
                  <IconChevronsLeft className="size-4" />
                </Button>
                <Button
                  variant="outline"
                  className="size-8"
                  size="icon"
                  onClick={() => handlePageChange(guidelineData.page - 1)}
                  disabled={!guidelineData.has_prev}>
                  <IconChevronLeft className="size-4" />
                </Button>
                <Button
                  variant="outline"
                  className="size-8"
                  size="icon"
                  onClick={() => handlePageChange(guidelineData.page + 1)}
                  disabled={!guidelineData.has_next}>
                  <IconChevronRight className="size-4" />
                </Button>
                <Button
                  variant="outline"
                  className="hidden lg:flex size-8"
                  size="icon"
                  onClick={() => handlePageChange(totalPages)}
                  disabled={!guidelineData.has_next || guidelineData.page >= totalPages}>
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
