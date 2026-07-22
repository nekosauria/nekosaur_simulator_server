from dataclasses import dataclass

@dataclass
class DetectionResult:
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