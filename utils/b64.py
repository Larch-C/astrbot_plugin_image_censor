from PIL import Image
import base64
import io
import os
import pathlib
import tempfile
from urllib.parse import unquote_to_bytes

def strip_b64_header(s: str) -> bytes:
    """准确提取 base64 & URL 解码"""
    # 1. 去掉 schema（可能是 base64:// 或 data:image/png;base64,）
    if "base64://" in s:
        s = s.split("base64://", 1)[1]
    if "base64," in s:
        s = s.split("base64,", 1)[1]

    # 2. URL 解码：把 %2B %2F 等换回 + /
    s = unquote_to_bytes(s).decode("ascii")

    # 3. 去掉空格 / 换行（某些平台会把长串自动折行）
    s = s.replace("\n", "").replace(" ", "")
    # 4. 末尾补齐 '='
    padding = len(s) % 4
    if padding:
        s += "=" * (4 - padding)
    return base64.b64decode(s, validate=False)    

def b64_to_jpeg_file(b64str: str, workdir: pathlib.Path) -> str:
    """用 Pillow 把任意格式统一转换为 JPEG"""
    raw = strip_b64_header(b64str)
    img = Image.open(io.BytesIO(raw))   # Pillow 能读 PNG/WebP/GIF
    img = img.convert("RGB")            # OpenCV 不支持透明通道
    fd, out_path = tempfile.mkstemp(dir=workdir, suffix=".jpg")
    os.close(fd)
    img.save(out_path, "JPEG", quality=92)
    return out_path                     # JPEG
