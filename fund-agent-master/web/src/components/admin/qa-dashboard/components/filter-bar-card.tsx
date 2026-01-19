import React from "react";
import { Card } from "@/components/ui/card";
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { DatePicker } from "@/components/ui/date-input";

interface FilterBarCardProps {
  timePreset: "3d" | "7d" | "30d" | "custom";
  onTimePresetChange: (value: "3d" | "7d" | "30d" | "custom") => void;
  startDate: string;
  onStartDateChange: (value: string) => void;
  endDate: string;
  onEndDateChange: (value: string) => void;
  currentTime: string;
  lastUpdated: string;
  onRefresh?: () => void;
}

export const FilterBarCard: React.FC<FilterBarCardProps> = ({
  timePreset,
  onTimePresetChange,
  startDate,
  onStartDateChange,
  endDate,
  onEndDateChange,
  currentTime,
  lastUpdated,
  onRefresh,
}) => {
  return (
    <Card className="flex flex-row items-center justify-between gap-4 px-4 py-3 bg-card border-border">
      <div className="flex items-center gap-4">
        {/* 时间筛选：预设时间维度 + 自定义时间范围 */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">时间范围：</span>
          <Select value={timePreset} onValueChange={onTimePresetChange}>
            <SelectTrigger className="h-8 w-28 text-xs bg-background border-border text-foreground">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="3d">近 3 天</SelectItem>
              <SelectItem value="7d">近 7 天</SelectItem>
              <SelectItem value="30d">近 30 天</SelectItem>
              <SelectItem value="custom">自定义</SelectItem>
            </SelectContent>
          </Select>
          <div className="flex items-center gap-1">
            <DatePicker
              value={startDate}
              onChange={onStartDateChange}
              placeholder="开始日期"
              disabled={timePreset !== "custom"}
            />
            <span className="text-xs text-muted-foreground ml-4 mr-2">至</span>
            <DatePicker
              value={endDate}
              onChange={onEndDateChange}
              placeholder="结束日期"
              disabled={timePreset !== "custom"}
            />
          </div>
        </div>
      </div>
      <div className="flex items-center gap-4 text-sm text-muted-foreground">
        <span>当前时间：{currentTime}</span>
        <Separator orientation="vertical" className="h-4 bg-border" />
        <span>数据更新：{lastUpdated}</span>
        <Button variant="outline" size="sm" onClick={onRefresh} className="bg-background border-border text-foreground hover:bg-accent">
          手动刷新
        </Button>
      </div>
    </Card>
  );
};
