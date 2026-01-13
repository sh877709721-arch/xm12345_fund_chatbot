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
    <Card className="flex-1 min-h-[160px] p-4 bg-card border-border">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-base font-semibold text-foreground">{title}</h2>
      </div>
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="rounded-md bg-muted p-3 border border-border">
          <div className="text-muted-foreground">总投票数</div>
          <div className="mt-1 text-xl font-semibold text-foreground">{totalCount}</div>
        </div>
        <div className="rounded-md bg-muted p-3 border border-border">
          <div className="text-muted-foreground">好评数</div>
          <div className="mt-1 text-xl font-semibold text-foreground">{goodCount}</div>
        </div>
        <div className="rounded-md bg-muted p-3 border border-border">
          <div className="text-muted-foreground">中评数</div>
          <div className="mt-1 text-xl font-semibold text-foreground">{mediumCount}</div>
        </div>
        <div className="rounded-md bg-muted p-3 border border-border">
          <div className="text-muted-foreground">差评数</div>
          <div className="mt-1 text-xl font-semibold text-foreground">{badCount}</div>
        </div>
      </div>
    </Card>
  );
};
