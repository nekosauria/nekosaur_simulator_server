from pathlib import Path

from PIL import Image
import os

from const.image_const import ImageConst


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
    if ext not in ImageConst.ALLOWED_EXTENSIONS:
        return None, f"不支援的圖片格式，請上傳 {', '.join(ImageConst.ALLOWED_EXTENSIONS)}", 400

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

def save_image_with_timestamp(image, save_transform_dir: Path, file_name: str = "result") -> Path:
    """
    將 PIL 圖片物件儲存至指定目錄，並自動加上時間戳記。並回傳路徑。
    """
    # 自動建立不存在的資料夾，避免噴出 FileNotFoundError 錯誤
    os.makedirs(save_transform_dir, exist_ok=True)

    # 組合完整路徑：目錄 / 前綴_時間戳記.png
    transform_image_path = save_transform_dir / file_name

    # 儲存圖片
    image.save(transform_image_path)

    return transform_image_path