from pathlib import Path
from typing import Dict

from const.image_const import ImageConst
from model.interface.base_transform_model import BaseTransformModel
from model.impl.stable_diffusion_transform_model import StableDiffusionTransformModel
from model.impl.sd_image_variations_transform_model import SDImageVariationsTransformModel
from util.device import get_linux_device

class TransformModelFactory:
    """全域模型工廠（單例模式），確保每種 transform 模型在記憶體中只會被加載一次"""
    _instances: Dict[str, BaseTransformModel] = {}

    @classmethod
    def init_models(cls, root_path: str):
        print("=== 初始化全域 Transform 模型常駐記憶體 ===")

        gpu_device = get_linux_device()

        sd_model = StableDiffusionTransformModel(
            model_path=Path(root_path) / "resource/model/transform/stable-diffusion-v1-5",
            ip_adapter_model_path=Path(root_path) / "resource/model/transform/IP-Adapter",
            device=gpu_device
        )
        sd_model.load()
        cls._instances[ImageConst.MODEL_STABLE_DIFFUSION] = sd_model
        print("=== stable_diffusion_transform 模型載入完畢 ===")

        sdv_model = SDImageVariationsTransformModel(
            model_path=Path(root_path) / "resource/model/transform/sd-image-variations-diffusers",
            device=gpu_device
        )
        sdv_model.load()
        cls._instances[ImageConst.MODEL_SD_IMAGE_VARIATIONS] = sdv_model
        print("=== sd_image_variations_transform 模型載入完畢 ===")

        print("=== 所有 Transform 模型載入完畢，準備就緒 ===")

    @classmethod
    def get_model(cls, model_type: str) -> BaseTransformModel:
        model = cls._instances.get(model_type)
        if model is None:
            raise ValueError(f"Unknown model type or model not initialized: {model_type}")
        return model