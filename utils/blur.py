import cv2
from pathlib import Path

def blur_image(image_path: str, out_path: Path, scale: int):
    """scale 越小，模糊程度越高，典型范围 60~120"""
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"OpenCV 读取不到图片: {image_path}")

    h, w = img.shape[:2]
    longest = max(w, h)

    # 1. 计算核大小 (至少 3，且必须是奇数)
    k = max(3, int(round(longest / scale)))
    if k % 2 == 0:
        k += 1

    # 2. 高斯模糊
    blurred = cv2.GaussianBlur(img, (k, k), sigmaX=0)

    # 3. 存储到文件
    cv2.imwrite(out_path, blurred, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
