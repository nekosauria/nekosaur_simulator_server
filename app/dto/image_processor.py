from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass
class SaveImageRequest:
    """
    圖片落地儲存的輸入資料結構。
    集中定義存檔所需的路徑慣例參數，讓各 service（detection/transform）
    不需自行組裝存放路徑，統一交由 ImageProcessor 處理。
    """

    req_image: Image.Image | None
    """
    待儲存的圖片物件，已轉換為 PIL.Image，非原始上傳的 FileStorage。
    若為 None，代表呼叫端尚未成功取得圖片，ImageProcessor 應拒絕處理。
    """

    category: str
    """
    圖片來源分類，對應存放的主目錄，決定存檔時要落地到哪個路徑
    （例如使用者上傳原圖、偵測結果圖、thecatapi 抓取圖）。
    """

    file_name: str
    """
    存檔時使用的檔名，通常沿用原始上傳檔名或以 md5 產生的檔名。
    """

    sub_dir: str | None
    """
    存放路徑下的子目錄，通常是模型名稱，例如 'yolov8n'、'stable_diffusion'，
    用於將不同模型產出的圖片分開存放。若為 None，則直接存在 category 對應的主目錄下。
    """

    convert_jpg: bool = True
    """
    是否將圖片轉存為 JPEG 格式。預設為 True；
    若需保留原始格式（例如原圖存檔避免失真），呼叫端應明確傳入 False。
    """


@dataclass
class SaveImageResult:
    """
    圖片落地儲存的輸出結果，供呼叫端（service 層）組裝各自的 Result DTO 使用。
    """

    path: Path
    """
    圖片實際存檔後的完整路徑。
    """

    md5: str
    """
    存檔圖片的 md5 雜湊值，用於去重與資料庫比對。
    """



