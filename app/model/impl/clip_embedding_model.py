from pathlib import Path
from typing import override, Union

import numpy as np
from PIL.Image import Image
from sentence_transformers import SentenceTransformer

from const.image_const import ImageConst
from model.interface.base_embedding_model import BaseEmbeddingModel
from util.common import common

logger = common.logger


class ClipEmbeddingModel(BaseEmbeddingModel):
    def __init__(
            self,
            model_path: Path,
            device: str = "cpu"
    ):
        self._model_path = model_path
        self.device = device
        self._model: SentenceTransformer | None = None

    @override
    @property
    def model_path(self) -> Path:
        return self._model_path

    @override
    @property
    def name(self) -> str:
        return ImageConst.MODEL_CLIP_VIT_B_32

    @override
    def load(self) -> None:
        # SentenceTransformer 第一參數可直接吃本機資料夾路徑，
        # 不會走 Hugging Face Hub 下載，前提是該路徑底下已是完整的
        # sentence-transformers 格式模型檔（config.json / modules.json 等）
        self._model = SentenceTransformer(str(self._model_path), device=self.device)

    @override
    def encode_image(self, image: Image) -> np.ndarray:
        return self._model.encode(image)
