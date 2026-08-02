from abc import ABC, abstractmethod
from pathlib import Path

from PIL import Image

class BaseTransformModel(ABC):

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
        """啟動時載入模型至記憶體/GPU，只執行一次"""
        ...

    @abstractmethod
    def generate(self, *args, **kwargs) -> Image.Image:
        """執行單次生成，回傳輸出圖片路徑"""
        ...