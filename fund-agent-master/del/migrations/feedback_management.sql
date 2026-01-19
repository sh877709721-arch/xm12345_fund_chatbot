-- 反馈表管理SQL脚本
-- 包含常用的查询、统计和管理操作

-- ==========================================
-- 1. 基础查询操作
-- ==========================================

-- 查看所有反馈
SELECT
    id,
    LEFT(content, 50) || '...' as content_preview,
    phone,
    status,
    created_time,
    updated_time
FROM feedback
ORDER BY created_time DESC;

-- 查看单个反馈详情
SELECT * FROM feedback WHERE id = 1;

-- 查看包含图片的反馈
SELECT
    id,
    content,
    phone,
    status,
    created_time,
    CASE
        WHEN images IS NOT NULL AND images != '[]'::jsonb THEN '有图片'
        ELSE '无图片'
    END as has_images
FROM feedback
WHERE images IS NOT NULL AND images != '[]'::jsonb
ORDER BY created_time DESC;

-- ==========================================
-- 2. 状态管理
-- ==========================================

-- 标记反馈为已处理
UPDATE feedback
SET status = 'P', updated_time = CURRENT_TIMESTAMP
WHERE id = 1;

-- 标记反馈为已删除（软删除）
UPDATE feedback
SET status = 'D', updated_time = CURRENT_TIMESTAMP
WHERE id = 1;

-- 恢复已删除的反馈
UPDATE feedback
SET status = 'A', updated_time = CURRENT_TIMESTAMP
WHERE id = 1 AND status = 'D';

-- ==========================================
-- 3. 统计查询
-- ==========================================

-- 按状态统计反馈数量
SELECT
    status,
    COUNT(*) as count,
    CASE status
        WHEN 'A' THEN '激活状态'
        WHEN 'P' THEN '处理中'
        WHEN 'D' THEN '已删除'
        ELSE '未知状态'
    END as status_desc
FROM feedback
GROUP BY status;

-- 按月统计反馈数量
SELECT
    DATE_TRUNC('month', created_time) as month,
    COUNT(*) as feedback_count,
    COUNT(CASE WHEN images IS NOT NULL AND images != '[]'::jsonb THEN 1 END) as with_images_count
FROM feedback
WHERE status = 'A'
GROUP BY DATE_TRUNC('month', created_time)
ORDER BY month DESC;

-- 近7天反馈统计
SELECT
    DATE(created_time) as date,
    COUNT(*) as daily_count,
    COUNT(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 END) as with_phone_count
FROM feedback
WHERE created_time >= CURRENT_DATE - INTERVAL '7 days'
    AND status = 'A'
GROUP BY DATE(created_time)
ORDER BY date DESC;

-- ==========================================
-- 4. 图片数据管理
-- ==========================================

-- 查看反馈中的图片信息
SELECT
    id,
    content,
    jsonb_array_length(images) as image_count,
    images
FROM feedback
WHERE images IS NOT NULL
    AND images != '[]'::jsonb
ORDER BY created_time DESC;

-- 统计有图片的反馈比例
SELECT
    COUNT(*) as total_feedbacks,
    COUNT(CASE WHEN images IS NOT NULL AND images != '[]'::jsonb THEN 1 END) as with_images,
    ROUND(
        (COUNT(CASE WHEN images IS NOT NULL AND images != '[]'::jsonb THEN 1 END)::float / COUNT(*)) * 100,
        2
    ) as with_images_percentage
FROM feedback
WHERE status = 'A';

-- ==========================================
-- 5. 数据清理
-- ==========================================

-- 清理超过一年的已删除反馈
DELETE FROM feedback
WHERE status = 'D'
    AND updated_time < CURRENT_DATE - INTERVAL '1 year';

-- 清理空内容或无效的反馈
DELETE FROM feedback
WHERE (content IS NULL OR TRIM(content) = '')
    AND status = 'D';

-- ==========================================
-- 6. 导出数据
-- ==========================================

-- 导出激活状态的反馈（用于备份或分析）
COPY (
    SELECT
        id,
        content,
        phone,
        status,
        created_time,
        updated_time,
        CASE
            WHEN images IS NOT NULL AND images != '[]'::jsonb THEN '有图片'
            ELSE '无图片'
        END as image_status
    FROM feedback
    WHERE status = 'A'
    ORDER BY created_time DESC
) TO '/tmp/feedback_export.csv' WITH CSV HEADER;

-- ==========================================
-- 7. 性能优化
-- ==========================================

-- 重建索引（如果查询性能下降）
REINDEX INDEX idx_feedback_status;
REINDEX INDEX idx_feedback_created_time;

-- 分析表统计信息（优化查询计划）
ANALYZE feedback;

-- 查看表大小
SELECT
    pg_size_pretty(pg_total_relation_size('feedback')) as total_size,
    pg_size_pretty(pg_relation_size('feedback')) as table_size,
    pg_size_pretty(pg_total_relation_size('feedback') - pg_relation_size('feedback')) as index_size;