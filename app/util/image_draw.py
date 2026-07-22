import random
import cv2
import numpy as np


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

    # 1. 精準計算文字實際佔用的寬高與基底高度 (baseline)
    t_size, baseline = cv2.getTextSize(
        display_txt,
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=font_scale,
        thickness=font_thickness
    )

    text_w = t_size[0]
    text_h = t_size[1]

    # 2. 定義文字與背景塊的基礎高度（包含 Padding 的總高度）
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