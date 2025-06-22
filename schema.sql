-- 删除已存在的表格（如果存在），方便重新初始化
DROP TABLE IF EXISTS links;

-- 创建一个新的表格来存储链接
CREATE TABLE links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    short_code TEXT UNIQUE NOT NULL,
    original_url TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
); 