import React from "react";
import { Card } from "@/components/ui/card";

interface KpiCardProps {
  totalQa: number;
  avgDailyQa: number;
  totalVotes: number;
  goodRate: number;
  loading?: boolean;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  totalQa,
  avgDailyQa,
  totalVotes,
  goodRate,
  loading = false,
}) => {
  if (loading) {
    return (
      <Card className="flex-1 p-4 bg-[#1f2937] border-[#374151]">
        <h2 className="mb-3 text-base font-semibold text-gray-100">核心 KPI</h2>
        <div className="space-y-3 text-sm">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="flex items-center justify-between rounded-md bg-[#111827] px-3 py-2 border border-[#374151] animate-pulse">
              <div className="h-4 w-20 bg-gray-700 rounded"></div>
              <div className="h-4 w-16 bg-gray-700 rounded"></div>
            </div>
          ))}
        </div>
      </Card>
    );
  }

  return (
    <Card className="flex-1 p-4 bg-[#1f2937] border-[#374151]">
      <h2 className="mb-3 text-base font-semibold text-gray-100">核心 KPI</h2>
      <div className="space-y-3 text-sm">
        <div className="flex items-center justify-between rounded-md bg-[#111827] px-3 py-2 border border-[#374151]">
          <span className="text-gray-300">累计问答量</span>
          <span className="text-lg font-semibold text-gray-100">
            {totalQa.toLocaleString()}
          </span>
        </div>
        <div className="flex items-center justify-between rounded-md bg-[#111827] px-3 py-2 border border-[#374151]">
          <span className="text-gray-300">日均问答量</span>
          <span className="text-lg font-semibold text-gray-100">
            {avgDailyQa.toLocaleString()}
          </span>
        </div>
        <div className="flex items-center justify-between rounded-md bg-[#111827] px-3 py-2 border border-[#374151]">
          <span className="text-gray-300">总投票数</span>
          <span className="text-lg font-semibold text-gray-100">
            {totalVotes.toLocaleString()}
          </span>
        </div>
        <div className="flex items-center justify-between rounded-md bg-[#111827] px-3 py-2 border border-[#374151]">
          <span className="text-gray-300">好评率</span>
          <span className="text-lg font-semibold text-green-400">
            {goodRate.toFixed(2)}%
          </span>
        </div>
      </div>
    </Card>
  );
};
