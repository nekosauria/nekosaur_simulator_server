import logging
from pathlib import Path
from typing import Dict, override

from model.impl.clip_embedding_model import ClipEmbeddingModel
from model.interface.base_embedding_model import BaseEmbeddingModel
from model.interface.base_model_factory import BaseModelFactory
from util.common import common
from util.device import get_gpu_device, log_device_memory
from util.step_timer import StepTimer

logger = common.logger


class EmbeddingModelFactory(BaseModelFactory[BaseEmbeddingModel]):
    """全域模型工廠（單例模式），確保每種模型在記憶體中只會被加載一次"""
    _instances: Dict[str, BaseEmbeddingModel] = {}

    @override
    @classmethod
    def init_models(cls, root_path: str):
        """在 Flask App 啟動時，由全域呼叫此函式進行『冷啟動』加載"""
        logger.info("=== 初始化全域 Embedding 模型常駐記憶體 ===")
        config = common.config
        # 自動辨識最佳硬體
        gpu_device = get_gpu_device()

        timer = StepTimer()

        log_device_memory(
            gpu_device,
            component="embedding_factory",
            stage="before_all_models",
            log_level=logging.INFO,
        )
########################################################################################################################
        # 預先載入 CLIP 模型
        with timer.track("clip_load_cost"):
            clip_path = Path(f'{config.get('model', "clip_vit_b_32_model_path")}')
            clip_model = ClipEmbeddingModel(
                model_path=clip_path,
                device=gpu_device
            )
            clip_model.load()
            cls._instances[clip_model.name] = clip_model
        logger.info(f"=== clip 模型載入完畢，耗時 {timer.costs['clip_load_cost']}s ===")

        log_device_memory(
            gpu_device,
            component=clip_model.name,
            stage="after_load",
            log_level=logging.INFO,
        )


        logger.info("=== 所有 Embedding 模型載入完畢，準備就緒 ===")
        log_device_memory(
            gpu_device,
            component="embedding_factory",
            stage="after_all_models",
            log_level=logging.INFO,
        )