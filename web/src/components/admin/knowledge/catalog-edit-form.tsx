import * as React from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export type DialogStateType = "add" | "edit";

interface CatalogEditFormProps {
  dialogType: DialogStateType;
  formData: {
    id: number; // 改为可选
    name: string; // 改为可选
    catalog_level_1: string;
    catalog_level_2: string;
    catalog_level_3: string;
  };
  onChange: React.Dispatch<
    React.SetStateAction<{
      id: number;
      name: string;
      catalog_level_1: string;
      catalog_level_2: string;
      catalog_level_3: string;
    }>
  >;
  onSave: () => void;
  onCancel?: () => void;
}

const CatalogEditForm: React.FC<CatalogEditFormProps> = ({
  dialogType,
  formData,
  onChange,
  onSave,
  onCancel,
}) => {
  return (
    <div className="grid gap-4 py-4">
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="level1" className="text-right">
          一级目录 *
        </Label>
        <Input
          id="level1"
          value={formData.catalog_level_1}
          onChange={(e) =>
            onChange({
              id: formData.id, // 保留 id（如果存在）
              name: formData.name, // 保留 name（如果存在）
              catalog_level_1: e.target.value,
              catalog_level_2: formData.catalog_level_2,
              catalog_level_3: formData.catalog_level_3,
            })
          }
          className="col-span-3"
          placeholder="请输入一级目录名称"
        />
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="level2" className="text-right">
          二级目录 *
        </Label>
        <Input
          id="level2"
          value={formData.catalog_level_2}
          onChange={(e) =>
            onChange({
              id: formData.id,
              name: formData.name,
              catalog_level_1: formData.catalog_level_1,
              catalog_level_2: e.target.value,
              catalog_level_3: formData.catalog_level_3,
            })
          }
          className="col-span-3"
          placeholder="请输入二级目录名称"
        />
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="level3" className="text-right">
          三级目录 *
        </Label>
        <Input
          id="level3"
          value={formData.catalog_level_3}
          onChange={(e) =>
            onChange({
              id: formData.id,
              name: formData.name,
              catalog_level_1: formData.catalog_level_1,
              catalog_level_2: formData.catalog_level_2,
              catalog_level_3: e.target.value,
            })
          }
          className="col-span-3"
          placeholder="请输入三级目录名称"
        />
      </div>

      <div className="flex justify-end gap-2 pt-4">
        {onCancel && (
          <Button variant="outline" onClick={onCancel}>
            取消
          </Button>
        )}
        <Button onClick={onSave}>
          {dialogType === "edit" ? "更新目录" : "创建目录"}
        </Button>
      </div>
    </div>
  );
};

export default CatalogEditForm;
