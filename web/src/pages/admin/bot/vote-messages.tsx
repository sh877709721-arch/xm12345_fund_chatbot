
import { VoteStatsTableOptimized } from "@/components/admin/bot/vote-stats-table-optimized";

export default function VoteMessages() {
  return (
    <div className="flex gap-2 h-full">
      {/* 优化后的数据表格 */}
      <div className="flex-1 flex flex-col p-6">
        <VoteStatsTableOptimized />
      </div>
    </div>
  );
}