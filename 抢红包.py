# ====== pyrogram =======
import pyromod
from pyromod.helpers import ikb, array_chunk  # inlinekeyboard
from pyrogram import Client, idle, filters
from pyrogram.types import Message, InlineKeyboardMarkup, User
from pyrogram.enums import ParseMode
from pyrogram.raw import functions
from urllib.parse import urlparse, parse_qs
# ====== pyrogram end =====

from contextlib import closing, suppress
from typing import List, Union, Any, Optional
from pathlib import Path
import asyncio
from loguru import logger
import sys
import re
from functools import wraps
import random

# ====== Config ========
ROOTPATH: Path = Path(__file__).parent.absolute()
DEBUG = True
# 更改以下两个参数
# txt 文件的名字
NAME = "cheryywk"
# 监控红包的群聊 ID 如果不知道,启动机器人后发送 /getID 就可以了
REDPACK_GROUP_ID = -1001968860718
API_ID = 21341224
API_HASH = "2d910cf3998019516d6d4bbb53713f20"
SESSION_PATH: Path = Path(ROOTPATH, "sessions", f"{NAME}.txt")
__desc__ = """
抢红包
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
    diagnose=True
)
# ===== logger end =====

# ===== error handle =====


def capture_err(func):
    """handle error and notice user"""
    @wraps(func)
    async def capture(client: Client, message: Message, *args, **kwargs):
        try:
            return await func(client, message, *args, **kwargs)
        except Exception as err:
            await message.reply(f"机器人 Panic 了:\n<code>{err}</code>")
            raise err
    return capture
# ====== error handle end =========

# ====== Client maker =======


def makeClient(path: Path) -> Client:
    session_string = path.read_text(encoding="utf8")
    return Client(
        name="test",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=session_string,
        in_memory=True
    )


async def makeSessionString(**kwargs) -> str:
    client = Client(
        name="test",
        api_id=API_ID,
        api_hash=API_HASH,
        in_memory=True,
        **kwargs
    )

    async with client as c:
        print(await c.export_session_string())


app = makeClient(SESSION_PATH)
# ====== Client maker end =======

# ====== helper function  ====


def parse_url(url: str):
    parsed = urlparse(url)
    return parsed.path[1:], parse_qs(parsed.query)['start']

# ====== helper function end ====

# ===== Handle ======


@app.on_message(filters=filters.command("start") & filters.private)
@capture_err
async def start(client: Client, message: Message):
    await message.reply_text(__desc__)

# @bao5bot 5027290533


@app.on_message(filters=filters.chat(5027290533) & filters.inline_keyboard)
async def handle_redpacket_bot(client: Client, message: Message):
    reply_markup = message.reply_markup.inline_keyboard[0]
    for button in reply_markup:
        if "点击领取红包" in button.text:
            logger.success(f"开始抢红包！")
            await client.request_callback_answer(message.chat.id, message.id, button.callback_data)
            # await message.reply("红包程序已经抢了,请查看结果！")
    logger.error("红包程序无法识别或者已经抢完了")
    # await message.reply("红包程序无法识别或者已经抢完了")


@app.on_message(filters=filters.chat(REDPACK_GROUP_ID) & filters.inline_keyboard)
@capture_err
async def handle_redpacket(client: Client, message: Message):
    reply_markup = message.reply_markup.inline_keyboard[0]
    for button in reply_markup:
        if "抢红包 点底部开始" in button.text:
            url = button.url
            username, start_param = parse_url(url)
            # await message.reply(f"发现红包!! 跳转机器人:{username} param:{start_param[0]}")
            logger.success(f"发现红包!! 跳转机器人:{username} param:{start_param[0]}")

            bot_peer_id = await client.resolve_peer(username)

            await client.invoke(
                functions.messages.StartBot(
                    bot=bot_peer_id,
                    peer=bot_peer_id,
                    start_param=start_param[0],
                    random_id=random.randint(1000, 9999)
                )
            )


@app.on_message(filters=filters.command("getID"))
@capture_err
async def get_ID(client: Client, message: Message):
    await message.reply(
        f"当前会话的ID:<code>{message.chat.id}</code>"
    )


# ==== Handle end =====


async def main():
    global app
    await app.start()
    user = await app.get_me()

    # ===== Test Code =======
    # chat_id = await app.get_chat("@w2ww2w2w")
    # print(chat_id)

    # ======== Test Code end ==========

    logger.success(
        f"""
-------login success--------
username: {user.first_name}
type: {"Bot" if user.is_bot else "User"}
@{user.username}
----------------------------
"""
    )

    await idle()
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    with closing(loop):
        with suppress(asyncio.exceptions.CancelledError):
            loop.run_until_complete(main())
        loop.run_until_complete(asyncio.sleep(3.0))  # task cancel wait 等待任务结束
    # asyncio.run(makeSessionString())
