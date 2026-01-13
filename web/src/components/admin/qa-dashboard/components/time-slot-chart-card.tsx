import React from "react";
import ReactECharts from "echarts-for-react";
import { Card } from "@/components/ui/card";

interface TimeSlotDataItem {
  time: string;
  value: number;
}

interface TimeSlotChartCardProps {
  title?: string;
  data?: TimeSlotDataItem[];
  loading?: boolean;
}

export const TimeSlotChartCard: React.FC<TimeSlotChartCardProps> = ({
  title = "时段分布",
  data = [],
  loading = false,
}) => {
  if (loading) {
    return (
      <Card className="flex flex-col p-4 bg-[#1f2937] border-[#374151]">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-100">{title}</h2>
        </div>
        <div className="flex-1 h-[200px] w-full flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      </Card>
    );
  }
  const option = {
    backgroundColor: "transparent",
    grid: {
      left: "10%",
      right: "10%",
      bottom: "15%",
      top: "10%",
      containLabel: true,
    },
    xAxis: {
      type: "category",
      data: data.map((item) => item.time),
      axisLine: {
        lineStyle: {
          color: "#4b5563",
        },
      },
      axisLabel: {
        color: "#9ca3af",
        fontSize: 11,
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
        fontSize: 11,
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
    },
    series: [
      {
        name: "问答量",
        type: "bar",
        data: data.map((item) => item.value),
        itemStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              {
                offset: 0,
                color: "#8b5cf6",
              },
              {
                offset: 1,
                color: "#6366f1",
              },
            ],
          },
          borderRadius: [4, 4, 0, 0],
        },
        barWidth: "50%",
      },
    ],
  };

  return (
    <Card className="flex flex-col p-4 bg-[#1f2937] border-[#374151]">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-base font-semibold text-gray-100">{title}</h2>
      </div>
      <div className="flex-1 h-[200px] w-full">
        <ReactECharts option={option} style={{ height: "100%", width: "100%" }} />
      </div>
    </Card>
  );
};
