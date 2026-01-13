import React from "react";
import { Card } from "@/components/ui/card";

interface AbnormalStatsCardProps {
  title?: string;
  totalCount: number;
  goodCount: number;
  mediumCount: number;
  badCount: number;
}

export const AbnormalStatsCard: React.FC<AbnormalStatsCardProps> = ({
  title = "投票类型统计",
  totalCount,
  goodCount,
  mediumCount,
  badCount,
}) => {
  return (
    <Card className="flex-1 min-h-[160px] p-4 bg-[#1f2937] border-[#374151]">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-base font-semibold text-gray-100">{title}</h2>
      </div>
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="rounded-md bg-[#111827] p-3 border border-[#374151]">
          <div className="text-gray-400">总投票数</div>
          <div className="mt-1 text-xl font-semibold text-gray-100">{totalCount}</div>
        </div>
        <div className="rounded-md bg-[#111827] p-3 border border-[#374151]">
          <div className="text-gray-400">好评数</div>
          <div className="mt-1 text-xl font-semibold text-gray-100">{goodCount}</div>
        </div>
        <div className="rounded-md bg-[#111827] p-3 border border-[#374151]">
          <div className="text-gray-400">中评数</div>
          <div className="mt-1 text-xl font-semibold text-gray-100">{mediumCount}</div>
        </div>
        <div className="rounded-md bg-[#111827] p-3 border border-[#374151]">
          <div className="text-gray-400">差评数</div>
          <div className="mt-1 text-xl font-semibold text-gray-100">{badCount}</div>
        </div>
      </div>
    </Card>
  );
};
