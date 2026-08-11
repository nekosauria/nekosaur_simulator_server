-- 查詢所有的表
SELECT * FROM image;
SELECT * FROM image_detection;
SELECT * FROM image_transform;
SELECT * FROM image_embedding;

-- vector index 相似圖查詢
WITH target_image AS (
    SELECT VEC_ToText(vector_512) AS target_vec
    FROM image_embedding
    WHERE image_id = 1
    LIMIT 1
)
SELECT
    -- 相似度計算結果
    VEC_DISTANCE_COSINE(ie.vector_512, VEC_FromText(t.target_vec)) AS distance,

    -- 1. 向量表 (image_embedding) 欄位
    ie.id          AS embedding_id,
    ie.model_name  AS embedding_model,
    ie.created_at  AS embedding_created_at,

    -- 2. 圖片主表 (image) 欄位
    img.id         AS image_id,
    img.md5_hash   AS image_md5,
    img.origin_path,
    img.image_source,
    img.raw_source,
    img.is_deleted,
    img.deleted_at,
    img.last_checked_at,
    img.created_at AS image_created_at,

    -- 3. 物件偵測流水表 (image_detection) 欄位
    det.id               AS detection_id,
    det.md5_hash         AS detection_md5,
    det.detect_path,
    det.detect_model,
    det.has_cat,
    det.is_preprocessed  AS detection_is_preprocessed,
    det.predict_list,
    det.tag_results,

    -- 4. 風格轉換流水表 (image_transform) 欄位
    trans.id              AS transform_id,
    trans.md5_hash        AS transform_md5,
    trans.transform_path,
    trans.transform_model,
    trans.style_ref_path,
    trans.is_use,
    trans.is_preprocessed AS transform_is_preprocessed

FROM image_embedding ie
CROSS JOIN target_image t
-- 聯結圖片主表
LEFT JOIN image img
       ON ie.image_id = img.id
-- 聯結物件偵測表 (根據 FK: image_id)
LEFT JOIN image_detection det
       ON img.id = det.image_id
-- 聯結風格轉換表 (根據 FK: image_id)
LEFT JOIN image_transform trans
       ON img.id = trans.image_id

WHERE ie.model_name = 'clip-ViT-B-32'
  AND ie.image_id != 1
  AND img.is_deleted = FALSE  -- 順便排除已被標記刪除的圖片
ORDER BY distance ASC
LIMIT 10;


-- left join 所有表查看所有資料
SELECT
    img.id                  AS image_id,
    img.md5_hash             AS image_md5,
    img.origin_path,
    img.image_source,
    img.raw_source,
    img.is_deleted,
    img.created_at           AS image_created_at,

    det.id                   AS detection_id,
    det.detect_path,
    det.detect_model,
    det.predict_list,
    det.tag_results,
    det.created_at           AS detection_created_at,

    trans.id                 AS transform_id,
    trans.transform_path,
    trans.transform_model,
    trans.created_at         AS transform_created_at,

    emb.id                   AS embedding_id,
    emb.model_name           AS embedding_model,
    emb.vector_512,
    emb.created_at           AS embedding_created_at

FROM image AS img
         LEFT JOIN image_detection AS det
                   ON det.image_id = img.id
         LEFT JOIN image_transform AS trans
                   ON trans.image_id = img.id
         LEFT JOIN image_embedding AS emb
                   ON emb.image_id = img.id
WHERE img.is_deleted = 0 and img.id in (
        1, 2
    )
ORDER BY img.id;
