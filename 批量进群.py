# /bin/python3
# 批量进群
# 请将需要登陆的账号放在 sessions 文件夹下
# ====== pyrogram =======
import pyromod
from pyromod.helpers import ikb, array_chunk  # inlinekeyboard
from pyrogram import Client, idle, filters
from pyrogram.types import Message, InlineKeyboardMarkup, BotCommand, CallbackQuery
from pyrogram.handlers import MessageHandler
from pyrogram.enums import ParseMode
from pyrogram.raw import functions
# ====== pyrogram end =====

from contextlib import closing, suppress
from typing import List, Union, Any, Optional
from pathlib import Path
import asyncio
from loguru import logger
import sys
import re
from functools import wraps
import os
import sys
import glob

# ====== Config ========
ROOTPATH: Path = Path(__file__).parent.absolute()
DEBUG = True
API_ID = 21341224
API_HASH = "2d910cf3998019516d6d4bbb53713f20"
__desc__ = """
批量进群
"""
SESSION_PATH: Path = Path(ROOTPATH, "sessions")
if not SESSION_PATH.exists():
    logger.error("Not Found Session folder!")
    SESSION_PATH.mkdir()
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


def makeClient(path: Path) -> Client:
    session_string = path.read_text(encoding="utf8")
    return Client(
        name=path.stem,
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=session_string,
        in_memory=True
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
            name=name, session_string=session,
            api_id=API_ID, api_hash=API_HASH, in_memory=True
        )
        for name, session in file_content_list
    ]


async def main():

    clients = loadClientsInFolder()
    logger.success(
        f"一共加载了{len(clients)}个账号:{[client.name for client in clients]}"
    )

    for app in clients:
        async with app:
            await app.invoke(functions.account.UpdateStatus(offline=False))
            me = await app.get_me()
            print(me.first_name, "登录成功")

            if os.path.exists(os.path.join(sys.path[0], "groups.txt")):
                with open("groups.txt", "r") as f:
                    content = f.readlines()
                    for i in content:

                        try:
                            chat = await app.get_chat(i.replace("\n", ''))
                            logger.info(f"入群 {chat}")
                            await app.join_chat(chat.id)
                            logger.success(
                                "%s %s %s %s" % (
                                    me.first_name, "加入",
                                    i.replace("\n", ''), "成功")
                            )
                        except Exception as error:
                            logger.error(
                                "%s %s %s %s %s" %
                                (
                                    me.first_name, "加入",
                                    i.replace("\n", ''), "失败", error
                                )
                            )

            # 处理机器人
            if os.path.exists(os.path.join(sys.path[0], "bots.txt")):
                with open("bots.txt", 'r') as f:
                    content = f.readlines()
                    for i in content:
                        try:
                            await app.send_message((await app.get_users(i.replace("\n", ''))).id, "/start")
                            print(me.first_name, "向", i.replace(
                                "\n", ''), "发送 /start 成功")
                        except:
                            print(me.first_name, "向", i.replace(
                                "\n", ''), "发送 /start 失败")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    with closing(loop):
        with suppress(asyncio.exceptions.CancelledError):
            loop.run_until_complete(main())
        loop.run_until_complete(asyncio.sleep(3.0))  # task cancel wait 等待任务结束
    # asyncio.run(makeSessionString())
