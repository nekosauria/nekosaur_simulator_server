DROP TABLE IF EXISTS image_embedding;
DROP TABLE IF EXISTS image_transform;
DROP TABLE IF EXISTS image_detection;
DROP TABLE IF EXISTS image;

-- 1. 圖片主表（儲存原始圖片實體資訊）
CREATE TABLE image (
    id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    md5_hash      CHAR(32) NOT NULL,
    origin_path   VARCHAR(512) NOT NULL,
    image_source  VARCHAR(512) NULL,
    raw_source    JSON NULL COMMENT '第三方 API 回傳的原始 JSON 備查 or 使用者上傳圖片內容 (JSON)',
    is_deleted    TINYINT(1) DEFAULT 0 NOT NULL,
    deleted_at    DATETIME NULL,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    UNIQUE KEY uq_md5_hash (md5_hash),
    KEY idx_is_deleted (is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- 2. 物件偵測流水表 (1:N)
CREATE TABLE image_detection (
    id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    image_id      BIGINT UNSIGNED NOT NULL COMMENT '對應 image.id',
    md5_hash      CHAR(32) NOT NULL,
    detect_path   VARCHAR(512) NULL COMMENT '標註框圖路徑',
    detect_model  VARCHAR(64) NOT NULL COMMENT '例如: yolov8n, yolov11x',
    predict_list  JSON NULL COMMENT '偵測結果: JSON',
    tag_results   JSON NULL COMMENT 'drawable tag: JSON',
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_detection_image FOREIGN KEY (image_id) REFERENCES image (id) ON DELETE RESTRICT,
    KEY idx_image_model (image_id, detect_model)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. 風格轉換流水表 (1:N)
CREATE TABLE image_transform (
    id               BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    image_id         BIGINT UNSIGNED NOT NULL COMMENT '原圖 ID',
    md5_hash         CHAR(32) NOT NULL,
    transform_path   VARCHAR(512) NOT NULL COMMENT '轉換後的圖片路徑',
    transform_model  VARCHAR(64) NOT NULL COMMENT '例如: sd-image-variations-v2',
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_transform_image FOREIGN KEY (image_id) REFERENCES image (id) ON DELETE RESTRICT,
    KEY idx_image_model (image_id, transform_model)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. 向量表 (1:N)
CREATE TABLE image_embedding (
    id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    image_id    BIGINT UNSIGNED NOT NULL COMMENT '對應 image.id',
    model_name  VARCHAR(64) NOT NULL COMMENT '例如: clip-vit-b32',
    vector_512  VECTOR(512) NOT NULL COMMENT 'CLIP 512維向量',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_embedding_image FOREIGN KEY (image_id) REFERENCES image (id) ON DELETE RESTRICT,
    CONSTRAINT uq_image_model UNIQUE (image_id, model_name), -- 防止同個 model 重複計算
    VECTOR INDEX idx_vector_512 (vector_512) M=8 DISTANCE=cosine
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;