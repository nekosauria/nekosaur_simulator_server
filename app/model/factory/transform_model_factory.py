from pathlib import Path
from typing import Dict, override

from const.image_const import ImageConst
from model.interface.base_model_factory import BaseModelFactory
from model.interface.base_transform_model import BaseTransformModel
from model.impl.stable_diffusion_transform_model import StableDiffusionTransformModel
from model.impl.sd_image_variations_transform_model import SDImageVariationsTransformModel
from util.common import common
from util.device import get_gpu_device

logger = common.logger

class TransformModelFactory(BaseModelFactory[BaseTransformModel]):
    """全域模型工廠（單例模式），確保每種 transform 模型在記憶體中只會被加載一次"""
    _instances: Dict[str, BaseTransformModel] = {}

    @override
    @classmethod
    def init_models(cls, root_path: str):
        logger.info("=== 初始化全域 Transform 模型常駐記憶體 ===")
        config = common.config
        gpu_device = get_gpu_device()


########################################################################################################################
        # 預先載入 StableDiffusionTransformModel 模型
        sd_model = StableDiffusionTransformModel(
            model_path=Path(config.get('model', "stable_diffusion_model_path")),
            ip_adapter_model_path=Path(f'{config.get('model', "ip_adapter_model_path")}'),
            device=gpu_device
        )
        sd_model.load()
        cls._instances[ImageConst.MODEL_STABLE_DIFFUSION] = sd_model
        logger.info("=== stable_diffusion_transform 模型載入完畢 ===")


########################################################################################################################
        # 預先載入 SDImageVariationsTransformModel 模型
        sdv_model = SDImageVariationsTransformModel(
            model_path=Path(f'{config.get('model', "sd_image_variations_model_path")}'),
            device=gpu_device
        )
        sdv_model.load()
        cls._instances[ImageConst.MODEL_SD_IMAGE_VARIATIONS] = sdv_model
        logger.info("=== sd_image_variations_transform 模型載入完畢 ===")


        logger.info("=== 所有 Transform 模型載入完畢，準備就緒 ===")

