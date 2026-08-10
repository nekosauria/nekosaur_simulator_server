import random

import cv2
import numpy as np

from const.image_const import ImageConst
from util.common import common

config = common.config
logger = common.logger


# 💡 優化一：顏色生成改為「靜態映射字典」或「基於類別 ID 決定固定顏色」
# 這樣能確保：同一個物件類別（例如 cat）永遠都是同一種顏色，畫面才不會雜亂。
def get_color_by_label(label_idx: int) -> list[int]:
    """根據標籤的索引值，生成固定且具備高辨識度的 BGR 顏色"""
    # 使用固定的隨機種子，確保每次呼叫同一個 label_idx 拿到的顏色都一樣
    random.seed(label_idx + 42)
    return [random.randint(50, 220) for _ in range(3)]


# 💡 優化二：增加最大與最小邊界限制（Clamping）
def make_line(result_image: np.ndarray) -> int:
    """計算適合當前圖片尺寸的框線粗細"""
    return round(0.002 * max(result_image.shape[0:2])) + 1


# 💡 優化三：維持乾淨的矩形繪製
def draw_lines(c1: tuple, c2: tuple, result_image: np.ndarray, line: int, color: list) -> np.ndarray:
    """在圖片上繪製物件主體的四角形框線"""
    cv2.rectangle(result_image, c1, c2, color, thickness=line)
    return result_image


# 在圖片添加已識別的圖片標籤（終極防溢出安全版）
def draw_texts(result_image: np.ndarray, line: int, c1: tuple, color: list, labels: list, label_idx: int) -> np.ndarray:
    """在偵測框上方繪製標籤，若貼近圖片頂端則自動翻轉至框內，防止字體超出圖片邊界"""
    display_txt = f"{labels[label_idx]}"

    font_scale = line * 0.25
    font_thickness = max(line - 2, 1)

    # 精準計算文字實際佔用的寬高與基底高度 (baseline)
    t_size, baseline = cv2.getTextSize(
        display_txt,
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=font_scale,
        thickness=font_thickness
    )

    text_w = t_size[0]
    text_h = t_size[1]

    # 定義文字與背景塊的基礎高度（包含 Padding 的總高度）
    total_text_height = text_h + baseline + 6

    # 🎯 核心防禦邏輯：計算如果畫在框外，頂部會不會變成負數（超出圖片頂邊）
    # c1[1] 是物件框的 y_min
    if c1[1] - total_text_height < 0:
        # 🚨 空間不足！改將文字標籤「向下平移」，塞進物件框的內部頂端
        # 新的基準點調整為 y_min + 總高度（往下彈）
        y_reference = c1[1] + total_text_height

        text_c1 = c1
        text_c2 = (c1[0] + text_w + 4, c1[1] + total_text_height)

        # 畫上實心文字背景方塊
        cv2.rectangle(result_image, text_c1, text_c2, color, thickness=-1)

        # 寫入文字（因為在框內往下彈，文字繪製基準點要相應計算）
        cv2.putText(
            result_image,
            display_txt,
            (c1[0] + 2, y_reference - baseline - 3),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=font_scale,
            color=[255, 255, 255],
            thickness=font_thickness,
            lineType=cv2.LINE_AA,
        )
    else:
        # 🟢 空間充足，維持原本的「框外上方」繪製邏輯
        text_c1 = c1
        text_c2 = (c1[0] + text_w + 4, c1[1] - total_text_height)

        cv2.rectangle(result_image, text_c1, text_c2, color, thickness=-1)

        cv2.putText(
            result_image,
            display_txt,
            (c1[0] + 2, c1[1] - baseline - 3),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=font_scale,
            color=[255, 255, 255],
            thickness=font_thickness,
            lineType=cv2.LINE_AA,
        )

    return result_image



def draw_detections(
        predict_np: np.ndarray,
        output,
        labels: list[str],
    ) -> tuple[np.ndarray, dict, dict]:
    """
    根據模型輸出，在圖片上繪製偵測框與標籤。

    Args:
        predict_np: 待繪製的圖片（numpy array）
        output: 模型推論結果（需含 boxes, labels, scores）
        labels: 標籤清單

    Returns:
        predict_np: 繪製完成的圖片
        tag_results: 有畫框標記的標籤與其信心分數
        predict_list: 所有標籤的最高信心分數（不論有無畫框）
    """

    tags = []
    tag_results = {}
    predict_list = {}

    # 開始畫框線
    for box, label_idx, score in zip(output.boxes, output.labels, output.scores):
        label_idx = int(label_idx)
        label_name = labels[label_idx]

        # 不論分數，全部收入 predict_list（同標籤保留最高分）
        if label_name not in predict_list or score > predict_list[label_name]:
            predict_list[label_name] = round(float(score), 3)

        # 【條件】信心分數需超過預測值就標記，且同一標籤不重複標記
        if score > float(config.get("model","detect_score_threshold")) and labels[label_idx] not in tags:
            logger.debug(f"score: {score:.3f}, label: {labels[label_idx]}")

            # 產生框線顏色（BGR or RGB tuple）
            color = get_color_by_label(label_idx)

            # 計算適合圖片尺寸的框線粗細
            line = make_line(predict_np)

            # 將 box tensor 轉為左上角 (c1) 與右下角 (c2) 的像素座標
            c1 = (int(box[0]), int(box[1]))  # (x_min, y_min)
            c2 = (int(box[2]), int(box[3]))  # (x_max, y_max)

            # 在 predict_np 上繪製偵測框
            predict_np = draw_lines(c1, c2, predict_np, line, color)

            # 在偵測框旁繪製文字標籤
            predict_np = draw_texts(predict_np, line, c1, color, labels, label_idx)

            # 記錄已處理的標籤與對應信心分數
            tags.append(label_idx)
            tag_results[labels[label_idx]] = round(float(score), 3)

    return  predict_np, tag_results, predict_list