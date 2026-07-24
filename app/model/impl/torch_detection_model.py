from pathlib import Path
from typing import List, override

import torch
import torchvision
from PIL.Image import Image

from const.image_const import ImageConst
from dto.detection_result import DetectionResult
from model.interface.base_detection_model import BaseDetectionModel


class TorchDetectionModel(BaseDetectionModel):
    def __init__(self, model_path: Path, score_threshold: float = 0.5, device: str = "cpu"):
        self._model_path = model_path
        self.device = device
        self._model = None
        self._score_threshold = score_threshold
        self._labels = ImageConst.TORCH_LABELS

    @override
    @property
    def model_path(self) -> Path:
        return self._model_path

    @override
    @property
    def name(self) -> str:
        return "torchvision.models.detection.maskrcnn_resnet50_fpn"

    @override
    @property
    def labels(self) -> List[str]:
        return self._labels

    @override
    def load(self) -> None:
        print(f"loading model from {self.model_path}, device: {self.device}")
        raw = torch.load(self.model_path, weights_only=False)
        print(type(raw))  # 看這裡
        self._model = raw.to(self.device)
        self._model.eval()

    @override
    def predict(self, image: Image) -> DetectionResult:
        if self._model is None:
            raise RuntimeError("模型尚未載入，請先呼叫 load()")

        image_tensor = torchvision.transforms.functional.to_tensor(image).to(self.device)
        """
        將 PIL Image 轉成 PyTorch 張量
        PyTorch Tensor (以此例來說)
        shape = [C,H,W]
        dtype = float32

        value = 0~1
        R = 255 / 255 = 1.0
        G = 128 / 255 ≈ 0.502
        B = 64 / 255 ≈ 0.251

        """

        """
        以 4 pixel 圖為例

        [R, G, B]
        紅色 = [255, 0, 0]
        綠色 = [0, 255, 0]
        藍色 = [0, 0, 255]
        白色 = [255, 255, 255]


        像素值（HWC 格式）： [
            [[255, 0, 0], [0, 255, 0]],
            [[0, 0, 255], [255, 255, 255]]
        ]
        等同於 tensor（CHW 格式) ： ([
            [
                [1.0, 0.0],
                [0.0, 1.0]
            ],

            [
                [0.0, 1.0],
                [0.0, 1.0]
            ],

            [
                [0.0, 0.0],
                [1.0, 1.0]
            ]
        ])

        CHW = Channel × Height × Width
        C = Channel（顏色通道，RGB 就是 3）
        H = Height（圖片高度，幾個像素）
        W = Width（圖片寬度，幾個像素）
        """

        output = self._model([image_tensor])[0]
        boxes, labels, scores = [], [], []
        # 每個 label 若有重複取分數最高
        best = {}  # label_str -> (box, label_idx, score)

        # 將輸出的 tensors 整個拉回 CPU 記憶體並轉成 numpy/list，
        # 這樣在後面的 Python 迴圈與型別轉換（int, float）速度最快且絕對不會跨裝置報錯。
        out_boxes = output["boxes"].cpu().detach().numpy()
        out_labels = output["labels"].cpu().detach().tolist()
        out_scores = output["scores"].cpu().detach().tolist()

        for box, label, score in zip(out_boxes, out_labels, out_scores):
            label_str = self._labels[int(label)]
            score_f = round(float(score), 4)
            if label_str not in best or score_f > best[label_str][2]:
                best[label_str] = (box, int(label), score_f)

        for box, label_idx, score in best.values():
            boxes.append((int(box[0]), int(box[1]), int(box[2]), int(box[3])))
            labels.append(label_idx)
            scores.append(score)

        return DetectionResult(boxes=boxes, labels=labels, scores=scores)