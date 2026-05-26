import torch
from diffusers import StableDiffusionImg2ImgPipeline
from diffusers.utils import load_image
from util.common import common
from datetime import datetime

# =========================
# config
# =========================

# get conf
config = common.config
ora_img = config.get('model', "user_ora_img")
ref_img = config.get('model', "style_ref_img")
out_img = config.get('model', "user_out_img")
DIFFUSION_MODEL_PATH = config.get('model', "diffusion_model_path")
IP_ADAPTER_PATH = config.get('model', "ip_adapter_model_path")

# =========================
# device
# =========================

if torch.cuda.is_available():
    device = "cuda"
    dtype = torch.float16
elif torch.backends.mps.is_available():
    device = "mps"
    # Mac MPS 建議 fp32
    dtype = torch.float32
else:
    device = "cpu"
    dtype = torch.float32

print(f"device={device}")
print(f"dtype={dtype}")

# =========================
# pipeline
# =========================

# base model
# .to("cuda"), .to("mps"), .to("cpu")
pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
    DIFFUSION_MODEL_PATH,
    torch_dtype=dtype,
    local_files_only=True,
    safety_checker = None,  # 🔥 關掉
    requires_safety_checker = False
)
pipe.to(device)

# memory optimize
pipe.vae.enable_slicing()

# =========================
# load ip adapter
# =========================

pipe.load_ip_adapter(
    IP_ADAPTER_PATH,
    subfolder="models",
    weight_name="ip-adapter_sd15.bin",
    local_files_only=True
)

# IP adapter strength
# 最推薦的「自由發揮」區間：保有微弱特徵但給予 AI 極大空間 (0.1-1.0)
pipe.set_ip_adapter_scale(0.3)

# =========================
# images
# =========================

# 原圖
init_image = load_image(ora_img)
# 參考圖
ref_image = load_image(ref_img)

# =========================
# prompt
# =========================

prompt = 'please change image style like a cat and dinosaur combine animal'

negative_prompt = 'empty, low quality'


# =========================
# generate
# =========================
print("tokenizer:", pipe.tokenizer)


result = pipe(
    prompt=prompt,
    negative_prompt=negative_prompt, # 建議將此參數也大幅簡化或保持空白，以獲得最大自由度。

    # --- 1. 大幅降低參考圖的影響 (最重要) ---
    image=init_image,
    ip_adapter_image=ref_image,
    # 如果可能，完全移除 ip_adapter_image 或 init_image 會是「最自由」的狀態。
    # 但如果必須保留，請將其權重降到最低。例如：
    # ip_adapter_image=[ref_image] * [0.1] # 如果 IP-Adapter 支援權重

    # --- 2. 控制模型「創意思維」的核心參數 ---
    # `strength` 決定模型對 `init_image` 的修改程度。
    # 0.0 = 完全不變; 1.0 = 完全重寫。
    # 「最自由發揮」必須設定為 1.0。
    strength=0.6,

    # `guidance_scale` (也叫 CFG Scale) 決定模型多貼近 prompt 字面意思。
    # 低數值 (1.0 - 5.0) 給予模型更多自由去「解釋」prompt。
    # 高數值 (10.0+) 讓模型必須嚴格遵循 prompt。
    # 1.0 是最自由的，有時可能導致內容不相關，但最有創意。
    guidance_scale=2.0, # 甚至可以嘗試 0.5 到 2.0 之間的數值

    # --- 3. 增加生成過程的隨機性和細節 ---
    # 更多的步數給模型更多機會在每一步引入隨機性和細節。
    num_inference_steps=10, # 從 30 增加到 50-70

).images[0]

# =========================
# save
# =========================

# 產生時間戳記字串，格式例如：20240514_143005
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# 組合檔名
out_img = f"{out_img}_output_{timestamp}.png"

result.save(out_img)
print(f"saved => {out_img}")

