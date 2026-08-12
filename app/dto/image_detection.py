from dataclasses import dataclass

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

    detect_model: str
    """
    使用的偵測模型名稱，對應 ImageConst 內 MODEL_* 常數，DetectionModelFactory 依此取得常駐模型實例。
    """


@dataclass
class DetectionResult:
    """
    偵測服務的輸出結果，供 controller 組裝 API response 或寫入 DB 使用。
    """

    detect_image: Image.Image | None
    """
        畫有標籤框（Bounding Box）與類別標籤的處理後圖片物件（PIL.Image）。
        若推論過程失敗或未繪製，可為 None。
    """

    tag_results: dict
    """
    各標籤的信心分數彙總，例如 {"cat": 0.9213}，供前端快速顯示辨識結果。
    """

    predict_list: dict
    """
    完整的模型預測結果列表，包含各標籤對應的信心分數細節。
    """

    has_cat: bool
    """
    本次偵測結果中是否包含「貓」這個類別。
    由 tag_results 依信心分數門檻判斷後得出，
    供上層流程判斷是否為合法上傳圖片（無貓則視為 422，不繼續往下跑相似度搜尋與風格轉換）。
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