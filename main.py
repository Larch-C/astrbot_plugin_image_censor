from astrbot.api import logger
from astrbot.api.all import *
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.message_components import Image
from astrbot.api.star import Context, Star, register

import aiohttp
import base64
import httpx
import os
import tempfile
from nudenet import NudeDetector
from pathlib import Path
from urllib.parse import urlparse, unquote

detector = NudeDetector()
tempfile_path = "//AstrBot/data/plugins/astrbot_plugin_image_censor/tmp"

@register("image_censor", "Omnisch", "回复结果图片审查", "0.1.0")
class ImageCensor(Star):
    def __init__(self, context: Context):
        super().__init__(context)
    
    @staticmethod
    async def download_image(url: str) -> bytes | None:
        """下载图片"""
        url = url.replace("https://", "http://")
        try:
            async with aiohttp.ClientSession() as client:
                response = await client.get(url)
                img_bytes = await response.read()
                return img_bytes
        except Exception as e:
            logger.error(f"图片下载失败: {e}")

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
            tmp = tempfile.NamedTemporaryFile(delete=False, dir=tempfile_path, suffix=suffix)
            tmp.write((await httpx.AsyncClient().get(s)).content)
            tmp.close()
            return tmp.name

        # 3. data-URI / 原始 base64
        # Path 会报 "File name too long"
        if s.startswith("data:") or len(s) > 1024:
            _, b64 = s.split(",", 1) if "," in s else ("", s)
            tmp = tempfile.NamedTemporaryFile(delete=False, dir=tempfile_path, suffix=".jpg")
            tmp.write(base64.b64decode(b64))
            tmp.close()
            return tmp.name

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

        for idx, seg in enumerate(result.chain):
            """处理单个消息段"""
            if isinstance(seg, Image):
                real_path = await self.ensure_local(seg)
                if real_path and Path(real_path).is_file():
                    logger.info(f"正在审查图片: {real_path}")
                    out_path = tempfile_path + "/" + event.message_obj.message_id + "_censored.jpg"
                    detector.censor(
                        real_path,
                        classes=[
                            "FEMALE_GENITALIA_COVERED",
                            "FEMALE_BREAST_EXPOSED",
                            "FEMALE_GENITALIA_EXPOSED",
                            "MALE_GENITALIA_EXPOSED"
                        ],
                        output_path=out_path
                    )
                    result.chain[idx] = Image.fromFileSystem(path=out_path)
                    logger.info(f"图片审查完成，保存到: {out_path}")
