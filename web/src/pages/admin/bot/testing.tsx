import { useState } from "react";
import * as React from "react";
import { BatchList } from "@/components/admin/bot/batch-list";
import { DataTable } from "@/components/admin/bot/annotation-table";
import { Database } from "lucide-react";
import { useEffect } from "react";

import { toast } from "sonner";
import type {
  KnowledgeLabelBatch,
  KnowledgeLabelWithDetailRequest,
} from "@/utils/request/knowledge-label";
import {
  type KnowledgeLabelWithDetailPage,
  getKnowledgeLabelBatchs,
  getKnowledgeLabelsWithDetailsPaginationByBatchId,
} from "@/utils/request/knowledge-label";

import { type KnowledgeLabelType } from "@/components/admin/bot/annotation-table";

export default function TestingBotPage() {
  const [selectedBatchId, setSelectedBatchId] = useState<number | null>(null);
  const [batchList, setBatchList] = useState<KnowledgeLabelBatch[]>([]);
  const [loadingBatch, setLoadingBatch] = useState(true);
  const [searchParams, setSearchParams] =
    useState<KnowledgeLabelWithDetailRequest>({
      batch_id: 1,
      name: "",
      pass_state: "all",
      filled_by: "",
      page: 1,
      size: 10,
    });
  const [knowledgeLabelsWithDetail, setKnowledgeLabelsWithDetails] =
    useState<KnowledgeLabelWithDetailPage>({
      items: [],
      total: 0,
      page: 1,
      size: 10,
      has_next: false,
      has_prev: false,
    });
  const [loading, setLoading] = useState(false);
  // 获取指定批次的标注清单
  const fetchLabelsByBatchId = async (
    batchId: number,
    name: string | undefined,
    pass_state: "passed" | "unpassed" | "unchecked" | "all" = "all",
    filled_by: string | undefined,
    page: number = 1,
    size: number = 10
  ) => {
    try {
      setLoading(true);
      const params = {
        batch_id: batchId,
        name,
        pass_state,
        filled_by,
        page,
        size,
      };

      const dataKnowledgeLabels =
        await getKnowledgeLabelsWithDetailsPaginationByBatchId(params);

      setKnowledgeLabelsWithDetails({
        items: dataKnowledgeLabels.items,
        total: dataKnowledgeLabels.total,
        page: dataKnowledgeLabels.page,
        size: dataKnowledgeLabels.size,
        has_next: dataKnowledgeLabels.has_next,
        has_prev: dataKnowledgeLabels.has_prev,
      });
    } catch (error) {
      console.error("获取标注清单失败:", error);
      toast.error("获取标注清单失败");
    } finally {
      setLoading(false);
    }
  };

  // 获取批次列表
  const fetchBatches = async () => {
    try {
      setLoadingBatch(true);
      const data: KnowledgeLabelBatch[] = await getKnowledgeLabelBatchs();
      setBatchList(data);

      // 如果有批次，则默认选中第一个
      if (data.length > 0) {
        const firstBatchId = data[0].id;
        setSelectedBatchId(firstBatchId);
        setSearchParams((prev) => ({
          ...prev,
          batch_id: firstBatchId,
        }));
        fetchLabelsByBatchId(
          firstBatchId,
          searchParams.name,
          searchParams.pass_state,
          searchParams.filled_by,
          searchParams.page,
          searchParams.size
        );
      }
    } catch (error) {
      console.error("获取批次列表失败:", error);
      toast.error("获取批次列表失败");
    } finally {
      setLoadingBatch(false);
    }
  };

  useEffect(() => {
    fetchBatches();
  }, []);

  // 处理切换批次
  const handleSelectBatch = (batchId: number | null) => {
    setSelectedBatchId(batchId);
    if (batchId !== null) {
      setSearchParams((prev) => ({
        ...prev,
        batch_id: batchId,
        page: 1,
        name: "",
      }));
      fetchLabelsByBatchId(
        batchId,
        searchParams.name,
        searchParams.pass_state,
        searchParams.filled_by,
        searchParams.page,
        searchParams.size
      );
    }
  };

  // 处理搜索
  const handleSearch = (
    name?: string,
    pass_state?: KnowledgeLabelType | "all"
  ) => {
    if (selectedBatchId !== null) {
      // 修复：使用传入的参数而不是旧的 searchParams 值
      setSearchParams((prev) => ({
        ...prev,
        page: 1,
        name: name !== undefined ? name : prev.name,
        pass_state: pass_state !== undefined ? pass_state : prev.pass_state,
      }));

      // 修复：使用当前传入的参数值发起请求
      fetchLabelsByBatchId(
        selectedBatchId,
        name !== undefined ? name : searchParams.name,
        pass_state !== undefined ? pass_state : searchParams.pass_state,
        searchParams.filled_by,
        searchParams.page,
        searchParams.size
      );
    }
  };

  // 处理重置搜索
  const handleReset = () => {
    if (selectedBatchId !== null) {
      setSearchParams((prev) => ({
        ...prev,
        name: "",
        pass_state: "all",
        page: 1,
        size: 10,
      }));
    }
  };

  // 处理分页变化
  const handlePageChange = (page: number) => {
    if (selectedBatchId !== null) {
      setSearchParams((prev) => ({
        ...prev,
        page,
      }));
    }
  };

  // 处理页面大小变化
  const handlePageSizeChange = (size: number) => {
    if (selectedBatchId !== null) {
      setSearchParams((prev) => ({
        ...prev,
        page: 1, // 重置到第一页
        size,
      }));
    }
  };

  React.useEffect(() => {
    if (selectedBatchId !== null) {
      fetchLabelsByBatchId(
        selectedBatchId,
        searchParams.name,
        searchParams.pass_state,
        searchParams.filled_by,
        searchParams.page,
        searchParams.size
      );
    }
  }, [searchParams, selectedBatchId]);

  return (
    <div className="flex gap-2 h-full">
      {/* 左侧目录树 */}
      <div className="h-full flex-[1] min-w-[200px] border-r border-border bg-card flex flex-col overflow-hidden">
        <div className="p-4 border-b border-border">
          <div className="flex items-center gap-2 mb-4">
            <Database className="w-5 h-5 text-primary" />
            <h1 className="text-lg font-semibold text-foreground">
              机器人测试
            </h1>
          </div>
        </div>
        <BatchList
          loading={loadingBatch}
          batchList={batchList}
          setBatchList={setBatchList}
          selectedBatchId={selectedBatchId}
          onSelectBatch={handleSelectBatch}
          itemCount={0}
          completedCount={0}
          onDeleteSuccess={fetchBatches}
        />
      </div>
      {/* 右侧表格区域 */}
      <div className="flex-[5] flex flex-col h-full">
        <DataTable
          batchId={selectedBatchId}
          data={knowledgeLabelsWithDetail.items}
          pagination={{
            total: knowledgeLabelsWithDetail.total,
            page: knowledgeLabelsWithDetail.page,
            size: knowledgeLabelsWithDetail.size,
            hasNext: knowledgeLabelsWithDetail.has_next,
            hasPrev: knowledgeLabelsWithDetail.has_prev,
          }}
          loading={loading}
          searchParams={{
            batch_id: searchParams.batch_id,
            name: searchParams.name,
            pass_state: searchParams.pass_state,
            filled_by: searchParams.filled_by,
            page: searchParams.page,
            size: searchParams.size,
          }}
          onSearch={handleSearch}
          onReset={handleReset}
          onPageChange={handlePageChange}
          onPageSizeChange={handlePageSizeChange}
        />
      </div>
    </div>
  );
}
