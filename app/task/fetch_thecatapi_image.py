import io
from pathlib import Path

import requests

from service.image_processor import save_image
from util.common import common
from entity.image import Image

import PIL.Image

from util.image import save_image_with_md5

# get conf
config = common.config
logger = common.logger


def fetch_cat_image_url():
    # fetch api
    response = requests.get(
        config.get('api', "thecatapi_url") + config.get('api', "thecatapi_key")
    )
    response.raise_for_status()

    data = response.json()

    return data


def download_image(url: str) -> tuple[Path, str]:
    """下載網路圖片並透過 save_image_with_md5 儲存至指定目錄，回傳 (檔案路徑, md5_hash)。"""
    # 1. 下載圖片 bytes
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    fetch_data = response.content

    # 2. 轉為 PIL Image 物件
    fetch_img = PIL.Image.open(io.BytesIO(fetch_data))

    # 3. 取得原始檔名
    fetch_img_name = url.split("/")[-1]

    # 4. 取得儲存目錄並呼叫 save_image_with_md5
    download_dir = Path(config.get("api", "thecatapi_ora_img_path"))

    download_path, download_md5 = save_image_with_md5(
        image=fetch_img, save_transform_dir=download_dir, file_name=fetch_img_name, convert_jpg=False
    )

    return download_path, download_md5


def trigger(count=1):
    for i in range(count):
        try:
            logger.info(f"Download image {i + 1}/{count}")

            # 取得 fetch api info
            fetch_data = fetch_cat_image_url()
            url = fetch_data[0]["url"]
            logger.debug(f"Image URL: {url}")

            # 下載 image
            download_path, download_md5 = download_image(url)
            logger.debug(f"Saved to: {download_path}")
            logger.debug(f"Absolute download_path: {download_path.resolve()}")

            # 寫入 image table
            # image -> md5_hash, origin_path, image_source
            image_id = save_image(Image(
                            md5_hash=download_md5,
                            origin_path=download_path,
                            image_source=config.get('api', "thecatapi_url"),
                            raw_source=fetch_data
                      ))

            logger.debug(f"image_id: {image_id}")

            # 寫入 detect info

            # 寫入 vector info

        except Exception as e:
            logger.exception(
                f"Download image failed ({i + 1}/{count}): {e}"
            )