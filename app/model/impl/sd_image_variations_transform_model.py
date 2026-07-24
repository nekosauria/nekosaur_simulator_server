from typing import override

from diffusers import StableDiffusionImageVariationPipeline
from PIL import Image
from torchvision import transforms
from pathlib import Path

from const.image_const import ImageConst
from model.interface.base_transform_model import BaseTransformModel
from util.image import resize_with_padding, save_image_with_timestamp


class SDImageVariationsTransformModel(BaseTransformModel):
    def __init__(self, model_path: Path, device: str = "cpu", ora_point: float = 0.7, ref_point: float = 0.3):
        self._model_path = model_path
        self.device = device
        self.ora_point = ora_point
        self.ref_point = ref_point
        self.pipe = None

    @override
    @property
    def model_path(self) -> Path:
        return self._model_path

    @override
    @property
    def name(self) -> str:
        return ImageConst.MODEL_SD_IMAGE_VARIATIONS

    @override
    def load(self) -> None:
        self.pipe = StableDiffusionImageVariationPipeline.from_pretrained(
            str(self._model_path),
            revision="v2.0",
            local_files_only=True,
            safety_checker=None,
            requires_safety_checker=False
        ).to(self.device)

    @override
    def generate(self, init_image_path: str, ref_image_path: str, output_dir: str) -> str:
        ora_img = resize_with_padding(Image.open(init_image_path).convert("RGB"))
        ref_img = resize_with_padding(Image.open(ref_image_path).convert("RGB"))

        tform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Resize((224, 224), interpolation=transforms.InterpolationMode.BICUBIC, antialias=False),
            transforms.Normalize([0.48145466, 0.4578275, 0.40821073], [0.26862954, 0.26130258, 0.27577711]),
        ])
        ora_img = tform(ora_img).to(self.device).unsqueeze(0)
        ref_img = tform(ref_img).to(self.device).unsqueeze(0)

        inp_fusion = (ora_img * self.ora_point) + (ref_img * self.ref_point)
        result = self.pipe(inp_fusion, guidance_scale=3)["images"][0]

        return save_image_with_timestamp(image=result, output_dir=output_dir, prefix=ImageConst.MODEL_SD_IMAGE_VARIATIONS)