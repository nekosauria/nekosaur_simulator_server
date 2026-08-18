import atexit
import os
from http.client import HTTPException

from flask import Flask, jsonify
from flask_cors import CORS

from const.image_const import ImageConst
from route.image import image_bp
from model.factory.detection_model_factory import DetectionModelFactory
from model.factory.transform_model_factory import TransformModelFactory
from model.factory.embedding_model_factory import EmbeddingModelFactory
from util.common import common
from worker.fetch_thecatapi_consumer import fetch_thecatapi_consumer
from worker.image_daemon_process_consumer import image_daemon_process_consumer

config = common.config
logger = common.logger

CONSUMERS = [fetch_thecatapi_consumer,image_daemon_process_consumer]


def create_app():
    app = Flask(__name__)
    CORS(app)

    # 註冊 blueprint (routes)
    app.register_blueprint(image_bp)

    # ======================================================================================================================
    # === 全域例外處理 (Global Error Handlers) ===
    # ======================================================================================================================

    # 業務邏輯自訂驗證失敗 (400)
    @app.errorhandler(ValueError)
    def handle_value_error(e):
        logger.warning(f"Validation ValueError: {e}")
        return jsonify({"success": False, "error": str(e)}), 400

    # 捕獲所有 HTTP 規範內的 Client/Server 異常 (4xx, 5xx)
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        # 4xx 客戶端錯誤：僅記 warning 或 info，並回傳原生的 4xx code 與 message
        if e.code < 500:
            logger.info(f"HTTP Client Error [{e.code}]: {e.description}")
            return jsonify({"success": False, "error": e.description}), e.code

        # HTTP 5xx 錯誤仍記錄 ERROR Log
        logger.error(f"HTTP Server Error [{e.code}]: {e.description}", exc_info=True)
        return jsonify({"success": False, "error": e.description}), e.code

    # 捕獲未預期的非 HTTP Exception (Python Code Error -> 統一轉 500)
    @app.errorhandler(Exception)
    def handle_global_exception(e):
        logger.error(f"Unhandled Python Exception: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Internal Server Error"}), 500

    @app.route('/favicon.ico')
    def favicon():
        return '', 204

    @app.route("/", methods=["GET", "POST"])
    def index():
        return jsonify({"status": "Flask API Is Running", "message": "Hello World"})

    return app


def init_stage(app_root_path):
    # 資料夾檢查並建立所需資料夾
    dirs_to_create = [
        # api (thecatapi) path
        os.path.join(app_root_path, config.get('image', 'thecatapi_origin_path')),
        os.path.join(app_root_path, config.get('image', 'thecatapi_detect_path'), ImageConst.MODEL_TORCH),
        os.path.join(app_root_path, config.get('image', 'thecatapi_detect_path'), ImageConst.MODEL_YOLO),
        os.path.join(app_root_path, config.get('image', 'thecatapi_transform_path'), ImageConst.MODEL_STABLE_DIFFUSION),
        os.path.join(app_root_path, config.get('image', 'thecatapi_transform_path'), ImageConst.MODEL_SD_IMAGE_VARIATIONS),

        # user_upload path
        os.path.join(app_root_path, config.get('image', 'user_upload_origin_path')),
        os.path.join(app_root_path, config.get('image', 'user_upload_detect_path'), ImageConst.MODEL_TORCH),
        os.path.join(app_root_path, config.get('image', 'user_upload_detect_path'), ImageConst.MODEL_YOLO),
        os.path.join(app_root_path, config.get('image', 'user_upload_transform_path'), ImageConst.MODEL_STABLE_DIFFUSION),
        os.path.join(app_root_path, config.get('image', 'user_upload_transform_path'), ImageConst.MODEL_SD_IMAGE_VARIATIONS),

        # log path
        os.path.join(app_root_path, config.get('global', 'log_path'))
    ]

    for folder_path in dirs_to_create:
        os.makedirs(folder_path, exist_ok=True)
        logger.info(f"Directory checked/created: {folder_path}")


def model_stage(app_root_path):
    # 在 App 啟動時就把模型餵進記憶體
    logger.info(f"app.root_path: {app_root_path}")
    EmbeddingModelFactory.init_models(app_root_path)
    DetectionModelFactory.init_models(app_root_path)
    TransformModelFactory.init_models(app_root_path)

def consumer_stage():
    # 啟動 RabbitMQ consumer（背景 thread），須在 model_stage 之後執行
    # 確保 consumer 收到第一筆訊息時，embedding/detection/transform model 都已經 load 完成
    for consumer in CONSUMERS:
        consumer.start()
        logger.info(f"Consumer started: {consumer.queue_name}")

    # app 關閉時（正常退出 / SIGTERM）優雅停止所有 consumer
    atexit.register(lambda: [c.stop() for c in CONSUMERS])


if __name__ == '__main__':
    app = create_app()

    init_stage(app.root_path)
    model_stage(app.root_path)
    consumer_stage()

    app.run(debug=False, host=config.get('server', 'web_base_host'), port=config.get('server', 'web_base_port'))