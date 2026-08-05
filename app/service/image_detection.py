import numpy as np
from PIL import Image

from const.image_const import ImageConst
from model.interface.base_detection_model import BaseDetectionModel
from util.common import common
from util.image_draw import draw_detections

logger = common.logger


class ImageDetection:

    def __init__(self, model: BaseDetectionModel):
        self._model = model

    def make_detect_image(self, file) -> tuple[dict, dict, np.ndarray]:
        """
        接收前端上傳的檔案物件，儲存原始圖片後執行物件偵測，
        並將偵測結果（框線 + 標籤）繪製後存檔。

        Args:
            file: 前端上傳的檔案物件（需支援 .read() 與 .filename）

        Returns:
                - tag_results (dict): 預測分數的信心分數
                - predict_list (dict): 各標籤對應的信心分數
                - result_np (np.ndarray): 偵測結果圖片的網址
        """

        # init var
        labels = self._model.labels
        logger.debug(f"labels: {labels}")

        ora_image = Image.open(file)
        ora_np = np.array(ora_image.copy())  # 複製原圖作為繪圖畫布（RGB numpy array）

        # -----------------------------------------------------------
        # 執行推論，取第一張圖片的結果（回傳格式：list of dict）
        output = self._model.predict(ora_image)  # ← 統一介面，與模型實作無關
        # -----------------------------------------------------------

        # 畫物件偵測框線
        tag_results, predict_list, result_np = draw_detections(
            output, labels, ora_np, ImageConst.SCORE_THRESHOLD
        )

        return tag_results, predict_list, result_np