from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np
from PIL.Image import Image


class BaseEmbeddingModel(ABC):

    @property
    @abstractmethod
    def model_path(self) -> Path:
        """取得模型路徑"""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """模型識別名稱"""
        ...

    @abstractmethod
    def load(self) -> None:
        """載入模型權重"""
        ...

    @abstractmethod
    def encode_image(self, image: Image) -> np.ndarray:
        """將單張圖片編碼為向量"""
        ...
