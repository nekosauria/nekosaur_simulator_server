from pathlib import Path

from dto.image_processor import SaveImageRequest, SaveImageResult
from util.image import save_image_with_md5
from util.common import common


config = common.config
logger = common.logger


class ImageProcessor:
    """
    統一管理圖片落地儲存的路徑慣例與 md5 計算。
    """
    @staticmethod
    def save_image(req: SaveImageRequest) -> SaveImageResult:

        base_dir = Path(config.get("image", req.category))
        save_dir = base_dir
        if req.sub_dir:
            save_dir = base_dir / req.sub_dir

        # 寫入圖片
        path, md5 = save_image_with_md5(
            image=req.req_image,
            save_dir=save_dir,
            file_name=req.file_name,
            convert_jpg=req.convert_jpg,
        )
        logger.debug(f"[ImageProcessor] category={req.category} path={path} md5={md5}")

        return SaveImageResult(
            path=path,
            md5=md5
        )
