import traceback

from aop.lock import sqlite_table_lock
from flask import Blueprint, request, jsonify, url_for
from service.sys_state import get_image_process_count

from util.image import validate_image
from const.image_const import ImageConst
from service.image_detection_service import ImageDetectionService
from service.image_transform_service import ImageTransformService
from model.factory.detection_model_factory import DetectionModelFactory
from model.factory.transform_model_factory import TransformModelFactory
from util.common import common

image_bp = Blueprint("image", __name__)


@image_bp.route('/count', methods=['GET'])
def get_count():
    count = get_image_process_count("image_process")
    return jsonify({"image_process_count": count})


@image_bp.route('/upload', methods=['POST'])
@sqlite_table_lock(lock_class="image_process", ttl_seconds=300, retry_interval=3.0, timeout=30, max_concurrent=2)
def upload_image():

########################################################################################################################
    # 格式校驗 & 取參數
    file, error, status = validate_image(request.files)
    if error:
        return jsonify({"success": False, "error": error}), status


    detect_model = request.form.get("detect_model", ImageConst.MODEL_YOLO)
    transform_model = request.form.get("transform_model", ImageConst.MODEL_SD_IMAGE_VARIATIONS)
    print(f"detect_model: {detect_model}, transform_model: {transform_model}")


########################################################################################################################
    # 檢查上傳圖是否有貓
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
        tag_results, predict_list, ora_img, detect_img = svcd.make_detect_image(file, detect_model)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


########################################################################################################################
    # save user images with jpg
    # time.sleep(5)


########################################################################################################################
    # vector search similar image
    # time.sleep(5)


########################################################################################################################
    # style transform two images
    # 目前提供 1.sd_image_variations_transform, 2.stable_diffusion_transform
    # 預設使用 sd_image_variations_transform 硬體需求較低

    try:
        # 取得 ref_image_path & output_dir
        init_image_path =  common.config.get('model', "user_ora_img")
        ref_image_path =  common.config.get('model', "style_ref_img")
        output_dir = common.config.get('model', "user_out_img_path")

        # === 直接從全域單例工廠取得常駐記憶體的模型 ===
        try:
            t_model = TransformModelFactory.get_model(transform_model)
        except ValueError as ve:
            traceback.print_exc()
            return jsonify({"error": str(ve)}), 400

        # === 開始跑預測 ===
        svct = ImageTransformService(model=t_model)
        origin_image_transform = svct.predict(init_image_path, ref_image_path, output_dir)
        similar_image_transform = origin_image_transform

        print(f"origin_image_transform: {origin_image_transform}, similar_image_transform: {similar_image_transform}")

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


        ########################################################################################################################
    # return data
    return jsonify({
        "success": True,
        "detector_image": url_for(
            'static',
            filename=f'images/user_input/detect/orange_cat.png',
            _external=True
        ),
        "similar_image": url_for(
            'static',
            filename=f'images/thecatapi/ora/9c2e9a67525fd5e01bee60516b653d3a_clh.jpg',
            _external=True
        ),
        "origin_image_transform": url_for(
            'static',
            filename=f'images/user_input/output/sd_image_variations_20260526_152735.png',
            _external=True
        ),
        "similar_image_transform": url_for(
            'static',
            filename=f'images/thecatapi/output/sd_image_variations_20260627_194647.png',
            _external=True
        ),
    }), 200

