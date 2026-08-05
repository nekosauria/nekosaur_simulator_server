from dao.image import insert
from entity.image import Image


def save_image(image: Image) -> int:

    image_id = insert(image)

    return image_id

