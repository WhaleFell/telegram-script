"""
频道机器人,用于转发信息到指定频道.并添加内联按钮
需要修改一下 pyromod 代码
因为 pyromod listen 时没有做 message.from_user.id 是否存在的判断

# patch
if not message.from_user:
    message_from_user_id = None
else:
    message_from_user_id = message.from_user.id

or

pip install git+https://github.com/thezass/pyromod.git
"""
__desc__ = """
这是一个自动转发信息到指定频道的机器人,转发的信息将添加链接按钮.
使用方法：
/start 教程
下面两个命令需要管理员私聊机器人:
/send 输入发送的信息,并按照提示选择发送的群
/setButton 设置按钮文案及链接
/setChannel 设置需要转发的群名称例如 @test
"""

import asyncio
from asyncio import Lock
from contextlib import closing, suppress
from pydantic import BaseModel
from loguru import logger
import sys
# https://pypi.org/project/pyromod/
import pyromod
from pyromod.helpers import ikb, array_chunk
import pyrogram
from pyrogram import Client, filters, idle, compose
from pyrogram.types import Message, InlineKeyboardMarkup
from typing import List, Union, Any
from pathlib import Path
import click
import os

# ======= Config ========
DEBUG = True
API_ID = 21341224
API_HASH = "2d910cf3998019516d6d4bbb53713f20"
NAME = "add_button_bot"
# 机器人 session 列表
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise Exception("not found BOT_TOKEN environment variable")


# ======= Do not modify the following code ======
ROOTPATH = Path(__file__).parent.as_posix()
DATAPATH = Path(ROOTPATH, "data")
DATAPATH.mkdir(exist_ok=True)
JSONDBPATH = Path(DATAPATH, "data.json")


# logger
logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:HH:mm:ss}</green> | {name}:{function} {level} | <level>{message}</level>",
    level="DEBUG" if DEBUG else "INFO",
    backtrace=True,
    diagnose=True
)


class StoreJsonDB(BaseModel):
    ForwardChannle: str = None
    #  (TEXT, VALUE, TYPE)
    InlineKeyboard: list[tuple] = [
        ("测试", "t.me/test", "url")
    ]
    Lines: int = 3

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        if not JSONDBPATH.exists():
            self.dumpsFile()
        self.loadsFile()

    def dumpsFile(self):
        JSONDBPATH.write_text(
            data=self.model_dump_json(),
            encoding="utf8"
        )

    def loadsFile(self):
        jsondata = JSONDBPATH.read_text(encoding="utf8")
        import json
        d = json.loads(jsondata)
        self.ForwardChannle = d["ForwardChannle"]
        self.InlineKeyboard = d["InlineKeyboard"]
        self.Lines = d["Lines"]

    def get_kb(self) -> InlineKeyboardMarkup:
        self.loadsFile()
        lines = array_chunk(self.InlineKeyboard, self.Lines)
        keyboard = ikb(lines)
        return keyboard


jsDB = StoreJsonDB()


def mkAPP(
    session_string: Union[None, str] = None,
    bot_token: Union[None, str] = None,
    in_memory: bool = True
):
    """
    Create pyrogram Clien Object.
    Must provide `ROOTPATH` and `NAME` global various.
    """
    if Path(ROOTPATH, "%s.session" % NAME).exists():
        logger.info("session exists!use session to login")
        return Client(
            name=NAME,
            api_id=API_ID,
            api_hash=API_HASH,
        )
    elif session_string:
        logger.info("login by session string!")
        return Client(
            name=NAME,
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=session_string,
            in_memory=in_memory
        )
    elif bot_token:
        logger.info("use tg bot login with bot_token..")
        return Client(
            name=NAME,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=bot_token,
            in_memory=in_memory
        )

    logger.error(
        "no .session no session string no bot_token please manual login!")

    return Client(
        name=NAME,
        api_id=API_ID,
        api_hash=API_HASH,
    )


app = mkAPP(bot_token=BOT_TOKEN, in_memory=False)


@app.on_message(filters=filters.command("start"))
async def start(client: Client, message: Message):
    await message.reply_text(__desc__)


@app.on_message(filters=filters.private & filters.command("send"))
async def forwardMsgToChannel(client: Client, message: Message):
    try:
        ans: Message = await message.chat.ask("请发送您想转发到频道的信息,将自动添加按钮:", timeout=200)
        # https://docs.pyrogram.org/api/methods/copy_message
        keyboard = jsDB.get_kb()
        await ans.copy(
            chat_id=jsDB.ForwardChannle,  # channel id
            reply_markup=keyboard
        )
        await message.reply("发送到频道成功！")

    except pyromod.listen.ListenerTimeout:
        await message.reply("超时 200s,请重新开始")
    except Exception as exc:
        await message.reply(f"发送错误:\n <code>{exc}</code>")


@app.on_message(filters=filters.channel)
async def addButtonOnChan(client: Client, message: Message):
    # await message.edit_reply_markup(reply_markup=jsDB.get_kb())

    await client.edit_message_reply_markup(
        message.chat.id,
        message.id,
        reply_markup=jsDB.get_kb()
    )
    logger.success(f"add button on channle msg:{message.text.strip()[:10]}")


def parseBtns(text: str) -> List[tuple]:
    lines = text.split('\n')  # 按行分割字符串
    result = []
    for line in lines:
        if '-' in line:
            # 如果行中包含“-”，则将其分割成元组并添加到结果列表中
            t = [a.strip() for a in line.split('-')]
            t.append("url")
            result.append(tuple(t))
    return result


@app.on_message(filters=filters.private & filters.command("setChannel"))
async def setChannel(client: Client, message: Message):
    try:
        ans: Message = await message.chat.ask(
            "设置需要发送的频道名称例如: @test",
            timeout=200
        )

        jsDB.ForwardChannle = ans.text.strip()
        jsDB.dumpsFile()

        await message.reply(f"这是您设置的频道:{jsDB.ForwardChannle}如果不满意可以 /setChannel 重新改")

    except pyromod.listen.ListenerTimeout:
        await message.reply("设置群超时 200s,请重新开始")
    except Exception as exc:
        await message.reply(f"设置频道错误 /setChannel 重新改:\n <code>{exc}</code>")


@app.on_message(filters=filters.private & filters.command("setButton"))
async def setButton(client: Client, message: Message):
    try:
        ans: Message = await message.chat.ask(
            """
设置按钮文本和文本:\n 格式:
文本-链接
文本2-链接2
文本3-链接3
            """,
            timeout=200
        )
        res = parseBtns(ans.text)

        lineCount: Message = await message.chat.ask("请输入每行的按钮数(大于0的整数):", timeout=200)
        jsDB.Lines = int(lineCount.text)
        jsDB.InlineKeyboard = res
        jsDB.dumpsFile()

        keyboard = jsDB.get_kb()
        await message.reply("这是您设置的按钮:如果不满意可以 /setButton 重新改", reply_markup=keyboard)

    except pyromod.listen.ListenerTimeout:
        await message.reply("设置按钮超时 200s,请重新开始")
    except Exception as exc:
        await message.reply(f"设置按钮错误 /setButton 重新改:\n <code>{exc}</code>")


@logger.catch()
async def runmain():
    global app

    await app.start()

    user = await app.get_me()
    # chat_id = await app.get_chat("@w2ww2w2w")
    # print(chat_id)

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


@click.group()
def cli():
    pass


@click.command(help="start")
def start():
    loop = asyncio.get_event_loop()
    with closing(loop):
        with suppress(asyncio.exceptions.CancelledError):
            loop.run_until_complete(runmain())

        loop.run_until_complete(asyncio.sleep(3.0))  # task cancel wait 等待任务结束


cli.add_command(start)

if __name__ == "__main__":
    cli()
