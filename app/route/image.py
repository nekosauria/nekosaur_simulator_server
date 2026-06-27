from aop.lock import sqlite_table_lock
from flask import Blueprint, request, jsonify, url_for
from service.sys_state import get_image_process_count
import time

from util.image import validate_image

image_bp = Blueprint("image", __name__)


@image_bp.route('/count', methods=['GET'])
def get_count():
    count = get_image_process_count("image_process")
    return jsonify({"image_process_count": count})


@image_bp.route('/upload', methods=['POST'])
@sqlite_table_lock(lock_class="image_process", ttl_seconds=300, retry_interval=3.0, timeout=30, max_concurrent=2)
def upload_image():

    # 格式校驗
    # 格式校驗
    file, error, status = validate_image(request.files)
    if error:
        return jsonify({"success": False, "error": error}), status

    detect_model = request.form.get("detect_model", "yolo")
    transform_model = request.form.get("transform_model", "sd_image_variations_transform")

    print(detect_model, transform_model)

    # 檢查上傳圖是否有貓

    # save user images with jpg

    # vector search similar image
    time.sleep(5)

    # style transform two images
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

