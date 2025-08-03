# AstrBot 图片审查插件

AstrBot 图片审查插件，为机器人回复中可能出现的成人内容图像打码，使能够顺利发送原本可能被社交平台屏蔽的消息。

## 使用方法

启用插件后，机器人在发送消息前会审查消息中的图片，若模型认为其包含成人内容，则对全图进行高斯模糊处理再发送。

- `/censor help` 查看帮助

## 可选模型

- [NudeNet](https://github.com/notAI-tech/NudeNet): 本地轻量模型，审查图中是否有特定人体部位。插画、漫画测试表现不稳定。

- [Sightengine Image Moderation](https://sightengine.com/image-moderation): 使用 API 判断图像中含成人内容的可能性。免费订阅有限额。
  > 由于插件会审查机器人发送的**所有**图片，因此可能花费高于预期的配额，请谨慎使用。
