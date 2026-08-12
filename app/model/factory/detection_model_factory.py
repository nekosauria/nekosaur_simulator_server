import logging
from pathlib import Path
from typing import Dict, override

from model.interface.base_detection_model import BaseDetectionModel
from model.impl.torch_detection_model import TorchDetectionModel
from model.impl.yolo_detection_model import YoloDetectionModel
from model.interface.base_model_factory import BaseModelFactory
from util.common import common
from util.device import get_gpu_device, log_device_memory
from util.step_timer import StepTimer

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

        timer = StepTimer()

        log_device_memory(
            gpu_device,
            component="detection_factory",
            stage="before_all_models",
            log_level=logging.INFO,
        )
########################################################################################################################
        # 預先載入 Torch 模型
        with timer.track("torch_load_cost"):
            torch_path = Path(f'{config.get('model', "maskrcnn_model")}')
            torch_model = TorchDetectionModel(
                model_path=torch_path,
                device=gpu_device
            )
            torch_model.load()
            cls._instances[torch_model.name] = torch_model
        logger.info(f"=== torch 模型載入完畢，耗時 {timer.costs['torch_load_cost']}s ===")

        log_device_memory(
            gpu_device,
            component=torch_model.name,
            stage="after_load",
            log_level=logging.INFO,
        )
########################################################################################################################
        # 預先載入 YOLO 模型
        with timer.track("yolo_load_cost"):
            yolo_path = Path(f'{config.get('model', "yolo11n")}')
            yolo_model = YoloDetectionModel(
                model_path=yolo_path,
                device=gpu_device
            )
            yolo_model.load()
            cls._instances[yolo_model.name] = yolo_model
        logger.info(f"=== yolo 模型載入完畢，耗時 {timer.costs['yolo_load_cost']}s ===")

        log_device_memory(
            gpu_device,
            component=yolo_model.name,
            stage="after_load",
            log_level=logging.INFO,
        )


        logger.info("=== 所有 Detection 模型載入完畢，準備就緒 ===")
        log_device_memory(
            gpu_device,
            component="detection_factory",
            stage="after_all_models",
            log_level=logging.INFO,
        )