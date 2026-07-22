from ultralytics import YOLO
from utils.pypath import load_PP

# https://docs.ultralytics.com/models/yolo11/
# 下載 yolo11n model（最輕量版本）
model = YOLO("yolo11n.pt")  # 第一次執行會自動下載權重

# get 對應 labels
labels = list(model.names.values())

print(labels)
# ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
#  'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
#  'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
#  'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
#  'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
#  'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
#  'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
#  'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
#  'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
#  'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
#  'toothbrush']

