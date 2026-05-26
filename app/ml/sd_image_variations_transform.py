from diffusers import StableDiffusionImageVariationPipeline
from PIL import Image
from torchvision import transforms
from util.image import resize_with_padding, get_ml_device, save_image_with_timestamp
from dataclasses import dataclass

# config model
@dataclass
class SDImageVariationsTransformConfig:
    init_image_path: str
    ref_image_path: str
    output_dir: str
    sd_image_variations_model_path: str
    # 原圖權重
    ora_point: float = 0.7
    # 參考圖權重
    ref_point: float = 0.3

# service
class SDImageVariationsTransformService:
    def __init__(self, config: SDImageVariationsTransformConfig):
        """
        【功能：只做模型初始化與載入資源】
        不牽涉任何圖片、Prompt 等單次生成的參數。
        """
        self.config = config
        self.device, self.dtype = get_ml_device()

        # pipeline
        self.pipe = StableDiffusionImageVariationPipeline.from_pretrained(
            self.config.sd_image_variations_model_path,
            revision="v2.0",
            local_files_only=True,
            safety_checker=None,
            requires_safety_checker=False
        )
        self.pipe.to(self.device)

    def generate(self) -> None:
            ora_img = resize_with_padding(
                Image.open(self.config.init_image_path).convert("RGB")
            )
            ref_img = resize_with_padding(
                Image.open(self.config.ref_image_path).convert("RGB")
            )
            tform = transforms.Compose([
                transforms.ToTensor(),
                transforms.Resize(
                    (224, 224),
                    interpolation=transforms.InterpolationMode.BICUBIC,
                    antialias=False,
                    ),
                transforms.Normalize(
                  [0.48145466, 0.4578275, 0.40821073],
                  [0.26862954, 0.26130258, 0.27577711]),
            ])
            # 讀取兩張圖並處理
            ora_img = tform(ora_img).to(self.device).unsqueeze(0)
            ref_img = tform(ref_img).to(self.device).unsqueeze(0)

            # 輸出兩張圖權重
            inp_fusion = (ora_img * self.config.ora_point) + (ref_img * self.config.ref_point)
            out = self.pipe(inp_fusion, guidance_scale=3)
            result = out["images"][0]


            save_image_with_timestamp(
                image=result,
                output_dir=self.config.output_dir,
                prefix="sd_image_variations"
            )

            pass