-- 修复现有场景图层的不透明度默认值
-- 将opacity为NULL、0或无效值的记录设置为1.0（100%不透明度）

-- 更新opacity为NULL的记录
UPDATE scene_layers 
SET opacity = 1.0 
WHERE opacity IS NULL;

-- 更新opacity为0的记录
UPDATE scene_layers 
SET opacity = 1.0 
WHERE opacity = 0;

-- 更新opacity小于0的记录
UPDATE scene_layers 
SET opacity = 1.0 
WHERE opacity < 0;

-- 更新opacity大于1的记录
UPDATE scene_layers 
SET opacity = 1.0 
WHERE opacity > 1;

-- 验证更新结果
SELECT 
    COUNT(*) as total_layers,
    COUNT(CASE WHEN opacity = 1.0 THEN 1 END) as default_opacity_layers,
    MIN(opacity) as min_opacity,
    MAX(opacity) as max_opacity,
    AVG(opacity) as avg_opacity
FROM scene_layers;

-- 显示更新的统计信息
SELECT 
    '修复完成：所有图层不透明度已设置为有效值范围（0.0-1.0），默认为1.0（100%不透明）' as status; 