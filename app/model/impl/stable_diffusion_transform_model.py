from typing import override

from diffusers import StableDiffusionImg2ImgPipeline
from diffusers.utils import load_image
from PIL import Image

from const.image_const import ImageConst
from model.interface.base_transform_model import BaseTransformModel
from pathlib import Path


class StableDiffusionTransformModel(BaseTransformModel):
    def __init__(self, model_path: Path, ip_adapter_model_path, device: str = "cpu", ip_adapter_scale: float = 0.3):
        """
        【功能：只做模型初始化與載入資源】
        不牽涉任何圖片、Prompt 等單次生成的參數。
        """
        self._model_path = model_path
        self.ip_adapter_model_path = ip_adapter_model_path
        self.device = device

        # IP adapter strength
        # 最推薦的「自由發揮」區間：保有微弱特徵但給予 AI 極大空間 (0.1-1.0)
        self.ip_adapter_scale = ip_adapter_scale

        # 固定生成參數，不對外開放調整
        self.prompt = "a hybrid creature combining cat and dinosaur, masterpiece, high quality, highly detailed"
        self.negative_prompt = "blurry, low quality, distorted, deformed, noise, artifacts, bad anatomy, text, watermark"

        # model parameter weight
        # --- 控制模型「創意思維」的核心參數 ---
        # `strength` 決定模型對 `init_image` 的修改程度。
        # 0.0 = 完全不變; 1.0 = 完全重寫。
        # 「最自由發揮」必須設定為 1.0。
        self.strength = 0.65

        # `guidance_scale` (也叫 CFG Scale) 決定模型多貼近 prompt 字面意思。
        # 低數值 (1.0 - 5.0) 給予模型更多自由去「解釋」prompt。
        # 高數值 (10.0+) 讓模型必須嚴格遵循 prompt。
        # 1.0 是最自由的，有時可能導致內容不相關，但最有創意。
        # 甚至可以嘗試 0.5 到 2.0 之間的數值
        self.guidance_scale = 7.5

        # --- 增加生成過程的隨機性和細節 ---
        # 更多的步數給模型更多機會在每一步引入隨機性和細節。
        # 從 30 增加到 50-70
        self.num_inference_steps = 30

        self.pipe = None

    @override
    @property
    def model_path(self) -> Path:
        return self._model_path

    @override
    @property
    def name(self) -> str:
        return ImageConst.MODEL_STABLE_DIFFUSION

    @override
    def load(self) -> None:
        # 1. preload model to memory
        self.pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
            str(self._model_path),
            local_files_only=True,
            safety_checker=None,
            requires_safety_checker=False
        ).to(self.device)
        self.pipe.vae.enable_slicing()  # 記憶體優化

        # 2. 載入外掛元件 (IP Adapter)
        self.pipe.load_ip_adapter(
            self.ip_adapter_model_path,
            subfolder="models",
            weight_name="ip-adapter_sd15.bin",
            local_files_only=True
        )
        self.pipe.set_ip_adapter_scale(self.ip_adapter_scale)

        # 檢查所在的 device
        for name, module in self.pipe.image_encoder.named_parameters():
            print(f"MODEL_STABLE_DIFFUSION Image Encoder Device: {module.device}")
            break

        print("=== 核心模型與權重已成功載入 GPU，準備就緒！ ===")

    @override
    def generate(self, init_image_path: Path, ref_image_path: Path) -> Image.Image:
        # load images
        init_image = load_image(str(init_image_path)).convert("RGB")
        ref_image = load_image(str(ref_image_path)).convert("RGB")

        # 對齊：強迫圖片調整為 512x512 (或 64 的倍數)，防止 VAE 卷積維度出錯產生網格亂碼
        init_image = init_image.resize((512, 512), Image.Resampling.LANCZOS)
        ref_image = ref_image.resize((512, 512), Image.Resampling.LANCZOS)

        # inference
        result = self.pipe(
            prompt=self.prompt,
            negative_prompt=self.negative_prompt,
            image=init_image,
            ip_adapter_image=ref_image,
            strength=self.strength,
            guidance_scale=self.guidance_scale,
            num_inference_steps=self.num_inference_steps
        ).images[0]

        return result
