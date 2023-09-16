# ===== Sqlalchemy =====
from sqlalchemy import select, insert, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncAttrs, async_sessionmaker, AsyncSession
from datetime import datetime
# ====== sqlalchemy end =====

# ====== pyrogram =======
import pyromod
from pyromod.helpers import ikb, array_chunk  # inlinekeyboard
from pyrogram import Client, idle, filters
from pyrogram.types import Message, InlineKeyboardMarkup, ReplyKeyboardMarkup, BotCommand
from pyrogram.handlers import MessageHandler
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
NAME = os.environ.get("NAME") or "WFTest8964Bot"
# SQLTIE3 sqlite+aiosqlite:///database.db  # 数据库文件名为 database.db 不存在的新建一个
# 异步 mysql+aiomysql://user:password@host:port/dbname
DB_URL = "mysql+aiomysql://root:123456@localhost/supplyTGBot?charset=utf8mb4"
API_ID = 21341224
API_HASH = "2d910cf3998019516d6d4bbb53713f20"
SESSION_PATH: Path = Path(ROOTPATH, "sessions", f"{NAME}.txt")
__desc__ = """
发布规则  付费广告 消耗 1 Cion

发布付费广告严格要求如下
1：行数限制15行内【超过百分百不通过】
2：禁止发布虚假内容，禁止诈骗欺骗用户🚫
3：无需备注累计广告次数，机器人会自动统计

请编写好广告词，点击下方【📝自助发布】
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


app = makeClient(SESSION_PATH)

# ====== Client maker end =======

# ====== Content enum =======


class Content(object):

    ZZFB = "💫自助发布"
    WYCZ = "✨我要充值"
    GRZX = "👩‍🦱个人中心"

    def KEYBOARD(self) -> ReplyKeyboardMarkup:
        keyboard = ReplyKeyboardMarkup(
            [
                [self.ZZFB, self.WYCZ],
                [self.GRZX]
            ],
            resize_keyboard=True
        )
        return keyboard


content = Content()

# ====== Content enum End =======

# ====== helper function  ====


async def askQuestion(queston: str, client: Client, message: Message, timeout: int = 200) -> Union[Message, bool]:
    try:
        ans: Message = await message.chat.ask(queston, timeout=timeout)
        return ans
    except pyromod.listen.ListenerTimeout:
        await message.reply(f"超时 {timeout}s,请重新开始")
    except Exception as exc:
        await message.reply(f"发送错误:\n <code>{exc}</code>")
    return False


def try_int(string: str) -> Union[str, int]:
    try:
        return int(string)
    except:
        return string


# ====== helper function end ====

# ====== DB model =====

engine = create_async_engine(DB_URL, pool_pre_ping=True, pool_recycle=600)

# 会话构造器
async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'user'
    __table_args__ = {'comment': '供需机器人用户表'}

    id: Mapped[str] = mapped_column(
        String(20), primary_key=True, comment="用户 ID")

    reg_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), comment='注册时间'
    )

    coin: Mapped[int] = mapped_column(
        nullable=False, default=100, comment="用户的coin数量"
    )

    count: Mapped[int] = mapped_column(
        nullable=False, default=0, comment="用户的发布次数"
    )


# ======= DB model End =====

# ===== Handle ======


@app.on_message(filters=filters.command("start") & filters.private & ~filters.me)
@capture_err
async def start(client: Client, message: Message):
    await message.reply_text(__desc__, reply_markup=content.KEYBOARD())


@app.on_message(filters=filters.regex(content.ZZFB) & filters.private & ~filters.me)
@capture_err
async def sendSupply(client: Client, message: Message):
    await message.reply_text("自助发布")


@app.on_message(filters=filters.regex(content.WYCZ) & filters.private & ~filters.me)
@capture_err
async def addCoin(client: Client, message: Message):
    await message.reply_text("我要充值")


@app.on_message(filters=filters.regex(content.GRZX) & filters.private & ~filters.me)
@capture_err
async def accountCenter(client: Client, message: Message):
    await message.reply_text("个人中心")

# ==== Handle end =====


async def main():
    global app
    await app.start()
    user = await app.get_me()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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
        [
            BotCommand("start", "开始"),
        ]
    )

    await idle()
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    with closing(loop):
        with suppress(asyncio.exceptions.CancelledError):
            loop.run_until_complete(main())
        loop.run_until_complete(asyncio.sleep(3.0))  # task cancel wait 等待任务结束
