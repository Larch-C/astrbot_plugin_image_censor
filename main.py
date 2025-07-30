from astrbot.api import logger
from astrbot.api.all import *
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register

import astrbot.api.message_components as Comp
import aiohttp
import base64

from nudenet import NudeDetector
from pathlib import Path

_detector = NudeDetector()

@register("image_censor", "Omnisch", "回复结果图片审查", "0.1.0")
class ImageCensor(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def _download_image(url: str) -> bytes | None:
        """下载图片"""
        url = url.replace("https://", "http://")
        try:
            async with aiohttp.ClientSession() as session:
                response = await session.get(url)
                img_bytes = await response.read()
                return img_bytes
        except Exception as e:
            logger.error(f"图片下载失败: {e}")

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
    async def on_decorating_result(self, event: AstrMessageEvent, result: MessageEventResult):
        """对即将发送的信息进行图片审查"""
        images: list[bytes] = []
        messages = event.get_messages()

        async def _process_segment(_seg):
            """处理单个消息段"""
            if isinstance(_seg, Comp.Image):
                if hasattr(_seg, "url") and _seg.url:
                    img_url = _seg.url
                    if Path(img_url).is_file():
                        with open(img_url, "rb") as img_file:
                            images.append(img_file.read())
                    else:
                        if img_msg := await self._download_image(img_url):
                            images.append(img_msg)
                elif hasattr(_seg, "file"):
                    file_content = _seg.file
                    if isinstance(file_content, str):
                        if Path(file_content).is_file():
                            with open(file_content, "rb") as img_file:
                                images.append(img_file.read())
                        else:
                            if file_content.startswith("base64://"):
                                file_content = file_content[len("base64://"):]
                            file_content = base64.b64decode(file_content)
                    if isinstance(file_content, bytes):
                        images.append(file_content)

        for seg in messages:
            await _process_segment(seg)

        if len(images) > 0:
            logger.info(f"检测到 {len(images)} 张图片，开始审查...")
        else:
            logger.info("没有检测到图片，跳过审查。")
