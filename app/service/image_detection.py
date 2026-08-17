import numpy as np

from dto.image_detection import DetectionResult, DetectionRequest
from dto.image_processor import SaveImageRequest
from model.interface.base_detection_model import BaseDetectionModel
from util.common import common
from util.image import check_file_exists
from util.image_draw import draw_detections

from service.image_processor import ImageProcessor as ImageProcessorService

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

        has_cat = "cat" in tag_results

        # 儲存偵測結果圖
        detect_image = PIL.Image.fromarray(predict_np)

        # return data
        logger.debug( f"tag_results: {tag_results}, predict_list: {predict_list}")

        return DetectionResult(
            detect_image=detect_image,
            tag_results=tag_results,
            predict_list=predict_list,
            has_cat= has_cat
        )


    @staticmethod
    def save_image_detection_metadata(image_detection_entity: ImageDetectionEntity) -> ImageDetectionEntity :
        image_detection_entity = ImageDetectionDao.insert(image_detection_entity)

        return image_detection_entity


    @staticmethod
    def get_image_detection_metadata_by_image_id(
            image_id: int,
            detect_model: str,
    ) -> ImageDetectionEntity | None:
        return ImageDetectionDao.get_image_detection_by_image_id(image_id, detect_model)

    @staticmethod
    def get_or_generate_detection(
            image_entity,
            req_image,
            detect_model: str,
            save_category: str,
            is_preprocessed: bool,
    ) -> ImageDetectionEntity:
        """
        檢查是否已有 detection 紀錄，有則直接回傳，
        沒有則產生一筆新的（推論 → 存檔 → 寫 DB）。

        :param save_category: 存檔分類，決定實體檔案存到哪個 category 目錄
                               （例如 "thecatapi_detect_path"、"user_upload_detect_path"）
        :param is_preprocessed: 新產生的這筆紀錄是否為「預處理」產生
                                （背景批次任務產出 = True；即時回應使用者請求產出 = False）
        """
        # === 檢查是否已有 detection 紀錄 ===
        existing_detection_entity = ImageDetection.get_image_detection_metadata_by_image_id(
            image_id=image_entity.id,
            detect_model=detect_model,
        )

        # 有紀錄時，使用 util 檢查實體檔案是否存在
        if existing_detection_entity is not None:
            if check_file_exists(str(existing_detection_entity.detect_path)):
                return existing_detection_entity

            # 實體檔案遺失，紀錄 error 並繼續往下執行重新推論與補檔
            logger.error(
                f"Detection metadata exists (ID: {existing_detection_entity.id}), "
                f"but physical file is missing at: {existing_detection_entity.detect_path}. Regenerating..."
            )

        # === 沒有紀錄或實體檔遺失，執行物件偵測模型推論 ===
        detect_res = ImageDetection.process_image_detection(
            DetectionRequest(
                req_image=req_image,
                detect_model=detect_model,
            )
        )

        # === 將標註框圖存檔（依 save_category 決定存放目錄）===
        detect_result = ImageProcessorService.save_image(SaveImageRequest(
            req_image=detect_res.detect_image,
            category=save_category,
            file_name=image_entity.file_name,
            sub_dir=detect_model,
            convert_jpg=True,
        ))

        # === 寫入 image_detection metadata，回傳新建立的 entity ===
        return ImageDetection.save_image_detection_metadata(
            ImageDetectionEntity(
                image_id=image_entity.id,
                md5_hash=detect_result.md5,
                detect_path=detect_result.path,
                detect_model=detect_model,
                predict_list=detect_res.predict_list,
                tag_results=detect_res.tag_results,
                has_cat=detect_res.has_cat,
                is_preprocessed=is_preprocessed,
            )
        )