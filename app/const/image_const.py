from pathlib import Path

# 常數不需要用 self.var
# 一般來說要 new object 時才會用到 self.var
class ImageConst:

    # 💡 新增模型名稱常數
    # detect
    MODEL_TORCH = "torch"
    MODEL_YOLO = "yolo"

    # transform
    MODEL_STABLE_DIFFUSION = "stable_diffusion_transform"
    MODEL_SD_IMAGE_VARIATIONS = "sd_image_variations_transform"

    # 用於物件偵測的標籤
    TORCH_LABELS = [
        "unlabeled",
        "person",
        "bicycle",
        "car",
        "motorcycle",
        "airplane",
        "bus",
        "train",
        "truck",
        "boat",
        "traffic light",
        "fire hydrant",
        "street sign",
        "stop sign",
        "parking meter",
        "bench",
        "bird",
        "cat",
        "dog",
        "horse",
        "sheep",
        "cow",
        "elephant",
        "bear",
        "zebra",
        "giraffe",
        "hat",
        "backpack",
        "umbrella",
        "shoe",
        "eye glasses",
        "handbag",
        "tie",
        "suitcase",
        "frisbee",
        "skis",
        "snowboard",
        "sports ball",
        "kite",
        "baseball bat",
        "baseball glove",
        "skateboard",
        "surfboard",
        "tennis racket",
        "bottle",
        "plate",
        "wine glass",
        "cup",
        "fork",
        "knife",
        "spoon",
        "bowl",
        "banana",
        "apple",
        "sandwich",
        "orange",
        "broccoli",
        "carrot",
        "hot dog",
        "pizza",
        "donut",
        "cake",
        "chair",
        "couch",
        "potted plant",
        "bed",
        "mirror",
        "dining table",
        "window",
        "desk",
        "toilet",
        "door",
        "tv",
        "laptop",
        "mouse",
        "remote",
        "keyboard",
        "cell phone",
        "microwave",
        "oven",
        "toaster",
        "sink",
        "refrigerator",
        "blender",
        "book",
        "clock",
        "vase",
        "scissors",
        "teddy bear",
        "hair drier",
        "toothbrush"
    ]

    YOLO_LABELS = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
     'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
     'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
     'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
     'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
     'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
     'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
     'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
     'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
     'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
     'toothbrush']

    SCORE_THRESHOLD= 0.5


    ALLOWED_EXTENSIONS = {
        # 一般常見格式
        'jpg', 'jpeg', 'png',
        'webp', 'bmp',
        # iPhone (iOS)
        'heic', 'heif',
        # Android
        'avif',
        # RAW 格式 (部分高階手機)
        'dng'
    }

    # sqlite lock class
    IMAGE_PROCESS = "image_process"