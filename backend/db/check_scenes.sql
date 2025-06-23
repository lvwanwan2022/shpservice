-- 检查场景数据库状态
-- 用于调试场景列表接口问题

-- 1. 查看所有用户
SELECT 
    id, 
    username, 
    email,
    created_at
FROM users 
ORDER BY created_at;

-- 2. 查看所有场景
SELECT 
    s.id,
    s.name,
    s.description,
    s.is_public,
    s.user_id,
    u.username as creator,
    s.created_at,
    s.updated_at,
    (SELECT COUNT(*) FROM scene_layers sl WHERE sl.scene_id = s.id) as layer_count
FROM scenes s
LEFT JOIN users u ON s.user_id = u.id
ORDER BY s.created_at DESC;

-- 3. 查看场景的公开状态分布
SELECT 
    is_public,
    COUNT(*) as count
FROM scenes 
GROUP BY is_public;

-- 4. 查看每个用户的场景数量
SELECT 
    u.username,
    u.id as user_id,
    COUNT(s.id) as scene_count,
    COUNT(CASE WHEN s.is_public = true THEN 1 END) as public_scenes,
    COUNT(CASE WHEN s.is_public = false THEN 1 END) as private_scenes
FROM users u
LEFT JOIN scenes s ON u.id = s.user_id
GROUP BY u.id, u.username
ORDER BY scene_count DESC; 