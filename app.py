from flask import Flask
from flask_cors import CORS

from const.image_const import ImageConst
from route.image import image_bp
from model.factory.detection_model_factory import DetectionModelFactory
from model.factory.transform_model_factory import TransformModelFactory

app = Flask(__name__)
CORS(app)

# 註冊 blueprint (routes)
app.register_blueprint(image_bp)


@app.route("/", methods=["GET", "POST"])
def index():
    # 前後端分離 , flask 只負責傳 backend jsonx
    return {"status": "Flask API Is Running" , "message": "Hello World"}


def init_stage():
    #在 App 啟動時就把模型餵進記憶體
    print(f"app.root_path: {app.root_path}")
    DetectionModelFactory.init_models(app.root_path)
    TransformModelFactory.init_models(app.root_path)

if __name__ == '__main__':
    init_stage()
    app.run(debug=False, host=ImageConst.WEB_BASE_HOST, port=ImageConst.WEB_BASE_PORT)
