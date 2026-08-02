from pathlib import Path
from PIL import Image

from model.interface.base_transform_model import BaseTransformModel

class ImageTransformService:

    def __init__(self, model: BaseTransformModel):
        self._model = model

    def predict(self, init_image_path: Path, ref_image_path: Path) -> Image.Image:

        transform_image_path = self._model.generate(init_image_path, ref_image_path)

        return transform_image_path