import hashlib
import io
from pathlib import Path

from PIL import Image

from const.image_const import ImageConst
from util.common import common

logger = common.logger


def collect_image_paths(folder, recursive: bool = True) -> list[str]:
    # 取得資料夾內所有照片
    folder = Path(folder)
    pattern = "**/*" if recursive else "*"

    logger.debug(f"collect_image_paths: folder={folder}, recursive={recursive}, exists={folder.exists()}")

    paths = sorted(
        str(p) for p in folder.glob(pattern)
        if p.is_file() and p.suffix.lower().lstrip(".") in ImageConst.ALLOWED_EXTENSIONS
    )

    logger.debug(f"collect_image_paths: found {len(paths)} images in {folder}")

    return paths


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
    if image.mode != "RGB":
        image = image.convert("RGB")

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


def save_image_with_md5(
    image: Image.Image,
    save_dir: Path,
    file_name: str = "result",
    convert_jpg: bool = True,
    quality: int = 90,
) -> tuple[Path, str]:
    """將 PIL 圖片物件儲存至指定目錄，自動加上 md5 並回傳 (路徑, md5_hash)。

        :param image: PIL Image 物件
        :param save_dir: 儲存目錄
        :param file_name: 檔名 (可帶原副檔名)
        :param convert_jpg: 是否強制轉換為 .jpg 格式 (預設為 True)
        :param quality: 若為 JPEG 格式時的壓縮品質 (1-100)
        :return: (最終檔案路徑, md5_hash)
    """
    # 1. 判斷圖片格式與副檔名
    ext = Path(file_name).suffix.lower()
    save_kwargs = {}

    if convert_jpg:
        fmt = "JPEG"
        ext = ".jpg"
        save_kwargs["quality"] = quality
        if image.mode in ("RGBA", "P", "LA"):
            image = image.convert("RGB")
    else:
        fmt = image.format
        if not fmt:
            if ext in (".jpg", ".jpeg"):
                fmt = "JPEG"
            else:
                fmt = "PNG"

        if fmt == "JPEG":
            save_kwargs["quality"] = quality

        if not ext:
            ext = f".{fmt.lower()}"

    # 2. 寫入記憶體緩衝區並計算 MD5
    buffer = io.BytesIO()
    image.save(buffer, format=fmt, **save_kwargs)
    image_bytes = buffer.getvalue()
    md5_hash = hashlib.md5(image_bytes).hexdigest()

    # 3. 組合檔名並寫入實體檔案
    stem = Path(file_name).stem
    out_path = save_dir / f"{md5_hash}_{stem}{ext}"
    out_path.write_bytes(image_bytes)

    return out_path, md5_hash


def get_md5(content: bytes) -> str:
    """計算 MD5"""
    return hashlib.md5(content).hexdigest()

