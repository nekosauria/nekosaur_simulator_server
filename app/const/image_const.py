from util.common import common

config = common.config

thecatapi_image_source = config.get('image', 'thecatapi_image_source')
thecatapi_origin_path = config.get('image', 'thecatapi_origin_path')
thecatapi_detect_path = config.get('image', 'thecatapi_detect_path')
thecatapi_transform_path = config.get('image', 'thecatapi_transform_path')

user_upload_image_source = config.get('image', 'user_upload_image_source')
user_upload_origin_path = config.get('image', 'user_upload_origin_path')
user_upload_detect_path = config.get('image', 'user_upload_detect_path')
user_upload_transform_path = config.get('image', 'user_upload_transform_path')

# 常數不需要用 self.var
# 一般來說要 new object 時才會用到 self.var
class ImageConst:

    # 💡 新增模型名稱常數
    # 上傳圖片路徑, 直接從 config 拿參數
    # User Upload
    USER_UPLOAD_IMAGE_SOURCE = user_upload_image_source
    USER_UPLOAD_ORIGIN_PATH = user_upload_origin_path
    USER_UPLOAD_DETECT_PATH = user_upload_detect_path
    USER_UPLOAD_TRANSFORM_PATH = user_upload_transform_path
    # TheCatAPI
    THECATAPI_IMAGE_SOURCE = thecatapi_image_source
    THECATAPI_ORIGIN_PATH = thecatapi_origin_path
    THECATAPI_DETECT_PATH = thecatapi_detect_path
    THECATAPI_TRANSFORM_PATH = thecatapi_transform_path
    # image_source -> image_detect_path
    IMAGE_SOURCE_TO_DETECT_PATH = {
        THECATAPI_IMAGE_SOURCE: THECATAPI_DETECT_PATH,
        USER_UPLOAD_IMAGE_SOURCE: USER_UPLOAD_DETECT_PATH,
    }
    # image_source -> image_transform_path
    IMAGE_SOURCE_TO_TRANSFORM_PATH = {
        THECATAPI_IMAGE_SOURCE: THECATAPI_TRANSFORM_PATH,
        USER_UPLOAD_IMAGE_SOURCE: USER_UPLOAD_TRANSFORM_PATH,
    }


    # detect
    # "torchvision.models.detection.maskrcnn_resnet50_fpn"
    MODEL_TORCH = "maskrcnn_model"
    # "ultralytics.YOLO"
    MODEL_YOLO = "yolo11n"

    # transform
    MODEL_STABLE_DIFFUSION = "stable-diffusion-v1-5"
    MODEL_SD_IMAGE_VARIATIONS = "sd-image-variations-diffusers"

    # embedding
    MODEL_CLIP_VIT_B_32 = "clip-ViT-B-32"

    # 💡 模型名稱 Array / List
    DETECT_MODELS = [
        MODEL_TORCH,
        MODEL_YOLO,
    ]

    TRANSFORM_MODELS = [
        MODEL_STABLE_DIFFUSION,
        MODEL_SD_IMAGE_VARIATIONS,
    ]

    EMBEDDING_MODELS = [
        MODEL_CLIP_VIT_B_32
    ]

    # 用於物件偵測的標籤
    TORCH_LABELS = [
        "unlabeled", "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
        "traffic light", "fire hydrant", "street sign", "stop sign", "parking meter", "bench", "bird", "cat", "dog",
        "horse",
        "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "hat", "backpack", "umbrella", "shoe",
        "eye glasses", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite",
        "baseball bat",
        "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "plate", "wine glass", "cup", "fork",
        "knife",
        "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza",
        "donut", "cake", "chair", "couch", "potted plant", "bed", "mirror", "dining table", "window", "desk",
        "toilet", "door", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave", "oven",
        "toaster", "sink", "refrigerator", "blender", "book", "clock", "vase", "scissors", "teddy bear", "hair drier",
        "toothbrush"
    ]

    YOLO_LABELS = [
        'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
        'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
        'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
        'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
        'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
        'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
        'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
        'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
        'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
        'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
        'toothbrush'
    ]

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