# 一个文件监控信息
# 需要安装的依赖
# pip install loguru pydantic pyrogram
# 运行 python 监控信息.py

# 需要监控的关键词
keyword = ["飞机", "幼小女生"]
# 如果有 TGBot.session 文件下面的两项可以省略
api_id = 1111
api_hash = ""

LogLevel = "INFO"  # 日志级别 INFO 正常 DEBUG 超级详细
forword_id = ["me"]  # 需要转发的id me为收藏夹

# ======== 下面的东西不要动，球球了帅哥 ============


import pyrogram
from pyrogram.types import Message
from loguru import logger
from typing import List, Union, Set
from pydantic import BaseModel
from pyrogram.handlers import MessageHandler
from pathlib import Path
import sys
import asyncio
from pyrogram import Client, idle



ROOTPATH = Path(__file__).parent.absolute()


class KeyMonitorConfig(BaseModel):
    enable: bool  # 是否启动
    keyword: List[str] = ["做爱"]
    forword_id: List[Union[str, int]] = ["me"]


class Config(BaseModel):
    name: str = "TGBot"
    api_id: Union[str, int]
    api_hash: str
    LogLevel: str = "DEBUG"
    keyMonitor: Union[KeyMonitorConfig, str, None] = None


conf = Config(
    api_id=api_id,
    api_hash=api_hash,
    LogLevel=LogLevel,
    keyMonitor=KeyMonitorConfig(
        enable=True,
        keyword=keyword,
        forword_id=forword_id
    )
)

# RuntimeError: uvloop does not support Windows at the moment
try:
    import uvloop
    uvloop.install()
except ImportError:
    logger.info("UVloop not found use default event loop!")


# handles with Messages


async def forwardKeyworkMessageToMe(client: pyrogram.client.Client, message: Message):
    logger.debug(f"rev: {message.text}")
    if (message.text and conf.keyMonitor.enable):
        for key in conf.keyMonitor.keyword:
            if key in message.text:
                for fid in conf.keyMonitor.forword_id:
                    await message.forward(chat_id=fid)
                    logger.success(
                        "catch key:%s forward: %s" %
                        (key, message.text[:10].strip())
                    )


def getLogger(loglevel):
    logger.remove()
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:HH:mm:ss}</green> | {name}:{function} {level} | <level>{message}</level>",
        level=loglevel,
        backtrace=True,
        diagnose=True
    )


async def main():

    global app
    # use session to login
    if Path(ROOTPATH, "%s.session" % conf.name).exists():
        logger.info(".session exists!use session to login")
        app = Client(name=conf.name)
    else:
        app = Client(
            name=conf.name,
            api_id=conf.api_id,
            api_hash=conf.api_hash
        )

    await app.start()  # 启动

    app.add_handler(
        MessageHandler(
            forwardKeyworkMessageToMe,
            filters=None,
        )
    )

    user = await app.get_me()
    logger.success(
        f"login Account Success user:{user.first_name} phone_number:{user.phone_number}"
    )

    await idle()  # 堵塞

if __name__ == "__main__":
    getLogger(conf.LogLevel)
    asyncio.run(main())
