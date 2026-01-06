/*
 * Guidelines 模块数据库迁移脚本
 *
 * 说明：
 * - condition_embedding: TSVECTOR 类型，用于全文搜索（命名可能混淆，实际是 FTS 功能）
 * - condition_fts: VECTOR(1024) 类型，用于向量嵌入/语义搜索（命名可能混淆，实际是 embedding 功能）
 */

-- ============================================
-- 1. 启用 pgvector 扩展
-- ============================================
CREATE EXTENSION IF NOT EXISTS vector;


-- ============================================
-- 2. 创建 guidelines 表
-- ============================================

CREATE TABLE IF NOT EXISTS chatbot.guidelines
(
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    title VARCHAR(512) NOT NULL,
    condition TEXT NOT NULL,
    action TEXT NOT NULL,
    prompt_template TEXT,
    condition_embedding VECTOR(1024),          -- 全文搜索字段（TSVECTOR）
    condition_fts TSVECTOR,            -- 向量嵌入字段（1024维向量）
	priority BIGINT,
    status VARCHAR(255) NOT NULL DEFAULT 'A',
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS chatbot.guidelines
    OWNER to chatbot;

GRANT ALL ON TABLE chatbot.guidelines TO chatbot;
GRANT ALL ON TABLE chatbot.guidelines TO etl;


-- ============================================
-- 3. 创建索引
-- ============================================

-- GIN 索引用于全文搜索（condition_fts 字段）
CREATE INDEX IF NOT EXISTS idx_condition_fts
ON chatbot.guidelines USING gin (condition_fts);

-- GIN 索引用于向量搜索（condition_embedding 字段）
CREATE INDEX ON guidelines USING hnsw (condition_embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- B-tree 索引用于状态字段过滤
CREATE INDEX IF NOT EXISTS idx_guidelines_status
ON chatbot.guidelines (status);

-- B-tree 索引用于创建时间排序
CREATE INDEX IF NOT EXISTS idx_guidelines_created_time
ON chatbot.guidelines (created_time DESC);


-- ============================================
-- 4. 创建自动更新时间戳的触发器
-- ============================================
CREATE OR REPLACE FUNCTION chatbot.update_guidelines_updated_time()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_time = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_guidelines_updated_time
    BEFORE UPDATE ON chatbot.guidelines
    FOR EACH ROW
    EXECUTE FUNCTION chatbot.update_guidelines_updated_time();


-- ============================================
-- 5. 插入示例数据
-- ============================================
INSERT INTO chatbot.guidelines (title, condition, action, prompt_template, status)
VALUES
    (
        '高血压管理指南',
        '患者被诊断为高血压或血压持续升高',
        '提供高血压管理建议，包括药物治疗、生活方式调整等',
        '基于患者的高血压诊断，提供以下管理建议：\n1. 药物治疗方案\n2. 饮食控制建议\n3. 运动指导\n4. 定期监测指标\n5. 并发症预防',
        'A'
    ),
    (
        '糖尿病管理指南',
        '患者血糖异常或被诊断为糖尿病',
        '提供糖尿病管理建议，包括血糖监测、饮食控制等',
        '针对患者的血糖情况，提供以下管理建议：\n1. 血糖监测频率和方法\n2. 饮食控制原则\n3. 运动处方\n4. 药物使用指导\n5. 低血糖预防',
        'A'
    ),
    (
        '冠心病预防指南',
        '患者有心血管疾病风险因素',
        '提供冠心病预防建议和风险评估',
        '根据患者的心血管风险因素，提供以下预防建议：\n1. 风险因素评估\n2. 生活方式干预\n3. 药物预防策略\n4. 定期检查项目\n5. 紧急情况识别',
        'D'
    ),
    (
        '哮喘急性发作处理',
        '患者出现哮喘急性发作症状',
        '提供哮喘急性发作的紧急处理指导',
        '哮喘急性发作处理流程：\n1. 立即使用速效支气管舒张剂\n2. 评估严重程度\n3. 氧疗指导\n4. 就医指征\n5. 后续预防措施',
        'A'
    )
ON CONFLICT DO NOTHING;


-- ============================================
-- 6. 添加注释说明
-- ============================================
COMMENT ON TABLE chatbot.guidelines IS '临床指南表，存储医疗实践指南和处理流程';
COMMENT ON COLUMN chatbot.guidelines.id IS '主键ID';
COMMENT ON COLUMN chatbot.guidelines.title IS '指南标题';
COMMENT ON COLUMN chatbot.guidelines.condition IS '触发条件或适用情况';
COMMENT ON COLUMN chatbot.guidelines.action IS '应采取的行动或建议';
COMMENT ON COLUMN chatbot.guidelines.prompt_template IS 'AI提示词模板';
COMMENT ON COLUMN chatbot.guidelines.condition_embedding IS '全文搜索字段（TSVECTOR类型）';
COMMENT ON COLUMN chatbot.guidelines.condition_fts IS '向量嵌入字段（1024维向量）';
COMMENT ON COLUMN chatbot.guidelines.status IS '状态：A=激活, I=未激活, D=草稿, X=已删除';
COMMENT ON COLUMN chatbot.guidelines.created_time IS '创建时间';
COMMENT ON COLUMN chatbot.guidelines.updated_time IS '更新时间';


-- ============================================
-- 7. 验证查询
-- ============================================
-- 查看所有指南
-- SELECT * FROM chatbot.guidelines ORDER BY created_time DESC;

-- 查看激活状态的指南数量
-- SELECT status, COUNT(*) FROM chatbot.guidelines GROUP BY status;

-- 全文搜索示例
-- SELECT * FROM chatbot.guidelines WHERE condition_embedding @@ to_tsquery('高血压 & 管理');

-- 向量相似度搜索示例（需要查询向量）
-- SELECT title, action FROM chatbot.guidelines
-- ORDER BY condition_fts <=> '[...1024维向量...]'
-- LIMIT 5;
