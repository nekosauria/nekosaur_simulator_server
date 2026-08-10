from pathlib import Path
from typing import List, override

from PIL.Image import Image
from ultralytics import YOLO

from const.image_const import ImageConst
from dto.image_detection import ModelPrediction
from model.interface.base_detection_model import BaseDetectionModel
from util.common import common

logger = common.logger

class YoloDetectionModel(BaseDetectionModel):
    """YOLO 系列模型（ultralytics）"""

    def __init__(self, model_path: Path, device: str = "cpu"):
        self._model_path = model_path
        self.device = device
        self._model = None
        self._labels = ImageConst.YOLO_LABELS

    @override
    @property
    def model_path(self) -> Path:
        return self._model_path

    @override
    @property
    def name(self) -> str:
        return ImageConst.MODEL_YOLO

    @override
    @property
    def labels(self) -> List[str]:
        return self._labels

    @override
    def load(self) -> None:
        logger.info(f"loading model from {self.model_path}, device: {self.device}")
        self._model = YOLO(str(self.model_path)).to(self.device)

    @override
    def predict(self, image: Image) -> ModelPrediction:
        if self._model is None:
            raise RuntimeError("模型尚未載入，請先呼叫 load()")

        output = self._model(image, verbose=False, device=self.device)[0]
        boxes, labels, scores = [], [], []
        # 每個 label 若有重複取分數最高
        best = {}  # label_str -> (box, label_idx, score)

        # 把 output.boxes 移到 cpu() 再進行迴圈讀取，防止跨裝置資料存取卡頓或報錯
        for box in output.boxes.cpu():
            label_str = output.names[int(box.cls[0])]
            label_idx = self._labels.index(label_str) if label_str in self._labels else -1

            if label_idx == -1:
                continue

            score = round(float(box.conf[0]), 3)
            if label_str not in best or score > best[label_str][2]:
                best[label_str] = (box, label_idx, score)

        for box, label_idx, score in best.values():
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            boxes.append((int(x1), int(y1), int(x2), int(y2)))
            labels.append(label_idx)
            scores.append(score)

        return ModelPrediction(boxes=boxes, labels=labels, scores=scores)