---
name: nekosaur-project
description: >
  Context memory skill for the Nekosaur Simulator project — a full-stack cat image detection and style-transfer app.
  Use this skill whenever the user mentions nekosaur, cat simulator, cat image upload, thecatapi, neko style, dinosaur style,
  cat detection, YOLO, MaskRCNN, CLIP embedding, diffusers style transfer, SQLite AOP lock, MariaDB vector index, or asks
  about the backend/frontend of this specific project. Also trigger when the user asks about Flask + MariaDB + RabbitMQ
  architecture, the DAO/DTO/entity/service/route layering, the model factory pattern, local image storage under
  static/images, similarity detection, or the React frontend connected to this system.
  This skill gives Claude the full project context so it can answer questions, debug, and extend features without re-explanation.
---

# Nekosaur Simulator — Project Context

## Project Overview

A full-stack cat image platform with three core workflows:
1. **Fetch Pipeline** — Cron/APScheduler job fetches cat images from TheCatAPI → RabbitMQ → Worker → MariaDB + local static storage
2. **User Upload Flow** — User uploads image → detection (YOLO/MaskRCNN) confirms cat → CLIP embedding + vector similarity search → style transfer (Diffusers) → return grouped results
3. **Health/Cleaning Daemon** — Background daemon checks stored file existence against MariaDB records, keeps data consistent (soft-delete / re-check `last_checked_at` on the `image` table)

---

## Repository Structure

```
nekosaur_simulator/
├── nekosaur_simulator_server/   # Backend (Python + Flask)
└── nekosaur_simulator_client/   # Frontend (React.js, Vite)
```

### Backend layout (`nekosaur_simulator_server`)

```
app/
├── aop/            # lock.py — SQLite-based distributed/session lock (AOP-style)
├── const/          # image_const.py — shared constants
├── dao/            # image.py, image_detection.py, image_embedding.py, image_transform.py, sys_state.py
├── dto/            # image_detection.py, image_embedding.py, image_processor.py,
│                   # image_transform.py, image_upload.py, lock_config.py
├── entity/         # image.py, image_detection.py, image_embedding.py, image_transform.py, sys_state.py
├── model/
│   ├── factory/    # detection_model_factory.py, embedding_model_factory.py, transform_model_factory.py
│   ├── impl/       # clip_embedding_model.py, sd_image_variations_transform_model.py,
│   │               # stable_diffusion_transform_model.py, torch_detection_model.py, yolo_detection_model.py
│   └── interface/  # base_detection_model.py, base_embedding_model.py, base_model_factory.py, base_transform_model.py
├── route/          # image.py — Flask Blueprint / route layer
├── service/        # image.py, image_detection.py, image_embedding.py, image_processor.py,
│                   # image_transform.py, sys_state.py
├── task/           # fetch_thecatapi.py, image_daemon_process.py
├── util/           # common.py, image.py, image_draw.py, mariadb.py, rabbitmq.py, sqlite.py, step_timer.py, torch_util.py
└── worker/         # base_image_consumer.py, fetch_thecatapi_consumer.py, image_daemon_process_consumer.py
```

Local image storage lives under `static/images/`, split by source and stage:
```
static/images/
├── style/                     # style reference images (dinosaur styles, color variants)
├── thecatapi/
│   ├── origin/                # fetched TheCatAPI images
│   ├── detect/{model}/        # detection-annotated outputs, keyed by detector model name
│   └── transform/{model}/     # style-transferred outputs, keyed by transform model name
└── user_upload/
    ├── origin/
    ├── detect/{model}/
    └── transform/{model}/
```
There is no FTP layer — MariaDB stores relative paths under `static/images/...` and the Flask app serves/reads files locally.

---

## Backend — `nekosaur_simulator_server`

### Tech Stack
- **Language**: Python
- **Web Framework**: Flask
- **Primary DB**: MariaDB (four tables: `image`, `image_detection`, `image_transform`, `image_embedding`; vector index for similarity search)
- **Session / Lock DB**: SQLite3 (AOP-style lock for concurrent upload/session control, via `app/aop/lock.py`)
- **DB Access**: PyMySQL + DBUtils (`PooledDB`) connection pooling
- **Queue / Task Broker**: RabbitMQ (producer/consumer via `pika`)
- **Scheduler**: APScheduler / cron (triggers TheCatAPI fetch and daemon tasks)
- **File Storage**: local filesystem under `static/images/` (no FTP)
- **Cat Detection**: YOLO (ultralytics, `yolo_detection_model.py`) and Torch/MaskRCNN (`torch_detection_model.py`) behind `DetectionModelFactory`
- **Embedding**: CLIP (`clip_embedding_model.py`, sentence-transformers `clip-ViT-B-32`) behind `EmbeddingModelFactory`, used for MariaDB vector similarity search
- **Style Transfer**: HuggingFace Diffusers — `sd-image-variations-diffusers` and `stable-diffusion-v1-5` (+ IP-Adapter) behind `TransformModelFactory`
- **External API**: TheCatAPI (https://thecatapi.com)

### Architecture pattern
Strict layering: **route → service → dao → entity**, with separate **dto** objects at the controller/service/API-response boundaries. ML models follow a **factory + interface** pattern (`model/interface` defines base contracts, `model/impl` implements them, `model/factory` preloads singletons into GPU memory at startup via `init_models()` and exposes `get_model()`; `load()` is decoupled from `generate()`).

---

## Workflow 1 — User Upload Flow (Core Event-Driven)

```
[React Frontend]
      │
      │ User visits homepage → Flask reads SQLite table count → return stats
      │
      │ User uploads cat image
      ▼
[Flask Route (app/route/image.py)]
      │
      ├─ SQLite AOP Lock (app/aop/lock.py)
      │   • Check & insert lock record
      │   • Limit concurrent sessions (performance guard)
      │
      ├─ Image Legal Check
      │   • Validate size, format, type conversion (app/util/image.py)
      │
      ├─ Detection Service (image_detection.py)
      │   • DetectionModelFactory.get_model() → YOLO or MaskRCNN
      │   • Confirm image contains a cat; save annotated output under static/images/user_upload/detect/{model}/
      │
      ├─ Save Origin + Metadata
      │   • MD5-based dedup (glob match f"{md5}_*") before writing
      │   • Save origin file to static/images/user_upload/origin/
      │   • Persist metadata to MariaDB `image` table
      │
      ├─ Embedding + Similarity Search (image_embedding.py)
      │   • EmbeddingModelFactory.get_model() → CLIP vector
      │   • Query MariaDB vector index for most similar cat image
      │   • Missing-result handling resolved at service layer (return empty entity, not None)
      │
      ├─ Style Transfer (image_transform.py)
      │   • TransformModelFactory.get_model() → SD image variations / SD v1.5 + IP-Adapter
      │   • Transform both the origin image and the matched similar image
      │   • Save outputs under static/images/user_upload/transform/{model}/
      │
      ├─ Return to Frontend — ImageUploadResponse (dto/image_upload.py):
      │   grouped as success / origin / similar / metrics,
      │   each with image / detector / transform / embedding sub-groups
      │
      └─ SQLite AOP Lock Release
```

---

## Workflow 2 — Fetch Images Pipeline

```
[APScheduler / Cron]
      │ 定時觸發
      ▼
[fetch_thecatapi.py] — 抓取最新貓咪資料與圖片
      │
      ▼
[RabbitMQ Queue] — Producer 投遞消息
      │
      ▼
[fetch_thecatapi_consumer.py] — Subscriber 消費消息 (base_image_consumer.py)
      │
      ▼
[Image Processing Pipeline]
      • 下載圖片
      • 計算 MD5 唯一特徵值 (glob-based dedup, handles renamed files)
      │
      ├──────────────────────────────┐
      ▼                              ▼
[Local Storage]               [MariaDB]
static/images/thecatapi/       • image / image_detection / image_transform / image_embedding
origin, detect/{model},        • local relative paths (no FTP)
transform/{model}              • Image Vector (向量欄位, for CLIP similarity search)
```

---

## Workflow 3 — Health / Cleaning Daemon

```
[image_daemon_process.py → image_daemon_process_consumer.py]
      │
      ▼
[讀取 MariaDB `image` 表] — last_checked_at 只存在於主表 image，daemon 從這裡出發巡檢
      │
      ▼
[驗證 static/images 下實體檔案是否存在]
      │
      ├─ 存在 → 更新 last_checked_at → 跳過
      │
      └─ 遺失 → Soft Delete
                  • 更新 MariaDB: is_deleted = 1 (never hard-delete)
                  • 防止前端讀取到破圖
```

---

## Frontend — `nekosaur_simulator_client`

### Tech Stack
- **Framework**: React (Vite-based)
- **Styling**: Hand-drawn/doodle aesthetic — thick black borders, offset box shadows, Patrick Hand / Permanent Marker fonts, Morandi-toned warm muted palette anchored around `#fff8dc`; CSS class-based (BEM), no inline styles
- **API config**: `.env` + `services/config.js` abstraction layer (mirrors backend's `common.config.get()`)

### Key Features
- Homepage: display stats (cat count from SQLite)
- Upload UI (`UploadPanel`, `ImagePreview`): user uploads cat image
- Results display (`DetectorResultRow`, `TransformResultRow`, `CrossOriginDownloadButton`):
  - Similar cat from TheCatAPI
  - Original image (Nekosaur styled)
  - Similar image (Nekosaur styled)
- `preview-badge` BEM class system for status/model badges

---

## Key Design Decisions & Notes

| Topic | Detail |
|---|---|
| SQLite AOP Lock | Used to rate-limit concurrent uploads/sessions; not the main DB; `sqlite3` context manager only handles commit/rollback, not `close()` — needs a proper `@contextmanager` wrapper |
| MariaDB Vector Index | Enables fast similarity search over CLIP embeddings for cat matching |
| YOLO vs. Torch/MaskRCNN | YOLO is significantly faster and sufficient for cat detection; Torch/MaskRCNN kept as an alternate detector behind the same interface |
| Diffusers | Local HuggingFace models (`sd-image-variations-diffusers`, `stable-diffusion-v1-5` + IP-Adapter) for Nekosaur style transfer — not an external API |
| Model factory pattern | `load()` (heavy init, GPU preload at startup) is decoupled from `generate()` (per-request inference) for detection, embedding, and transform models alike |
| MD5 dedup | Glob pattern match (`f"{md5}_*"`) instead of exact path comparison, so renamed files still dedup correctly |
| No FTP | Raw and processed images are stored locally under `static/images/...`; MariaDB stores relative paths only |
| Soft Delete | `is_deleted = 1` flag; never hard-delete from MariaDB |
| `last_checked_at` | Lives only on the `image` table, since the health daemon traverses from there |
| Null handling | Service layer returns empty entities instead of `None` when e.g. vector search finds no match, keeping the route layer clean |
| Schema | 4 MariaDB tables (`image`, `image_detection`, `image_transform`, `image_embedding`) + SQLite `sys_state`; `UNIQUE KEY uq_image_detect_model` on `image_detection`; `image_transform` allows multiple rows per `(image_id, transform_model, style_ref_path)`, with `idx_is_use` for daemon query performance |

---

## Common Development Tasks

- **New API endpoint** → Flask Blueprint pattern in `app/route/image.py`, delegate to `app/service/`, register in `app.py`
- **Debug RabbitMQ consumer** → check `pika` connection, queue name, ack/nack logic in `app/worker/`
- **Modify DB schema** → update `script/db/mariadb_init_ddl.sql`; update `script/db/sqlite_db_init_ddl.sql` if `sys_state` affected
- **Tune YOLO/MaskRCNN detection** → adjust confidence threshold, check model weights path under `resource/model/detect/`; swap via `DetectionModelFactory`
- **Tune CLIP embedding / similarity search** → check `resource/model/embedding/clip-ViT-B-32/`, verify MariaDB vector index is enabled and re-index if needed
- **Style transfer issues** → check Diffusers model loading under `resource/model/transform/`, GPU/CPU device (`torch_util.py`), input image preprocessing
- **Local storage problems** → check `static/images/{thecatapi|user_upload}/{origin|detect|transform}/...` paths and permissions (no FTP involved)
- **DAO/service/route naming drift** → keep naming strictly aligned across layers (e.g. `get_image_X_by_image_id`); explicit column selection, no `SELECT *`

---

## Approach & Coding Conventions
- DRY, no redundant logic; explicit `if/else` over ternary; named variables computed before being passed into constructors; no dead code or unnecessary `None` defaults
- Verbose, interview-readable docstrings: class-level docstring for purpose/design intent, field-level docstrings for type semantics and downstream usage
- `logger.debug` logs candidate lists first, then the selected item(s)
- Four DTO layers: controller parsing (`ImageRequest`), service boundary DTOs, model inference layer (`ModelPrediction`), API response layer (`ImageUploadResponse`)
- Frontend: small, targeted incremental changes per request; semantic CSS class naming (e.g. `predict-block` → `detail-section`)

---

## Environment / Config Reminders
- TheCatAPI key → `.env` / `resource/config/config.ini`
- MariaDB + RabbitMQ connection info → `resource/config/config.ini` (see `config_template.ini`), accessed via `common.config.get()`
- MariaDB + RabbitMQ likely run as local services/containers (check `script/shell/setup_mariadb.md`, `setup_rabbitmq.md`)
- Diffusers/YOLO/MaskRCNN/CLIP model weights → local paths under `resource/model/`, confirm GPU availability with `torch.cuda.is_available()` (`app/util/torch_util.py`)
- `logging.basicConfig()` + manual handler combo in `_build_logger()` (`app/util/common.py`) can double-log — watch for this when adding new loggers