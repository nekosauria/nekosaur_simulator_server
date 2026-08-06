import requests

from dto.image_processor import SaveImageRequest
from service.image_metadata import ImageMetadata
from service.image_processor import ImageProcessor
from util.common import common
from entity.image import Image

from util.image import download_image

# get conf
config = common.config
logger = common.logger


def fetch_thecatapi_url() -> dict:
    # fetch api
    response = requests.get(
        config.get('api', "thecatapi_url") + config.get('api', "thecatapi_key")
    )
    response.raise_for_status()
    fetch_data = response.json()

    logger.debug(f"fetch_data: {fetch_data}")

    return fetch_data


def trigger(count=1):

    # 跑批次回圈
    for i in range(count):
        try:
            logger.debug(f"Download image {i + 1}/{count}")

            #  === 取得 fetch thecatapi data ===
            fetch_data = fetch_thecatapi_url()
            fetch_image_url = fetch_data[0]["url"]
            logger.debug(f"fetch_image_url: {fetch_image_url}")

            fetch_img, fetch_img_name = download_image(fetch_image_url)

            # ===  database 重複驗證 ===
            if False:
                # === 若資料庫已有 fetch_data 的 image md5, skip
                logger.error(f"fetch_thcat_api_img exists in database: {fetch_image_url}", exc_info=True)
                logger.error(f"fetch_thcat_api_data: {fetch_data}", exc_info=True)
                ...

            else:
                #  === 下載 image info ===
                # 儲存原圖
                fetch_res = ImageProcessor.save_image(SaveImageRequest(
                    req_image=fetch_img,
                    category="thecatapi_fetch_path",
                    file_name=fetch_img_name,
                    sub_dir=None,
                    convert_jpg=False,
                ))
                logger.debug(f"Saved to: {fetch_res.path}")

                # save image metadata
                image_entity = Image(
                    md5_hash=fetch_res.md5,
                    origin_path=fetch_res.path,
                    image_source=config.get('api', "thecatapi_url"),
                    raw_source=fetch_data
                )
                image_id = ImageMetadata.save_image_metadata(image_entity)
                logger.debug(f"image_id: {image_id}")


                #  === 寫入 detect info ===


                #  === 寫入 vector info ===


                #  === 寫入 transform info ===


        except Exception as e:
            logger.error(
                f"Download image failed ({i + 1}/{count}): {e}",
                exc_info=True
            )