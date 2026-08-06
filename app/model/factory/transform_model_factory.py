from pathlib import Path
from time import perf_counter
from typing import Dict, override

from const.image_const import ImageConst
from model.interface.base_model_factory import BaseModelFactory
from model.interface.base_transform_model import BaseTransformModel
from model.impl.stable_diffusion_transform_model import StableDiffusionTransformModel
from model.impl.sd_image_variations_transform_model import SDImageVariationsTransformModel
from util.common import common
from util.device import get_gpu_device, get_gpu_dtype

logger = common.logger

class TransformModelFactory(BaseModelFactory[BaseTransformModel]):
    """全域模型工廠（單例模式），確保每種 tra`nsform 模型在記憶體中只會被加載一次"""
    _instances: Dict[str, BaseTransformModel] = {}

    @override
    @classmethod
    def init_models(cls, root_path: str):
        logger.info("=== 初始化全域 Transform 模型常駐記憶體 ===")
        config = common.config
        gpu_device = get_gpu_device()
        gpu_dtype = get_gpu_dtype()


########################################################################################################################
        # 預先載入 StableDiffusionTransformModel 模型
        stable_diffusion_transform_start = perf_counter()
        sd_model = StableDiffusionTransformModel(
            model_path=Path(config.get('model', "stable_diffusion_model_path")),
            ip_adapter_model_path=Path(f'{config.get('model', "ip_adapter_model_path")}'),
            device=gpu_device,
            dtype=gpu_dtype,
        )
        sd_model.load()
        cls._instances[sd_model.name] = sd_model
        stable_diffusion_transform_cost = round(perf_counter() - stable_diffusion_transform_start, 3)
        logger.info(f"=== stable_diffusion_transform 模型載入完畢，耗時 {stable_diffusion_transform_cost}s ===")


########################################################################################################################
        # 預先載入 SDImageVariationsTransformModel 模型
        sd_image_variations_transform_start = perf_counter()
        sdv_model = SDImageVariationsTransformModel(
            model_path=Path(f'{config.get('model', "sd_image_variations_model_path")}'),
            device=gpu_device,
            dtype=gpu_dtype,
        )
        sdv_model.load()
        cls._instances[sdv_model.name] = sdv_model
        sd_image_variations_transform_start_cost = round(perf_counter() - sd_image_variations_transform_start, 3)
        logger.info(f"=== sd_image_variations_transform 模型載入完畢，耗時 {sd_image_variations_transform_start_cost}s ===")


        logger.info("=== 所有 Transform 模型載入完畢，準備就緒 ===")

