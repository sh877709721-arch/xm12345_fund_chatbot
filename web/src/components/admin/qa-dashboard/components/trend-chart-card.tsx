import React from "react";
import ReactECharts from "echarts-for-react";
import { Card } from "@/components/ui/card";

interface TrendDataItem {
  date: string;
  value: number;
}

interface TrendChartCardProps {
  title?: string;
  data?: TrendDataItem[];
  loading?: boolean;
}

export const TrendChartCard: React.FC<TrendChartCardProps> = ({
  title = "近7天问答量趋势",
  data = [],
  loading = false,
}) => {
  if (loading) {
    return (
      <Card className="min-h-[300px] p-4 bg-[#1f2937] border-[#374151]">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-100">{title}</h2>
        </div>
        <div className="h-[260px] w-full flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      </Card>
    );
  }
  const option = {
    backgroundColor: "transparent",
    grid: {
      left: "3%",
      right: "4%",
      bottom: "10%",
      top: "10%",
      containLabel: true,
    },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: data.map((item) => item.date),
      axisLine: {
        lineStyle: {
          color: "#4b5563",
        },
      },
      axisLabel: {
        color: "#9ca3af",
        fontSize: 12,
      },
    },
    yAxis: {
      type: "value",
      axisLine: {
        lineStyle: {
          color: "#4b5563",
        },
      },
      axisLabel: {
        color: "#9ca3af",
        fontSize: 12,
      },
      splitLine: {
        lineStyle: {
          color: "#374151",
          type: "dashed",
        },
      },
    },
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(31, 41, 55, 0.95)",
      borderColor: "#4b5563",
      borderWidth: 1,
      textStyle: {
        color: "#f3f4f6",
      },
      axisPointer: {
        type: "line",
        lineStyle: {
          color: "#60a5fa",
        },
      },
    },
    series: [
      {
        name: "问答量",
        type: "line",
        smooth: true,
        data: data.map((item) => item.value),
        itemStyle: {
          color: "#60a5fa",
        },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              {
                offset: 0,
                color: "rgba(96, 165, 250, 0.3)",
              },
              {
                offset: 1,
                color: "rgba(96, 165, 250, 0.05)",
              },
            ],
          },
        },
        lineStyle: {
          width: 2,
          color: "#60a5fa",
        },
      },
    ],
  };

  return (
    <Card className="min-h-[300px] p-4 bg-[#1f2937] border-[#374151]">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-base font-semibold text-gray-100">{title}</h2>
      </div>
      <div className="h-[260px] w-full">
        <ReactECharts option={option} style={{ height: "100%", width: "100%" }} />
      </div>
    </Card>
  );
};
