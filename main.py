from astrbot.api import logger
from astrbot.api.all import *
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.message_components import Image
from astrbot.api.star import Context, Star, register

import aiohttp
import httpx
import os
import tempfile
from nudenet import NudeDetector
from pathlib import Path
from urllib.parse import urlparse, unquote

from .utils.b64 import b64_to_jpeg_file
from .utils.blur import blur_image
from .utils.sightengine import request_sightengine


detector = NudeDetector()
TEMP_DIR = Path("/AstrBot/data/plugins/astrbot_plugin_image_censor/tmp")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

@register("image_censor", "Omnisch", "回复结果图片审查", "1.0.0")
class ImageCensor(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config or {}
        self.censor_model = self.config.get("censor_model")
        self.blur_scale = self.config.get("blur_scale")
        self.sightengine_config = self.config.get("sightengine_config")
        self.se_api_user = self.sightengine_config.get("api_user")
        self.se_api_secret = self.sightengine_config.get("api_secret")

    @staticmethod
    async def ensure_local(seg) -> str | None:
        """确保图片文件转换到本地，返回本地路径"""
        s = seg.file

        # 先把 file:// 方案头剥掉
        if s.startswith("file://"):
            s = unquote(urlparse(s).path)

        # 1. 已经是本地文件
        if os.path.isfile(s):
            return s

        # 2. http/https
        if s.startswith("http"):
            suffix = Path(urlparse(s).path).suffix or ".jpg"
            tmp = tempfile.NamedTemporaryFile(delete=False, dir=TEMP_DIR, suffix=suffix)
            tmp.write((await httpx.AsyncClient().get(s)).content)
            tmp.close()
            return tmp.name

        # 3. data-URI / 原始 base64
        # Path 会报 "File name too long"
        if s.startswith(("data:", "base64://")) or len(s) > 1024:
            yield b64_to_jpeg_file(s, TEMP_DIR)

        raise ValueError(f"无法识别的文件字段: {s[:80]}…")

    @filter.command_group("censor")
    def censor(self):
        """图片审查命令组"""
        pass

    @censor.command("help")
    async def help(self, event: AstrMessageEvent):
        """查看帮助"""
        yield event.plain_result(
            "图片审查插件使用方法:\n"
            "- 机器人发送图片时，插件会自动检测是否包含不适宜内容。\n"
            "- 如果图片包含不适宜内容，机器人会回复警告信息。\n"
            "- 如果图片安全，将回复确认信息。"
        )
        return

    @filter.on_decorating_result()
    async def on_decorating_result(self, event: AstrMessageEvent):
        """对即将发送的信息进行图片审查"""
        result = event.get_result()

        # 清空 TEMP_DIR 中的旧文件
        for tmp_file in TEMP_DIR.glob("*"):
            try:
                if tmp_file.is_file():
                    tmp_file.unlink()
            except Exception as e:
                logger.error(f"清理临时文件失败: {e}")

        for idx, seg in enumerate(result.chain):
            # 处理单个消息段
            if isinstance(seg, Image):
                origin_path = await self.ensure_local(seg)
                out_path = TEMP_DIR / f"blurred_{Path(origin_path).name}"
                if origin_path and Path(origin_path).is_file():
                    logger.info(f"正在审查图片: {origin_path}, 模型: {self.censor_model}")

                    # 使用 Sightengine 进行审查
                    if self.censor_model == "sightengine":
                        response = request_sightengine(origin_path, self.se_api_user, self.se_api_secret)
                        if response.get("status") == "success":
                            # 检查是否 R-18G
                            score_g = response.get("nudity", {}).get("gore", 0)
                            if score_g > 0.5:
                                blur_image(origin_path, out_path, self.blur_scale)
                                result.chain[idx] = Image.fromFileSystem(str(out_path))
                                logger.info(f"图片疑似包含 R-18G 内容 ({score_g})，已模糊处理。")
                            else:
                                # 检查是否 R-18
                                score_sa = response.get("nudity", {}).get("sexual_activity", 0)
                                score_sd = response.get("nudity", {}).get("sexual_display", 0)
                                score_er = response.get("nudity", {}).get("erotica", 0)
                                if score_sa > 0.5 or score_sd > 0.5 or score_er > 0.8:
                                    blur_image(origin_path, out_path, self.blur_scale)
                                    result.chain[idx] = Image.fromFileSystem(str(out_path))
                                    logger.info(f"图片疑似包含 R-18 内容 ({max(score_sa, score_sd)})，已模糊处理。")
                    
                    # 使用 NudeNet 进行审查
                    elif self.censor_model == "nudenet":
                        detect_result = detector.detect(origin_path)
                        for detection in detect_result:
                            if detection.get("class") in [
                                "FEMALE_BREAST_EXPOSED",
                                "FEMALE_GENITALIA_EXPOSED",
                                "ANUS_EXPOSED",
                                "MALE_GENITALIA_EXPOSED"
                            ]:
                                blur_image(origin_path, out_path, self.blur_scale)
                                result.chain[idx] = Image.fromFileSystem(str(out_path))
                                logger.info(f"图片疑似包含裸露内容，已模糊处理。")
