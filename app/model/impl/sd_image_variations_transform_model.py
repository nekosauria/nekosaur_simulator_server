from typing import override, Any

import torch
from diffusers import StableDiffusionImageVariationPipeline
from PIL import Image
from torchvision import transforms
from pathlib import Path

from const.image_const import ImageConst
from model.interface.base_transform_model import BaseTransformModel
from util.common import common
from util.device import empty_device_cache
from util.image import resize_with_padding

logger = common.logger


class SDImageVariationsTransformModel(BaseTransformModel):
    def __init__(
            self, model_path: Path,
            device: str = "cpu",
            dtype: Any = torch.float32,
            ora_point: float = 0.7,
            ref_point: float = 0.3
    ):
        self._model_path = model_path
        self.device = device
        self.dtype = dtype

        self.ora_point = ora_point
        self.ref_point = ref_point

        self.guidance_scale = 3.0  # 👈 控制「貼近這張拼貼特徵」的力道，數值越高變形重組越劇烈
        self.num_inference_steps = 38

        self.pipe = None

        # 測試用的隨機種子
        self.seed = 42

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
            torch_dtype=self.dtype,
            revision="v2.0",
            local_files_only=True,
            safety_checker=None,
            requires_safety_checker=False
        ).to(self.device)

        # 檢查所在的 device
        for name, module in self.pipe.image_encoder.named_parameters():
            logger.info(f"MODEL_SD_IMAGE_VARIATIONS Image Encoder Device: {module.device}")
            break

    @override
    def generate(self, init_image_path: Path, style_ref_image: Path) -> Image.Image:
        # 1. 讀取並統一基本尺寸
        init_image = resize_with_padding(Image.open(init_image_path), target_size=(256, 256))
        ref_image = resize_with_padding(Image.open(style_ref_image), target_size=(256, 256))

        # 2. 轉為 0 ~ 1 區間的 Tensor
        to_tensor = transforms.ToTensor()
        ora_tensor = to_tensor(init_image).to(self.device, dtype=self.dtype)
        ref_tensor = to_tensor(ref_image).to(self.device, dtype=self.dtype)

        # 在 0~1 的 RGB 空間做加權融合！
        fused_tensor = (ora_tensor * self.ora_point) + (ref_tensor * self.ref_point)

        # 4. 融合完成後，才做 CLIP 標準預處理 (Resize + Normalize)
        clip_normalize = transforms.Compose([
            transforms.Resize((224, 224), interpolation=transforms.InterpolationMode.BICUBIC, antialias=False),
            transforms.Normalize([0.48145466, 0.4578275, 0.40821073], [0.26862954, 0.26130258, 0.27577711]),
        ])

        inp_fusion = clip_normalize(fused_tensor).unsqueeze(0).to(self.device, dtype=self.dtype)

        # 5. 清理顯存
        empty_device_cache(self.device)

        # 6. 推論生成 (使用 attribute .images[0] 防範 dict 回傳差異)
        result = self.pipe(
            image=inp_fusion,
            guidance_scale=self.guidance_scale,
            num_inference_steps=self.num_inference_steps,
            # generator=torch.Generator(device=self.device).manual_seed(self.seed)
        ).images[0]

        return result