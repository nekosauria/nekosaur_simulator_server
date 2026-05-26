from PIL import Image
import torch
import os
from datetime import datetime

ALLOWED_EXTENSIONS = {
    # 一般常見格式
    'jpg', 'jpeg', 'png',
    'webp', 'bmp',
    # iPhone (iOS)
    'heic', 'heif',
    # Android
    'avif',
    # RAW 格式 (部分高階手機)
    'dng',
}

def validate_image(request_files):
    """
    校驗上傳圖片
    :return: (file, error_message, http_status)
             成功時 error_message = None, http_status = None
    """
    if 'image' not in request_files:
        return None, "沒有提供圖片", 400

    file = request_files['image']

    if file.filename == '':
        return None, "未選擇檔案", 400

    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return None, f"不支援的圖片格式，請上傳 {', '.join(ALLOWED_EXTENSIONS)}", 400

    return file, None, None

def resize_with_padding(image, target_size=(512, 512)):
    # 方案 1: 嘗試新版 Pillow (10.0+) 的 Resampling 屬性
    resample_filter = getattr(Image, 'Resampling', Image)

    # 方案 2: 嘗試抓取 LANCZOS，如果都抓不到，直接用數值 1 (LANCZOS 的底層常數)
    # 在 Pillow 中，LANCZOS、ANTIALIAS、1 其實指的都是同一個濾鏡
    final_filter = getattr(resample_filter, 'LANCZOS', 1)

    # 執行縮放
    image.thumbnail(target_size, final_filter)

    # 建立底圖
    new_image = Image.new("RGB", target_size, (0, 0, 0))
    # 將縮放後的圖貼在正中間
    new_image.paste(image, ((target_size[0] - image.size[0]) // 2,
                            (target_size[1] - image.size[1]) // 2))
    return new_image

def get_ml_device():
    if torch.cuda.is_available():
        device = "cuda"
        dtype = torch.float16

    elif torch.backends.mps.is_available():
        device = "mps"
        dtype = torch.float32

    else:
        device = "cpu"
        dtype = torch.float32

    print(f"device={device}")
    print(f"dtype={dtype}")

    return device, dtype



def save_image_with_timestamp(image, output_dir: str, prefix: str = "result") -> None:
    """
    將 PIL 圖片物件儲存至指定目錄，並自動加上時間戳記。不回傳任何路徑。
    """
    # 自動建立不存在的資料夾，避免噴出 FileNotFoundError 錯誤
    os.makedirs(output_dir, exist_ok=True)

    # 產生時間戳記
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 組合完整路徑：目錄 / 前綴_時間戳記.png
    filename = f"{prefix}_{timestamp}.png"
    output_path = os.path.join(output_dir, filename)

    # 儲存圖片
    image.save(output_path)
    print(f"saved => {output_path}")

    pass