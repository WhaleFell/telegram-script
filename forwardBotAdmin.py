# ===== Sqlalchemy =====
from sqlalchemy import select, insert, String, func, Boolean, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncAttrs, async_sessionmaker, AsyncSession
from datetime import datetime
# ====== sqlalchemy end =====

# ====== pyrogram =======
import pyromod
from pyromod.helpers import ikb, array_chunk  # inlinekeyboard
from pykeyboard import InlineButton, InlineKeyboard
from pyrogram import Client, idle, filters
from pyrogram.types import Message, InlineKeyboardMarkup, CallbackQuery
from pyrogram.enums import ParseMode
# ====== pyrogram end =====

from contextlib import closing, suppress
from typing import List, Union, Any, Optional
from pathlib import Path
import asyncio
from asyncio import Queue
from loguru import logger
import sys
import re
from functools import wraps

# ====== Config ========
ROOTPATH: Path = Path(__file__).parent.absolute()
DEBUG = True
NAME = "bot"
# SQLTIE3 sqlite+aiosqlite:///database.db  # 数据库文件名为 database.db 不存在的新建一个
# 异步 mysql+aiomysql://user:password@host:port/dbname
DB_URL = "mysql+aiomysql://root:123456@localhost/tgconfigs?charset=utf8mb4"
API_ID = 21341224
API_HASH = "2d910cf3998019516d6d4bbb53713f20"
SESSION_PATH: Path = Path(ROOTPATH, "sessions", f"{NAME}.txt")
__desc__ = """
欢迎使用爱国转载傀儡号管理系统！V2.0

用于实时转载群聊的信息、转载群聊历史信息,可用于TG群聊克隆、假公群。
是您的营销好帮手。

使用前请拉入爱国傀儡号: @wwww 到群聊/频道
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

# ====== callback Queue ========


class CallbackDataQueue(object):
    def __init__(self) -> None:
        self.queue = Queue()

    async def addCallback(self, callbackQuery: CallbackQuery):
        await self.queue.put(callbackQuery)

    async def moniterCallback(self, message: Message, timeout: int = 10) -> CallbackQuery:
        while True:
            cb: CallbackQuery = await asyncio.wait_for(self.queue.get(), timeout=timeout)
            if cb.message.id == message.id:
                return cb
            else:
                await self.queue.put(cb)


cd = CallbackDataQueue()

# ====== callback Queue end ========

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


def get_user_id():
    global user
    return str(user.id)


# ====== helper function end ====

# ====== db model ======
engine = create_async_engine(DB_URL)

# 会话构造器
async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class TGForwardConfig(Base):
    __tablename__ = "forward_configs"
    __table_args__ = {'comment': '转载配置表'}

    id: Mapped[int] = mapped_column(primary_key=True, comment="主键")
    # varchar(20) = String(20) 变长字符串
    user_id: Mapped[str] = mapped_column(
        String(20), comment="傀儡号的唯一标识符", default=get_user_id
    )
    source: Mapped[str] = mapped_column(String(20), comment="源群聊ID")
    dest: Mapped[str] = mapped_column(String(20), comment="目标群聊ID")
    forward_history_count: Mapped[int] = mapped_column(comment="转发历史信息的数量")
    forward_history_state: Mapped[bool] = mapped_column(
        Boolean(), comment="转发历史信息的状态", nullable=True, default=False)
    interval_second: Mapped[int] = mapped_column(doc="间隔时间单位 s", default=20)

    remove_word: Mapped[Optional[str]] = mapped_column(
        String(100), comment="删除的文字,用,分隔", nullable=True)
    cut_word: Mapped[Optional[str]] = mapped_column(
        String(100), comment="截断词,用 , 分隔", nullable=True)
    skip_word: Mapped[Optional[str]] = mapped_column(
        String(100), comment="跳过词,用 , 分隔", nullable=True)
    add_text: Mapped[Optional[str]] = mapped_column(
        String(100), comment="跳过语,用 , 分隔", nullable=True)
    # 使用 server_default 而不是 default ，因此值将由数据库本身处理。
    create_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), default=None, nullable=False
    )
    create_id: Mapped[str] = mapped_column(
        String(20), comment="设置机器人的用户ID", nullable=True)


# ====== db model end ======

# ====== Text Enum ======


class Content(object):

    def __init__(self) -> None:
        pass

    @property
    def START_KEYBOARD(self,) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboard()
        keyboard.row(
            InlineButton(text="🔄管理转载", callback_data="start_editor"),
            InlineButton(text="➕添加转载", callback_data="start_add")
        )
        keyboard.row(
            InlineButton(text="🏠返回", callback_data="return")
        )

        return keyboard


content = Content()

# ====== Text Enum end =====

# ===== Handle ======


@app.on_callback_query(filters=)
async def handle_callback_query(client: Client, callback_query: CallbackQuery):
    await cd.addCallback(callback_query)


@app.on_message(filters=filters.command("start") & filters.private & ~filters.me)
@capture_err
async def start(client: Client, message: Message):
    await message.reply(__desc__, reply_markup=content.START_KEYBOARD)


@app.on_message(filters=filters.command("state") & filters.private & ~filters.me)
@capture_err
async def start(client: Client, message: Message):
    async with async_session() as session:
        result = await session.execute(
            text("SHOW TABLES;")
        )
        string = ""
        for k, name in enumerate(result.fetchall()[0]):
            string += f"【{k}】{name}\n"
        await message.reply(f"目前有的傀儡号:\n{string}")


@app.on_message(filters=filters.command("id") & filters.private & ~filters.me)
@capture_err
async def handle_id_command(client: Client, message: Message):
    ans: Message = await askQuestion("请输入用户名、邀请链接等，机器人会尝试获取id", client, message)

    id = await client.get_chat(chat_id=try_int(ans.text))

    await ans.reply(f"恭喜你。获取到 id 了：\n 类型：<code>{id.type}</code>\n ID:<code>{id.id}</code>")


# ==== Handle end =====


async def main():
    global app, user
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
