# ===== Sqlalchemy =====
from sqlalchemy import select, insert, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncAttrs,
    async_sessionmaker,
    AsyncSession,
)
from datetime import datetime

# ====== sqlalchemy end =====

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
NAME = os.environ.get("NAME") or "bot"
# SQLTIE3 sqlite+aiosqlite:///database.db  # 数据库文件名为 database.db 不存在的新建一个
# 异步 mysql+aiomysql://user:password@host:port/dbname
DB_URL = "mysql+aiomysql://root:123456@localhost/tgconfigs?charset=utf8mb4"
API_ID = 21341224
API_HASH = "2d910cf3998019516d6d4bbb53713f20"
SESSION_PATH: Path = Path(ROOTPATH, "sessions", f"{NAME}.txt")
__desc__ = """
这是一个 telegram pyrogram 机器人单文件编程模板,个人自用
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


async def makeSessionString(**kwargs) -> str:
    client = Client(
        name="test", api_id=API_ID, api_hash=API_HASH, in_memory=True, **kwargs
    )

    async with client as c:
        string = await c.export_session_string()
        print(string)
        return string


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


app = makeClient(SESSION_PATH)

# ====== Client maker end =======

# ====== helper function  ====


async def askQuestion(
    queston: str, client: Client, message: Message, timeout: int = 200
) -> Optional[Message]:
    try:
        ans: Message = await message.chat.ask(  # type:ignore
            queston, timeout=timeout
        )  # type:ignore
        return ans
    except pyromod.listen.ListenerTimeout:
        await message.reply(f"超时 {timeout}s,请重新开始")
    except Exception as exc:
        await message.reply(f"发送错误:\n <code>{exc}</code>")
    return None


def try_int(string: str) -> Union[str, int]:
    try:
        return int(string)
    except:
        return string


# ====== helper function end ====

# ===== Handle ======


@app.on_message(
    filters=filters.command("start") & filters.private & ~filters.me
)
@capture_err
async def start(client: Client, message: Message):
    await message.reply_text(__desc__)


@app.on_message(filters=filters.command("id") & filters.private & ~filters.me)
@capture_err
async def handle_id_command(client: Client, message: Message):
    ans: Optional[Message] = await askQuestion(
        "请输入用户名、邀请链接等,机器人会尝试获取id", client, message
    )

    if ans:
        _id = await client.get_chat(chat_id=try_int(ans.text))
        await ans.reply(
            f"恭喜你。获取到 id 了：\n 类型：<code>{_id.type}</code>\n ID:<code>{_id.id}</code>"  # type:ignore
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

    await app.set_bot_commands(
        [BotCommand("start", "开始"), BotCommand("id", "尝试获取 ID")]
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
