from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image


@dataclass
class SaveImageRequest:
    req_image: Image.Image | None
    category: str           # 對應存放目錄
    file_name: str
    sub_dir: str | None     # 通常是 model 名稱，例如 'yolov8n'、'stable_diffusion'
    convert_jpg: bool = True


@dataclass
class SaveImageResult:
    path: Path
    md5: str