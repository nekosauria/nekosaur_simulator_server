import hashlib
import io
from pathlib import Path
from typing import Any, Dict

import PIL
import requests
from PIL import Image

from const.image_const import ImageConst
from util.common import common

logger = common.logger


def check_file_exists(file_path: str | Path) -> bool:
    """檢查實體檔案是否存在（用來判斷是否已被搬移/損壞/遺失）"""
    path_obj = Path(file_path) if isinstance(file_path, str) else file_path
    exists = path_obj.is_file()

    if not exists:
        logger.warning(f"File missing or invalid: {file_path}")
    else:
        logger.debug(f"check_file_exists: file_path={file_path}, exists=True")

    return exists


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


def resize_with_padding(image: Image.Image, target_size=(512, 512)) -> Image.Image:
    """將圖片按比例縮放並補黑邊 (Padding) 至指定尺寸"""
    # 複製一份避免修改到原始圖像，並轉為 RGB
    img = image.copy().convert("RGB")

    # 取得相容性最好的 LANCZOS 濾鏡 (優先用 Image.Resampling.LANCZOS，其次 Image.LANCZOS)
    resample_filter = getattr(Image, "Resampling", Image).LANCZOS

    # 按比例等比縮放
    img.thumbnail(target_size, resample_filter)

    # 建立目標尺寸的黑色底圖
    new_image = Image.new("RGB", target_size, (0, 0, 0))

    # 置中貼上
    paste_x = (target_size[0] - img.size[0]) // 2
    paste_y = (target_size[1] - img.size[1]) // 2
    new_image.paste(img, (paste_x, paste_y))

    return new_image


def _prepare_image_bytes(
        image: Image.Image,
        file_name: str,
        convert_jpg: bool,
        quality: int,
) -> tuple[bytes, str]:
    """依命名慣例決定輸出格式/副檔名，並將圖片序列化為 bytes。

    抽出此函式是為了讓 save_image_with_md5 (寫檔) 與
    compute_image_md5 (只算 md5，不寫檔) 共用同一份格式判斷邏輯。

    :param convert_jpg: True 時強制轉 JPEG 並套用 quality 壓縮 (有損)；
                         False 時保留原格式、不做任何壓縮 (原圖存檔用)。
    :return: (image_bytes, ext)
    """
    ext = Path(file_name).suffix.lower()
    save_kwargs = {}

    if convert_jpg:
        fmt = "JPEG"
        ext = ".jpg"
        save_kwargs["quality"] = quality
        if image.mode in ("RGBA", "P", "LA"):
            image = image.convert("RGB")
    else:
        # 不轉檔情境：保留原格式，不做 quality 壓縮 (避免非必要地改變原圖 bytes / md5)
        fmt = image.format
        if not fmt:
            fmt = "JPEG" if ext in (".jpg", ".jpeg") else "PNG"
        if not ext:
            ext = f".{fmt.lower()}"

    buffer = io.BytesIO()
    image.save(buffer, format=fmt, **save_kwargs)
    return buffer.getvalue(), ext


def get_md5(content: bytes) -> str:
    """計算 MD5"""
    return hashlib.md5(content).hexdigest()


def save_image_with_md5(
        image: Image.Image,
        save_dir: Path,
        file_name: str = "result",
        convert_jpg: bool = True,
        quality: int = 100 # 預設為 100 (最高品質/不壓縮)
) -> tuple[Path, str]:
    """將 PIL 圖片物件儲存至指定目錄，自動加上 md5 並回傳 (路徑, md5_hash)。

    :param image: PIL Image 物件
    :param save_dir: 儲存目錄
    :param file_name: 檔名 (可帶原副檔名)
    :param convert_jpg: 是否強制轉換為 .jpg 格式 (預設為 False)
    :param quality: 若為 JPEG 格式時的壓縮品質 (1-100)
    :return: (最終檔案路徑, md5_hash)
    """
    image_bytes, ext = _prepare_image_bytes(image, file_name, convert_jpg, quality)
    md5_hash = get_md5(image_bytes)

    stem = Path(file_name).stem
    out_path = save_dir / f"{md5_hash}_{stem}{ext}"
    out_path.write_bytes(image_bytes)

    return out_path, md5_hash


def compute_image_md5(
        image: Image.Image,
        file_name: str = "result",
        convert_jpg: bool = False,
        quality: int = 100 # 預設為 100 (最高品質/不壓縮)
) -> str:
    """依 save_image_with_md5 相同的格式判斷邏輯計算圖片內容的 md5，但不寫入檔案。

    供 get_or_save_image 在寫檔前先判斷該內容 (md5) 是否已經存在。
    """
    image_bytes, _ = _prepare_image_bytes(image, file_name, convert_jpg, quality)
    return get_md5(image_bytes)


def url_to_pil_image(image_url: str) -> tuple[PIL.Image.Image, str]:
    """從 URL 下載圖片，回傳 (PIL Image 物件, 原始檔名)。"""
    response = requests.get(image_url, timeout=10)
    response.raise_for_status()

    image_bytes = response.content
    image = PIL.Image.open(io.BytesIO(image_bytes))

    file_name = image_url.split("/")[-1]

    return image, file_name


def get_raw_source_info(
    file, filename: str = "unknown"
) -> Dict[str, Any]:
    """
    解析 Flask FileStorage 上傳檔案的基本資訊與特徵

    :param file: Flask 的 request.files 檔案物件 (FileStorage)
    :param filename: 檔案名稱 (選填，若未傳則自動從 file.filename 抓取)
    :return: 圖片資訊字典 (JSON)
    """
    # 優先使用傳入的 filename，若無則抓取 file.filename
    file_name = filename if filename != "unknown" else getattr(file, "filename", "unknown")

    # 1. 讀取檔案 size 並計算大小
    file.seek(0, 2)  # 移動指標到末端取得 byte 長度
    file_size_bytes = file.tell()
    file.seek(0)     # **極重要**：重置指標回開頭，避免影響後續讀取

    # 2. 開啟圖片解析特徵
    image = Image.open(file)
    file.seek(0)     # 讀取完 Image 後再次重置指標

    width, height = image.size
    img_format = (image.format or "UNKNOWN").upper()
    color_mode = image.mode

    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else img_format.lower()

    return {
        "filename": file_name,
        "extension": ext,
        "format": img_format,
        "width": width,
        "height": height,
        "aspect_ratio": round(width / height, 2) if height > 0 else 0,
        "color_mode": color_mode,
        "file_size_bytes": file_size_bytes,
        "file_size_kb": round(file_size_bytes / 1024, 2),
    }