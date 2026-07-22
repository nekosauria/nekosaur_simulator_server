from pathlib import Path
from typing import Dict

from const.image_const import ImageConst
from model.interface.base_detection_model import BaseDetectionModel
from model.impl.torch_detection_model import TorchDetectionModel
from model.impl.yolo_detection_model import YoloDetectionModel
from util.device import get_linux_device

class DetectionModelFactory:
    """全域模型工廠（單例模式），確保每種模型在記憶體中只會被加載一次"""
    _instances: Dict[str, BaseDetectionModel] = {}

    @classmethod
    def init_models(cls, root_path: str):
        """在 Flask App 啟動時，由全域呼叫此函式進行『冷啟動』加載"""
        print("=== 初始化全域模型常駐記憶體 ===")

        # 自動辨識 Linux 最佳硬體
        gpu_device = get_linux_device()

        # 預先載入 Torch 模型
        torch_path = Path(root_path) / "resource/model/detect" / "maskrcnn_model.pt"
        torch_model = TorchDetectionModel(
            model_path=torch_path,
            score_threshold=ImageConst.SCORE_THRESHOLD,
            device=gpu_device
        )
        torch_model.load()  # 確保這裡執行了真正的 .load()
        cls._instances[ImageConst.MODEL_TORCH] = torch_model
        print("=== torch 模型載入完畢 ===")

        # 預先載入 YOLO 模型
        yolo_path = Path(root_path) / "resource/model/detect" / "yolo11n.pt"
        yolo_model = YoloDetectionModel(
            model_path=yolo_path,
            score_threshold=ImageConst.SCORE_THRESHOLD,
            device=gpu_device
        )
        yolo_model.load()  # 確保這裡執行了真正的 .load()
        cls._instances[ImageConst.MODEL_YOLO] = yolo_model
        print("=== yolo 模型載入完畢 ===")

        print("=== 所有 Detection 模型載入完畢，準備就緒 ===")

    @classmethod
    def get_model(cls, model_type: str) -> BaseDetectionModel:
        """API 路由呼叫這個方法，直接從記憶體拿，不讀寫硬碟"""
        model = cls._instances.get(model_type)
        if model is None:
            raise ValueError(f"Unknown model type or model not initialized: {model_type}")
        return model