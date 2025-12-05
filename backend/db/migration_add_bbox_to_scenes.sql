-- 迁移脚本：为scenes表添加bbox字段
-- 执行时间：2024年

-- 添加bbox字段到scenes表
ALTER TABLE IF EXISTS public.scenes 
ADD COLUMN IF NOT EXISTS bbox JSONB;

-- 添加注释
COMMENT ON COLUMN public.scenes.bbox IS '场景范围边界框，格式为JSON: {"minx": number, "miny": number, "maxx": number, "maxy": number} 或数组格式 [minx, miny, maxx, maxy]';
