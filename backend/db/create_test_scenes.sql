-- 创建测试场景数据
-- 用于测试场景列表接口

-- 首先检查是否有多个用户，如果没有则创建
INSERT INTO users (id, username, password, email, created_at)
SELECT 
    nextval('users_id_seq'),
    'testuser1',
    'hashed_password_123',
    'testuser1@example.com',
    NOW()
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'testuser1');

INSERT INTO users (id, username, password, email, created_at)
SELECT 
    nextval('users_id_seq'),
    'testuser2',
    'hashed_password_456',
    'testuser2@example.com',
    NOW()
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'testuser2');

-- 获取用户ID
DO $$
DECLARE
    user1_id INTEGER;
    user2_id INTEGER;
    admin_id INTEGER;
BEGIN
    -- 获取用户ID
    SELECT id INTO user1_id FROM users WHERE username = 'testuser1';
    SELECT id INTO user2_id FROM users WHERE username = 'testuser2';
    SELECT id INTO admin_id FROM users WHERE username = 'admin';
    
    -- 如果用户不存在，跳过
    IF user1_id IS NULL OR user2_id IS NULL THEN
        RAISE NOTICE '用户不存在，跳过创建场景';
        RETURN;
    END IF;
    
    -- 创建testuser1的公开场景
    INSERT INTO scenes (id, name, description, is_public, user_id, created_at, updated_at)
    VALUES (
        nextval('scenes_id_seq'),
        'testuser1的公开场景',
        '这是testuser1创建的公开场景，所有人都可以看到',
        true,
        user1_id,
        NOW(),
        NOW()
    ) ON CONFLICT (id) DO NOTHING;
    
    -- 创建testuser1的私有场景
    INSERT INTO scenes (id, name, description, is_public, user_id, created_at, updated_at)
    VALUES (
        nextval('scenes_id_seq'),
        'testuser1的私有场景',
        '这是testuser1创建的私有场景，只有创建者可以看到',
        false,
        user1_id,
        NOW(),
        NOW()
    ) ON CONFLICT (id) DO NOTHING;
    
    -- 创建testuser2的公开场景
    INSERT INTO scenes (id, name, description, is_public, user_id, created_at, updated_at)
    VALUES (
        nextval('scenes_id_seq'),
        'testuser2的公开场景',
        '这是testuser2创建的公开场景，所有人都可以看到',
        true,
        user2_id,
        NOW(),
        NOW()
    ) ON CONFLICT (id) DO NOTHING;
    
    -- 创建testuser2的私有场景
    INSERT INTO scenes (id, name, description, is_public, user_id, created_at, updated_at)
    VALUES (
        nextval('scenes_id_seq'),
        'testuser2的私有场景',
        '这是testuser2创建的私有场景，只有创建者可以看到',
        false,
        user2_id,
        NOW(),
        NOW()
    ) ON CONFLICT (id) DO NOTHING;
    
    -- 如果admin用户存在，创建admin的公开场景
    IF admin_id IS NOT NULL THEN
        INSERT INTO scenes (id, name, description, is_public, user_id, created_at, updated_at)
        VALUES (
            nextval('scenes_id_seq'),
            'admin的公开场景',
            '这是管理员创建的公开场景',
            true,
            admin_id,
            NOW(),
            NOW()
        ) ON CONFLICT (id) DO NOTHING;
    END IF;
    
    RAISE NOTICE '测试场景创建完成';
END $$; 