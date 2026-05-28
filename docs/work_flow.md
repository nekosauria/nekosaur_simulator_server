# Event Life Cycle Work Flow


## User Side Core Event Driven
```
[前端 React]                                   [後端 Flask API]
      │                                                │
      │ User Access 網頁 Homepage：查看 SQLite 統計人數   │ ──────────────> (從 SQLite 讀取 table count)
      │                                                │  
      │ User Upload 貓咪圖  ───────────────────────────>│
      │                                                │
      │                                       [ SQLite AOP Lock (performance issue) ]
      │                                       • 檢查鎖定並 insert & update state
      │                                       • lock with mutli session limit
      │                                                │
      │                                       [ Image Legal Check ]
      │                                       • 驗證大小、格式與型態轉換
      │                                                │
      │                                       [ YOLO Match Check ]
      │                                       • 進行物件偵測，確認影像有貓
      │                                                │
      │                                       [ Similarity Detection ]
      │                                       • 透過 MariaDB 向量索引
      │                                         檢索出最相似的貓咪
      │                                                │
      │                                                │
      │                                       [ Save to Storage ]
      │                                       • 將使用者圖片寫入 FTP
      │                                       • 紀錄 Metadata 到 MariaDB
      │                                                │
      │                                       [ Diffusers Style Change ]
      │                                       • 撈取上述兩張圖片
      │                                       • 使用 ml model 
      │                                         進行 nekosaur 風格轉換
      │                                                │
      │<─ return (Similar 圖片) ────────────────────────┤
      │<─ return (原圖 & 相似圖片風格轉化 transfrom 圖片) ─┤
      │                                       [ AOP Release SQLite Lock ]
      │                                                │
      v                                                v
```


## Fetch Images Tasks
```
[ 排程與外部觸發 ]                            [ 核心非同步處理與儲存層 ]
        │                                                 │
  (Cron Scheduler)                                        │
        │ 定時觸發                                         │
        v                                                 │
  (curl Cat API)                                          │
        │ 抓取最新貓咪資料與圖片                              │
        v                                                 │
  [ RabbitMQ Queue ] ───────────────────────── 投遞消息 ─>─>│
  (Message Queue Producer)                                │
                                                          v
                                              [ Python RabbitMQ Worker ]
                                              • 監聽佇列，訂閱並消費消息 (Subscriber)
                                                          │
                                                          v
                                              [ Image Processing Pipeline ]
                                              • 進行圖片下載與基本處理
                                              • 計算圖片的唯一特徵值 (with md5)
                                                          │
                                                          v
                                              [ Storage Layer (儲存分流) ]
                                                          │
                                        ┌─────────────────┴─────────────────┐
                                        ▼                                   ▼
                                 [ FTP Storage ]                   [ MariaDB 資料庫 ]
                                 • 儲存實體原始圖檔                 (With Vector Index Plugin)
                                                                    ├─ Metadata 
                                                                    ├─ FTP Image Paths (實體路徑)
                                                                    └─ Image Vector column (向量欄位)

```

## Cleaning Images Tasks
```
[ 啟動定時任務 / 常駐 Daemon ]
             │
             v
   [ 1. 檢查資料庫紀錄 ] ────────────────> 讀取 MariaDB 內所有圖片的實體 FTP 路徑
             │
             v
   [ 2. 驗證實體檔案 ] ──────────────────> 依據路徑，逐一檢查 FTP 伺服器上該檔案是否存在？
             │
             ├─> 【 狀況 A：檔案存在 】 ──> 保持原狀，跳過不處理
             │
             └─> 【 狀況 B：檔案遺失 】 ──> [ 3. 執行軟刪除 (Soft Delete) ]
                                                    │
                                                    v
                                            更新 MariaDB 該筆紀錄狀態
                                            (例如：is_deleted = 1)
                                            防止前端未來再度讀取到破圖

```
