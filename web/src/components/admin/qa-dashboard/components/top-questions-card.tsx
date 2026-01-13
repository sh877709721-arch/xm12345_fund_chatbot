import React from "react";
import ReactECharts from "echarts-for-react";
import { Card } from "@/components/ui/card";

interface TopQuestionDataItem {
  question: string;
  count: number;
}

interface TopQuestionsCardProps {
  title?: string;
  data?: TopQuestionDataItem[];
  topN?: number;
  loading?: boolean;
}

export const TopQuestionsCard: React.FC<TopQuestionsCardProps> = ({
  title = "高频问答 TOP5",
  data = [],
  topN = 5,
  loading = false,
}) => {
  if (loading) {
    return (
      <Card className="min-h-[280px] p-4 bg-[#1f2937] border-[#374151]">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-100">{title}</h2>
        </div>
        <div className="h-[240px] w-full flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      </Card>
    );
  }

  const displayData = data.slice(0, topN).reverse();
  
  const option = {
    backgroundColor: "transparent",
    grid: {
      left: "35%",
      right: "10%",
      bottom: "10%",
      top: "10%",
      containLabel: false,
    },
    xAxis: {
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
    yAxis: {
      type: "category",
      data: displayData.map((item) => item.question.length > 10 ? item.question.substring(0, 10) + "..." : item.question),
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
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(31, 41, 55, 0.95)",
      borderColor: "#4b5563",
      borderWidth: 1,
      textStyle: {
        color: "#f3f4f6",
      },
      formatter: (params: any) => {
        const item = displayData[params[0].dataIndex];
        return `${item.question}<br/>提问次数: ${item.count}`;
      },
    },
    series: [
      {
        name: "提问次数",
        type: "bar",
        data: displayData.map((item) => item.count),
        itemStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 1,
            y2: 0,
            colorStops: [
              {
                offset: 0,
                color: "#10b981",
              },
              {
                offset: 1,
                color: "#34d399",
              },
            ],
          },
          borderRadius: [0, 4, 4, 0],
        },
        barWidth: "60%",
      },
    ],
  };

  return (
    <Card className="min-h-[280px] p-4 bg-[#1f2937] border-[#374151]">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-base font-semibold text-gray-100">{title}</h2>
      </div>
      <div className="h-[240px] w-full">
        <ReactECharts option={option} style={{ height: "100%", width: "100%" }} />
      </div>
    </Card>
  );
};
