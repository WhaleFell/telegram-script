"""
需要一个取数据的机器人
使用人数:1-2个人自用
功能需求：
给机器人发数据条数 可以前面加个/qc 条数
然后就从服务器里面的文件里取出15行
整理为txt或者其他文档的数据发给使用人
取完的数据可删可不删 但是每次发送的不能重复
预算100-180

1.加一个查询功能 比如 cx 1 然后返回第一条数据 cx 3 就返回第三条数据
2.加一个和改名机器人差不多的功能 不是发送qc 1就返回文件吗 再加一个 qc 1 文档名 然后就返回 一条 打包为txt 名为文档名
"""

import asyncio
from asyncio import Lock
from contextlib import closing, suppress
from loguru import logger
import sys
from pyrogram import Client, filters, idle
from pyrogram.types import Message
from typing import List, BinaryIO, Union
from pathlib import Path
import io
import pandas as pd
from flask import Flask, request
from threading import Thread

DEBUG = True
NAME = "SendElsFieldsBot"
API_ID = 21341224
API_HASH = "2d910cf3998019516d6d4bbb53713f20"
# 会话字符串
# SESSION_STRING = "AQFFpCgAhMnylQvYl5rPK1j4EKSnlPRT1i9-6JdVGY7lI-cIaQGIY2AQCInlHgkg_BYEf_cRrbFTZHE7ziasFsTx5tjInW-VZdu8ldEje63L6FMbQPXyX5FmgVMg8n8Wezqx-ys708j5VPobt9P1RsMOTzXybPmF6TASfGnA61znRvgj8ep7xnmfMYIuihUvTz3ld0RIRQGpMl0Ht6HYn7UvSlZs1eKb78DmvN4O1-u2YMhdh9E0kLKp4CPXdtg7nYEQE3xWr9byI05wNJC4fByWZvb_QJluviqAFAlJehZwRzcn42j_F9lSfkePMFSnDB0RbZBWwyPgapXGLlBX7TjGIaxkKQAAAAGIAbLoAA"
SESSION_STRING = None
# 机器人 token
BOT_TOKEN = "5337179721:AAEqto5YzuyfK7fJCD3n6jaryqdPbhy1AhI"
# BOT_TOKEN = None
# 机器人描述
BOTDESC = """
/start 开始
/qc + 条数 + 文件名(可选) 从文件获取对应的条数并以文件名发送
/re 重置使用的条数
/state 查看当前文件状态
/cx + 第几条数据 返回第几条单个数据
"""
PORT = 88

# ===== 以下代码不要改动 ==========


ROOTPATH = Path(__file__).parent.resolve()
DATADIR = Path(ROOTPATH, "data").resolve()

lock = Lock()
web = Flask(__name__)


@web.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            file.save(Path(DATADIR, "file.xls").as_posix())
            return '文件上传成功并保存为 file.xls'
    return '''
    <h1>请上传 .xls 格式的文件！</h1>
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <input type="submit" value="上传">
    </form>
    '''


def mkAPP():
    if Path(ROOTPATH, "%s.session" % NAME).exists():
        logger.info("session exists!use session to login")
        return Client(
            name=NAME,
            api_id=API_ID,
            api_hash=API_HASH,
        )
    elif SESSION_STRING:
        logger.info("login by session string!")
        return Client(
            name=NAME,
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=SESSION_STRING,
            in_memory=True
        )
    elif BOT_TOKEN:
        logger.info("use tg bot login with bot_token..")
        return Client(
            name=NAME,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            in_memory=True
        )

    logger.error(
        "no .session no session string no bot_token please manual login!")

    return Client(
        name=NAME,
        api_id=API_ID,
        api_hash=API_HASH,
    )


class Progress(object):
    """
    储存读取 xls 表格的进度
    储存在 data/.progress 文件中
    纯字符串数字,记录一个文件读取到第几行
    异步锁
    """

    def __init__(self) -> None:
        self.filePath = Path(DATADIR, ".progress")
        if not self.filePath.exists():
            logger.error(".progress not exit init file 0")
            self.re_count()

    def get_count(self) -> int:
        count = self.filePath.read_text(encoding="utf8")
        return int(count)

    def __write_count(self, count):

        async def inner():
            async with lock:
                self.filePath.write_text(str(count), encoding="utf8")
            logger.success(f"异步写入{count} .progress 成功")

        try:
            loop = asyncio.get_running_loop()
            asyncio.ensure_future(inner(), loop=loop)
        except RuntimeError:
            logger.error("无法获取当前的事件循环.转为同步方式！")
            self.filePath.write_text(str(count), encoding="utf8")
            logger.success(f"同步写入{count} .progress 成功")

    def add_count(self, add: int) -> None:
        a = self.get_count()+add
        self.__write_count(a)

    def re_count(self) -> None:
        self.filePath.write_text("0", encoding="utf8")


class Excel(object):
    def __init__(self, file_path) -> None:
        self.file_path = file_path
        logger.info(f"load xls file in:{file_path}")

    def str_to_bytes(self, string: str) -> BinaryIO:
        return io.BytesIO(string.encode('utf-8'))

    def get_rows_from_excel(self, n: int, m: int) -> str:
        """
        读取 excel 文件从第 n 行到 第 n 行
        """
        file_path = self.file_path

        df = pd.read_excel(file_path, header=None)
        rows = df.iloc[n:m]
        rows_str = rows.to_string(index=False, header=False)
        return rows_str

    def get_column_count(self):
        """读取当前文件行数"""
        file_path = self.file_path
        df = pd.read_excel(file_path, header=None)
        column_count = df.shape[0]
        return column_count

    def get_row(self, row_index: int):
        file_path = self.file_path
        df = pd.read_excel(file_path, header=None)
        row = df.iloc[row_index-1]
        rows_str = row.to_string(index=False, header=False)
        return rows_str.replace("\n", "")


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

if not DATADIR.exists():
    logger.info("not found data dir,mk it.")
    DATADIR.mkdir()

prog = Progress()
bot = mkAPP()
xls = Excel(Path(DATADIR, "file.xls").as_posix())


@bot.on_message(filters=filters.command("start"))
async def start(client: Client, message: Message):
    return await client.send_message(
        chat_id=message.chat.id,
        reply_to_message_id=message.id,
        text=BOTDESC,
    )


@bot.on_message(filters=filters.command("cx"))
async def cx(client: Client, message: Message):
    args = message.command[1:]
    if len(args) > 0:
        try:
            param = int(args[0])
            logger.debug(f"查询文件第:{param}行")
        except ValueError:
            return await message.reply("参数必须是一个大于0的整数")
    else:
        return await message.reply("缺少参数")

    reply: Message = await client.send_message(
        text=f"正在查询文件第:{param}行",
        chat_id=message.chat.id,
        reply_to_message_id=message.id
    )

    try:
        d = xls.get_row(param)
        await client.send_message(
            chat_id=message.chat.id,
            reply_to_message_id=message.id,
            text=f"文件第{param}行：\n {d}"
        )
    except Exception as e:
        await reply.edit_text(f"读取文件第{param}行错误:\n<code>{str(e)[:1000]}</code>")
        logger.exception("错误！")


@bot.on_message(filters=filters.command("state"))
async def start(client: Client, message: Message):
    reply: Message = await client.send_message(
        chat_id=message.chat.id,
        reply_to_message_id=message.id,
        text="正在查询当前文件状态！",
    )

    try:
        c = prog.get_count()
        a = xls.get_column_count()
        await reply.edit_text(f"当前进度: {c}/{a}")
    except Exception as e:
        logger.exception("读取文件错误！")
        await message.reply_text(f"读取文件错误请检查文件！<code>{str(e)}</code>")


@bot.on_message(filters=filters.command("re"))
async def re(client: Client, message: Message):
    prog.re_count()
    logger.info("文件进度重置")
    await message.reply("文件进度重置成功！")


@bot.on_message(filters=filters.command("qc"))
async def get_xls(client: Client, message: Message):
    args = message.command[1:]
    # 检查是否有参数
    if len(args) > 0:
        try:
            param = int(args[0])
            # 无效参数过滤
            if param <= 0:
                raise ValueError
            if len(args) > 1:
                filename = str(args[1])
            else:
                filename = "data"

            logger.debug(f"参数:{param} 文件名:{filename}")

        except ValueError:
            return await message.reply("参数必须是一个大于0的整数")
    else:
        return await message.reply("缺少参数")

    reply: Message = await client.send_message(
        text=f"正在获取{param}条数据中",
        chat_id=message.chat.id,
        reply_to_message_id=message.id
    )

    try:
        c = prog.get_count()
        d = xls.get_rows_from_excel(c, c+param)
        a = xls.get_column_count()
        logger.success(f"文件进度{c+param}/{a}")
        if c+param > a:
            logger.error(f"读取条数超出文件进度 {c+param}/{a} 请回复小于{a}-{c}={a-c}的条数")
            return await reply.edit_text(f"读取条数超出文件进度 {c+param}/{a} 请回复小于{a}-{c}={a-c}的条数")

        await client.send_document(
            chat_id=message.chat.id,
            reply_to_message_id=message.id,
            document=xls.str_to_bytes(d),
            file_name="%s.txt" % filename,
            caption=f"已成功获取{param}条: 文件进度{c+param}/{a}"
        )
        prog.add_count(param)
    except Exception as e:
        await reply.edit_text(f"读取文件错误,读取条数:{param}\n<code>{str(e)[:1000]}</code>")
        logger.exception("错误！")


@logger.catch()
async def main():
    global bot
    await bot.start()

    user = await bot.get_me()
    logger.success(
        f"login Account Success user:{user.first_name} phone_number:{user.phone_number}"
    )

    await idle()
    await bot.stop()

if __name__ == "__main__":
    t = Thread(target=web.run, args=("0.0.0.0", PORT,))
    t.start()

    loop = asyncio.get_event_loop()
    with closing(loop):
        with suppress(asyncio.exceptions.CancelledError):
            loop.run_until_complete(main())
        loop.run_until_complete(asyncio.sleep(3.0))  # task cancel wait 等待任务结束
