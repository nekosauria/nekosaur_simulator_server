DROP TABLE IF EXISTS sys_state;

-- 系統狀態與並發鎖紀錄，對應 SQLite 的系統狀態資料表
CREATE TABLE IF NOT EXISTS sys_state (
    id            INTEGER PRIMARY KEY AUTOINCREMENT, -- 每筆紀錄唯一 ID
    lock_class    TEXT NOT NULL,                     -- 鎖的類別名稱 (例如: "Image_Process")
    expire_at     INTEGER NOT NULL,                  -- 鎖的過期時間戳 (Unix Timestamp，單位: 秒)
    is_locked     BOOLEAN NOT NULL DEFAULT 1,         -- TRUE = 處理中, FALSE = 已完成
    created_at    TEXT DEFAULT (datetime('now')),    -- 建立時間 (UTC)
    finished_at   TEXT DEFAULT NULL                  -- 完成時間 (UTC)，處理完成後更新
);

CREATE INDEX IF NOT EXISTS idx_sys_state_is_locked  ON sys_state (is_locked);