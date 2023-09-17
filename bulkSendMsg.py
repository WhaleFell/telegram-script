# ====== pyrogram =======
import pyromod
from pyromod.helpers import ikb, array_chunk  # inlinekeyboard
from pyrogram import Client, idle, filters
from pyrogram.handlers import MessageHandler
from pyrogram.handlers.raw_update_handler import RawUpdateHandler
from pyrogram.types import Message, InlineKeyboardMarkup
from pyrogram.enums import ParseMode
from pyrogram.raw import functions
import pyrogram
# ====== pyrogram end =====

from contextlib import closing, suppress
from typing import List, Union, Any, Optional, Tuple
from pathlib import Path
import asyncio
from loguru import logger
import sys
import re
from functools import wraps
import glob
import os
# https://github.com/jd/tenacity
from tenacity import retry, stop_after_attempt, wait_fixed


# ====== Config ========
ROOTPATH: Path = Path(__file__).parent.absolute()
SESSIONS_PATH: Path = Path(ROOTPATH, "sessions")
DEBUG = True
API_ID = 21341224
API_HASH = "2d910cf3998019516d6d4bbb53713f20"
# GROUP_ID = [-1001968860718]
GROUP_ID = [-1001963862221]
__desc__ = """
批量自动群发消息,等待解除禁言后就发送
将 session 放在 sessions folder 就自动登陆
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

banned_user: List[Tuple[Client, str]] = []

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


def loadTXTFile(path: Path) -> List[Tuple[Path, str]]:
    """
    txt 文件格式: session文件名,需要发送的内容
    """
    result = []
    with open(file=path.as_posix(), mode="r", encoding="utf8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            if len(parts) < 2:
                continue
            account = parts[0]
            content = ','.join(parts[1:])
            result.append((Path(SESSIONS_PATH, f"{account}.txt"), content))
    return result

# ====== Client maker end =======

# ====== helper function  ====


# ====== helper function end ====

# ===== Handle ======


# @app.on_message(filters=filters.command("start") & filters.private & ~filters.me)
async def start(client: Client, message: Message):
    await message.reply_text(__desc__)


@retry(stop=(stop_after_attempt(5),), wait=wait_fixed(2))
async def trySendMsg(client: Client, content: str,) -> bool:
    await client.send_message(
        chat_id=GROUP_ID[0],
        text=content
    )


async def tryMore(app: Client, content: str) -> bool:
    try:
        await trySendMsg(app, content)
        logger.success(f"{app.name} 发送成功！正在登出")
        await app.stop()
        return True
    except Exception as e:
        logger.error(f"{app.name} 重试5次仍然失败,进入监听解禁列表:{e}")
        logger.exception(e)


async def rawUpdateHandle(
    client: Client,
    update: pyrogram.raw.base.Update,
    users: pyrogram.types.User,
    chats: pyrogram.types.Chat
):
    """原始更新监听"""
    global apps
    if "UpdateChatDefaultBannedRights" in str(type(update)):
        if not update.default_banned_rights.send_messages:
            if hasattr(update.peer, "chat_id"):
                if -1*update.peer.chat_id in GROUP_ID:
                    await tryMore(client, apps[client])
            if hasattr(update.peer, "channel_id"):
                cid = int("-100" + str(update.peer.channel_id))
                if cid in GROUP_ID:
                    await tryMore(client, apps[client])

# ==== Handle end =====
cs = loadTXTFile(Path(ROOTPATH, "content.txt"))
apps = {
    makeClient(name): content
    for name, content in cs
}


@logger.catch()
async def main():
    global apps
    print(apps)
    for app, content in apps.items():

        await app.start()
        user = await app.get_me()
        await app.invoke(functions.account.UpdateStatus(offline=False))
        logger.success(
            f"""
        -------login success--------
        username: {user.first_name}
        type: {"Bot" if user.is_bot else "User"}
        @{user.username}
        ----------------------------
        """
        )

        # ===== Test Code =======

        res = await tryMore(app, content)
        if not res:
            logger.info(f"{app.name} 发送失败,添加解禁监听！")
            han = app.add_handler(
                RawUpdateHandler(
                    rawUpdateHandle
                )
            )

        # ======== Test Code end ==========

        # ======= Add handle ========

        # ======= Add Handle end =====

    await idle()

    for app, content in apps.items():
        await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    with closing(loop):
        with suppress(asyncio.exceptions.CancelledError):
            loop.run_until_complete(main())
        loop.run_until_complete(asyncio.sleep(3.0))  # task cancel wait 等待任务结束
    # asyncio.run(makeSessionString())
    pass
