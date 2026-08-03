import os

from flask import Flask
from flask_cors import CORS

from const.image_const import ImageConst
from route.image import image_bp
from model.factory.detection_model_factory import DetectionModelFactory
from model.factory.transform_model_factory import TransformModelFactory
from util.common import common

app = Flask(__name__)
CORS(app)

# 註冊 blueprint (routes)
app.register_blueprint(image_bp)
logger = common.logger

@app.route("/", methods=["GET", "POST"])
def index():
    # 前後端分離 , flask 只負責傳 backend jsonx
    return {"status": "Flask API Is Running" , "message": "Hello World"}

def init_stage():
    # 資料夾檢查並建立所需資料夾
    dirs_to_create = [
        # api (thecatapi) path
        os.path.join(app.root_path, common.config.get('api', 'thecatapi_ora_img_path')),
        os.path.join(app.root_path, common.config.get('api', 'thecatapi_transform_img_path'), ImageConst.MODEL_STABLE_DIFFUSION),
        os.path.join(app.root_path, common.config.get('api', 'thecatapi_transform_img_path'), ImageConst.MODEL_SD_IMAGE_VARIATIONS),

        # user_input path
        os.path.join(app.root_path, common.config.get('image', 'user_input_ora_path')),
        os.path.join(app.root_path, common.config.get('image', 'user_input_detect_path'), ImageConst.MODEL_TORCH),
        os.path.join(app.root_path, common.config.get('image', 'user_input_detect_path'), ImageConst.MODEL_YOLO),
        os.path.join(app.root_path, common.config.get('image', 'user_input_transform_path'), ImageConst.MODEL_STABLE_DIFFUSION),
        os.path.join(app.root_path, common.config.get('image', 'user_input_transform_path'), ImageConst.MODEL_SD_IMAGE_VARIATIONS),

        # log path
        os.path.join(app.root_path, common.config.get('global', 'log_path'))
    ]

    for folder_path in dirs_to_create:
        os.makedirs(folder_path, exist_ok=True)
        logger.info(f"Directory checked/created: {folder_path}")

    #在 App 啟動時就把模型餵進記憶體
    logger.info(f"app.root_path: {app.root_path}")
    DetectionModelFactory.init_models(app.root_path)
    TransformModelFactory.init_models(app.root_path)


if __name__ == '__main__':
    init_stage()
    app.run(debug=False, host=common.config.get('server', 'web_base_host'), port=common.config.get('server', 'web_base_port'))
