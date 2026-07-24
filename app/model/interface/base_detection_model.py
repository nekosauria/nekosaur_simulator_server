from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from PIL.Image import Image

from dto.detection_result import DetectionResult

class BaseDetectionModel(ABC):


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

    @property
    @abstractmethod
    def labels(self) -> List[str]:
        """定義公開屬性：取得該模型所有的標籤清單"""
        ...

    @abstractmethod
    def load(self) -> None:
        """載入模型權重"""
        ...

    @abstractmethod
    def predict(self, image: Image) -> DetectionResult:
        """執行推論，回傳標準化結果"""
        ...
