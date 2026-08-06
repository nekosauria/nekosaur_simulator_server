from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass
class TransformRequest:
    req_image: Image.Image | None
    category: str
    file_name: str
    transform_model: str
    style_ref_image: str

@dataclass
class TransformResult:
    transform_path: Path
    transform_md5: str
    transform_cost: float
