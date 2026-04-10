-- Initialize database with admin user and default data

-- Insert default admin user (password: admin123)
INSERT INTO users (uuid, username, email, password, role, status, api_key, created_at, updated_at)
VALUES (
    UUID(),
    'admin',
    'admin@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYMyzJ/I3K', -- bcrypt hash of 'admin123'
    'admin',
    'active',
    CONCAT('ak-', LOWER(UUID())),
    NOW(),
    NOW()
) ON DUPLICATE KEY UPDATE updated_at = NOW();

-- Create quota for admin
INSERT INTO user_quotas (user_id, daily_limit, weekly_limit, monthly_limit, created_at, updated_at)
SELECT 
    id, 
    1000000, -- 1M daily
    5000000, -- 5M weekly
    20000000, -- 20M monthly
    NOW(),
    NOW()
FROM users 
WHERE username = 'admin'
ON DUPLICATE KEY UPDATE updated_at = NOW();

-- Insert default prompt patterns
INSERT INTO prompt_patterns (pattern, pattern_type, risk_level, description, is_enabled, created_at, updated_at)
VALUES
    ('password|密码', 'sensitive_info', 'medium', '密码相关查询', TRUE, NOW(), NOW()),
    ('secret|密钥|secret', 'sensitive_info', 'high', '密钥相关查询', TRUE, NOW(), NOW()),
    ('salary|工资|薪资', 'sensitive_info', 'high', '薪资相关查询', TRUE, NOW(), NOW()),
    ('ignore previous|忽略之前', 'injection', 'high', '提示词注入攻击', TRUE, NOW(), NOW()),
    ('developer mode|开发者模式', 'injection', 'high', '开发者模式注入', TRUE, NOW(), NOW()),
    ('DAN mode|DAN', 'injection', 'high', 'DAN模式注入', TRUE, NOW(), NOW()),
    ('system prompt|系统提示', 'injection', 'high', '系统提示提取', TRUE, NOW(), NOW())
ON DUPLICATE KEY UPDATE updated_at = NOW();
