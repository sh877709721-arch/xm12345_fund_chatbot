import React from "react";
import ReactECharts from "echarts-for-react";
import { Card } from "@/components/ui/card";

interface TypeDistributionDataItem {
  name: string;
  value: number;
}

interface TypeDistributionCardProps {
  title?: string;
  data?: TypeDistributionDataItem[];
  loading?: boolean;
}

export const TypeDistributionCard: React.FC<TypeDistributionCardProps> = ({
  title = "问答类型占比",
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
  const colors = ["#60a5fa", "#8b5cf6", "#f59e0b", "#10b981", "#ef4444", "#ec4899"];
  
  const option = {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "item",
      backgroundColor: "rgba(31, 41, 55, 0.95)",
      borderColor: "#4b5563",
      borderWidth: 1,
      textStyle: {
        color: "#f3f4f6",
      },
      formatter: "{a} <br/>{b}: {c} ({d}%)",
    },
    legend: {
      orient: "vertical",
      left: "left",
      top: "middle",
      textStyle: {
        color: "#9ca3af",
        fontSize: 11,
      },
    },
    series: [
      {
        name: "类型占比",
        type: "pie",
        radius: ["40%", "70%"],
        center: ["60%", "50%"],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 4,
          borderColor: "#1f2937",
          borderWidth: 2,
        },
        label: {
          show: false,
          position: "center",
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: "bold",
            color: "#f3f4f6",
          },
        },
        labelLine: {
          show: false,
        },
        data: data.map((item, index) => ({
          ...item,
          itemStyle: {
            color: colors[index % colors.length],
          },
        })),
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
