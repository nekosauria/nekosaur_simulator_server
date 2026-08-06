import numpy as np

from const.image_const import ImageConst
from dto.image_detection import DetectionResult, DetectionRequest
from dto.image_processor import SaveImageRequest
from model.interface.base_detection_model import BaseDetectionModel
from service.image_processor import ImageProcessor
from util.common import common
from util.image_draw import draw_detections

import time
import PIL.Image

from model.factory.detection_model_factory import DetectionModelFactory

config = common.config
logger = common.logger


class ImageDetection:

    def __init__(self, model: BaseDetectionModel):
        self._model = model


    def _make_detect_image(self, req_image) -> tuple[dict, dict, np.ndarray]:
        """
        接收前端上傳的檔案物件，儲存原始圖片後執行物件偵測，
        並將偵測結果（框線 + 標籤）繪製後存檔。

        Args:
            file: 前端上傳的檔案物件（需支援 .read() 與 .filename）

        Returns:
                - tag_results (dict): 預測分數的信心分數
                - predict_list (dict): 各標籤對應的信心分數
                - predict_np (np.ndarray): 偵測結果圖片的網址
        """

        # init var
        labels = self._model.labels
        logger.debug(f"labels: {labels}")

        ora_np = np.array(req_image.copy())  # 複製原圖作為繪圖畫布（RGB numpy array）

        # -----------------------------------------------------------
        # 執行推論，取第一張圖片的結果（回傳格式：list of dict）
        output = self._model.predict(req_image)  # ← 統一介面，與模型實作無關
        # -----------------------------------------------------------

        # 畫物件偵測框線
        tag_results, predict_list, predict_np = draw_detections(
            output, labels, ora_np, ImageConst.SCORE_THRESHOLD
        )

        return tag_results, predict_list, predict_np


    @staticmethod
    def make_detect_image(req: DetectionRequest) -> tuple[dict, dict, np.ndarray]:
        """純粹跑模型偵測，不碰檔案 I/O。"""
        d_model = DetectionModelFactory.get_model(req.detect_model)
        svcd = ImageDetection(model=d_model)
        tag_results, predict_list, predict_np = svcd._make_detect_image(req.req_image)

        if predict_np is None or not isinstance(predict_np, np.ndarray) or predict_np.size == 0:
            raise ValueError("predict_np 不合法，無法寫入檔案")

        return tag_results, predict_list, predict_np


    @staticmethod
    def process_image_detection(req: DetectionRequest) -> DetectionResult:
        """處理圖片物件偵測與儲存流程。"""
        detector_image_start = time.perf_counter()

        # 跑模型偵測
        tag_results, predict_list, predict_np = ImageDetection.make_detect_image(req)

        # 儲存偵測結果圖
        detect_image = PIL.Image.fromarray(predict_np)
        detect_result = ImageProcessor.save_image(SaveImageRequest(
            req_image=detect_image,
            category=req.category,
            file_name=req.file_name,
            sub_dir=req.detect_model,
            convert_jpg=True
        ))

        logger.debug(
            f"tag_results: {tag_results}, predict_list: {predict_list}, "
            f"detect_path: {detect_result.path}, detect_md5: {detect_result.md5}"
        )
        detector_image_cost = round(time.perf_counter() - detector_image_start, 3)


        return DetectionResult(
            tag_results=tag_results,
            predict_list=predict_list,
            detect_path=detect_result.path,
            detect_md5=detect_result.md5,
            detect_cost=detector_image_cost
        )