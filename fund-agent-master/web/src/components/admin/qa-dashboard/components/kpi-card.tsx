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
      <Card className="flex-1 p-4 bg-card border-border">
        <h2 className="mb-3 text-base font-semibold text-foreground">核心 KPI</h2>
        <div className="space-y-3 text-sm">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="flex items-center justify-between rounded-md bg-muted px-3 py-2 border border-border animate-pulse">
              <div className="h-4 w-20 bg-muted-foreground/20 rounded"></div>
              <div className="h-4 w-16 bg-muted-foreground/20 rounded"></div>
            </div>
          ))}
        </div>
      </Card>
    );
  }

  return (
    <Card className="flex-1 p-4 bg-card border-border">
      <h2 className="mb-3 text-base font-semibold text-foreground">核心 KPI</h2>
      <div className="space-y-3 text-sm">
        <div className="flex items-center justify-between rounded-md bg-muted px-3 py-2 border border-border">
          <span className="text-muted-foreground">累计问答量</span>
          <span className="text-lg font-semibold text-foreground">
            {totalQa.toLocaleString()}
          </span>
        </div>
        <div className="flex items-center justify-between rounded-md bg-muted px-3 py-2 border border-border">
          <span className="text-muted-foreground">日均问答量</span>
          <span className="text-lg font-semibold text-foreground">
            {avgDailyQa.toLocaleString()}
          </span>
        </div>
        <div className="flex items-center justify-between rounded-md bg-muted px-3 py-2 border border-border">
          <span className="text-muted-foreground">总投票数</span>
          <span className="text-lg font-semibold text-foreground">
            {totalVotes.toLocaleString()}
          </span>
        </div>
        <div className="flex items-center justify-between rounded-md bg-muted px-3 py-2 border border-border">
          <span className="text-muted-foreground">好评率</span>
          <span className="text-lg font-semibold text-green-600 dark:text-green-400">
            {goodRate.toFixed(2)}%
          </span>
        </div>
      </div>
    </Card>
  );
};
