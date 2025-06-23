-- 快速修复用户表ID字段问题
-- 执行前请备份数据库

-- 方案1：修改现有表结构（推荐）
BEGIN;

-- 1. 添加email字段（如果不存在）
ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS email character varying(100);

-- 2. 将ID字段类型从INTEGER改为BIGINT
ALTER TABLE public.users 
ALTER COLUMN id TYPE BIGINT;

-- 3. 移除默认的序列生成器（因为我们要使用雪花算法）
ALTER TABLE public.users 
ALTER COLUMN id DROP DEFAULT;

-- 4. 添加email唯一约束（先处理可能的重复数据）
-- 如果存在重复邮箱，为重复的邮箱添加后缀
UPDATE public.users 
SET email = email || '_' || id::text 
WHERE email IN (
    SELECT email 
    FROM public.users 
    WHERE email IS NOT NULL 
    GROUP BY email 
    HAVING COUNT(*) > 1
) AND email IS NOT NULL;

-- 添加唯一约束
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'users_email_key') THEN
        ALTER TABLE public.users ADD CONSTRAINT users_email_key UNIQUE (email);
    END IF;
END $$;

COMMIT;

-- 查看修复结果
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'users' AND table_schema = 'public'
ORDER BY ordinal_position;

-- 查看约束信息
SELECT 
    tc.constraint_name, 
    tc.constraint_type, 
    cc.column_name
FROM information_schema.table_constraints tc
JOIN information_schema.constraint_column_usage cc 
    ON tc.constraint_name = cc.constraint_name
WHERE tc.table_name = 'users' AND tc.table_schema = 'public';

-- 如果需要为现有用户添加默认邮箱
-- UPDATE public.users SET email = username || '@temp.local' WHERE email IS NULL;

SELECT 'Users table structure fixed successfully!' as status; 