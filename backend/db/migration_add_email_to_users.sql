-- 为用户表添加email字段的迁移脚本
-- 执行前请备份数据库

-- 1. 添加email字段
ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS email character varying(100) COLLATE pg_catalog."default";

-- 2. 将ID字段类型从INTEGER改为BIGINT以支持雪花算法
-- 注意：如果表中已有数据，此操作可能需要较长时间
ALTER TABLE public.users 
ALTER COLUMN id TYPE BIGINT;

-- 3. 添加email字段的唯一约束
ALTER TABLE public.users 
ADD CONSTRAINT users_email_key UNIQUE (email);

-- 4. 为现有用户添加默认email（可选）
-- UPDATE public.users SET email = username || '@example.com' WHERE email IS NULL;

-- 查看结果
SELECT id, username, email, created_at FROM public.users; 