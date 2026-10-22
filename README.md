# Nekosaur Simulator

貓咪圖片辨識 + 風格轉換的實驗性專案。使用者上傳一張貓咪照片，系統會找出資料庫中最相似的貓咪，並將兩張圖片都轉換成「貓 + 恐龍」融合風格（Nekosaur）後回傳。

> ✅ **開發進度**：核心程式碼已完成實作，並完成手動部署與單機環境功能測試，目前可在本機/單機環境順暢跑通完整流程。

👉 **歡迎線上試用：** [https://nekosaur.com/](https://nekosaur.com/)

---

## 核心理念

1. **偵測** — 先確認上傳的圖片裡真的有貓，過濾掉不相關的圖片
2. **比對** — 從既有的貓咪資料庫中，找出視覺上最相似的一張
3. **轉換** — 把使用者的原圖跟找到的相似圖，都轉換成 Nekosaur 風格
4. **回傳** — 讓使用者同時看到「相似的貓」跟「風格轉換後的結果」

---

## 架構設計亮點（Architecture Highlights）

### 1. Model Factory Pattern（模型工廠模式）

偵測（Detection）、向量化（Embedding）、風格轉換（Transform）三種 ML 模型皆採用 Factory + Interface 抽象化設計：

* **介面隔離**：`model/interface` 定義統一介面（`base_detection_model.py`、`base_embedding_model.py`、`base_transform_model.py`）。
* **多元實作**：`model/impl` 提供多種演算法實作（YOLO、MaskRCNN、CLIP、SD Image Variations、SD v1.5 + IP-Adapter）。
* **預載入與權責分離**：在應用啟動時透過 `init_models()` 將模型預先載入 GPU 記憶體（Singleton），明確分離 `load()`（重量級初始化）與 `generate()`（單次推論），避免每個 HTTP 請求重複載入模型帶來的巨大開銷。
* **高靈活性**：未來替換或擴充模型（如將偵測從 YOLO 換成 MaskRCNN）只需實作介面並註冊至 Factory，完全無需改動 Service 層商業邏輯。

### 2. 嚴格分層架構與 DTO 邊界控管

後端採用嚴格的 `route` → `service` → `dao` → `entity` 四層架構，並在各層傳遞時使用獨立的 DTO（Data Transfer Object）進行界限防禦：

* `route/`：Flask Blueprint，解析 HTTP 請求並轉換為 `ImageRequest` (DTO)。
* `service/`：處理商業邏輯（偵測、比對、風格轉化、併發鎖控管），對外拋出 Service 邊界 DTO。
* `dao/`：資料存取層，堅持明確指定 Column 選取（不使用 `SELECT *`）。
* `entity/`：對應資料庫 Table 的資料結構。
* **全流程 DTO 流轉**：`ImageRequest`（Controller 解析）→ Service 邊界 DTO → `ModelPrediction`（模型推論）→ `ImageUploadResponse`（API 回應）。職責單一且降低模組間耦合度。

### 3. 基於 Glob Pattern 的 MD5 內容去重策略

圖片去重不採用簡單的「檔案路徑比對」，而是採用 **MD5 內容雜湊 + Glob Pattern**（`f"{md5}_*"`）進行檔案比對。即便檔案被重新命名或加上時間戳記，只要圖片內容相同即可精準識別，避免重複儲存、下載與模型運算資源的浪費。

---

## 三大工作流程

### 1. User Upload Flow（核心互動流程）

使用者上傳圖片 → 進入 Flask API：

```
SQLite AOP Lock（限制併發，保護效能與 GPU 資源）
        ↓
Image Legal Check（格式 / 大小驗證）
        ↓
MD5 去重 + 儲存原圖（static/images）+ MariaDB Metadata 寫入
        ↓
Embedding & Similarity Search（CLIP 向量化 → MariaDB Vector Index 找最相似貓咪）
        ↓
Detection Service（透過 Model Factory 動態呼叫 YOLO / MaskRCNN）
        ↓
Diffusers Style Transfer（原圖 + 相似圖 → Nekosaur 風格轉換）
        ↓
回傳分組結果（success / origin / similar / metrics）+ 釋放 Lock

```

### 2. Fetch Images Pipeline（背景資料收集）

```
排程（APScheduler / Cron）→ 呼叫 Cat API 抓圖 → RabbitMQ Queue
        ↓
Python Worker 消費訊息
        ↓
下載圖片 + 計算 MD5 唯一值（Glob 比對去重）
        ↓
分流儲存：本地檔案系統（static/images）＋ MariaDB（Metadata / 路徑 / 向量欄位）＋ 預處理 Model 生成圖片緩存  

```

### 3. Health / Cleaning Daemon（資料一致性維護）

```
Daemon 定時從 MariaDB 主表 image（last_checked_at）出發巡檢
        ↓
逐一檢查 static/images 實體檔案是否存在
        ↓
存在 → 更新 last_checked_at
遺失 → Soft Delete（is_deleted = 1，避免前端讀取破圖）
        ↓
若緩存使用過, 預處理 Model 生成圖片緩存   
```

---

## 技術棧

| 類別 | 技術實作                                                              |
| --- |-------------------------------------------------------------------|
| **後端框架** | Flask（route / service / dao / entity 分層 + DTO 邊界物件）               |
| **前端框架** | React（Vite）+ 手繪塗鴉風格 UI                                            |
| **主要資料庫** | MariaDB（Vector Index Plugin 相似度搜尋，PyMySQL + DBUtils 連線池）          |
| **併發控制** | SQLite（AOP Lock 資源鎖，非主資料庫）                                        |
| **訊息佇列** | RabbitMQ                                                          |
| **檔案儲存** | 本地檔案系統（`static/images`）                                           |
| **貓咪偵測** | YOLO（ultralytics）/ Torch MaskRCNN（可透過 Factory 切換）                 |
| **相似度向量** | CLIP（clip-ViT-B-32），透過 Embedding Factory 產出向量                     |
| **風格轉換** | HuggingFace Diffusers（SD Image Variations / SD v1.5 + IP-Adapter，本地模型） |
| **外部資料源** | TheCatAPI                                                         |

---

## 目前狀態與未來規劃

### ✅ 已完成項目

* [x] 三大 Workflow 流程設計與繪製
* [x] 手繪風格前端頁面串接
* [x] 後端核心模組實作（Route / Service / DAO / Entity / DTO / Model Factory）
* [x] 本機 / 單機環境手動部署
* [x] 全流程功能測試驗證（上傳 → 偵測 → 比對 → 風格轉換 → 回傳分組資料）

### 🚀 未來規劃與優化方向 (Roadmap)

* [ ] **遠端儲存整合**：抽換本地檔案系統，整合 FTP / S3 雲端圖片儲存。
* [ ] **容器化與自動化部署**：編寫 Dockerfile / Docker Compose，並建立 CI/CD Pipeline 與 Kubernetes (K8s) 部署檔。
* [ ] **測試覆蓋率提升**：撰寫單元測試（Unit Test）與端到端整合測試。
* [ ] **壓測與效能調優**：進行 Load / Stress Test，並優化 Production Web Server 配置（Gunicorn Worker 數、Timeout、GPU 資源限制）。
* [ ] **高可用架構**：搭建 MariaDB Vector Index 與 RabbitMQ 叢集化（Cluster）架構。
* [ ] **資料清理機制擴充**：補全過期與無效圖片的硬刪除（Hard Delete）排程任務。