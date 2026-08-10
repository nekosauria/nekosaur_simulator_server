from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass
class TransformRequest:
    """
    風格轉換服務的輸入資料結構。
    僅包含模型推論與存檔所需的最小欄位，不帶原始 FileStorage 物件，
    讓 TransformService 不需感知圖片來源（原圖 / 相似圖）的差異。
    """

    req_image: Image.Image | None
    """
    待轉換的圖片物件，已轉換為 PIL.Image，非原始上傳的 FileStorage。
    若為 None，代表呼叫端尚未成功取得圖片，TransformService 應拒絕處理。
    """

    transform_model: str
    """
    使用的風格轉換模型名稱，對應 ImageConst 內 MODEL_* 常數，
    例如 stable_diffusion、sd_image_variations，TransformModelFactory 依此取得常駐模型實例。
    """

    style_ref_image: str
    """
    風格轉換的參考圖路徑，模型會依此圖的風格對 req_image 進行轉換。
    """


@dataclass
class TransformResult:
    """
    風格轉換服務的輸出結果，供 controller 組裝 API response 或寫入 DB 使用。
    """

    transform_image: Image.Image | None
    """
        風格轉換後的處理後圖片物件（PIL.Image）。
        若推論過程失敗或未繪製，可為 None。
    """