DROP TABLE IF EXISTS sys_state;

CREATE TABLE IF NOT EXISTS sys_state (
    id            INTEGER PRIMARY KEY AUTOINCREMENT, -- 每筆紀錄唯一 ID
    lock_class    TEXT NOT NULL,                     -- 鎖的類別名稱 (例如: "Image_Process")
    timestamp     INTEGER NOT NULL,                  -- 鎖的過期時間戳 (Unix Timestamp，單位: 秒)
    is_locked     INTEGER DEFAULT 1,                 -- 1 = 處理中, 0 = 已完成
    created_at    TEXT DEFAULT (datetime('now')),    -- 建立時間 (UTC)
    finished_at   TEXT DEFAULT NULL                  -- 完成時間 (UTC)，處理完成後更新
);

CREATE INDEX IF NOT EXISTS idx_sys_state_is_locked  ON sys_state (is_locked);