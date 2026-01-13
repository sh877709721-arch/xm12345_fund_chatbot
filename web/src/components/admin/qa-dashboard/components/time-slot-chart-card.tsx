import React from "react";
import ReactECharts from "echarts-for-react";
import { Card } from "@/components/ui/card";
import { useTheme } from "@/components/theme-provider";

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
          color: axisLineColor,
        },
      },
      axisLabel: {
        color: axisLabelColor,
        fontSize: 11,
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
        fontSize: 11,
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
  }), [data, axisLineColor, axisLabelColor, splitLineColor, tooltipBg, tooltipBorder, tooltipText]);

  if (loading) {
    return (
      <Card className="flex flex-col p-4 bg-card border-border">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-base font-semibold text-foreground">{title}</h2>
        </div>
        <div className="flex-1 h-[200px] w-full flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="flex flex-col p-4 bg-card border-border">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-base font-semibold text-foreground">{title}</h2>
      </div>
      <div className="flex-1 h-[200px] w-full">
        <ReactECharts option={option} style={{ height: "100%", width: "100%" }} />
      </div>
    </Card>
  );
};
