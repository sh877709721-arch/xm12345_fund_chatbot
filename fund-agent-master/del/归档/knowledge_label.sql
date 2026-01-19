-- 表: knowledge_label_batch
CREATE TABLE knowledge_label_batch (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- 表: knowledge_label
CREATE TABLE knowledge_label (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NULL,
    batch_id BIGINT NOT NULL,
    created_by BIGINT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (batch_id) REFERENCES knowledge_label_batch(id) ON DELETE CASCADE
);

-- 表: knowledge_label_detail
CREATE TABLE knowledge_label_detail (
    id SERIAL PRIMARY KEY,
    knowledge_label_id BIGINT NOT NULL,  -- 建议使用小写和下划线命名
    title VARCHAR(255) NOT NULL,
    content TEXT NULL,
    context TEXT NULL,
    role knowledgeroleenum,
    is_pass BOOLEAN NULL,
    version BIGINT NULL,
    filled_by VARCHAR(255) NULL,
    created_by BIGINT NULL,
    status knowledgestatusenum NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (knowledge_label_id) REFERENCES knowledge_label(id) ON DELETE CASCADE
);