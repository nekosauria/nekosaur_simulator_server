import io
from pathlib import Path

import requests

from dto.image_processor import SaveImageRequest, SaveImageResult
from service.image_metadata import ImageMetadata
from service.image_processor import ImageProcessor
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


def download_image(url: str) -> SaveImageResult:
    """下載網路圖片並透過 save_image_with_md5 儲存至指定目錄，回傳 (檔案路徑, md5_hash)。"""
    # === 原始圖片處理 ===
    # 1. 下載圖片 bytes
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    fetch_data = response.content

    # 2. 轉為 PIL Image 物件
    fetch_img = PIL.Image.open(io.BytesIO(fetch_data))

    # 3. 取得原始檔名
    fetch_img_name = url.split("/")[-1]

    # 儲存原圖
    fetch_res = ImageProcessor.save_image(SaveImageRequest(
        req_image=fetch_img,
        category="thecatapi_fetch_path",
        file_name=fetch_img_name,
        sub_dir=None,
        convert_jpg=False,
    ))

    return fetch_res


def trigger(count=1):

    # 跑批次回圈
    for i in range(count):
        try:
            logger.info(f"Download image {i + 1}/{count}")

########################################################################################################################
            #  === 取得 fetch api info ===
            fetch_data = fetch_cat_image_url()
            url = fetch_data[0]["url"]
            logger.debug(f"Image URL: {url}")


########################################################################################################################
            #  === 下載 image ===
            fetch_res = download_image(url)
            logger.debug(f"Saved to: {fetch_res.path}")


########################################################################################################################
            #  === 寫入 image table ===
            # save image metadata
            image_entity = Image(
                md5_hash=fetch_res.md5,
                origin_path=fetch_res.path,
                image_source=config.get('api', "thecatapi_url"),
                raw_source=fetch_data
            )
            image_id = ImageMetadata.save_image_metadata(image_entity)
            logger.debug(f"image_id: {image_id}")


########################################################################################################################
            #  === 寫入 detect info ===


########################################################################################################################
        #  === 寫入 vector info ===



        except Exception as e:
            logger.exception(
                f"Download image failed ({i + 1}/{count}): {e}"
            )