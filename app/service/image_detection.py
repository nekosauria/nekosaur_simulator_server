import numpy as np

from dto.image_detection import DetectionResult, DetectionRequest
from model.interface.base_detection_model import BaseDetectionModel
from util.common import common
from util.image_draw import draw_detections

from dao.image_detection import ImageDetection as ImageDetectionDao
from entity.image_detection import ImageDetection as ImageDetectionEntity

import PIL.Image

from model.factory.detection_model_factory import DetectionModelFactory

config = common.config
logger = common.logger


class ImageDetectionModel:

    def __init__(self, model: BaseDetectionModel):
        self._model = model

    def start_predict(self, req_image: PIL.Image.Image) -> tuple[np.ndarray, dict, dict]:
        """
        接收前端上傳的檔案物件，儲存原始圖片後執行物件偵測，
        並將偵測結果（框線 + 標籤）繪製後存檔。

        Args:
            req_image: 前端上傳的檔案物件（需支援 .read() 與 .filename）

        Returns:
                - predict_np (np.ndarray): 偵測結果圖片的網址
                - tag_results (dict): 預測分數的信心分數
                - predict_list (dict): 各標籤對應的信心分數
        """

        # init var
        labels = self._model.labels
        logger.debug(f"labels: {labels}")

        # 確保進模型推論的圖片是 3 channel RGB（避免 RGBA/灰階圖片造成 tensor 維度不符）
        req_image = req_image.convert("RGB")

        req_np = np.array(req_image.copy())  # 複製原圖作為繪圖畫布（RGB numpy array）

        # -----------------------------------------------------------
        # 執行推論，取第一張圖片的結果（回傳格式：list of dict）
        output = self._model.predict(req_image)  # ← 統一介面，與模型實作無關
        # -----------------------------------------------------------

        # 畫物件偵測框線
        predict_np, tag_results, predict_list = draw_detections(
            req_np, output, labels
        )

        return  predict_np, tag_results, predict_list


class ImageDetection:
    @staticmethod
    def process_image_detection(req: DetectionRequest) -> DetectionResult:
        """處理圖片物件偵測與儲存流程。"""
        """純粹跑模型偵測，不碰檔案 I/O。"""

        # 取得模型
        d_model = DetectionModelFactory.get_model(req.detect_model)
        svcd = ImageDetectionModel(model=d_model)

        # 開始跑預測
        predict_np, tag_results, predict_list = svcd.start_predict(req.req_image)

        if predict_np is None or not isinstance(predict_np, np.ndarray) or predict_np.size == 0:
            raise ValueError("predict_np 不合法，無法寫入檔案")

        # 儲存偵測結果圖
        detect_image = PIL.Image.fromarray(predict_np)

        # return data
        logger.debug( f"tag_results: {tag_results}, predict_list: {predict_list}")

        return DetectionResult(
            detect_image=detect_image,
            tag_results=tag_results,
            predict_list=predict_list,
        )


    @staticmethod
    def save_image_detection_metadata(image_detection_entity: ImageDetectionEntity) -> ImageDetectionEntity :
        image_detection_entity = ImageDetectionDao.insert(image_detection_entity)

        return image_detection_entity