import React from "react";
import ReactECharts from "echarts-for-react";
import { Card } from "@/components/ui/card";
import { useTheme } from "@/components/theme-provider";

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

  const colors = ["#60a5fa", "#8b5cf6", "#f59e0b", "#10b981", "#ef4444", "#ec4899"];
  
  const tooltipBg = isDark ? "rgba(31, 41, 55, 0.95)" : "rgba(255, 255, 255, 0.95)";
  const tooltipBorder = isDark ? "#4b5563" : "#e5e7eb";
  const tooltipText = isDark ? "#f3f4f6" : "#111827";
  const legendText = isDark ? "#9ca3af" : "#6b7280";
  const borderColor = isDark ? "#1f2937" : "#ffffff";
  const emphasisText = isDark ? "#f3f4f6" : "#111827";
  
  const option = React.useMemo(() => ({
    backgroundColor: "transparent",
    tooltip: {
      trigger: "item",
      backgroundColor: tooltipBg,
      borderColor: tooltipBorder,
      borderWidth: 1,
      textStyle: {
        color: tooltipText,
      },
      formatter: "{a} <br/>{b}: {c} ({d}%)",
    },
    legend: {
      orient: "vertical",
      left: "left",
      top: "middle",
      textStyle: {
        color: legendText,
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
          borderColor: borderColor,
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
            color: emphasisText,
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
  }), [data, colors, tooltipBg, tooltipBorder, tooltipText, legendText, borderColor, emphasisText]);

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
