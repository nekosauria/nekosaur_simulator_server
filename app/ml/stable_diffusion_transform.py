from dataclasses import dataclass

from diffusers import StableDiffusionImg2ImgPipeline
from diffusers.utils import load_image
from util.image import get_ml_device, save_image_with_timestamp

# config model
@dataclass
class StableDiffusionConfig:

    init_image_path: str
    ref_image_path: str
    output_dir: str

    stable_diffusion_model_path: str
    ip_adapter_model_path: str

    prompt: str = "please change image style like a cat and dinosaur combine animal"
    negative_prompt: str = ""

    # IP adapter strength
    # 最推薦的「自由發揮」區間：保有微弱特徵但給予 AI 極大空間 (0.1-1.0)
    ip_adapter_scale: float = 0.3

    # model parameter weight
    # --- 2. 控制模型「創意思維」的核心參數 ---
    # `strength` 決定模型對 `init_image` 的修改程度。
    # 0.0 = 完全不變; 1.0 = 完全重寫。
    # 「最自由發揮」必須設定為 1.0。
    strength: float = 0.6

    # `guidance_scale` (也叫 CFG Scale) 決定模型多貼近 prompt 字面意思。
    # 低數值 (1.0 - 5.0) 給予模型更多自由去「解釋」prompt。
    # 高數值 (10.0+) 讓模型必須嚴格遵循 prompt。
    # 1.0 是最自由的，有時可能導致內容不相關，但最有創意。
    # 甚至可以嘗試 0.5 到 2.0 之間的數值
    guidance_scale: float = 2.0

    # --- 3. 增加生成過程的隨機性和細節 ---
    # 更多的步數給模型更多機會在每一步引入隨機性和細節。
    # 從 30 增加到 50-70
    num_inference_steps: int = 10


# service
class StableDiffusionService:

    def __init__(self, config: StableDiffusionConfig):
        """
        【功能：只做模型初始化與載入資源】
        不牽涉任何圖片、Prompt 等單次生成的參數。
        """
        self.config = config
        self.device, self.dtype = get_ml_device()

        # 1. preload model to memory
        self.pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
            self.config.stable_diffusion_model_path,
            torch_dtype=self.dtype,
            local_files_only=True,
            safety_checker=None,
            requires_safety_checker=False
        )
        self.pipe.to(self.device)
        self.pipe.vae.enable_slicing()  # 記憶體優化

        # 2. 載入外掛元件 (IP Adapter)
        self.pipe.load_ip_adapter(
            self.config.ip_adapter_model_path,
            subfolder="models",
            weight_name="ip-adapter_sd15.bin",
            local_files_only=True
        )
        print("=== 核心模型與權重已成功載入 GPU，準備就緒！ ===")


    def generate(self) -> None:
        # load images
        init_image = load_image(self.config.init_image_path)
        ref_image = load_image(self.config.ref_image_path)

        # inference
        result = self.pipe(
            prompt=self.config.prompt,
            negative_prompt=self.config.negative_prompt,
            image=init_image,
            ip_adapter_image=ref_image,
            strength=self.config.strength,
            guidance_scale=self.config.guidance_scale,
            num_inference_steps=self.config.num_inference_steps
        ).images[0]

        save_image_with_timestamp(
            image=result,
            output_dir=self.config.output_dir,
            prefix="stable_diffusion"
        )

        pass