import React from "react";
import ReactECharts from "echarts-for-react";
import { Card } from "@/components/ui/card";
import { useTheme } from "@/components/theme-provider";

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

  const axisLineColor = isDark ? "#4b5563" : "#e5e7eb";
  const axisLabelColor = isDark ? "#9ca3af" : "#6b7280";
  const splitLineColor = isDark ? "#374151" : "#e5e7eb";
  const tooltipBg = isDark ? "rgba(31, 41, 55, 0.95)" : "rgba(255, 255, 255, 0.95)";
  const tooltipBorder = isDark ? "#4b5563" : "#e5e7eb";
  const tooltipText = isDark ? "#f3f4f6" : "#111827";

  const option = React.useMemo(() => ({
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
          color: axisLineColor,
        },
      },
      axisLabel: {
        color: axisLabelColor,
        fontSize: 12,
      },
    },
    yAxis: {
      type: "value",
      axisLine: {
        lineStyle: {
          color: axisLineColor,
        },
      },
      axisLabel: {
        color: axisLabelColor,
        fontSize: 12,
      },
      splitLine: {
        lineStyle: {
          color: splitLineColor,
          type: "dashed",
        },
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
  }), [data, axisLineColor, axisLabelColor, splitLineColor, tooltipBg, tooltipBorder, tooltipText]);

  if (loading) {
    return (
      <Card className="min-h-[300px] p-4 bg-card border-border">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-base font-semibold text-foreground">{title}</h2>
        </div>
        <div className="h-[260px] w-full flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="min-h-[300px] p-4 bg-card border-border">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-base font-semibold text-foreground">{title}</h2>
      </div>
      <div className="h-[260px] w-full">
        <ReactECharts option={option} style={{ height: "100%", width: "100%" }} />
      </div>
    </Card>
  );
};
