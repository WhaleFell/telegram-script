#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
@File    :   getOKRedpacketBulk.py
@Time    :   2023/10/17 23:47:00
@Author  :   WhaleFall
@License :   (C)Copyright 2020-2023, WhaleFall
@Desc    :   批量登陆账号并抢夺 @okpay 的红包

实现原理:
@okpay 的红包
是点击按钮后通过 /start?param=? 这种参数识别,现在添加了
"""


# ====== pyrogram =======
from pyrogram import Client, idle, filters  # type: ignore
from pyrogram.handlers import MessageHandler  # type: ignore
from pyrogram.types import Message, InlineKeyboardMarkup, User
from pyrogram import errors
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
from functools import wraps
import os
import glob

# ====== Config ========
ROOTPATH: Path = Path(__file__).parent.absolute()
DEBUG = True
# 更改以下两个参数
# txt 文件的名字
# 监控红包的群聊 ID 如果不知道,启动机器人后发送 /getID 就可以了
# 可以监控多个群聊
REDPACK_GROUPS_ID = [
    -1001968860718,
    -1001968888888,
    -1001979255590,
    -1001811589217,
    -1001919310248,
]
API_ID = 21341224
API_HASH = "2d910cf3998019516d6d4bbb53713f20"
__desc__ = """
抢夺 @okpay 机器人的红包
2023/10/17 Update: 新增验证码的识别
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
        name=path.stem,
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=session_string,
        in_memory=True,
    )


def loadClientsInFolder() -> List[Client]:
    session_folder = Path(ROOTPATH, "sessions")
    file_paths = glob.glob(os.path.join(session_folder.as_posix(), "*.txt"))

    file_content_list = []
    for file_path in file_paths:
        with open(file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
            file_name = Path(file_path).stem
            file_content_list.append((file_name, file_content))

    return [
        Client(
            name=name,
            session_string=session,
            api_id=API_ID,
            api_hash=API_HASH,
            in_memory=True,
        )
        for name, session in file_content_list
    ]


# app = makeClient(SESSION_PATH)
# ====== Client maker end =======

# ====== helper function  ====


def parse_url(url: str):
    parsed = urlparse(url)
    return parsed.path[1:], parse_qs(parsed.query)["start"]


# ====== helper function end ====

# ===== Handle ======


# @bao5bot 5027290533


async def handle_all(client: Client, message: Message):
    print(message)


async def handle_inlineKeyboard_bot(client: Client, message: Message):
    logger.debug(f"识别到InlineKeyboard:{message.text}")
    for items in message.reply_markup.inline_keyboard:
        for item in items:
            try:
                await client.request_callback_answer(
                    chat_id=message.chat.id,
                    message_id=message.id,
                    callback_data=item.callback_data,
                )
            except errors.exceptions.bad_request_400.DataInvalid:
                logger.info("可忽略错误!")
            except Exception as e:
                logger.error(f"{client.me.first_name} 抢红包时出现错误!")


async def handle_redpacket_msg(client: Client, message: Message):
    logger.debug(f"识别到InlineKeyboard:{message.text}")
    if "红包" in message.text and client.me.first_name in message.text:
        for i in message.text.split("\n\n")[1].split("\n"):
            if client.me.first_name in i:
                logger.success(
                    "%s 抢到 %s " % client.me.first_name,
                    i.split(" ")[1].split("(")[0],
                    message.text.split("💰")[0].split(" ")[-1],
                )


# ==== Handle end =====


@logger.catch()
async def main():
    apps = loadClientsInFolder()

    for app in apps:
        await app.start()
        user = await app.get_me()

        # ===== Test Code =======

        # ======== Test Code end ==========

        # ======= Add handle ========
        # app.add_handler(
        #     MessageHandler(start, filters=filters.all)
        # )

        # app.add_handler(
        #     MessageHandler(get_ID, filters=filters.all)
        # )

        # @okpay 5703356189

        app.add_handler(MessageHandler(handle_all, filters=filters.me))

        # app.add_handler(
        #     MessageHandler(
        #         handle_inlineKeyboard_bot, filters=filters.inline_keyboard
        #     )
        # )

        # app.add_handler(
        #     MessageHandler(
        #         handle_redpacket_msg, filters=filters.inline_keyboard
        #     )
        # )

        # ======= Add Handle end =====

        logger.success(
            f"Login {user.first_name} {'@None' if not user.username else user.username}"
        )

    await idle()

    for app in apps:
        await app.stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    with closing(loop):
        with suppress(asyncio.exceptions.CancelledError):
            loop.run_until_complete(main())
        loop.run_until_complete(asyncio.sleep(3.0))  # task cancel wait 等待任务结束
