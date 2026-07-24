import hashlib
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from const.image_const import ImageConst
from model.interface.base_detection_model import BaseDetectionModel
from util.image_draw import get_color_by_label, make_line, draw_lines, draw_texts, draw_detections


class ImageDetectionService:

    def __init__(self, model: BaseDetectionModel):
        self._model = model

    def make_detect_image(self, file, model_type) -> tuple[dict, dict, str, str]:
        """
        接收前端上傳的檔案物件，儲存原始圖片後執行物件偵測，
        並將偵測結果（框線 + 標籤）繪製後存檔。

        Args:
            file: 前端上傳的檔案物件（需支援 .read() 與 .filename）
            model_type: 前端選擇的模型類型

        Returns:
                - tag_results (dict): 各標籤對應的信心分數
                - ora_img (str): 原圖片的網址
                - detect_img (str): 偵測結果圖片的網址
        """

        # add md5 key
        data = file.read()
        md5 = hashlib.md5(data).hexdigest()
        input_path  = Path(f"static/images/user_input/ora/{md5}_{file.filename}")
        output_path = Path(f"static/images/user_input/detect/{md5}_{model_type}_{file.filename}")

        # 寫入原圖
        input_path.write_bytes(data)
        ora_img = f"{ImageConst.WEB_BASE_URL}/static/images/user_input/ora/{input_path.name}"

        # init var
        labels = self._model.labels
        print(f"labels: {labels}")

        image = Image.open(input_path)
        result_image = np.array(image.copy())  # 複製原圖作為繪圖畫布（RGB numpy array）

        # -----------------------------------------------------------
        # 執行推論，取第一張圖片的結果（回傳格式：list of dict）
        output = self._model.predict(image)  # ← 統一介面，與模型實作無關
        # -----------------------------------------------------------

        # 畫物件偵測框線
        tag_results, predict_list, result_image = draw_detections(
            output, labels, result_image, ImageConst.SCORE_THRESHOLD
        )

        # ✅ imwrite 前確認 result_image 是合法的 numpy array
        if result_image is None or not isinstance(result_image, np.ndarray) or result_image.size == 0:
            raise ValueError("result_image 不合法，無法寫入檔案")

        # 直接對 result_image 原地修改，最後用 cv2 模組存檔
        # 將 RGB 轉回 BGR（OpenCV 預設色彩空間），再寫入輸出路徑
        cv2.imwrite(str(output_path), cv2.cvtColor(result_image, cv2.COLOR_RGB2BGR))

        # return data
        detect_img = f"{ImageConst.WEB_BASE_URL}/static/images/user_input/detect/{output_path.name}"
        print(tag_results, predict_list, ora_img, detect_img)

        return tag_results, predict_list, ora_img, detect_img