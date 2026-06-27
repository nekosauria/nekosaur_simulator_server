---
name: nekosaur-project
description: >
  Context memory skill for the Nekosaur Simulator project — a full-stack cat image detection and style-transfer app.
  Use this skill whenever the user mentions nekosaur, cat simulator, cat image upload, thecatapi, neko style, dinosaur style,
  cat detection, YOLO, diffusers style transfer, SQLite AOP lock, MariaDB vector index, or asks about the backend/frontend
  of this specific project. Also trigger when the user asks about Flask + MariaDB + RabbitMQ architecture,
  FTP image pipeline, similarity detection, or React frontend connected to this system.
  This skill gives Claude the full project context so it can answer questions, debug, and extend features without re-explanation.
---

# Nekosaur Simulator — Project Context

## Project Overview

A full-stack cat image platform with three core workflows:
1. **Fetch Pipeline** — Cron job fetches cat images from TheCatAPI → RabbitMQ → Worker → MariaDB + FTP
2. **User Upload Flow** — User uploads image → YOLO cat detection → vector similarity search → style transfer → return results
3. **Cleaning Task** — Daemon checks FTP file existence against MariaDB records, soft-deletes orphaned entries

---

## Repository Structure

```
nekosaur_simulator/
├── nekosaur_simulator_server/   # Backend (Python + Flask)
└── nekosaur_simulator_client/   # Frontend (React.js)
```

---

## Backend — `nekosaur_simulator_server`

### Tech Stack
- **Language**: Python
- **Web Framework**: Flask
- **Primary DB**: MariaDB (with Vector Index Plugin for similarity search)
- **Session / Lock DB**: SQLite3 (AOP-style lock for concurrent upload control)
- **Queue / Task Broker**: RabbitMQ (producer/consumer via `pika`)
- **Scheduler**: Cron (triggers TheCatAPI fetch)
- **File Storage**: FTP server (`ftplib`)
- **Cat Detection**: YOLO (object detection)
- **Style Transfer**: HuggingFace Diffusers (local ML model, Nekosaur style)
- **External API**: TheCatAPI (https://thecatapi.com)

---

## Workflow 1 — User Upload Flow (Core Event-Driven)

```
[React Frontend]
      │
      │ User visits homepage → Flask reads SQLite table count → return stats
      │
      │ User uploads cat image
      ▼
[Flask API]
      │
      ├─ SQLite AOP Lock
      │   • Check & insert lock record
      │   • Limit concurrent sessions (performance guard)
      │
      ├─ Image Legal Check
      │   • Validate size, format, type conversion
      │
      ├─ YOLO Match Check
      │   • Object detection — confirm image contains a cat
      │
      ├─ Similarity Detection
      │   • Query MariaDB Vector Index
      │   • Retrieve most similar cat image
      │
      ├─ Save to Storage
      │   • Write user image to FTP
      │   • Save metadata to MariaDB
      │
      ├─ Diffusers Style Transfer
      │   • Load user image + similar image
      │   • Apply Nekosaur style via local ML model
      │
      ├─ Return to Frontend:
      │   • Similar cat image
      │   • Original image (style-transferred)
      │   • Similar image (style-transferred)
      │
      └─ SQLite AOP Lock Release
```

---

## Workflow 2 — Fetch Images Pipeline

```
[Cron Scheduler]
      │ 定時觸發
      ▼
[curl TheCatAPI] — 抓取最新貓咪資料與圖片
      │
      ▼
[RabbitMQ Queue] — Producer 投遞消息
      │
      ▼
[Python RabbitMQ Worker] — Subscriber 消費消息
      │
      ▼
[Image Processing Pipeline]
      • 下載圖片
      • 計算唯一特徵值 (MD5)
      │
      ├──────────────────────────────┐
      ▼                              ▼
[FTP Storage]                 [MariaDB]
• 儲存實體原始圖檔              • Metadata
                               • FTP Image Paths
                               • Image Vector (向量欄位, for similarity search)
```

---

## Workflow 3 — Cleaning Images Task

```
[Daemon / Cron]
      │
      ▼
[讀取 MariaDB] — 取出所有圖片的 FTP 實體路徑
      │
      ▼
[驗證 FTP 檔案是否存在]
      │
      ├─ 存在 → 跳過
      │
      └─ 遺失 → Soft Delete
                  • 更新 MariaDB: is_deleted = 1
                  • 防止前端讀取到破圖
```

---

## Frontend — `nekosaur_simulator_client`

### Tech Stack
- **Framework**: React.js

### Key Features
- Homepage: display stats (cat count from SQLite)
- Upload UI: user uploads cat image
- Results display:
  - Similar cat from TheCatAPI
  - Original image (Nekosaur styled)
  - Similar image (Nekosaur styled)

---

## Key Design Decisions & Notes

| Topic | Detail |
|---|---|
| SQLite AOP Lock | Used to rate-limit concurrent uploads; not the main DB |
| MariaDB Vector Index | Enables fast cosine/L2 similarity search for cat matching |
| YOLO | Validates that uploaded image actually contains a cat before processing |
| Diffusers | Local HuggingFace model for Nekosaur style transfer (not an external API) |
| MD5 dedup | Prevents duplicate cat images from being stored in the fetch pipeline |
| Soft Delete | is_deleted = 1 flag; never hard-delete from MariaDB |
| FTP | All raw image files stored here; MariaDB only stores paths |

---

## Common Development Tasks

- **New API endpoint** → Flask Blueprint pattern, register in `app.py`
- **Debug RabbitMQ consumer** → check `pika` connection, queue name, ack/nack logic
- **Modify DB schema** → update MariaDB migration; update SQLite schema if stats table affected
- **Tune YOLO detection** → adjust confidence threshold, check model weights path
- **Style transfer issues** → check Diffusers model loading, GPU/CPU device, input image preprocessing
- **FTP problems** → check `ftplib.FTP` credentials, passive mode (set_pasv(True)), binary transfer mode
- **Vector search slow** → check MariaDB Vector Index plugin is enabled, re-index if needed

---

## Environment / Config Reminders
- TheCatAPI key → .env
- FTP credentials → .env, never hardcoded
- MariaDB + RabbitMQ + FTP likely run as Docker containers (check docker-compose.yml)
- Diffusers model weights → local path, confirm GPU availability with torch.cuda.is_available()