from functools import wraps
import re
import sys
from loguru import logger
from asyncio import Queue
import asyncio
from pathlib import Path
from typing import List, Union, Any, Optional
from contextlib import closing, suppress
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, CallbackQuery
from pyrogram import Client, idle, filters
from pykeyboard import InlineButton, InlineKeyboard
from pyromod.helpers import ikb, array_chunk  # inlinekeyboard
import pyromod
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncAttrs, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column, relationship, lazyload
from sqlalchemy import select, insert, String, func, Boolean, text, ForeignKey,delete
puppet_id = str(1212)
# ===== Sqlalchemy =====
# ====== sqlalchemy end =====

# ====== pyrogram =======
# ====== pyrogram end =====


# ====== Config ========
ROOTPATH: Path = Path(__file__).parent.absolute()
DEBUG = True
NAME = "bot"
# SQLTIE3 sqlite+aiosqlite:///database.db  # 数据库文件名为 database.db 不存在的新建一个
# 异步 mysql+aiomysql://user:password@host:port/dbname
DB_URL = "mysql+aiomysql://root:123456@localhost/tgforward?charset=utf8mb4"
API_ID = 21341224
API_HASH = "2d910cf3998019516d6d4bbb53713f20"
SESSION_PATH: Path = Path(ROOTPATH, "sessions", f"{NAME}.txt")
__desc__ = """
欢迎使用爱国转载傀儡号管理系统!V2.0

用于实时转载群聊的信息、转载群聊历史信息,可用于TG群聊克隆、假公群。
是您的营销好帮手。

使用前请拉入爱国傀儡号: @wwww 到群聊/频道
/reg 注册
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


async def askQuestion(queston: str, message: Message, client: Client = None, timeout: int = 200) -> Union[Message, bool]:
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
        String(20), comment="傀儡号的唯一标识符", default=puppet_id
    )
    user_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("user.id"), comment="创建任务的用户ID"
    )

    comment: Mapped[str] = mapped_column(
        String(20), comment="配置备注", default="无备注"
    )
    source: Mapped[str] = mapped_column(String(20), comment="源群聊ID")
    dest: Mapped[str] = mapped_column(String(20), comment="目标群聊ID")
    forward_history_count: Mapped[int] = mapped_column(comment="转发历史信息的数量",default=10)
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


class SQLManager(object):
    def __init__(self, AsyncSessionMaker: async_sessionmaker[AsyncSession]) -> None:
        self.AsyncSessionMaker = AsyncSessionMaker

    async def selectUserByID(self, id: str) -> Union[User, None]:
        """用用户id选择用户返回 User 模型"""
        # 关系加载技术！
        # https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html
        async with self.AsyncSessionMaker() as session:
            result = await session.execute(
                select(User)
                .where(User.id == id)
            )
            result = result.scalar_one_or_none()
            return result

    async def regUser(self, user: User) -> User:
        """register User"""
        async with self.AsyncSessionMaker() as session:
            result = await self.selectUserByID(id=user.id)
            if not result:
                session.add(user)
                await session.commit()
                return await self.selectUserByID(id=user.id)
            else:
                return result

    async def saveConfig(self, config: TGForwardConfig):
        """保存配置"""
        async with self.AsyncSessionMaker() as session:
            session.add(config)
            await session.commit()

    async def selectUserConfigs(self, id) -> Union[List[TGForwardConfig], None]:
        """根据用户 ID 选择用户的多个配置"""
        async with self.AsyncSessionMaker() as session:
            result = await session.scalar(
                select(User)
                .where(User.id == id)
            )
            if result:
                return result.configs
            else:
                return None
            
    async def selectConfigByTaskid(self,task_id:int)->Union[TGForwardConfig,None]:
        """根据任务 ID 选择任务"""
        async with self.AsyncSessionMaker() as session:
            result = await session.scalar(
                select(TGForwardConfig)
                .where(TGForwardConfig.task_id == task_id)
            )

            return result
    
    async def deleteConfigByTaskid(self,task_id:int)->None:
        """根据任务 ID 删除任务"""
        async with self.AsyncSessionMaker() as session:
            await session.execute(
                delete(TGForwardConfig)
                .where(TGForwardConfig.task_id == task_id)
            )
            await session.commit()


manager = SQLManager(async_session)


def parser(string: str, message: Message) -> "TGForwardConfig":
    data = {}

    for line in string.split('\n'):
        # print(line)
        match = re.match(r'^@@(.+?)\((.*?)\)=(.*)$', line.strip())
        if match:
            key = match.group(1)
            required = match.group(2) == '必'
            value = match.group(3).strip()
            # print("key:", key, "required", required, "value:", value)
            if value == '':
                value = None
            if not value and required:
                raise ValueError(f'{key} is required but missing')
            data[key] = value


    config = TGForwardConfig(
        forward_history_count=int(data['转载数量']),
        interval_second=data['转载间隔时间'],
        source=data['来源群组'],
        dest=data['目标群组'],
        remove_word=data['去除词'],
        cut_word=data['截断词'],
        skip_word=data['跳过词'],
        add_text=data['追加文本'],
        user_id=message.chat.id,
        comment=message.text
    )

    return config

# ====== db model end ======

# ====== Text Enum ======


class CallBackData():
    RETURN = "return"

    START_EDITOR = "start/editor"
    START_ADD = "start/add"
    START_ACCOUNT = "start/account"

    QUERY_PREFIX = "checkQuery/"
    QUERY_EDITOR = "query/editor/"
    QUERY_DELETED = "query/deleted/"


class Content(object):

    def __init__(self) -> None:
        pass

    @property
    def START_KEYBOARD(self,) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboard()
        keyboard.row(
            InlineButton(
                text="🔄管理转载", callback_data=CallBackData.START_EDITOR),
            InlineButton(text="➕添加转载", callback_data=CallBackData.START_ADD)
        )
        keyboard.row(
            InlineButton(
                text="❤账号信息", callback_data=CallBackData.START_ACCOUNT),
        )
        return keyboard

    @property
    def RETURN_KEYBOARD(self) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboard()
        keyboard.row(
            InlineButton(text="💨返回", callback_data=CallBackData.RETURN),
        )
        return keyboard

    def QUERY_KEYBOARD(self,id:str) -> InlineKeyboardMarkup:
        id = str(id)
        keyboard = InlineKeyboard()
        keyboard.row(
            # TODO: support editor config
            # InlineButton(text="💊编辑", callback_data=CallBackData.QUERY_EDITOR+id),
            InlineButton(text="❌删除", callback_data=CallBackData.QUERY_DELETED+id),
        )

        keyboard.row(
            InlineButton(text="💨返回", callback_data=CallBackData.RETURN),
        )

        return keyboard

    def addCode(self, code: str):
        return f"<code>{code}</code>"

    def GET_USER_INFO(self, user: User) -> str:
        string = f"""
用户信息:
用户ID:{self.addCode(user.id)}
注册时间:{self.addCode(user.reg_at)}
授权到期时间:{self.addCode(user.auth_time)}
配置任务数量:{len(user.configs)}
"""
        return string

    SET_TIXE: str = """
设置转发机器人的参数,**一字不落** 得按照以下格式发送(点击可以复制)

<code>
@@来源群组(必)=群组或频道ID
@@目标群组(必)=群组或频道ID
@@转载数量(必)=
@@转载间隔时间(非必)=
@@去除词(非必)=  
@@截断词(非必)=
@@跳过词(非必)=
@@追加文本(非必)=
</code>
"""

    def RESULT(self, config: TGForwardConfig) -> str:
        return f"""
数据保存成功:
任务备注: {self.addCode(config.comment)}
任务添加时间: {self.addCode(config.create_at)}
id: <code>{self.addCode(config.task_id)} // 任务id
来源群组：{self.addCode(config.source)}
目标群组：{self.addCode(config.dest)}
转载数量：{self.addCode(config.forward_history_count)}
转载间隔：{self.addCode(config.interval_second)}
去除词：{self.addCode(config.remove_word)}
截断词：{self.addCode(config.cut_word)}
跳过词：{self.addCode(config.skip_word)}
追加文本：{self.addCode(config.add_text)}
创建的用户 ID:{self.addCode(config.user_id)}
"""


content = Content()

# ====== Text Enum end =====

# ===== Handle ======


@app.on_callback_query()
@capture_err
async def handle_callback_query(client: Client, callback_query: CallbackQuery):
    if callback_query.data == CallBackData.RETURN:
        await callback_query.message.edit(__desc__, reply_markup=content.START_KEYBOARD)
        return

    elif callback_query.data == CallBackData.START_ADD:
        if not await manager.selectUserByID(id=callback_query.from_user.id):
            await callback_query.message.edit("对不起小姐,没有找到您的账号无法添加任务！请输入 /reg 注册吧!", reply_markup=content.RETURN_KEYBOARD)
            return

        await callback_query.message.edit(text=content.SET_TIXE, reply_markup=content.RETURN_KEYBOARD)
        ans: Message = await askQuestion(queston="请在 200s 内发送配置,否则重新开始!", message=callback_query.message)
        if ans:
            comment: Message = await askQuestion(queston="请输入您配置的备注(方便管理)", message=callback_query.message)
            if comment:
                config = parser(ans.text, message=comment)
                config_back = config
                await manager.saveConfig(config)
                await ans.reply(f"配置保存成功!\n{content.RESULT(config_back)}", reply_markup=content.RETURN_KEYBOARD)
        return

    elif callback_query.data == CallBackData.START_ACCOUNT:
        user = await manager.selectUserByID(id=callback_query.from_user.id)
        if user:
            await callback_query.message.edit(text=content.GET_USER_INFO(user), reply_markup=content.RETURN_KEYBOARD)
            return
        await callback_query.message.edit("对不起小姐,没有找到您的账号请输入 /reg 注册吧!", reply_markup=content.RETURN_KEYBOARD)
        return

    elif callback_query.data == CallBackData.START_EDITOR:
        configs = await manager.selectUserConfigs(id=callback_query.from_user.id)
        if configs:
            array = [
                (config.comment, f"{CallBackData.QUERY_PREFIX}/{config.task_id}")
                for config in configs
            ]
            array.append(("💨返回",CallBackData.RETURN))
            kbs = ikb(array_chunk(array, 1))

            await callback_query.message.edit("请选择您要编辑的配置", reply_markup=kbs)

        else:
            await callback_query.message.edit("对不起小姐,没有找到您配置的任何信息,请先配置哦!", reply_markup=content.RETURN_KEYBOARD)

    elif callback_query.data.startswith(CallBackData.QUERY_PREFIX):
        task_id = callback_query.data.split("/")[-1]

        config = await manager.selectConfigByTaskid(task_id=task_id)

        await callback_query.message.edit(f"您{config.comment}的配置信息:\n{content.RESULT(config)}", reply_markup=content.QUERY_KEYBOARD(config.task_id))

    elif callback_query.data.startswith(CallBackData.QUERY_DELETED):
        task_id = callback_query.data.split("/")[-1]
        config = await manager.deleteConfigByTaskid(task_id=task_id)
        await callback_query.message.edit("任务已成功删除！",reply_markup=content.RETURN_KEYBOARD)


    else:
        logger.error(f"未知的回调数据:{callback_query.data}")


@app.on_message(filters=filters.command("start") & filters.private & ~filters.me)
@capture_err
async def start(client: Client, message: Message):
    await message.reply(__desc__, reply_markup=content.START_KEYBOARD)


@app.on_message(filters=filters.command("reg") & filters.private & ~filters.me)
@capture_err
async def start(client: Client, message: Message):
    msg: Message = await message.reply("正在注册用户...")
    resp = await manager.regUser(
        User(id=message.chat.id)
    )
    await msg.edit_text(f"用户注册成功！\n{content.GET_USER_INFO(resp)}")


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

    await idle()
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    with closing(loop):
        with suppress(asyncio.exceptions.CancelledError):
            loop.run_until_complete(main())
        loop.run_until_complete(asyncio.sleep(3.0))  # task cancel wait 等待任务结束
    # asyncio.run(makeSessionString())
