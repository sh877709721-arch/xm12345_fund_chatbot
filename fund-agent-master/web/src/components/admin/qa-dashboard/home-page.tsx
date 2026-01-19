import React from "react";
import { FilterBarCard } from "./components/filter-bar-card";
import { KpiCard } from "./components/kpi-card";
import { TrendChartCard } from "./components/trend-chart-card";
import { TimeSlotChartCard } from "./components/time-slot-chart-card";
import { TypeDistributionCard } from "./components/type-distribution-card";
import { TopQuestionsCard } from "./components/top-questions-card";
import { AbnormalStatsCard } from "./components/abnormal-stats-card";
import { useDashboardData } from "@/hooks/use-dashboard-data";

const QaDashboardHomePage: React.FC = () => {
  // 时间筛选：预设时间维度 + 自定义时间范围（默认近 7 天）
  const [timePreset, setTimePreset] = React.useState<"3d" | "7d" | "30d" | "custom">("7d");
  const [startDate, setStartDate] = React.useState<string>("");
  const [endDate, setEndDate] = React.useState<string>("");

  // 获取大屏数据
  const { data, loading, error, refetch } = useDashboardData(startDate || undefined, endDate || undefined);

  const updateRangeByDays = React.useCallback((days: number) => {
    const end = new Date();
    const start = new Date();
    // 例如近 7 天：包含今天在内的 7 天
    start.setDate(end.getDate() - (days - 1));
    const format = (d: Date) => d.toISOString().slice(0, 10);
    setStartDate(format(start));
    setEndDate(format(end));
  }, []);

  React.useEffect(() => {
    if (timePreset === "custom") return;
    if (timePreset === "3d") updateRangeByDays(3);
    if (timePreset === "7d") updateRangeByDays(7);
    if (timePreset === "30d") updateRangeByDays(30);
  }, [timePreset, updateRangeByDays]);

  // 获取当前时间格式化
  const getCurrentTime = () => {
    const now = new Date();
    return now.toLocaleString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    }).replace(/\//g, "-");
  };

  // 计算上次更新时间
  const getLastUpdated = () => {
    if (!data) return "加载中...";
    return "刚刚";
  };

  // 计算时间范围描述
  const getTimeRangeTitle = () => {
    if (!startDate || !endDate) return "问答量趋势";
    
    const start = new Date(startDate);
    const end = new Date(endDate);
    const startStr = start.toLocaleDateString("zh-CN", {
      month: "2-digit",
      day: "2-digit",
    });
    const endStr = end.toLocaleDateString("zh-CN", {
      month: "2-digit",
      day: "2-digit",
    });
    
    if (timePreset === "3d") return "近3天问答量趋势";
    if (timePreset === "7d") return "近7天问答量趋势";
    if (timePreset === "30d") return "近30天问答量趋势";
    return `${startStr} 至 ${endStr} 问答量趋势`;
  };

  // 错误处理
  if (error) {
    return (
      <div className="flex h-full items-center justify-center bg-background">
        <div className="text-center">
          <div className="mb-4 text-6xl">⚠️</div>
          <h2 className="mb-2 text-xl font-semibold text-foreground">加载失败</h2>
          <p className="text-muted-foreground">{error.message}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 rounded-md bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90"
          >
            重新加载
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col gap-4 p-4 bg-background">
      {/* 顶部筛选与时间区：筛选和时间展示保持同一行 */}
      <FilterBarCard
        timePreset={timePreset}
        onTimePresetChange={(value) =>
          setTimePreset(value as "3d" | "7d" | "30d" | "custom")
        }
        startDate={startDate}
        onStartDateChange={setStartDate}
        endDate={endDate}
        onEndDateChange={setEndDate}
        currentTime={getCurrentTime()}
        lastUpdated={getLastUpdated()}
        onRefresh={refetch}
      />

      {/* 中间主体：左中右三列布局 */}
      <div className="grid flex-1 grid-cols-12 gap-4">
        {/* 左侧：核心 KPI 卡片 */}
        <div className="col-span-12 flex flex-col lg:col-span-3">
          <KpiCard
            totalQa={data?.kpi?.total_qa || 0}
            avgDailyQa={data?.kpi?.avg_daily_qa || 0}
            totalVotes={data?.kpi?.total_votes || 0}
            goodRate={data?.kpi?.good_rate || 0}
            loading={loading}
          />
        </div>

        {/* 中间：趋势 & 分布 & 来源占比 */}
        <div className="col-span-12 flex flex-col space-y-4 lg:col-span-6">
          <TrendChartCard 
            title={getTimeRangeTitle()}
            data={data?.trend?.series || []} 
            loading={loading} 
          />

          <div className="grid flex-1 min-h-[260px] grid-cols-2 gap-4">
            <TimeSlotChartCard data={data?.time_slot?.series || []} loading={loading} />
            <TypeDistributionCard
              title="问答来源占比"
              data={data?.source?.distribution || []}
              loading={loading}
            />
          </div>
        </div>

        {/* 右侧：高频问答 TOP5 */}
        <div className="col-span-12 flex flex-col space-y-4 lg:col-span-3">
          <TopQuestionsCard
            data={data?.top_questions?.questions || []}
            loading={loading}
          />
          <AbnormalStatsCard
            totalCount={data?.vote_stats?.total_count || 0}
            goodCount={data?.vote_stats?.good_count || 0}
            mediumCount={data?.vote_stats?.medium_count || 0}
            badCount={data?.vote_stats?.bad_count || 0}
          />
        </div>
      </div>
    </div>
  );
};

export default QaDashboardHomePage;
