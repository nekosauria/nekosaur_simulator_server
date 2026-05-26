import os
import requests
import hashlib
from util.common import common

# get conf
config = common.config
cat_key = config.get('api', "thecatapi_key")
DOWNLOAD_DIR = config.get('api', "thecatapi_ora_img_path")
API_URL = config.get('api', "thecatapi_url") + cat_key


def get_md5(content: bytes) -> str:
    """計算 MD5"""
    return hashlib.md5(content).hexdigest()


def fetch_cat_image_url():
    response = requests.get(API_URL)
    response.raise_for_status()

    data = response.json()
    return data[0]["url"]


def download_image(url: str, save_dir=DOWNLOAD_DIR):
    os.makedirs(save_dir, exist_ok=True)

    img_data = requests.get(url).content

    # 計算 MD5
    md5_hash = get_md5(img_data)

    # 原始檔名
    original_name = url.split("/")[-1]

    # 新檔名：md5 + 原檔名
    new_filename = f"{md5_hash}_{original_name}"

    file_path = os.path.join(save_dir, new_filename)

    with open(file_path, "wb") as f:
        f.write(img_data)

    return file_path, md5_hash


if __name__ == "__main__":
    url = fetch_cat_image_url()
    print("Image URL:", url)

    path, md5 = download_image(url)

    print("MD5:", md5)
    print("Saved to:", path)