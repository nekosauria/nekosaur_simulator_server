# Nekosaur Simulator

貓咪圖片辨識 + 風格轉換的實驗性專案。使用者上傳一張貓咪照片，系統會找出資料庫中最相似的貓咪，並將兩張圖片都轉換成「貓 + 恐龍」融合風格（Nekosaur）後回傳。

> 🚧 開發中：目前僅完成整體 workflow 設計，尚未完成開發。本 README 先記錄核心理念與架構，之後會隨開發進度更新。

---

## 核心理念

1. **偵測** — 先確認上傳的圖片裡真的有貓，過濾掉不相關的圖片
2. **比對** — 從既有的貓咪資料庫中，找出視覺上最相似的一張
3. **轉換** — 把使用者的原圖跟找到的相似圖，都轉換成 Nekosaur 風格
4. **回傳** — 讓使用者同時看到「相似的貓」跟「風格轉換後的結果」

---

## 三大工作流程

### 1. User Upload Flow（核心互動流程）

使用者上傳圖片 → 進入 Flask API：

```
SQLite AOP Lock（限制併發，保護效能）
        ↓
Image Legal Check（格式 / 大小驗證）
        ↓
YOLO Match Check（確認圖片內有貓）
        ↓
Similarity Detection（MariaDB 向量索引找最相似貓咪）
        ↓
Save to Storage（寫入 FTP + MariaDB Metadata）
        ↓
Diffusers Style Change（原圖 + 相似圖 → Nekosaur 風格轉換）
        ↓
回傳結果 + 釋放 Lock
```

### 2. Fetch Images Pipeline（背景資料收集）

```
Cron 排程 → 呼叫 Cat API 抓圖 → RabbitMQ Queue
        ↓
Python Worker 消費訊息
        ↓
下載圖片 + 計算 MD5 唯一值
        ↓
分流儲存：FTP（實體檔案）＋ MariaDB（Metadata / 路徑 / 向量欄位）
```

### 3. Cleaning Images Task（資料一致性維護）

```
Daemon 定時讀取 MariaDB 內所有圖片路徑
        ↓
逐一檢查 FTP 上的實體檔案是否還存在
        ↓
存在 → 略過；遺失 → Soft Delete（is_deleted = 1，避免前端讀到破圖）
```

---

## 技術棧（規劃）

| 類別 | 技術 |
|---|---|
| 後端框架 | Flask |
| 主要資料庫 | MariaDB（Vector Index Plugin 做相似度搜尋） |
| 併發控制 | SQLite（AOP Lock，非主資料庫） |
| 訊息佇列 | RabbitMQ |
| 檔案儲存 | FTP |
| 貓咪偵測 | YOLO |
| 風格轉換 | HuggingFace Diffusers（本地模型，非外部 API） |
| 前端 | React |
| 外部資料來源 | TheCatAPI |

---

## 目前狀態

- [x] 三大 workflow 流程設計
- [x] 前端頁面串接
- [ ] 後端模組實作
- [ ] 部署 / Docker 化

