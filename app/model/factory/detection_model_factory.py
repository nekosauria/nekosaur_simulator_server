from pathlib import Path
from time import perf_counter
from typing import Dict, override

from const.image_const import ImageConst
from model.interface.base_detection_model import BaseDetectionModel
from model.impl.torch_detection_model import TorchDetectionModel
from model.impl.yolo_detection_model import YoloDetectionModel
from model.interface.base_model_factory import BaseModelFactory
from util.common import common
from util.device import get_gpu_device

logger = common.logger


class DetectionModelFactory(BaseModelFactory[BaseDetectionModel]):
    """全域模型工廠（單例模式），確保每種模型在記憶體中只會被加載一次"""
    _instances: Dict[str, BaseDetectionModel] = {}

    @override
    @classmethod
    def init_models(cls, root_path: str):
        """在 Flask App 啟動時，由全域呼叫此函式進行『冷啟動』加載"""
        logger.info("=== 初始化全域 Detection 模型常駐記憶體 ===")
        config = common.config
        # 自動辨識最佳硬體
        gpu_device = get_gpu_device()


########################################################################################################################
        # 預先載入 Torch 模型
        torch_start = perf_counter()
        torch_path = Path(f'{config.get('model', "maskrcnn_model")}')
        torch_model = TorchDetectionModel(
            model_path=torch_path,
            score_threshold=ImageConst.SCORE_THRESHOLD,
            device=gpu_device
        )
        torch_model.load()
        cls._instances[ImageConst.MODEL_TORCH] = torch_model
        torch_cost = round(perf_counter() - torch_start, 3)
        logger.info(f"=== torch 模型載入完畢，耗時 {torch_cost}s ===")


########################################################################################################################
        # 預先載入 YOLO 模型
        yolo_start = perf_counter()
        yolo_path = Path(f'{config.get('model', "yolo11n")}')
        yolo_model = YoloDetectionModel(
            model_path=yolo_path,
            score_threshold=ImageConst.SCORE_THRESHOLD,
            device=gpu_device
        )
        yolo_model.load()
        cls._instances[ImageConst.MODEL_YOLO] = yolo_model
        yolo_cost = round(perf_counter() - yolo_start, 3)
        logger.info(f"=== yolo 模型載入完畢，耗時 {yolo_cost}s ===")


        logger.info("=== 所有 Detection 模型載入完畢，準備就緒 ===")
