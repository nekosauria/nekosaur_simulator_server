from model.interface.base_transform_model import BaseTransformModel

class ImageTransformService:

    def __init__(self, model: BaseTransformModel):
        self._model = model
        self._loaded = False

    def predict(self, init_image_path: str, ref_image_path: str, output_dir: str) -> str:

        transform_image_path = self._model.generate(init_image_path, ref_image_path, output_dir)

        return transform_image_path