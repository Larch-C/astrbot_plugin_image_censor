from astrbot.api import logger
from astrbot.api.all import *
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.message_components import Image
from astrbot.api.star import Context, Star, register

import aiohttp
import base64
import httpx
import tempfile
from nudenet import NudeDetector
from pathlib import Path

_detector = NudeDetector()

async def ensure_local(seg):
    s = seg.file

    # 1) data URL / raw base64
    if s.startswith("base64://") or s[:50].rstrip("=").__len__() > 1000:
        data = s.split(",", 1)[-1]            # 去掉 schema 头
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        tmp.write(base64.b64decode(data))
        tmp.close()
        return tmp.name

    # 2) http(s)
    if s.startswith("http"):
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=Path(s).suffix or ".jpg")
        tmp.write((await httpx.AsyncClient().get(s)).content)
        tmp.close()
        return tmp.name

    # 3) 已经是本地文件
    return s

@register("image_censor", "Omnisch", "回复结果图片审查", "0.1.0")
class ImageCensor(Star):
    def __init__(self, context: Context):
        super().__init__(context)
    
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
        images: list[bytes] = []
        result = event.get_result()

        async def _process_segment(_seg):
            """处理单个消息段"""
            if isinstance(_seg, Image):
                logger.info(f"检测到图片")
                real_path = await ensure_local(_seg)
                if real_path and Path(real_path).is_file():
                    with open(real_path, "rb") as f:
                        img_bytes = f.read()
                    images.append(img_bytes)

        for seg in result.chain:
            await _process_segment(seg)

        if len(images) > 0:
            logger.info(f"检测到 {len(images)} 张图片，开始审查...")
        else:
            logger.info("没有检测到图片，跳过审查。")
