-- =============================================
-- 用户服务管理系统 - 数据库操作SQL
-- 创建时间: 2024
-- 描述: 为每个用户提供独立的Geoserver和Martin服务管理功能
-- =============================================

-- 1. 创建用户服务配置表
-- =============================================
CREATE TABLE IF NOT EXISTS user_service_configs (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    service_name VARCHAR(100) NOT NULL,           -- 服务名称
    service_type VARCHAR(20) NOT NULL CHECK (service_type IN ('geoserver', 'martin')),
    service_status VARCHAR(20) DEFAULT 'stopped' CHECK (service_status IN ('running', 'stopped', 'error', 'starting', 'stopping')),
    config_data JSONB NOT NULL,                   -- 服务配置参数
    port_number INTEGER,                          -- 分配的端口号
    resource_quota JSONB,                         -- 资源配额信息
    description TEXT,                             -- 服务描述
    is_default BOOLEAN DEFAULT FALSE,             -- 是否为默认服务
    auto_start BOOLEAN DEFAULT FALSE,             -- 是否自动启动
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_started_at TIMESTAMP,                    -- 最后启动时间
    last_stopped_at TIMESTAMP,                    -- 最后停止时间
    UNIQUE(user_id, service_name, service_type)   -- 用户内服务名唯一
);

-- 添加注释
COMMENT ON TABLE user_service_configs IS '用户服务配置表 - 存储每个用户的Geoserver和Martin服务配置';
COMMENT ON COLUMN user_service_configs.service_type IS '服务类型: geoserver 或 martin';
COMMENT ON COLUMN user_service_configs.service_status IS '服务状态: running, stopped, error, starting, stopping';
COMMENT ON COLUMN user_service_configs.config_data IS '服务配置参数(JSON格式)';
COMMENT ON COLUMN user_service_configs.port_number IS '分配给该服务的端口号';
COMMENT ON COLUMN user_service_configs.resource_quota IS '资源配额信息(JSON格式)';
COMMENT ON COLUMN user_service_configs.is_default IS '是否为用户的默认服务实例';
COMMENT ON COLUMN user_service_configs.auto_start IS '系统启动时是否自动启动该服务';

-- 2. 创建服务运行日志表
-- =============================================
CREATE TABLE IF NOT EXISTS service_logs (
    id BIGINT PRIMARY KEY,
    service_config_id BIGINT NOT NULL REFERENCES user_service_configs(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    operation_type VARCHAR(50) NOT NULL,          -- 操作类型
    operation_status VARCHAR(20) NOT NULL CHECK (operation_status IN ('success', 'failed', 'pending')),
    log_message TEXT,                             -- 日志详细信息
    error_details JSONB,                          -- 错误详情
    execution_time_ms INTEGER,                    -- 操作执行时间(毫秒)
    ip_address VARCHAR(45),                       -- 操作者IP地址
    user_agent TEXT,                              -- 用户代理信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 添加注释
COMMENT ON TABLE service_logs IS '服务运行日志表 - 记录所有服务操作和状态变化';
COMMENT ON COLUMN service_logs.operation_type IS '操作类型: start, stop, restart, config_update, create, delete等';
COMMENT ON COLUMN service_logs.operation_status IS '操作状态: success, failed, pending';
COMMENT ON COLUMN service_logs.error_details IS '错误详情(JSON格式)';
COMMENT ON COLUMN service_logs.execution_time_ms IS '操作执行时间(毫秒)';

-- 3. 创建系统资源配额表
-- =============================================
CREATE TABLE IF NOT EXISTS system_resource_quotas (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    max_geoserver_services INTEGER DEFAULT 3 CHECK (max_geoserver_services >= 0),     -- 最大Geoserver服务数
    max_martin_services INTEGER DEFAULT 5 CHECK (max_martin_services >= 0),           -- 最大Martin服务数
    max_memory_mb INTEGER DEFAULT 2048 CHECK (max_memory_mb > 0),                     -- 最大内存(MB)
    max_storage_mb INTEGER DEFAULT 10240 CHECK (max_storage_mb > 0),                  -- 最大存储(MB)
    concurrent_requests INTEGER DEFAULT 100 CHECK (concurrent_requests > 0),          -- 并发请求数
    quota_type VARCHAR(20) DEFAULT 'standard' CHECK (quota_type IN ('basic', 'standard', 'premium')),
    effective_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expiry_date TIMESTAMP,                        -- 配额过期时间
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, is_active, effective_date)    -- 确保用户同时只有一个有效配额
);

-- 添加注释
COMMENT ON TABLE system_resource_quotas IS '系统资源配额表 - 管理用户的资源使用限制';
COMMENT ON COLUMN system_resource_quotas.quota_type IS '配额类型: basic, standard, premium';
COMMENT ON COLUMN system_resource_quotas.max_memory_mb IS '用户所有服务的最大内存使用量(MB)';
COMMENT ON COLUMN system_resource_quotas.max_storage_mb IS '用户的最大存储空间(MB)';
COMMENT ON COLUMN system_resource_quotas.concurrent_requests IS '用户服务的最大并发请求数';

-- 4. 创建服务端口分配表
-- =============================================
CREATE TABLE IF NOT EXISTS service_port_allocations (
    id BIGINT PRIMARY KEY,
    port_number INTEGER NOT NULL UNIQUE CHECK (port_number BETWEEN 1024 AND 65535),
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    service_config_id BIGINT REFERENCES user_service_configs(id) ON DELETE SET NULL,
    allocation_status VARCHAR(20) DEFAULT 'allocated' CHECK (allocation_status IN ('allocated', 'released', 'reserved')),
    allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    released_at TIMESTAMP,
    notes TEXT
);

-- 添加注释
COMMENT ON TABLE service_port_allocations IS '服务端口分配表 - 管理端口的分配和释放';
COMMENT ON COLUMN service_port_allocations.allocation_status IS '端口状态: allocated(已分配), released(已释放), reserved(预留)';

-- 5. 创建索引
-- =============================================

-- 用户服务配置表索引
CREATE INDEX IF NOT EXISTS idx_user_service_configs_user_id ON user_service_configs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_service_configs_type_status ON user_service_configs(service_type, service_status);
CREATE INDEX IF NOT EXISTS idx_user_service_configs_port ON user_service_configs(port_number);
CREATE INDEX IF NOT EXISTS idx_user_service_configs_created_at ON user_service_configs(created_at);
CREATE INDEX IF NOT EXISTS idx_user_service_configs_default ON user_service_configs(user_id, is_default) WHERE is_default = TRUE;

-- 服务日志表索引
CREATE INDEX IF NOT EXISTS idx_service_logs_service_config_id ON service_logs(service_config_id);
CREATE INDEX IF NOT EXISTS idx_service_logs_user_id ON service_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_service_logs_created_at ON service_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_service_logs_operation_type ON service_logs(operation_type);
CREATE INDEX IF NOT EXISTS idx_service_logs_status ON service_logs(operation_status);
CREATE INDEX IF NOT EXISTS idx_service_logs_recent ON service_logs(user_id, created_at DESC);

-- 资源配额表索引
CREATE INDEX IF NOT EXISTS idx_system_resource_quotas_user_id ON system_resource_quotas(user_id);
CREATE INDEX IF NOT EXISTS idx_system_resource_quotas_active ON system_resource_quotas(is_active);
CREATE INDEX IF NOT EXISTS idx_system_resource_quotas_effective ON system_resource_quotas(effective_date, expiry_date);

-- 端口分配表索引
CREATE INDEX IF NOT EXISTS idx_service_port_allocations_status ON service_port_allocations(allocation_status);
CREATE INDEX IF NOT EXISTS idx_service_port_allocations_user_id ON service_port_allocations(user_id);

-- 6. 创建触发器函数
-- =============================================

-- 更新时间戳触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表创建更新时间戳触发器
CREATE TRIGGER update_user_service_configs_updated_at 
    BEFORE UPDATE ON user_service_configs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_resource_quotas_updated_at 
    BEFORE UPDATE ON system_resource_quotas 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 服务状态变更记录触发器函数
CREATE OR REPLACE FUNCTION log_service_status_change()
RETURNS TRIGGER AS $$
BEGIN
    -- 当服务状态发生变化时，记录到日志表
    IF OLD.service_status IS DISTINCT FROM NEW.service_status THEN
        INSERT INTO service_logs (
            id,
            service_config_id,
            user_id,
            operation_type,
            operation_status,
            log_message,
            created_at
        ) VALUES (
            (SELECT nextval('pg_catalog.pg_sequences') WHERE schemaname = 'public' LIMIT 1),
            NEW.id,
            NEW.user_id,
            'status_change',
            'success',
            format('服务状态从 %s 变更为 %s', COALESCE(OLD.service_status, 'null'), NEW.service_status),
            CURRENT_TIMESTAMP
        );
        
        -- 更新最后启动/停止时间
        IF NEW.service_status = 'running' THEN
            NEW.last_started_at = CURRENT_TIMESTAMP;
        ELSIF NEW.service_status = 'stopped' THEN
            NEW.last_stopped_at = CURRENT_TIMESTAMP;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 创建服务状态变更触发器
CREATE TRIGGER trigger_log_service_status_change
    BEFORE UPDATE ON user_service_configs
    FOR EACH ROW EXECUTE FUNCTION log_service_status_change();

-- 7. 插入默认数据
-- =============================================

-- 为现有用户创建默认资源配额
INSERT INTO system_resource_quotas (
    id,
    user_id, 
    max_geoserver_services, 
    max_martin_services, 
    max_memory_mb, 
    max_storage_mb, 
    concurrent_requests, 
    quota_type
)
SELECT 
    (SELECT COALESCE(MAX(id), 0) + ROW_NUMBER() OVER() FROM system_resource_quotas),
    u.id,
    CASE 
        WHEN u.username = 'admin' THEN 10  -- 管理员更多资源
        ELSE 3 
    END,
    CASE 
        WHEN u.username = 'admin' THEN 20
        ELSE 5 
    END,
    CASE 
        WHEN u.username = 'admin' THEN 8192
        ELSE 2048 
    END,
    CASE 
        WHEN u.username = 'admin' THEN 51200
        ELSE 10240 
    END,
    CASE 
        WHEN u.username = 'admin' THEN 500
        ELSE 100 
    END,
    CASE 
        WHEN u.username = 'admin' THEN 'premium'
        ELSE 'standard' 
    END
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM system_resource_quotas srq 
    WHERE srq.user_id = u.id AND srq.is_active = TRUE
);

-- 预留系统端口范围
INSERT INTO service_port_allocations (
    id,
    port_number,
    allocation_status,
    notes
)
SELECT 
    port_number,
    port_number,
    'reserved',
    '系统预留端口'
FROM generate_series(1, 1023) AS port_number
WHERE NOT EXISTS (
    SELECT 1 FROM service_port_allocations spa 
    WHERE spa.port_number = generate_series.port_number
);

-- 预留常用服务端口
INSERT INTO service_port_allocations (
    id,
    port_number,
    allocation_status,
    notes
)
VALUES 
    (8080, 8080, 'reserved', 'Geoserver默认端口'),
    (3000, 3000, 'reserved', 'Martin默认端口'),
    (5432, 5432, 'reserved', 'PostgreSQL端口'),
    (80, 80, 'reserved', 'HTTP端口'),
    (443, 443, 'reserved', 'HTTPS端口'),
    (22, 22, 'reserved', 'SSH端口')
ON CONFLICT (port_number) DO NOTHING;

-- 8. 创建用于管理的视图
-- =============================================

-- 用户服务统计视图
CREATE OR REPLACE VIEW user_service_stats AS
SELECT 
    u.id AS user_id,
    u.username,
    COUNT(CASE WHEN usc.service_type = 'geoserver' THEN 1 END) AS geoserver_count,
    COUNT(CASE WHEN usc.service_type = 'martin' THEN 1 END) AS martin_count,
    COUNT(CASE WHEN usc.service_status = 'running' THEN 1 END) AS running_services,
    COUNT(usc.id) AS total_services,
    srq.max_geoserver_services,
    srq.max_martin_services,
    srq.quota_type
FROM users u
LEFT JOIN user_service_configs usc ON u.id = usc.user_id
LEFT JOIN system_resource_quotas srq ON u.id = srq.user_id AND srq.is_active = TRUE
GROUP BY u.id, u.username, srq.max_geoserver_services, srq.max_martin_services, srq.quota_type;

-- 服务状态概览视图
CREATE OR REPLACE VIEW service_status_overview AS
SELECT 
    service_type,
    service_status,
    COUNT(*) AS count,
    COUNT(DISTINCT user_id) AS user_count
FROM user_service_configs
GROUP BY service_type, service_status
ORDER BY service_type, service_status;

-- 端口使用情况视图
CREATE OR REPLACE VIEW port_usage_overview AS
SELECT 
    allocation_status,
    COUNT(*) AS port_count,
    MIN(port_number) AS min_port,
    MAX(port_number) AS max_port
FROM service_port_allocations
GROUP BY allocation_status
ORDER BY allocation_status;

-- 9. 添加约束检查函数
-- =============================================

-- 检查用户服务数量限制的函数
CREATE OR REPLACE FUNCTION check_user_service_limit()
RETURNS TRIGGER AS $$
DECLARE
    user_quota RECORD;
    current_count INTEGER;
BEGIN
    -- 获取用户配额
    SELECT * INTO user_quota 
    FROM system_resource_quotas 
    WHERE user_id = NEW.user_id AND is_active = TRUE;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION '用户未配置资源配额';
    END IF;
    
    -- 检查对应服务类型的数量限制
    SELECT COUNT(*) INTO current_count
    FROM user_service_configs 
    WHERE user_id = NEW.user_id AND service_type = NEW.service_type;
    
    IF NEW.service_type = 'geoserver' AND current_count >= user_quota.max_geoserver_services THEN
        RAISE EXCEPTION '已达到Geoserver服务数量上限: %', user_quota.max_geoserver_services;
    END IF;
    
    IF NEW.service_type = 'martin' AND current_count >= user_quota.max_martin_services THEN
        RAISE EXCEPTION '已达到Martin服务数量上限: %', user_quota.max_martin_services;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 创建约束检查触发器
CREATE TRIGGER trigger_check_user_service_limit
    BEFORE INSERT ON user_service_configs
    FOR EACH ROW EXECUTE FUNCTION check_user_service_limit();

-- 10. 创建管理函数
-- =============================================

-- 分配可用端口的函数
CREATE OR REPLACE FUNCTION allocate_available_port(p_user_id BIGINT, p_service_config_id BIGINT)
RETURNS INTEGER AS $$
DECLARE
    available_port INTEGER;
BEGIN
    -- 查找最小的可用端口（从8081开始，避免常用端口）
    SELECT port_number INTO available_port
    FROM generate_series(8081, 65535) AS port_number
    WHERE port_number NOT IN (
        SELECT port_number 
        FROM service_port_allocations 
        WHERE allocation_status IN ('allocated', 'reserved')
        AND port_number IS NOT NULL
    )
    ORDER BY port_number
    LIMIT 1;
    
    IF available_port IS NULL THEN
        RAISE EXCEPTION '没有可用的端口';
    END IF;
    
    -- 分配端口
    INSERT INTO service_port_allocations (
        id, port_number, user_id, service_config_id, allocation_status
    ) VALUES (
        available_port, available_port, p_user_id, p_service_config_id, 'allocated'
    );
    
    RETURN available_port;
END;
$$ language 'plpgsql';

-- 释放端口的函数
CREATE OR REPLACE FUNCTION release_port(p_port_number INTEGER)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE service_port_allocations 
    SET allocation_status = 'released',
        released_at = CURRENT_TIMESTAMP,
        user_id = NULL,
        service_config_id = NULL
    WHERE port_number = p_port_number 
    AND allocation_status = 'allocated';
    
    RETURN FOUND;
END;
$$ language 'plpgsql';

-- =============================================
-- SQL执行完成提示
-- =============================================
DO $$
BEGIN
    RAISE NOTICE '==============================================';
    RAISE NOTICE '用户服务管理系统数据库结构创建完成！';
    RAISE NOTICE '- 已创建 4 个主要数据表';
    RAISE NOTICE '- 已创建相关索引和约束';
    RAISE NOTICE '- 已创建触发器和管理函数';
    RAISE NOTICE '- 已插入默认配额数据';
    RAISE NOTICE '- 已创建管理视图';
    RAISE NOTICE '==============================================';
END $$; 