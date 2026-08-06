from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass
class DetectionRequest:
    """
    偵測服務的輸入資料結構。
    僅包含模型推論與存檔所需的最小欄位，不帶原始 FileStorage 物件，
    讓 DetectionService 不需感知上傳來源（使用者上傳 / thecatapi 抓取）的差異。
    """

    req_image: Image.Image | None
    """
    待偵測的圖片物件，已轉換為 PIL.Image，非原始上傳的 FileStorage。
    若為 None，代表呼叫端尚未成功取得圖片，DetectionService 應拒絕處理。
    """

    category: str
    """
    圖片來源分類，決定存檔時要落地到哪個路徑（例如使用者上傳 or thecatapi 圖片）。
    """

    file_name: str
    """
    存檔時使用的檔名，通常沿用原始上傳檔名或以 md5 產生的檔名。
    """

    detect_model: str
    """
    使用的偵測模型名稱，對應 ImageConst 內 MODEL_* 常數，DetectionModelFactory 依此取得常駐模型實例。
    """


@dataclass
class DetectionResult:
    """
    偵測服務的輸出結果，供 controller 組裝 API response 或寫入 DB 使用。
    """

    tag_results: dict
    """
    各標籤的信心分數彙總，例如 {"cat": 0.9213}，供前端快速顯示辨識結果。
    """

    predict_list: dict
    """
    完整的模型預測結果列表，包含各標籤對應的信心分數細節。
    """

    detect_path: Path
    """
    偵測結果圖（含 draw box 標註）的實際存檔路徑。
    """

    detect_md5: str
    """
    偵測結果圖的 md5 雜湊值。
    """

    detect_cost: float
    """
    本次偵測（含模型推論與存檔）耗費的時間，單位為秒，已四捨五入至小數點後 3 位。
    """

@dataclass
class ModelPrediction:
    """
    模型推論結果的標準化資料結構。
    所有模型（Torch、YOLO、ONNX...）的 predict() 都必須回傳此格式，
    確保 DetectionService 不感知底層框架差異。
    """

    boxes: list[tuple[int, int, int, int]]
    """
    偵測到的物件邊界框清單，每個元素為 (x_min, y_min, x_max, y_max) 像素座標。
    x_min, y_min = 左上角；x_max, y_max = 右下角。
    與 boxes 、labels、scores 三個 list 的索引一一對應。
    """

    labels: list[int]
    """
    偵測到的物件類別 index 清單，對應 ImageConst 內 MODEL LABEL 常數。
    例如 LABELS = ['cat', 'dog']，label=0 代表 cat、label=1 代表 dog。
    使用 int index 而非字串，讓 service 層可直接用 labels[label] 查名稱。
    """

    scores: list[float]
    """
    各物件的信心分數清單，範圍 0.0 ~ 1.0，已四捨五入至小數點後 4 位。
    分數越高代表模型對該偵測結果越有把握。
    """