import json
import time
from pathlib import Path

from aop.lock import sqlite_table_lock
from flask import Blueprint, request, jsonify

from dto.lock_config import LockConfig
from entity.sys_state import SysState
from service.sys_state import get_image_process_count
import PIL.Image

from util.image import validate_image, save_image_with_md5, collect_image_paths
from const.image_const import ImageConst
from service.image_detection import ImageDetection
from service.image_transform import ImageTransform
from model.factory.detection_model_factory import DetectionModelFactory
from model.factory.transform_model_factory import TransformModelFactory
from util.common import common
import numpy as np


config = common.config
logger = common.logger

image_bp = Blueprint("image", __name__)

lock_config = LockConfig(
    lock_class=ImageConst.IMAGE_PROCESS,
    ttl_seconds=int(config.get('lock', 'ttl_seconds')),
    retry_interval=float(config.get('lock', 'retry_interval')),
    timeout=int(config.get('lock', 'timeout')),
    max_concurrent=int(config.get('lock', 'max_concurrent')),
)


@image_bp.route('/count', methods=['GET'])
def get_count():
    # === 取得 api 使用次數 (sqlite) ===
    count = get_image_process_count(SysState(lock_class="image_process"))
    style_ref_image_paths = Path(config.get('image', "style_ref_image_paths"))
    style_ref_path = collect_image_paths(style_ref_image_paths)


    # === return data ===
    response_data = {
        "image_process_count": count,
        "style_ref_image_paths": style_ref_path
    }

    # pretty print data
    logger.debug("=== [/count Response Data] ===")
    logger.debug(json.dumps(response_data, indent=2, ensure_ascii=False))

    return jsonify(response_data), 200


@image_bp.route('/upload', methods=['POST'])
@sqlite_table_lock(lock_config)
def upload_image():
########################################################################################################################
    #  ===  格式校驗 & 取參數  ===
    api_start = time.perf_counter()

    ora_file, error, status = validate_image(request.files)
    if error:
        return jsonify({"success": False, "error": error}), status

    ora_filename = ora_file.filename

    detect_model = request.form.get("detect_model", ImageConst.MODEL_YOLO)
    transform_model = request.form.get("transform_model", ImageConst.MODEL_STABLE_DIFFUSION)
    style_ref_image = request.form.get("style_ref_image", config.get('image', "default_style_ref_img"))

    web_base_url = config.get('server', 'web_base_url')

    logger.debug(f"detect_model: {detect_model}, transform_model: {transform_model}")


########################################################################################################################
    #  ===  檢查上傳圖是否有貓  ===
    # 預設使用 yolo 需求較低
    detector_image_start = time.perf_counter()


    try:
        # === 直接從全域單例工廠取得常駐記憶體的模型 ===
        try:
            d_model = DetectionModelFactory.get_model(detect_model)
        except ValueError as ve:
            logger.error(f"ValueError: {ve}", exc_info=True)
            return jsonify({"error": str(ve)}), 400


        # === 開始跑預測 ===
        svcd = ImageDetection(model=d_model)
        tag_results, predict_list, result_np = svcd.make_detect_image(ora_file)


        # === 儲存原圖 (使用 save_image_with_md5) ===
        ora_file.seek(0)  # reset image index

        ora_image = PIL.Image.open(ora_file)  # 載入為 PIL Image 物件
        ora_dir = Path(config.get("image", "user_input_ora_path"))

        # 使用 save_image_with_md5 儲存並取得自動生成的檔名路徑與 md5
        ora_path, ora_md5 = save_image_with_md5(
            image=ora_image, save_transform_dir=ora_dir, file_name=ora_filename, convert_jpg=False
        )
        logger.debug(f"ora_path: {ora_path}, md5: {ora_md5}")

        ora_file.seek(0)  # 讀取完畢後再次重置指標


        # === 寫入 detect image ===
        # ✅ imwrite 前確認 result_image 是合法的 numpy array
        if result_np is None or not isinstance(result_np, np.ndarray) or result_np.size == 0:
            raise ValueError("result_np 不合法，無法寫入檔案")

        # 1. 將 NumPy Array (RGB) 轉換為 PIL Image 物件
        detect_image = PIL.Image.fromarray(result_np)

        # 2. 設定 detect 圖片儲存目錄
        detect_dir = Path(config.get('image', "user_input_detect_path")) / detect_model

        # 3. 使用 save_image_with_md5 儲存
        detect_path, detect_md5 = save_image_with_md5(
            image=detect_image,
            save_transform_dir=detect_dir,
            file_name=ora_filename
        )
        logger.debug(
            f'tag_results: {tag_results}, predict_list: {predict_list}, detect_path: {detect_path}, detect_md5: {detect_md5}')
        detector_image_cost = round(time.perf_counter() - detector_image_start, 3)

    except Exception as e:
        logger.error(f"Exception: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500



########################################################################################################################
    #  === vector search similar image  ===
    similar_image_start = time.perf_counter()

    similar_path = ora_path

    logger.debug(f'similar_path:{similar_path}')
    similar_image_cost = round(time.perf_counter() - similar_image_start, 3)



########################################################################################################################
    #  ===  style transform two images  ===
    # 目前提供 1.stable_diffusion_transform, 2.sd_image_variations_transform
    # 預設使用 stable_diffusion_transform 跑比較快

    # 風格轉換
    try:

        # ===  取得 transform_path & 風格轉換參考圖  ===
        transform_path = Path(f'{config.get("image", "transform_path")}')
        logger.debug(f'style_ref_image: {style_ref_image}, transform_path: {transform_path}')


        # === 直接從全域單例工廠取得常駐記憶體的模型 ===
        try:
            t_model = TransformModelFactory.get_model(transform_model)
        except ValueError as ve:
            logger.error(f"ValueError: {ve}", exc_info=True)
            return jsonify({"error": str(ve)}), 400


        # === 開始跑預測 ===
        svct = ImageTransform(model=t_model)


        # === 原圖 transform ===
        origin_image_transform_start = time.perf_counter()
        origin_image_transform = svct.generate(ora_path, Path(style_ref_image))
        # save image
        origin_transform_path, origin_transform_md5= save_image_with_md5(
            image=origin_image_transform, save_transform_dir=transform_path / transform_model, file_name=ora_filename
        )
        logger.debug(f"origin_transform_path: {ora_path}, origin_transform_md5: {ora_md5}")
        origin_image_transform_cost = round(time.perf_counter() - origin_image_transform_start, 3)


        # ===  相似圖 transform ===
        similar_image_transform_start = time.perf_counter()
        similar_image_transform = ora_path
        # save image
        similar_transform_path = similar_image_transform
        logger.debug(f"similar_transform_path: {ora_path}, similar_transform_md5: {ora_md5}")
        similar_image_transform_cost = round(time.perf_counter() - similar_image_transform_start, 3)


        # ===  print transform images path ===
        logger.debug(f"origin_transform_path: {origin_transform_path}, similar_transform_path: {similar_transform_path}")


    except Exception as e:
        logger.error(f"Exception: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500



########################################################################################################################

#  ===  組合 return data 字典  ===
    response_data = {
        "success": True,
        # 偵測圖片參數
        "detector_image": f"{web_base_url}/{detect_path.as_posix()}",
        "predict_list": predict_list,
        "tag_results": tag_results,
        "detector_image_cost": detector_image_cost,
        # 向量搜尋參數
        "similar_image": f"{web_base_url}/{similar_path.as_posix()}",
        "similar_image_cost": similar_image_cost,
        # transform model 參數
        "origin_image_transform": f"{web_base_url}/{origin_transform_path.as_posix()}",
        "origin_image_transform_cost": origin_image_transform_cost,
        "similar_image_transform": f"{web_base_url}/{similar_transform_path.as_posix()}",
        "similar_image_transform_cost": similar_image_transform_cost,
        "image_process_count": get_image_process_count(SysState(lock_class=ImageConst.IMAGE_PROCESS)),
        # cost time
        "api_cost": round(time.perf_counter() - api_start, 3),
    }

    # === 送出前 Print Log ===
    logger.debug("=== [/upload Response Data] ===")
    # pretty print
    logger.debug(json.dumps(response_data, indent=2, ensure_ascii=False))

    return jsonify(response_data), 200

