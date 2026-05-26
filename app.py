from flask import Flask
from flask_cors import CORS
from route.image import image_bp

app = Flask(__name__)
CORS(app)

# 註冊 blueprint (routes)
app.register_blueprint(image_bp)


@app.route("/", methods=["GET", "POST"])
def index():
    # 前後端分離 , flask 只負責傳 backend jsonx
    return {"status": "Flask API Is Running" , "message": "Hello World"}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
