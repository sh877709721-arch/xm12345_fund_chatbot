-- 创建用户管理相关的SQL脚本
-- 对应Python SQLAlchemy模型中的User和UserRoles类

-- 1. 创建角色枚举类型
CREATE TYPE chatbot.role_enum AS ENUM (
    'superadmin',
    'normal_user',
    'engineer'
);

DROP TABLE chatbot.user_roles;
DROP TABLE chatbot.users;

-- 2. 创建用户表 (对应 User 类)
CREATE TABLE chatbot.users (
    id bigserial,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. 创建用户角色关联表 (对应 UserRoles 类)
CREATE TABLE chatbot.user_roles (
    id BIGSERIAL PRIMARY KEY,
    user_id bigserial,
    role role_enum NOT NULL,
    status VARCHAR(255) DEFAULT 'A',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);



-- 4. 创建索引以提高查询性能
-- 用户表索引
CREATE INDEX idx_users_username ON chatbot.users(username);
CREATE INDEX idx_users_email ON chatbot.users(email);
CREATE INDEX idx_users_is_active ON chatbot.users(is_active);
CREATE INDEX idx_users_created_at ON chatbot.users(created_at);

-- 用户角色表索引
CREATE INDEX idx_user_roles_user_id ON chatbot.user_roles(user_id);
CREATE INDEX idx_user_roles_role ON chatbot.user_roles(role);

-- 5. 创建触发器函数，自动更新 updated_at 字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 6. 为users表创建updated_at触发器
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 7. 为user_roles表创建updated_at触发器
CREATE TRIGGER update_user_roles_updated_at
    BEFORE UPDATE ON user_roles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 8. 添加约束确保每个用户只能有一个相同角色
ALTER TABLE user_roles ADD CONSTRAINT unique_user_role
    UNIQUE (user_id, role);

-- 9. 插入一些示例数据 (可选)
INSERT INTO users (username, email, hashed_password, full_name) VALUES
('admin', 'admin@example.com', '$2b$12$placeholder_hash', '系统管理员'),
('engineer1', 'engineer1@example.com', '$2b$12$placeholder_hash', '工程师1'),
('user1', 'user1@example.com', '$2b$12$placeholder_hash', '普通用户1');

INSERT INTO user_roles (user_id, role)
SELECT id, 'superadmin' FROM users WHERE username = 'admin';

INSERT INTO user_roles (user_id, role)
SELECT id, 'engineer' FROM users WHERE username = 'engineer1';

INSERT INTO user_roles (user_id, role)
SELECT id, 'normal_user' FROM users WHERE username = 'user1';

-- 10. 创建一些有用的视图
-- 用户详细信息视图（包含角色）
CREATE VIEW user_details AS
SELECT
    u.id,
    u.username,
    u.email,
    u.full_name,
    u.is_active,
    u.created_at,
    u.updated_at,
    array_agg(ur.role) as roles
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
GROUP BY u.id, u.username, u.email, u.full_name, u.is_active, u.created_at, u.updated_at;

-- 11. 添加注释
COMMENT ON TABLE users IS '用户基本信息表，对应Python User模型类';
COMMENT ON TABLE user_roles IS '用户角色关联表，对应Python UserRoles模型类';
COMMENT ON COLUMN users.id IS '用户唯一标识符，使用UUID类型';
COMMENT ON COLUMN users.username IS '用户名，必须唯一';
COMMENT ON COLUMN users.email IS '邮箱地址，必须唯一';
COMMENT ON COLUMN users.hashed_password IS '密码哈希值，存储加密后的密码';
COMMENT ON COLUMN users.full_name IS '用户全名，可选字段';
COMMENT ON COLUMN users.is_active IS '用户是否激活，默认为true';
COMMENT ON COLUMN users.created_at IS '创建时间，默认为当前时间';
COMMENT ON COLUMN users.updated_at IS '最后更新时间，自动更新';
COMMENT ON COLUMN user_roles.id IS '自增主键';
COMMENT ON COLUMN user_roles.user_id IS '关联的用户ID，外键引用users.id';
COMMENT ON COLUMN user_roles.role IS '用户角色，使用枚举类型限制可选值';

-- 12. 创建一些有用的查询函数
-- 检查用户是否有特定角色的函数
CREATE OR REPLACE FUNCTION user_has_role(user_uuid UUID, target_role role_enum)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM user_roles
        WHERE user_id = user_uuid AND role = target_role
    );
END;
$$ LANGUAGE plpgsql;

-- 获取用户所有角色的函数
CREATE OR REPLACE FUNCTION get_user_roles(user_uuid UUID)
RETURNS role_enum[] AS $$
BEGIN
    RETURN ARRAY(
        SELECT role FROM user_roles
        WHERE user_id = user_uuid
    );
END;
$$ LANGUAGE plpgsql;