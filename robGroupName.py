# ====== pyrogram =======
import pyromod
from pyromod.helpers import ikb, array_chunk  # inlinekeyboard
from pyrogram import Client, idle, filters  # type:ignore
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    BotCommand,
    CallbackQuery,
)
from pyrogram.handlers import MessageHandler  # type:ignore
from pyrogram.enums import ParseMode
from pyrogram import errors

# ====== pyrogram end =====

from contextlib import closing, suppress
from typing import List, Union, Any, Optional, Callable
from pathlib import Path
import asyncio
from loguru import logger
import sys
import re
from functools import wraps
import os
import sys
import glob
import httpx
from httpx import Limits

# ====== Config ========
ROOTPATH: Path = Path(__file__).parent.absolute()
DEBUG = False
NAME = os.environ.get("NAME") or "cheryywk"
API_ID = 21341224
API_HASH = "2d910cf3998019516d6d4bbb53713f20"
SESSION_FOLDER = Path(ROOTPATH, "sessions")
SESSION_PATH: Path = Path(SESSION_FOLDER, f"{NAME}.txt")

# 需要监控的名称 @xuncha  @baobei @heshi @hexiao
ROB_GROUP_NAME = ["xuncha", "baobei", "heshi", "hexiao"]
# 需要设置群名称的群,抢注通知 -1001963862221
GROUP_ID: int = -1001833946235
__desc__ = """
群组名字抢注程序
"""
# ====== Config End ======

# ===== logger ====
logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:HH:mm:ss}</green> | {name}:{function} {level} | <level>{message}</level>",
    level="DEBUG" if DEBUG else "INFO",
    backtrace=True,
    diagnose=True,
)
# ===== logger end =====

# ===== error handle =====


def capture_err(func):
    """handle error and notice user"""

    @wraps(func)
    async def capture(
        client: Client, message: Union[Message, CallbackQuery], *args, **kwargs
    ):
        try:
            return await func(client, message, *args, **kwargs)
        except errors.exceptions.flood_420.FloodWait as wait_err:
            logger.error(f"太快了进入等待:{wait_err.value}s")
            await asyncio.sleep(wait_err.value)  # type:ignore
        except Exception as err:
            if isinstance(message, CallbackQuery):
                await message.message.reply(
                    f"机器人按钮回调 Panic 了:\n<code>{err}</code>"
                )
            else:
                await message.reply(f"机器人 Panic 了:\n<code>{err}</code>")
            raise err

    return capture


# ====== error handle end =========

# ====== Client maker =======


def makeClient(path: Path) -> Client:
    session_string = path.read_text(encoding="utf8")
    return Client(
        name=path.stem,
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=session_string,
        in_memory=True,
    )


app = makeClient(SESSION_PATH)

# ====== Client maker end =======

# ====== helper function  ====
# https://t.me/python_zh_zh


class CheckNameExist(object):
    """检测一个用户名是否存在"""

    def __init__(self) -> None:
        self.stratURL = "https://t.me/"
        self.session = httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Linux; U; Android 9; zh-CN; LON-AL00 Build/HUAWEILON-AL00) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.108 UCBrowser/13.1.7.1097 Mobile Safari/537.36"
            },
            verify=False,
            limits=Limits(max_connections=1000, max_keepalive_connections=500),
            follow_redirects=True,
            timeout=8,
        )
        self.availableQueue = asyncio.Queue()

    async def isExist(self, name: str) -> bool:
        resp = await self.session.get(self.stratURL + name)
        if resp.url != self.stratURL + name:
            logger.debug(f"@{name} not found (302 redirect)")
            return False

        if "tgme_icon_user" in resp.text:
            logger.debug(f"@{name} not found")
            return False

        logger.debug(f"@{name} exist")
        return True

    async def loopCheck(self, name: str):
        """循环检测"""
        while True:
            try:
                is_exist = await self.isExist(name)
            except Exception as exc:
                logger.exception(f"requests error:{exc}")
                continue

            if not is_exist:
                logger.success(f"检测到 @{name} 可用")
                await self.availableQueue.put(name)
                return

            logger.info(f"{name} 不可用！")
            await asyncio.sleep(0.5)

    async def multiLoopCheck(self, names: List[str]):
        current_loop = asyncio.get_running_loop()
        for name in names:
            logger.info(f"ADD {name} conruntine")
            asyncio.ensure_future(self.loopCheck(name), loop=current_loop)


checker = CheckNameExist()

# ====== helper function end ====

# ===== Handle ======


@app.on_message(filters=filters.command("start"))
@capture_err
async def start(client: Client, message: Message):
    await message.reply_text(__desc__)


@app.on_message(filters=filters.command("getID"))
@capture_err
async def get_ID(client: Client, message: Message):
    await message.reply(
        f"当前会话的ID:<code>{message.chat.id}</code>\n发送方用户ID:<code>{message.from_user.id}</code>"
    )


# ==== Handle end =====


async def setGroupLinkLoop(client: Client, queue: asyncio.Queue):
    while True:
        try:
            name = await queue.get()
            if await client.set_chat_username(GROUP_ID, name):
                logger.success(f"修改成{name}成功！")
                await client.send_message(
                    chat_id=GROUP_ID, text=f"抢注 {name} 成功！"
                )
        except errors.exceptions.flood_420.FloodWait as wait_err:
            logger.error(f"改名太快了进入等待:{wait_err.value}s")
            await asyncio.sleep(wait_err.value)  # type:ignore
        except Exception as exc:
            logger.exception(f"改名出现错误:{exc}")
            continue


@logger.catch()
async def main():
    global app
    await app.start()
    user = await app.get_me()
    logger.success(
        f"""
-------login success--------
username: {user.first_name}
type: {"Bot" if user.is_bot else "User"}
@{user.username}
----------------------------
"""
    )
    await app.send_message(chat_id=GROUP_ID, text=f"开始抢注以下名称:{ROB_GROUP_NAME}")
    await checker.multiLoopCheck(ROB_GROUP_NAME)
    await setGroupLinkLoop(app, checker.availableQueue)

    # ===== Test Code =======
    # chat_id = await app.get_chat("@w2ww2w2w")
    # print(chat_id)

    # ======== Test Code end ==========

    await idle()
    await app.stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    with closing(loop):
        with suppress(asyncio.exceptions.CancelledError):
            loop.run_until_complete(main())

        loop.run_until_complete(asyncio.sleep(3.0))  # task cancel wait 等待任务结束
