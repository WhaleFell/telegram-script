# ====== pyrogram =======
from pyrogram import Client, idle, filters  # type:ignore
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    BotCommand,
    CallbackQuery,
)
from pyrogram.handlers import MessageHandler  # type:ignore
from pyrogram.enums import ParseMode

# ====== pyrogram end =====


# ====== Type hint ======
from typing import List, Union, Any, Optional
from pydantic import BaseModel

# ====== Type hint end ====

from contextlib import closing, suppress
from pathlib import Path
import asyncio
from loguru import logger
import sys
import re
from functools import wraps
import os
import sys
import glob
import csv

# ====== Config ========
ROOTPATH: Path = Path(__file__).parent.absolute()
CONFIGPATH: Path = Path(ROOTPATH, "config.csv")
DEBUG = True
NAME = os.environ.get("NAME") or "cheryywk"
API_ID = 21341224
API_HASH = "2d910cf3998019516d6d4bbb53713f20"
SESSION_PATH: Path = Path(ROOTPATH, "sessions", f"{NAME}.txt")
__desc__ = """
批量登陆 sessions 下的账号,间隔时间发送指定信息.
编辑目录下的 config.csv 格式:

需要发送的群聊ID,自定义信息,间隔时间

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


# ====== error handle end =========

# ====== Client maker =======


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


# ====== Client maker end =======

# ====== helper function  ====


class Config(BaseModel):
    group_id: int
    content: str
    interval: float


def loadCSVConfig() -> List[Config]:
    with open(
        CONFIGPATH.as_posix(), newline="", mode="r", encoding="utf8"
    ) as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # 跳过表头
        configs: List[Config] = []
        for row in reader:
            if not row:
                continue
            group_id = row[0]
            content = row[1]
            interval = row[2]
            configs.append(
                Config(
                    group_id=int(group_id),
                    content=content,
                    interval=int(interval),
                )
            )

        return configs


async def IntervalSend(client: Client, config: Config):
    # logger.info(
    #     f"{client.name} ADD Task {config.group_id} ==> {config.content} interval(s): {config.interval}s"
    # )
    try:
        await client.send_message(chat_id=config.group_id, text=config.content)
        await asyncio.sleep(delay=config.interval)
        logger.success(
            f"{client.name} 发送 {config.group_id} ==> {config.content}"
        )
    except Exception as exc:
        logger.error(f"{client.name} 发送 {config.group_id} 错误!{exc}")
        await asyncio.sleep(delay=config.interval)


# ====== helper function end ====

# ===== Handle ======


# ==== Handle end =====


async def main():
    try:
        configs = loadCSVConfig()
        if not configs:
            raise Exception("没有配置!")
    except Exception as exc:
        logger.exception(f"load csv config error 请检查 config.csv 文件:{exc}!")
        raise exc

    apps = loadClientsInFolder()

    login_apps = []
    for app in apps:
        try:
            await app.start()
            user = await app.get_me()
            logger.success(
                f"Login {user.first_name} {'@None' if not user.username else user.username}"
            )
            login_apps.append(app)
        except Exception as exc:
            logger.error(f"{app.name} Login Error 登陆错误! {exc}")
            continue

    while True:
        for login_app in login_apps:
            for config in configs:
                # asyncio.ensure_future(IntervalSend(app, config=config)) # 同时发
                await IntervalSend(login_app, config=config)

    await idle()
    for app in login_apps:
        await app.stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    with closing(loop):
        with suppress(asyncio.exceptions.CancelledError):
            loop.run_until_complete(main())
        loop.run_until_complete(asyncio.sleep(3.0))  # task cancel wait 等待任务结束
    # asyncio.run(makeSessionString())
