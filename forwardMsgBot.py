# ===== Sqlalchemy =====
from dataclasses import dataclass
from sqlalchemy import select, insert, func, update, ForeignKey
from sqlalchemy import BigInteger, String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncAttrs, async_sessionmaker, AsyncSession
from datetime import datetime, timedelta
# ====== sqlalchemy end =====

# ====== pyrogram =======
# https://stackoverflow.com/questions/74163185/send-premium-emoji-with-pyrogram
import pyromod
# ListenerTypes.CALLBACK_QUERY
from pyromod.listen.listen import ListenerTypes
from pyromod.helpers import ikb, array_chunk
from pyrogram import Client, idle, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineQueryResult, CallbackQuery, User
from pyrogram.enums import ParseMode
# ====== pyrogram end =====

from contextlib import closing, suppress
from typing import List, Union, Any, Optional
from pathlib import Path
import asyncio
from loguru import logger
import sys
import os
import re
from functools import wraps
import time
from asyncio import Queue

# ====== Config ========
ROOTPATH: Path = Path(__file__).parent.absolute()
DEBUG = True
NAME = os.environ.get("NAME") or "user628"
# SQLTIE3 sqlite+aiosqlite:///database.db  # 数据库文件名为 database.db 不存在的新建一个
# 异步 mysql+aiomysql://user:password@host:port/dbname
DB_URL = os.environ.get(
    "DB_URL") or "mysql+aiomysql://root:123456@localhost/tgforward?charset=utf8mb4"
API_ID = 21341224
API_HASH = "2d910cf3998019516d6d4bbb53713f20"
SESSION_PATH: Path = Path(ROOTPATH, "sessions", f"{NAME}.txt")
__desc__ = """
傀儡号,请在仆人处设置参数!
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


# ===== error handle ======


def capture_err(func):
    """handle error and notice user"""
    @wraps(func)
    async def capture(client: Client, message: Union[Message, CallbackQuery], *args, **kwargs):
        try:
            return await func(client, message, *args, **kwargs)
        except Exception as err:
            if isinstance(message, CallbackQuery):
                await message.message.reply(f"机器人按钮回调 Panic 了:\n<code>{err}</code>")
            else:
                await message.reply(f"机器人 Panic 了:\n<code>{err}</code>")
            raise err
    return capture

# ====== error handle end =========


# 创建数据库引擎
# https://github.com/talkpython/web-applications-with-fastapi-course/issues/4
engine = create_async_engine(DB_URL, pool_pre_ping=True, pool_recycle=600)


class Base(AsyncAttrs, DeclarativeBase):
    pass


# 会话构造器
async_session = async_sessionmaker(bind=engine, expire_on_commit=False)

user = User(id=212121212)


def get_user_id():
    """
    获取当前 puppet 的用户 ID
    TODO: 仅仅在多 puppet 的场景下使用
    """

    global user
    return str(user.id)


# 定义数据模型


class User(Base):
    __tablename__ = 'user'
    __table_args__ = {'comment': '转载用户表'}

    id: Mapped[str] = mapped_column(
        String(20), primary_key=True, comment="用户 ID")

    configs: Mapped[List["TGForwardConfig"]] = relationship(
        'TGForwardConfig', backref='user', lazy='subquery')

    reg_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), comment='注册时间'
    )
    auth_time: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now() + timedelta(days=7), nullable=True, comment='授权时间')

    def __repr__(self):
        return f'<User(user_id={self.id}, reg_at={self.reg_at}, auth_time={self.auth_time})>'


class TGForwardConfig(Base):
    __tablename__ = "forward_configs"
    __table_args__ = {'comment': '转载配置表'}

    task_id: Mapped[int] = mapped_column(primary_key=True, comment="任务主键")
    # varchar(20) = String(20) 变长字符串 puppet: 傀儡 /ˈpʌp.ɪt/
    puppet_id: Mapped[str] = mapped_column(
        String(20), comment="傀儡号的唯一标识符", default=get_user_id()
    )
    user_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("user.id"), comment="创建任务的用户ID"
    )

    comment: Mapped[str] = mapped_column(
        String(20), comment="配置备注", default="无备注"
    )
    source: Mapped[str] = mapped_column(String(20), comment="源群聊ID")
    dest: Mapped[str] = mapped_column(String(20), comment="目标群聊ID")
    forward_history_count: Mapped[int] = mapped_column(
        comment="转发历史信息的数量", default=10)
    forward_history_state: Mapped[bool] = mapped_column(
        Boolean(), comment="转发历史信息的状态", nullable=True, default=False)
    interval_second: Mapped[int] = mapped_column(
        comment="间隔时间单位 s", default=20)

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
        server_default=func.now(), default=None, nullable=False, comment="任务添加的时间"
    )


# 仅同步使用
# Base.metadata.create_all(engine)


class TGForwardConfigManager:
    def __init__(self):
        self.session: async_sessionmaker[AsyncSession] = async_session
        self.all_config_cache: List[TGForwardConfig] = None

    async def switch_forword_history_state(self, config: TGForwardConfig):
        async with self.session() as session:
            await session.execute(
                update(TGForwardConfig)
                .where(TGForwardConfig.task_id == config.task_id)
                .where(TGForwardConfig.puppet_id == get_user_id())
                .values(
                    forward_history_state=not config.forward_history_state)
            )
            await session.commit()
            await self.flash_configs_cache()

    async def flash_configs_cache(self) -> List[TGForwardConfig]:
        async with self.session() as session:
            configs = await session.execute(
                select(TGForwardConfig)
                .where(
                    TGForwardConfig.puppet_id == get_user_id()
                )
            )
            await session.commit()
            self.all_config_cache = configs.scalars().all()

            return self.all_config_cache

    async def selectConfigByTaskid(self, task_id: int) -> Union[TGForwardConfig, None]:
        """根据任务 ID 选择任务"""
        task_id = int(task_id)
        async with self.session() as session:
            result = await session.scalar(
                select(TGForwardConfig)
                .where(TGForwardConfig.task_id == task_id)
                .where(
                    TGForwardConfig.puppet_id == get_user_id()
                )
            )

            return result


# manager 用于管理数据库
manager = TGForwardConfigManager()


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


@app.on_message(filters=filters.command("start") & filters.private & ~filters.me)
async def start(client: Client, message: Message):
    await message.reply_text(__desc__)


async def askQuestion(queston: str, message: Message, timeout: int = 200) -> Union[Message, bool]:
    try:
        ans: Message = await message.chat.ask(queston, timeout=timeout)
        return ans
    except pyromod.listen.ListenerTimeout:
        await message.reply(f"超时 {timeout}s,请重新开始")
    except Exception as exc:
        await message.reply(f"发送错误:\n <code>{exc}</code>")
    return False


@app.on_message(filters=filters.command("getID") & ~filters.me)
@capture_err
async def get_ID(client: Client, message: Message):
    await message.reply(
        f"当前会话的ID:<code>{message.chat.id}</code>"
    )


def process_string(input_string, delete_words=None, check_words=None, append_text=None, truncate_words=None):
    """
    处理字符串的函数
    用 Python 写一个处理字符串的函数：
    1. 提供一个由逗号分隔每个需要删除词语的字符串,在提供的字符串中删除这些词语
    2. 提供一个由逗号分隔每个词语的字符串,如果在提供的字符串中包含这些词语就返回 None
    3. 提供一段文本,在提供字符串的结尾添加换行再添加这段文本
    4. 提供一个由逗号分隔每个截断词的字符串，如果字符串中包含这些词语的话就提取这词语前面的字符串。

    :param input_string: 需要处理的字符串
    :param delete_words: 由逗号分隔每个需要删除词语的字符串
    :param check_words: 由逗号分隔每个词语的字符串，如果在提供的字符串中包含这些词语就返回 None
    :param append_text: 需要添加的文本
    :param truncate_words: 由逗号分隔每个截断词的字符串，如果字符串中包含这些词语的话就提取这词语前面的字符串
    :return: 处理后的字符串
    """
    # 删除需要删除的词语
    if delete_words:
        delete_words_list = delete_words.split(',')
        for word in delete_words_list:
            input_string = input_string.replace(word.strip(), '')

    # 检查是否包含需要检查的词语
    if check_words:
        check_words_list = check_words.split(',')
        for word in check_words_list:
            if word.strip() in input_string:
                return None

    # 在字符串结尾添加文本
    if append_text:
        input_string += '\n' + append_text

    # 截断字符串
    if truncate_words:
        truncate_words_list = truncate_words.split(',')
        for word in truncate_words_list:
            index = input_string.find(word.strip())
            if index != -1:
                input_string = input_string[:index]

    return input_string


@app.on_message(filters=filters.group | filters.channel)
async def handle_ch_gp(client: Client, message: Message):
    # handle all message in channel or group
    # ！！！这可能会造成性能问题 ！！！
    if not manager.all_config_cache:
        return
    for config in manager.all_config_cache:
        if str(message.chat.id) == config.source:
            logger.info(
                f"[{config.comment}] source({message.chat.id})==>dest({config.dest}) {message.text}")
            if not message.text:
                # return await message.copy(chat_id=int(config.dest))
                return await client.copy_message(
                    chat_id=int(config.dest),
                    from_chat_id=message.chat.id,
                    message_id=message.id,
                    parse_mode=ParseMode.HTML,
                )

            text = process_string(
                message.text, delete_words=config.remove_word,
                check_words=config.skip_word, append_text=config.add_text, truncate_words=config.cut_word
            )

            if text:
                return await client.send_message(chat_id=int(config.dest), text=text)

        # 双向转发时开启
        # elif str(message.chat.id) == config.dest:
        #     logger.info(
        #         f"dest({message.chat.id})==>source({config.source}) {message.text}")
        #     if not message.text:
        #         return await message.copy(chat_id=config.source)

        #     text = process_string(message.text, delete_words=config.remove_word,
        #                           check_words=config.skip_word, append_text=config.add_text, truncate_words=config.cut_word)
        #     if text:
        #         return await client.send_message(chat_id=config.source, text=text)


@app.on_message(filters=filters.command("forwardHistoryMsg") & filters.private)
@capture_err
async def forwardHistoryMsg(client: Client, message: Message):
    logger.info("激活！")
    task_id = message.command[1]

    config: TGForwardConfig = await manager.selectConfigByTaskid(task_id=task_id)
    if not config:
        return await message.reply(f"没有找到您设置的信息.{task_id}")

    # if not config:
    #     return await message.reply("没有找到您设置的信息,请使用 /set 设置!")
    # elif isinstance(config, list):
    #     string = ""
    #     for k, cf in enumerate(configs):
    #         string += f"【{k}】{cf.source} ==> {cf.dest}\n"

    #     choose: Message = await askQuestion(queston=f"您设置了多组群聊,请选择需要转发的群聊!(直接发送选择的编号):\n{string}", client=client, message=message, timeout=20)
    #     config = configs[int(choose.text)]
    #     # User not send button!
    #     # buttons = [
    #     #     (f"源群组:{cf.source}", f"{k}")
    #     #     for k, cf in enumerate(configs)
    #     # ]

    #     # lines = array_chunk(buttons, 1)
    #     # keyboard = ikb(lines)
    #     # msg_markup: Message = await client.send_message(
    #     #     chat_id=message.chat.id,
    #     #     text=f"您设置了多组群聊,请选择需要转发的群聊!",
    #     #     reply_markup=keyboard
    #     # )
    #     # callback_query = await cd.moniterCallback(msg_markup)
    #     # print(callback_query.data)
    #     # return
    # else:
    #     config = configs

    await message.reply(f"您的源群组:<code>{config.dest}</code> 目标群组:<code>{config.source}</code> \n 读取历史信息:{config.forward_history_count} 发送间隔:{config.interval_second}s\n转发状态{config.forward_history_state} **现在开始转发**")

    msgs: List[Message] = []
    start_time = time.time()

    async for msg in client.get_chat_history(chat_id=int(config.source), limit=config.forward_history_count):
        msgs.append(msg)

    await message.reply(f"读取了{len(msgs)}条信息，正在按顺序进行转发!")

    for ms in reversed(msgs):
        # await ms.copy(chat_id=int(config.dest))
        await client.copy_message(
            chat_id=int(config.dest),
            from_chat_id=ms.chat.id,
            message_id=ms.id,
            parse_mode=ParseMode.HTML
        )
        logger.success(
            f"Bulk Forward:{config.source} ==> {config.dest}"
        )
        await asyncio.sleep(delay=config.interval_second)

    end_time = time.time()

    await message.reply(f"转发完成,一共转发了{len(msgs)}条信息,耗时 {end_time-start_time}")
    await manager.switch_forword_history_state(config)


# @app.on_message(filters=filters.all)
# async def hanleAllMsg(client: Client, message: Message):
#     print(message.text)


def try_int(string: str) -> Union[str, int]:
    try:
        return int(string)
    except:
        return string


@app.on_message(filters=filters.command("flash_task") & filters.private & ~filters.me)
@capture_err
async def handle_id_command(client: Client, message: Message):
    config = await manager.flash_configs_cache()

    await message.reply(
        f"更新任务列表成功！\n 当前账号:<code>{get_user_id()}</code>\n有{len(config)}条任务"
    )


@app.on_message(filters=filters.command("id") & filters.private & ~filters.me)
@capture_err
async def handle_id_command(client: Client, message: Message):
    ans: Message = await askQuestion("请输入用户名、邀请链接等，机器人会尝试获取id", client, message)

    id = await client.get_chat(chat_id=try_int(ans.text))

    await ans.reply(f"恭喜你。获取到 id 了：\n 类型：<code>{id.type}</code>\n ID:<code>{id.id}</code>")


async def flashConfigsCache():
    while True:
        try:
            await asyncio.sleep(5)
            config = await manager.flash_configs_cache()
            logger.success(f"成功刷新:{len(config)}条任务")
        except Exception as e:
            logger.error(f"flash config cache error{e}")


@logger.catch()
async def main():
    # 异步使用 Base.metadata.create_all
    global user, app

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await app.start()
    user = await app.get_me()
    await manager.flash_configs_cache()
    asyncio.create_task(flashConfigsCache())

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
    # 数据库
    await engine.dispose()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    with closing(loop):
        with suppress(asyncio.exceptions.CancelledError):
            loop.run_until_complete(main())

        loop.run_until_complete(asyncio.sleep(3.0))  # task cancel wait 等待任务结束

    # asyncio.run(makeSessionString(
    #     bot_token="6600787006:AAFbLYNf2rv_fiTLDsuvXYT_cue8GR6bm18"))
