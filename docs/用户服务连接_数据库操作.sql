-- =============================================
-- 用户服务连接管理系统 - 简化版数据库操作SQL
-- 描述: 用户添加自己的Geoserver和Martin服务连接信息
-- =============================================

-- 1. 创建用户服务连接配置表（简化版）
-- =============================================
CREATE TABLE IF NOT EXISTS user_service_connections (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    service_name VARCHAR(100) NOT NULL,           -- 服务名称
    service_type VARCHAR(20) NOT NULL CHECK (service_type IN ('geoserver', 'martin')),
    server_url VARCHAR(500) NOT NULL,             -- 服务地址
    connection_config JSONB NOT NULL,             -- 连接配置（用户名密码、API密钥等）
    description TEXT,                             -- 服务描述
    is_default BOOLEAN DEFAULT FALSE,             -- 是否为默认服务
    is_active BOOLEAN DEFAULT TRUE,               -- 是否启用
    last_tested_at TIMESTAMP,                     -- 最后测试时间
    test_status VARCHAR(20) DEFAULT 'unknown',    -- 测试状态：success, failed, unknown
    test_message TEXT,                            -- 测试结果信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, service_name, service_type)   -- 用户内服务名唯一
);

-- 添加注释
COMMENT ON TABLE user_service_connections IS '用户服务连接配置表 - 存储用户外部Geoserver和Martin服务连接信息';
COMMENT ON COLUMN user_service_connections.service_type IS '服务类型: geoserver 或 martin';
COMMENT ON COLUMN user_service_connections.server_url IS '外部服务的完整访问地址';
COMMENT ON COLUMN user_service_connections.connection_config IS '连接配置(JSON格式，包含认证信息等)';
COMMENT ON COLUMN user_service_connections.is_default IS '是否为该类型服务的默认连接';
COMMENT ON COLUMN user_service_connections.test_status IS '最后一次连接测试状态';

-- 2. 创建索引
-- =============================================
CREATE INDEX IF NOT EXISTS idx_user_service_connections_user_id ON user_service_connections(user_id);
CREATE INDEX IF NOT EXISTS idx_user_service_connections_type ON user_service_connections(service_type);
CREATE INDEX IF NOT EXISTS idx_user_service_connections_active ON user_service_connections(is_active);
CREATE INDEX IF NOT EXISTS idx_user_service_connections_default ON user_service_connections(user_id, service_type, is_default) WHERE is_default = TRUE;

-- 3. 创建触发器函数
-- =============================================

-- 更新时间戳触发器函数
CREATE OR REPLACE FUNCTION update_connection_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 创建更新时间戳触发器
CREATE TRIGGER update_user_service_connections_updated_at 
    BEFORE UPDATE ON user_service_connections 
    FOR EACH ROW EXECUTE FUNCTION update_connection_updated_at();

-- 确保每个用户每种服务类型只有一个默认连接的触发器
CREATE OR REPLACE FUNCTION ensure_single_default_connection()
RETURNS TRIGGER AS $$
BEGIN
    -- 如果新记录设置为默认，取消该用户该服务类型的其他默认设置
    IF NEW.is_default = TRUE THEN
        UPDATE user_service_connections 
        SET is_default = FALSE 
        WHERE user_id = NEW.user_id 
        AND service_type = NEW.service_type 
        AND id != NEW.id
        AND is_default = TRUE;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 创建默认连接唯一性触发器
CREATE TRIGGER ensure_single_default_connection_trigger
    BEFORE INSERT OR UPDATE ON user_service_connections
    FOR EACH ROW EXECUTE FUNCTION ensure_single_default_connection();

-- 4. 删除不需要的表（如果存在）
-- =============================================
DROP TABLE IF EXISTS service_logs CASCADE;
DROP TABLE IF EXISTS system_resource_quotas CASCADE;
DROP TABLE IF EXISTS service_port_allocations CASCADE;

-- 删除旧的user_service_configs表（如果存在）
DROP TABLE IF EXISTS user_service_configs CASCADE;

-- 删除相关函数
DROP FUNCTION IF EXISTS allocate_available_port(BIGINT, BIGINT);
DROP FUNCTION IF EXISTS release_port(INTEGER);
DROP FUNCTION IF EXISTS log_service_status_change();
DROP FUNCTION IF EXISTS check_user_service_limit();

-- =============================================
-- 完成提示
-- =============================================
DO $$
BEGIN
    RAISE NOTICE '==============================================';
    RAISE NOTICE '用户服务连接管理系统数据库结构创建完成！';
    RAISE NOTICE '- 已创建简化的用户服务连接配置表';
    RAISE NOTICE '- 已删除不必要的日志、配额、端口管理表';
    RAISE NOTICE '- 专注于分布式服务连接管理';
    RAISE NOTICE '==============================================';
END $$; 