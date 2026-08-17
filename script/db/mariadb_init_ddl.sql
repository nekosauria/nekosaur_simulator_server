-- 清空 table 測試用
--SET FOREIGN_KEY_CHECKS = 0;
--
--TRUNCATE TABLE image_embedding;
--TRUNCATE TABLE image_transform;
--TRUNCATE TABLE image_detection;
--TRUNCATE TABLE image;
--
--SET FOREIGN_KEY_CHECKS = 1;


DROP TABLE IF EXISTS image_embedding;
DROP TABLE IF EXISTS image_transform;
DROP TABLE IF EXISTS image_detection;
DROP TABLE IF EXISTS image;

-- 1. 圖片主表（儲存原始圖片實體資訊）
CREATE TABLE image (
    id               BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    md5_hash         CHAR(32) NOT NULL,
    origin_path      VARCHAR(512) NOT NULL,
    image_source     VARCHAR(512) NULL,
    file_name       VARCHAR(255) NOT NULL COMMENT '圖片檔名',
    raw_source       JSON NULL COMMENT '第三方 API 回傳的原始 JSON 備查 or 使用者上傳圖片檔名 (JSON)',
    is_deleted       BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at       DATETIME NULL,
    last_checked_at  DATETIME NULL COMMENT 'health daemon 上次檢查（存在性/有無貓，連同關聯 detection/transform）的時間',
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    UNIQUE KEY uq_md5_hash (md5_hash),
    KEY idx_is_deleted (is_deleted),
    KEY idx_last_checked_at (last_checked_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- 2. 物件偵測流水表 (1:detect_model_count，同 image_id + 同 detect_model 允許1筆歷史紀錄)
CREATE TABLE image_detection (
    id               BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    image_id         BIGINT UNSIGNED NOT NULL COMMENT '對應 image.id',
    md5_hash         CHAR(32) NOT NULL COMMENT '此標註框圖自身的 md5',
    detect_path      VARCHAR(512) NULL COMMENT '標註框圖路徑',
    detect_model     VARCHAR(64) NOT NULL COMMENT '例如: yolov8n, yolov11x',
    has_cat          BOOLEAN NOT NULL DEFAULT FALSE COMMENT '該次偵測是否偵測到貓',
    is_preprocessed  BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否為預處理(非使用者當下觸發)產生的偵測結果',
    predict_list     JSON NULL COMMENT '偵測結果: JSON',
    tag_results      JSON NULL COMMENT 'drawable tag: JSON',
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_detection_image FOREIGN KEY (image_id) REFERENCES image (id) ON DELETE RESTRICT,
    UNIQUE KEY uq_md5_hash (md5_hash),
    UNIQUE KEY uq_image_detect_model (image_id, detect_model),
    KEY idx_has_cat (has_cat)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- 3. 風格轉換流水表 (1:N，同 image_id + 同 transform_model + 同 style_ref 可多筆)
CREATE TABLE image_transform (
    id               BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    image_id         BIGINT UNSIGNED NOT NULL COMMENT '原圖 ID',
    md5_hash         CHAR(32) NOT NULL COMMENT '此轉換後圖片自身的 md5',
    transform_path   VARCHAR(512) NOT NULL COMMENT '轉換後的圖片路徑',
    transform_model  VARCHAR(64) NOT NULL COMMENT '例如: sd-image-variations-v2',
    style_ref_path   VARCHAR(255) NOT NULL COMMENT '使用的風格參考圖路徑，例如: static/images/style/dinosaur.png',
    is_use           BOOLEAN NOT NULL DEFAULT FALSE COMMENT '此快取是否已被使用過',
    is_preprocessed  BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否為預處理(非使用者當下觸發)產生的快取',
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_transform_image FOREIGN KEY (image_id) REFERENCES image (id) ON DELETE RESTRICT,
    UNIQUE KEY uq_md5_hash (md5_hash),
    KEY idx_image_model_style (image_id, transform_model, style_ref_path),
    KEY idx_is_use (image_id, is_use)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- 4. 向量表 (1:embedding_model_count)
CREATE TABLE image_embedding (
    id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    image_id    BIGINT UNSIGNED NOT NULL COMMENT '對應 image.id',
    model_name  VARCHAR(64) NOT NULL COMMENT '例如: clip-vit-b32',
    vector_512  VECTOR(512) NOT NULL COMMENT 'CLIP 512維向量',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_embedding_image FOREIGN KEY (image_id) REFERENCES image (id) ON DELETE RESTRICT,
    CONSTRAINT uq_image_model UNIQUE (image_id, model_name), -- 防止同個 model 重複計算
    VECTOR INDEX idx_vector_512 (vector_512) M=32 DISTANCE=cosine
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;