-- 创建反馈表
-- 创建时间: 2025-12-15
-- 描述: 用户反馈功能表，支持文字和图片反馈

-- 删除表（如果存在）
DROP TABLE IF EXISTS "feedback" CASCADE;

-- 创建反馈表
CREATE TABLE "feedback" (
    "id" BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    "content" TEXT NOT NULL,                    -- 反馈内容（必填）
    "images" JSONB,                             -- 图片信息（JSON格式，可选）
    "phone" TEXT,                               -- 联系电话（可选）
    "status" VARCHAR(255) NOT NULL DEFAULT 'A', -- 状态：A-激活，D-删除，P-处理中
    "created_time" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    "updated_time" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP   -- 更新时间
);

-- 创建索引
CREATE INDEX "idx_feedback_status" ON "feedback" ("status");
CREATE INDEX "idx_feedback_created_time" ON "feedback" ("created_time" DESC);

-- 添加注释
COMMENT ON TABLE "feedback" IS '用户反馈表';
COMMENT ON COLUMN "feedback"."id" IS '反馈ID，主键';
COMMENT ON COLUMN "feedback"."content" IS '反馈内容，用户详细描述的问题或建议';
COMMENT ON COLUMN "feedback"."images" IS '图片信息，JSON格式存储图片URL、文件名等信息';
COMMENT ON COLUMN "feedback"."phone" IS '联系电话，便于后续联系用户';
COMMENT ON COLUMN "feedback"."status" IS '反馈状态：A-激活，D-删除，P-处理中';
COMMENT ON COLUMN "feedback"."created_time" IS '创建时间';
COMMENT ON COLUMN "feedback"."updated_time" IS '最后更新时间';

-- 创建更新时间的触发器
CREATE OR REPLACE FUNCTION update_feedback_updated_time()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_time = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_feedback_updated_time
    BEFORE UPDATE ON "feedback"
    FOR EACH ROW
    EXECUTE FUNCTION update_feedback_updated_time();

-- 示例数据插入（可选）
INSERT INTO "feedback" ("content", "phone", "status") VALUES
    ('系统响应速度很慢，希望能够优化', '13800138000', 'A'),
    ('建议增加夜间模式功能', NULL, 'A'),
    ('界面设计很美观，使用体验不错', '13900139000', 'A');

-- 查询示例
-- 1. 查看所有激活状态的反馈
-- SELECT * FROM "feedback" WHERE "status" = 'A' ORDER BY "created_time" DESC;

-- 2. 查看包含图片的反馈
-- SELECT * FROM "feedback" WHERE "images" IS NOT NULL AND "images" != '[]'::jsonb;

-- 3. 按时间范围查询反馈
-- SELECT * FROM "feedback"
-- WHERE "created_time" >= '2025-12-01'
-- AND "created_time" < '2025-12-16'
-- ORDER BY "created_time" DESC;