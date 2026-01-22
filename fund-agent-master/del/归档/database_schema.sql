-- =====================================================
-- AI Agent Management Database Schema
-- =====================================================

-- 创建数据库（如果需要）
-- CREATE DATABASE IF NOT EXISTS chatbot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE chatbot;

-- =====================================================
-- 1. Agent实例管理
-- =====================================================
CREATE TABLE agent_instances (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'Agent实例ID',
    instance_name VARCHAR(100) NOT NULL UNIQUE COMMENT '实例名称',
    instance_code VARCHAR(50) NOT NULL UNIQUE COMMENT '实例代码',
    description TEXT COMMENT '实例描述',
    status ENUM('active', 'inactive', 'maintenance') DEFAULT 'active' COMMENT '实例状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by VARCHAR(50) COMMENT '创建人',

    INDEX idx_instance_code (instance_code),
    INDEX idx_status (status)
) ENGINE=InnoDB COMMENT='Agent实例表';

-- =====================================================
-- 2. Agent版本管理
-- =====================================================
CREATE TABLE agent_versions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '版本ID',
    instance_id BIGINT NOT NULL COMMENT '所属实例ID',
    version_name VARCHAR(50) NOT NULL COMMENT '版本名称',
    version_code VARCHAR(20) NOT NULL COMMENT '版本号',
    version_description TEXT COMMENT '版本描述',
    agent_config JSON COMMENT 'Agent完整配置',
    is_current BOOLEAN DEFAULT FALSE COMMENT '是否当前版本',
    status ENUM('draft', 'testing', 'production', 'deprecated') DEFAULT 'draft' COMMENT '版本状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by VARCHAR(50) COMMENT '创建人',

    FOREIGN KEY (instance_id) REFERENCES agent_instances(id) ON DELETE CASCADE,
    UNIQUE KEY uk_instance_version (instance_id, version_code),
    INDEX idx_instance_id (instance_id),
    INDEX idx_status (status)
) ENGINE=InnoDB COMMENT='Agent版本管理表';

-- =====================================================
-- 3. 系统消息模板管理
-- =====================================================
CREATE TABLE message_templates (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '模板ID',
    instance_id BIGINT NOT NULL COMMENT '所属实例ID',
    template_name VARCHAR(100) NOT NULL COMMENT '模板名称',
    template_key VARCHAR(50) NOT NULL COMMENT '模板标识(如DEFAULT_SYSTEM_MESSAGE)',
    language ENUM('zh', 'en') DEFAULT 'zh' COMMENT '语言',
    template_content TEXT NOT NULL COMMENT '模板内容',
    template_type ENUM('system', 'rule', 'knowledge', 'prompt') DEFAULT 'system' COMMENT '模板类型',
    variables JSON COMMENT '模板变量定义',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    version_id BIGINT COMMENT '关联版本ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    FOREIGN KEY (instance_id) REFERENCES agent_instances(id) ON DELETE CASCADE,
    FOREIGN KEY (version_id) REFERENCES agent_versions(id) ON DELETE SET NULL,
    UNIQUE KEY uk_template_key_lang (instance_id, template_key, language, version_id),
    INDEX idx_template_type (template_type),
    INDEX idx_template_key (template_key)
) ENGINE=InnoDB COMMENT='消息模板管理表';

-- =====================================================
-- 4. 知识库管理
-- =====================================================
CREATE TABLE knowledge_sources (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '知识源ID',
    instance_id BIGINT NOT NULL COMMENT '所属实例ID',
    source_name VARCHAR(100) NOT NULL COMMENT '知识源名称',
    source_type ENUM('document', 'database', 'api', 'graph', 'vector') NOT NULL COMMENT '知识源类型',
    source_config JSON COMMENT '知识源配置',
    connection_params JSON COMMENT '连接参数',
    search_config JSON COMMENT '搜索配置',
    priority INT DEFAULT 1 COMMENT '优先级',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    version_id BIGINT COMMENT '关联版本ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    FOREIGN KEY (instance_id) REFERENCES agent_instances(id) ON DELETE CASCADE,
    FOREIGN KEY (version_id) REFERENCES agent_versions(id) ON DELETE SET NULL,
    INDEX idx_source_type (source_type),
    INDEX idx_instance_source (instance_id, source_type)
) ENGINE=InnoDB COMMENT='知识库源管理表';

-- =====================================================
-- 5. 知识文档管理
-- =====================================================
CREATE TABLE knowledge_documents (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '文档ID',
    source_id BIGINT NOT NULL COMMENT '所属知识源ID',
    document_title VARCHAR(200) NOT NULL COMMENT '文档标题',
    document_path VARCHAR(500) COMMENT '文档路径',
    document_content LONGTEXT COMMENT '文档内容',
    document_hash VARCHAR(64) COMMENT '文档哈希值',
    file_size BIGINT COMMENT '文件大小',
    mime_type VARCHAR(100) COMMENT 'MIME类型',
    metadata JSON COMMENT '文档元数据',
    vector_status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending' COMMENT '向量化状态',
    embedding_model VARCHAR(50) COMMENT '嵌入模型',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    FOREIGN KEY (source_id) REFERENCES knowledge_sources(id) ON DELETE CASCADE,
    INDEX idx_source_id (source_id),
    INDEX idx_vector_status (vector_status),
    INDEX idx_document_hash (document_hash)
) ENGINE=InnoDB COMMENT='知识文档管理表';

-- =====================================================
-- 6. 用户会话管理
-- =====================================================
CREATE TABLE user_sessions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '会话ID',
    instance_id BIGINT NOT NULL COMMENT 'Agent实例ID',
    session_id VARCHAR(100) NOT NULL UNIQUE COMMENT '会话唯一标识',
    user_id VARCHAR(100) COMMENT '用户ID',
    user_info JSON COMMENT '用户信息',
    session_metadata JSON COMMENT '会话元数据',
    status ENUM('active', 'ended', 'timeout') DEFAULT 'active' COMMENT '会话状态',
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
    end_time TIMESTAMP NULL COMMENT '结束时间',
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后活动时间',

    FOREIGN KEY (instance_id) REFERENCES agent_instances(id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_last_activity (last_activity)
) ENGINE=InnoDB COMMENT='用户会话管理表';

-- =====================================================
-- 7. 对话消息记录
-- =====================================================
CREATE TABLE chat_messages (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '消息ID',
    session_id BIGINT NOT NULL COMMENT '会话ID',
    message_role ENUM('user', 'assistant', 'system', 'tool') NOT NULL COMMENT '消息角色',
    message_content LONGTEXT COMMENT '消息内容',
    message_metadata JSON COMMENT '消息元数据',
    token_count INT COMMENT 'Token数量',
    model_used VARCHAR(50) COMMENT '使用的模型',
    response_time INT COMMENT '响应时间(毫秒)',
    knowledge_used JSON COMMENT '使用的知识信息',
    function_calls JSON COMMENT '函数调用信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    FOREIGN KEY (session_id) REFERENCES user_sessions(id) ON DELETE CASCADE,
    INDEX idx_session_created (session_id, created_at),
    INDEX idx_message_role (message_role),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB COMMENT='对话消息记录表';

-- =====================================================
-- 8. 用户反馈管理
-- =====================================================
CREATE TABLE user_feedback (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '反馈ID',
    message_id BIGINT NOT NULL COMMENT '关联消息ID',
    session_id BIGINT NOT NULL COMMENT '会话ID',
    feedback_type ENUM('like', 'dislike', 'report') NOT NULL COMMENT '反馈类型',
    feedback_score TINYINT COMMENT '反馈评分(1-5)',
    feedback_content TEXT COMMENT '反馈内容',
    feedback_reason VARCHAR(200) COMMENT '反馈原因',
    user_id VARCHAR(100) COMMENT '用户ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    FOREIGN KEY (message_id) REFERENCES chat_messages(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES user_sessions(id) ON DELETE CASCADE,
    INDEX idx_message_feedback (message_id, feedback_type),
    INDEX idx_feedback_type (feedback_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB COMMENT='用户反馈管理表';

-- =====================================================
-- 9. Agent配置管理
-- =====================================================
CREATE TABLE agent_configurations (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '配置ID',
    instance_id BIGINT NOT NULL COMMENT '所属实例ID',
    version_id BIGINT COMMENT '关联版本ID',
    config_key VARCHAR(100) NOT NULL COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    config_type ENUM('string', 'number', 'boolean', 'json', 'array') DEFAULT 'string' COMMENT '配置类型',
    config_category VARCHAR(50) COMMENT '配置分类',
    is_encrypted BOOLEAN DEFAULT FALSE COMMENT '是否加密',
    description TEXT COMMENT '配置描述',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    FOREIGN KEY (instance_id) REFERENCES agent_instances(id) ON DELETE CASCADE,
    FOREIGN KEY (version_id) REFERENCES agent_versions(id) ON DELETE SET NULL,
    UNIQUE KEY uk_config_key_version (instance_id, config_key, version_id),
    INDEX idx_config_category (config_category)
) ENGINE=InnoDB COMMENT='Agent配置管理表';

-- =====================================================
-- 10. Function工具管理
-- =====================================================
CREATE TABLE function_tools (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '工具ID',
    instance_id BIGINT NOT NULL COMMENT '所属实例ID',
    tool_name VARCHAR(100) NOT NULL COMMENT '工具名称',
    tool_code VARCHAR(50) NOT NULL COMMENT '工具代码',
    tool_description TEXT COMMENT '工具描述',
    tool_schema JSON COMMENT '工具Schema定义',
    tool_config JSON COMMENT '工具配置',
    tool_type ENUM('builtin', 'custom', 'api') DEFAULT 'custom' COMMENT '工具类型',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    version_id BIGINT COMMENT '关联版本ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    FOREIGN KEY (instance_id) REFERENCES agent_instances(id) ON DELETE CASCADE,
    FOREIGN KEY (version_id) REFERENCES agent_versions(id) ON DELETE SET NULL,
    UNIQUE KEY uk_tool_code_instance (instance_id, tool_code),
    INDEX idx_tool_type (tool_type)
) ENGINE=InnoDB COMMENT='Function工具管理表';

-- =====================================================
-- 11. 系统日志表
-- =====================================================
CREATE TABLE system_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID',
    instance_id BIGINT COMMENT 'Agent实例ID',
    session_id BIGINT COMMENT '会话ID',
    log_level ENUM('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL') NOT NULL COMMENT '日志级别',
    log_category VARCHAR(50) COMMENT '日志分类',
    log_message TEXT NOT NULL COMMENT '日志消息',
    log_data JSON COMMENT '日志数据',
    user_id VARCHAR(100) COMMENT '用户ID',
    request_id VARCHAR(100) COMMENT '请求ID',
    ip_address VARCHAR(45) COMMENT 'IP地址',
    user_agent TEXT COMMENT '用户代理',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    FOREIGN KEY (instance_id) REFERENCES agent_instances(id) ON DELETE SET NULL,
    FOREIGN KEY (session_id) REFERENCES user_sessions(id) ON DELETE SET NULL,
    INDEX idx_log_level (log_level),
    INDEX idx_log_category (log_category),
    INDEX idx_created_at (created_at),
    INDEX idx_request_id (request_id)
) ENGINE=InnoDB COMMENT='系统日志表';

-- =====================================================
-- 12. 性能监控表
-- =====================================================
CREATE TABLE performance_metrics (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '指标ID',
    instance_id BIGINT COMMENT 'Agent实例ID',
    metric_name VARCHAR(100) NOT NULL COMMENT '指标名称',
    metric_value DECIMAL(15,4) NOT NULL COMMENT '指标值',
    metric_unit VARCHAR(20) COMMENT '指标单位',
    metric_tags JSON COMMENT '指标标签',
    measurement_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '测量时间',

    FOREIGN KEY (instance_id) REFERENCES agent_instances(id) ON DELETE SET NULL,
    INDEX idx_metric_name_time (metric_name, measurement_time),
    INDEX idx_measurement_time (measurement_time)
) ENGINE=InnoDB COMMENT='性能监控指标表';

-- =====================================================
-- 初始化数据
-- =====================================================

-- 创建默认的Agent实例
INSERT INTO agent_instances (instance_name, instance_code, description, created_by) VALUES
('公积金政务服务助手', 'fund_assistant', '厦门市公积金政务服务智能助手系统', 'admin');

-- 创建默认的系统消息模板
INSERT INTO message_templates (instance_id, template_name, template_key, language, template_content, template_type, created_by) VALUES
(1, '默认系统消息', 'DEFAULT_SYSTEM_MESSAGE', 'zh', '你是厦门市公积金政务服务助手小金灵。你必须严格遵守以下规则：

**核心原则：**
- 使用知识库内容，简要回答用户的问题
- 如果有多个问题逐一回答
- 严禁添加知识库之外的任何信息、推测或细节
- 不得编造具体的操作步骤、界面描述等未知内容
- 知识库中的关键信息你要十分注意，非常重要

**禁止行为：**
- 禁止添加材料中没有的操作步骤
- 禁止推测具体的界面交互流程
- 禁止补充"常识性"但未在材料中的细节
- 禁止混合不同文档的信息片段
- 禁止材料里未提及的单位和电话不要出现
- 禁止回复材料中明确不能对外说明的内容
- 禁止自行编造、推测', 'system', 'admin'),

(1, '规则系统消息', 'RULE_SYSTEM_MESSAGE', 'zh', '审核上下文，明确公积金类型、资格、待遇身份区别，针对用户问题，
请检查该回答是否符合检索知识原意，一句话补充[注意事项]
**核心原则：**
- 判断话题无关，可回答 "我是您的人工智能助手，生成的内容可能不准确，请仔细甄别。"
- 只能使用下面提供的知识库内容回答问题
- 严禁添加知识库之外的任何信息、推测或细节
- 不得编造具体的操作步骤、界面描述等未知内容
**禁止行为：**
- 禁止添加材料中没有的操作步骤
- 禁止推测具体的界面交互流程
- 禁止补充"常识性"但未在材料中的细节
- 禁止混合不同文档的信息片段
- 禁止材料里未提及的单位和电话不要出现', 'rule', 'admin'),

(1, '规则模板', 'RULE_SYSTEM_TEMPLATE', 'zh', '检索知识:\n {knowledge}
问题: {question}
解答: {answer}
 **[注意事项]**:', 'prompt', 'admin');

-- 创建默认配置
INSERT INTO agent_configurations (instance_id, config_key, config_value, config_type, config_category, description, created_by) VALUES
(1, 'llm_model', 'qwen-max', 'string', 'llm', '使用的LLM模型', 'admin'),
(1, 'max_tokens', '2000', 'number', 'llm', '最大生成Token数', 'admin'),
(1, 'temperature', '0.7', 'number', 'llm', '生成温度参数', 'admin'),
(1, 'rag_enabled', 'true', 'boolean', 'rag', '是否启用RAG功能', 'admin'),
(1, 'doc_top_n', '5', 'number', 'rag', '文档检索Top数量', 'admin'),
(1, 'graph_top_n', '3', 'number', 'rag', '图谱检索Top数量', 'admin'),
(1, 'enable_graph_search', 'true', 'boolean', 'rag', '是否启用图谱搜索', 'admin'),
(1, 'enable_query_rewrite', 'false', 'boolean', 'rag', '是否启用查询重写', 'admin'),
(1, 'stream_response', 'true', 'boolean', 'response', '是否流式响应', 'admin'),
(1, 'timeout_seconds', '30', 'number', 'system', '请求超时时间', 'admin');