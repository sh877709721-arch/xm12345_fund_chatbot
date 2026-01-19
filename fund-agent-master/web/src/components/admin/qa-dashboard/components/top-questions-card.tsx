import React from "react";
import ReactECharts from "echarts-for-react";
import { Card } from "@/components/ui/card";
import { useTheme } from "@/components/theme-provider";

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
  const { theme } = useTheme();
  const [isDark, setIsDark] = React.useState(() => {
    if (theme === "dark") return true;
    if (theme === "light") return false;
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  });

  React.useEffect(() => {
    const updateTheme = () => {
      if (theme === "dark") {
        setIsDark(true);
      } else if (theme === "light") {
        setIsDark(false);
      } else {
        setIsDark(window.matchMedia("(prefers-color-scheme: dark)").matches);
      }
    };
    updateTheme();
    
    if (theme === "system") {
      const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
      mediaQuery.addEventListener("change", updateTheme);
      return () => mediaQuery.removeEventListener("change", updateTheme);
    }
  }, [theme]);

  const displayData = React.useMemo(() => data.slice(0, topN).reverse(), [data, topN]);
  
  const axisLineColor = isDark ? "#4b5563" : "#e5e7eb";
  const axisLabelColor = isDark ? "#9ca3af" : "#6b7280";
  const splitLineColor = isDark ? "#374151" : "#e5e7eb";
  const tooltipBg = isDark ? "rgba(31, 41, 55, 0.95)" : "rgba(255, 255, 255, 0.95)";
  const tooltipBorder = isDark ? "#4b5563" : "#e5e7eb";
  const tooltipText = isDark ? "#f3f4f6" : "#111827";
  
  const option = React.useMemo(() => ({
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
          color: axisLineColor,
        },
      },
      axisLabel: {
        color: axisLabelColor,
        fontSize: 11,
      },
      splitLine: {
        lineStyle: {
          color: splitLineColor,
          type: "dashed",
        },
      },
    },
    yAxis: {
      type: "category",
      data: displayData.map((item) => item.question.length > 10 ? item.question.substring(0, 10) + "..." : item.question),
      axisLine: {
        lineStyle: {
          color: axisLineColor,
        },
      },
      axisLabel: {
        color: axisLabelColor,
        fontSize: 11,
      },
    },
    tooltip: {
      trigger: "axis",
      backgroundColor: tooltipBg,
      borderColor: tooltipBorder,
      borderWidth: 1,
      textStyle: {
        color: tooltipText,
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
  }), [displayData, axisLineColor, axisLabelColor, splitLineColor, tooltipBg, tooltipBorder, tooltipText]);

  if (loading) {
    return (
      <Card className="min-h-[280px] p-4 bg-card border-border">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-base font-semibold text-foreground">{title}</h2>
        </div>
        <div className="h-[240px] w-full flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="min-h-[280px] p-4 bg-card border-border">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-base font-semibold text-foreground">{title}</h2>
      </div>
      <div className="h-[240px] w-full">
        <ReactECharts option={option} style={{ height: "100%", width: "100%" }} />
      </div>
    </Card>
  );
};
