-- 用户反馈系统数据库表结构
-- 可独立使用，与现有系统解耦
-- PostgreSQL版本

-- 反馈表
CREATE TABLE IF NOT EXISTS feedback_items (
    id BIGINT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL, -- 'feature' 或 'bug'
    module VARCHAR(50) NOT NULL,   -- 'frontend' 或 'backend'
    type VARCHAR(50) NOT NULL,     -- 'ui' 或 'code'
    priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
    status VARCHAR(20) DEFAULT 'open',     -- 'open', 'in_progress', 'resolved', 'closed'
    
    -- 用户信息（可以根据实际系统调整）
    user_id VARCHAR(100),          -- 支持字符串ID，兼容雪花算法
    username VARCHAR(100),
    user_email VARCHAR(200),
    
    -- 统计信息
    support_count INTEGER DEFAULT 0,
    oppose_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    
    -- 附件信息
    has_attachments BOOLEAN DEFAULT FALSE,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 反馈附件表
CREATE TABLE IF NOT EXISTS feedback_attachments (
    id BIGINT PRIMARY KEY,
    feedback_id BIGINT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50),          -- 'image', 'document', 'archive'
    file_size BIGINT,
    file_path VARCHAR(500),
    mime_type VARCHAR(100),
    
    -- 图片特殊信息
    is_screenshot BOOLEAN DEFAULT FALSE,
    image_width INTEGER,
    image_height INTEGER,
    
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
);

-- 用户投票表
CREATE TABLE IF NOT EXISTS feedback_votes (
    id BIGINT PRIMARY KEY,
    feedback_id BIGINT NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    username VARCHAR(100),
    vote_type VARCHAR(10) NOT NULL,  -- 'support' 或 'oppose'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
    UNIQUE (feedback_id, user_id)
);

-- 评论表
CREATE TABLE IF NOT EXISTS feedback_comments (
    id BIGINT PRIMARY KEY,
    feedback_id BIGINT NOT NULL,
    parent_id BIGINT,               -- 支持回复评论
    
    content TEXT NOT NULL,
    
    -- 用户信息
    user_id VARCHAR(100) NOT NULL,
    username VARCHAR(100),
    user_email VARCHAR(200),
    
    -- 状态
    is_deleted BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES feedback_comments(id) ON DELETE CASCADE
);

-- 更新触发器：自动更新统计信息

-- 触发器函数：更新投票统计
CREATE OR REPLACE FUNCTION update_vote_counts() RETURNS TRIGGER AS $$
BEGIN
    UPDATE feedback_items 
    SET 
        support_count = (SELECT COUNT(*) FROM feedback_votes WHERE feedback_id = COALESCE(NEW.feedback_id, OLD.feedback_id) AND vote_type = 'support'),
        oppose_count = (SELECT COUNT(*) FROM feedback_votes WHERE feedback_id = COALESCE(NEW.feedback_id, OLD.feedback_id) AND vote_type = 'oppose'),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = COALESCE(NEW.feedback_id, OLD.feedback_id);
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- 投票统计触发器
CREATE TRIGGER trigger_update_vote_counts_insert
    AFTER INSERT ON feedback_votes
    FOR EACH ROW EXECUTE FUNCTION update_vote_counts();

CREATE TRIGGER trigger_update_vote_counts_update
    AFTER UPDATE ON feedback_votes
    FOR EACH ROW EXECUTE FUNCTION update_vote_counts();

CREATE TRIGGER trigger_update_vote_counts_delete
    AFTER DELETE ON feedback_votes
    FOR EACH ROW EXECUTE FUNCTION update_vote_counts();

-- 触发器函数：更新评论统计
CREATE OR REPLACE FUNCTION update_comment_count() RETURNS TRIGGER AS $$
BEGIN
    UPDATE feedback_items 
    SET 
        comment_count = (SELECT COUNT(*) FROM feedback_comments WHERE feedback_id = COALESCE(NEW.feedback_id, OLD.feedback_id) AND is_deleted = FALSE),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = COALESCE(NEW.feedback_id, OLD.feedback_id);
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- 评论统计触发器
CREATE TRIGGER trigger_update_comment_count_insert
    AFTER INSERT ON feedback_comments
    FOR EACH ROW EXECUTE FUNCTION update_comment_count();

CREATE TRIGGER trigger_update_comment_count_update
    AFTER UPDATE ON feedback_comments
    FOR EACH ROW EXECUTE FUNCTION update_comment_count();

CREATE TRIGGER trigger_update_comment_count_delete
    AFTER DELETE ON feedback_comments
    FOR EACH ROW EXECUTE FUNCTION update_comment_count();

-- 触发器函数：更新附件标记
CREATE OR REPLACE FUNCTION update_attachments_flag() RETURNS TRIGGER AS $$
BEGIN
    UPDATE feedback_items 
    SET 
        has_attachments = (SELECT COUNT(*) > 0 FROM feedback_attachments WHERE feedback_id = COALESCE(NEW.feedback_id, OLD.feedback_id)),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = COALESCE(NEW.feedback_id, OLD.feedback_id);
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- 附件统计触发器
CREATE TRIGGER trigger_update_attachments_flag_insert
    AFTER INSERT ON feedback_attachments
    FOR EACH ROW EXECUTE FUNCTION update_attachments_flag();

CREATE TRIGGER trigger_update_attachments_flag_delete
    AFTER DELETE ON feedback_attachments
    FOR EACH ROW EXECUTE FUNCTION update_attachments_flag();

-- 创建索引（PostgreSQL语法）
CREATE INDEX IF NOT EXISTS idx_feedback_items_category ON feedback_items(category);
CREATE INDEX IF NOT EXISTS idx_feedback_items_module ON feedback_items(module);
CREATE INDEX IF NOT EXISTS idx_feedback_items_type ON feedback_items(type);
CREATE INDEX IF NOT EXISTS idx_feedback_items_status ON feedback_items(status);
CREATE INDEX IF NOT EXISTS idx_feedback_items_user_id ON feedback_items(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_items_created_at ON feedback_items(created_at);
CREATE INDEX IF NOT EXISTS idx_feedback_items_support_count ON feedback_items(support_count);
CREATE INDEX IF NOT EXISTS idx_feedback_items_oppose_count ON feedback_items(oppose_count);
CREATE INDEX IF NOT EXISTS idx_feedback_items_comment_count ON feedback_items(comment_count);

CREATE INDEX IF NOT EXISTS idx_feedback_attachments_feedback_id ON feedback_attachments(feedback_id);
CREATE INDEX IF NOT EXISTS idx_feedback_attachments_file_type ON feedback_attachments(file_type);

CREATE INDEX IF NOT EXISTS idx_feedback_votes_feedback_id ON feedback_votes(feedback_id);
CREATE INDEX IF NOT EXISTS idx_feedback_votes_user_id ON feedback_votes(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_votes_vote_type ON feedback_votes(vote_type);

CREATE INDEX IF NOT EXISTS idx_feedback_comments_feedback_id ON feedback_comments(feedback_id);
CREATE INDEX IF NOT EXISTS idx_feedback_comments_parent_id ON feedback_comments(parent_id);
CREATE INDEX IF NOT EXISTS idx_feedback_comments_user_id ON feedback_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_comments_created_at ON feedback_comments(created_at);

-- 插入一些示例数据（可选）
-- INSERT INTO feedback_items (id, title, description, category, module, type, user_id, username, user_email) VALUES
-- (1, '增加深色主题支持', '希望系统能支持深色主题，减少眼部疲劳', 'feature', 'frontend', 'ui', '1', 'user1', 'user1@example.com'),
-- (2, '修复文件上传失败bug', '大文件上传时经常失败，需要修复', 'bug', 'backend', 'code', '2', 'user2', 'user2@example.com'),
-- (3, '优化数据加载速度', '页面加载速度较慢，希望优化性能', 'feature', 'backend', 'code', '1', 'user1', 'user1@example.com'); 