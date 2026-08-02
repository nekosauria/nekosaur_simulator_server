from datetime import datetime
import traceback
import hashlib
from pathlib import Path

from aop.lock import sqlite_table_lock
from flask import Blueprint, request, jsonify, url_for
from service.sys_state import get_image_process_count

from util.image import validate_image, save_image_with_timestamp
from const.image_const import ImageConst
from service.image_detection_service import ImageDetectionService
from service.image_transform_service import ImageTransformService
from model.factory.detection_model_factory import DetectionModelFactory
from model.factory.transform_model_factory import TransformModelFactory
from util.common import common
import numpy as np
import cv2

image_bp = Blueprint("image", __name__)


@image_bp.route('/count', methods=['GET'])
def get_count():
    count = get_image_process_count("image_process")
    return jsonify({"image_process_count": count})


@image_bp.route('/upload', methods=['POST'])
@sqlite_table_lock(lock_class="image_process", ttl_seconds=300, retry_interval=3.0, timeout=30, max_concurrent=2)
def upload_image():

########################################################################################################################
    ### 格式校驗 & 取參數
    file, error, status = validate_image(request.files)
    if error:
        return jsonify({"success": False, "error": error}), status

    detect_model = request.form.get("detect_model", ImageConst.MODEL_YOLO)
    transform_model = request.form.get("transform_model", ImageConst.MODEL_SD_IMAGE_VARIATIONS)
    print(f"detect_model: {detect_model}, transform_model: {transform_model}")


########################################################################################################################
    ### 檢查上傳圖是否有貓
    # 預設使用 yolo 需求較低
    try:
        # === 直接從全域單例工廠取得常駐記憶體的模型 ===
        try:
            d_model = DetectionModelFactory.get_model(detect_model)
        except ValueError as ve:
            traceback.print_exc()
            return jsonify({"error": str(ve)}), 400

        # === 開始跑預測 ===
        svcd = ImageDetectionService(model=d_model)
        tag_results, predict_list, result_np = svcd.make_detect_image(file)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    ### save user images with jpg
    # add md5 key
    file.seek(0) # reset image index
    data = file.read()
    md5 = hashlib.md5(data).hexdigest()

    # 產生時間戳記
    timestamp = datetime.now().strftime("%Y%m%d")

    # image 檔名
    ora_file_name = f"{timestamp}_{md5}_{file.filename}"

    ## 寫入原圖
    ora_dir = Path(common.config.get('image', "user_input_ora_path"))
    ora_path = ora_dir / ora_file_name
    ora_path.write_bytes(data)
    print(f'ora_path: {ora_path}')

    ## 寫入 detect image
    # ✅ imwrite 前確認 result_image 是合法的 numpy array
    if result_np is None or not isinstance(result_np, np.ndarray) or result_np.size == 0:
        raise ValueError("result_np 不合法，無法寫入檔案")

    # 直接對 result_image 原地修改，最後用 cv2 模組存檔
    # 將 RGB 轉回 BGR（OpenCV 預設色彩空間），再寫入輸出路徑
    detect_dir = Path(common.config.get('image', "user_input_detect_path"))
    detect_path = detect_dir / detect_model / ora_file_name
    cv2.imwrite(str(detect_path), cv2.cvtColor(result_np, cv2.COLOR_RGB2BGR))

    print(f'tag_results: {tag_results}, predict_list: {predict_list}, detect_path: {detect_path}')


########################################################################################################################
    # vector search similar image
    similar_path = ora_path
    print(f'similar_path:{similar_path}')


########################################################################################################################
    # style transform two images
    # 目前提供 1.sd_image_variations_transform, 2.stable_diffusion_transform
    # 預設使用 sd_image_variations_transform 硬體需求較低

    # 風格轉換
    try:
        # 取得 ref_image_path & transform_path
        ref_image_path =  Path(f'{common.config.get('image', "style_ref_img")}')
        transform_path = Path(f'{common.config.get('image', "transform_path")}')
        print(f'ref_image_path: {ref_image_path}, transform_path: {transform_path}')

        # === 直接從全域單例工廠取得常駐記憶體的模型 ===
        try:
            t_model = TransformModelFactory.get_model(transform_model)
        except ValueError as ve:
            traceback.print_exc()
            return jsonify({"error": str(ve)}), 400

        # === 開始跑預測 ===
        svct = ImageTransformService(model=t_model)
        origin_transform_image = svct.predict(ora_path, ref_image_path)
        similar_transform_image = ora_path


    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    # save image
    origin_transform_path = save_image_with_timestamp(
        image=origin_transform_image, save_transform_dir=transform_path / transform_model, file_name=ora_file_name
    )
    similar_transform_path = similar_transform_image

    print(f"origin_transform_path: {origin_transform_path}, similar_transform_path: {similar_transform_path}")


########################################################################################################################

# 組合 return data 字典
    response_data = {
        "success": True,
        # 偵測圖片參數
        "detector_image": f"{common.config.get('server', 'web_base_url')}/{detect_path.as_posix()}",
        "predict_list": predict_list,
        "tag_results": tag_results,
        # 向量搜尋參數
        "similar_image": f"{common.config.get('server', 'web_base_url')}/{similar_path.as_posix()}",
        # transform model 參數
        "origin_image_transform": f"{common.config.get('server', 'web_base_url')}/{origin_transform_path.as_posix()}",
        "similar_image_transform": f"{common.config.get('server', 'web_base_url')}/{similar_transform_path.as_posix()}",
    }

    # === 送出前 Print Log ===
    print("=== [Response Data] ===")
    print(response_data)

    return jsonify(response_data), 200

