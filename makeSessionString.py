# 自动生成 session string 并保存到目录下的 session 文件夹
# 默认名字为账号的名字
# 教程
"""
Commands:
  listen        监听单个账号的所有信息
  listentgcode  批量登陆 sessions 文件夹下的 TXT,并监听每个账号的 tg 验证码
  loopget       循环获取账号 session string

`python makeSessionString.py listen txt名字` -- 监听单个账号的所有信息
`python makeSessionString.py listentgcode` -- 批量登陆 sessions 文件夹下的 TXT,并监听每个账号的 tg 验证码
`python makeSessionString.py loopget` -- 循环输入验证码导出账号 token

"""


# ====== pyrogram =======
import pyromod
from pyromod.helpers import ikb, array_chunk  # inlinekeyboard
from pyrogram import Client, idle, filters  # type:ignore
from pyrogram.types import Message, InlineKeyboardMarkup, User
from pyrogram.enums import ParseMode
from pyrogram.raw import functions
from pyrogram.handlers.message_handler import MessageHandler
from urllib.parse import urlparse, parse_qs

# ====== pyrogram end =====

from contextlib import closing, suppress
from typing import List, Union, Any, Optional
from pathlib import Path
import asyncio
from loguru import logger
import sys
import re
from functools import wraps
import random
import click
import os, glob

# ====== Config ========
ROOTPATH: Path = Path(__file__).parent.absolute()
DEBUG = True
NAME = None
API_ID = 21341224
API_HASH = "2d910cf3998019516d6d4bbb53713f20"
SESSION_PATH: Path = Path(ROOTPATH, "sessions")
# SESSION_FILE: Path = Path(SESSION_PATH, f"{NAME}.txt")
__desc__ = """
自动生成 Session string
"""
# ===== Config end ======


@click.group()
def cli():
    pass


if not SESSION_PATH.exists():
    logger.error(f"{str(SESSION_PATH)}目录不存在正在新建")
    SESSION_PATH.mkdir()


def makeClient(path: Path) -> Client:
    session_string = path.read_text(encoding="utf8")
    return Client(
        name="test",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=session_string,
        in_memory=True,
    )


async def makeSessionString(**kwargs) -> None:
    """生成 session 字符串"""
    client = Client(
        name="test", api_id=API_ID, api_hash=API_HASH, in_memory=True, **kwargs
    )

    async with client as c:
        string = await c.export_session_string()
        user = await c.get_me()
        if user.first_name == None:
            user.first_name = "None"
        if user.last_name == None:
            user.last_name = "None"

        logger.success(
            f"""
-------login success--------
username: {user.first_name+user.last_name}
type: {"Bot" if user.is_bot else "User"}
@{user.username}
----------------------------
"""
        )
        logger.success(
            f"获取 {user.first_name+user.last_name} Session 成功！\n{string}"
        )
        Path(
            SESSION_PATH,
            f"{str(user.first_name+user.last_name)}.txt".replace("None", ""),
        ).write_text(data=string, encoding="utf8")


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


@click.command(help="循环获取账号 session string")
def loopGet():
    i = 0
    while True:
        i += 1
        logger.info(f"正在申请第{i}个账号")
        try:
            asyncio.run(makeSessionString())
        except KeyboardInterrupt:
            logger.success("退出！！")
            sys.exit(0)
        except Exception as e:
            logger.error(f"生成时出现错误！{e}")


@click.command(help="监听单个账号的所有信息")
@click.argument("name")
def listen(name):
    app = makeClient(path=Path(SESSION_PATH, f"{name}.txt"))

    async def listen_handle(client: Client, message: Message):
        logger.info(f"{message.chat.id} receive message:{message.text}")

    async def run():
        await app.start()
        user = await app.get_me()

        if user.first_name == None:
            user.first_name = "None"
        if user.last_name == None:
            user.last_name = "None"
        logger.success(
            f"""
        -------login success--------
        username: {user.first_name+user.last_name}
        type: {"Bot" if user.is_bot else "User"}
        @{user.username}
        phone_number:{user.phone_number}
        ----------------------------
        """
        )

        app.add_handler(MessageHandler(listen_handle, filters=filters.all))

        await idle()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())


@click.command(help="批量登陆 sessions 文件夹下的 TXT,并监听每个账号的 tg 验证码")
def listenTGcode():
    async def user_info(client: Client) -> str:
        me = await client.get_me()
        first_name = ""
        last_name = ""
        username = ""
        if me.first_name:
            first_name = me.first_name

        if me.last_name:
            last_name = me.last_name

        if me.username:
            username = me.username

        return f"用户名:{first_name+last_name} @{username}"

    async def handle_tg_code(client: Client, message: Message):
        logger.success(
            f"{await user_info(client=client)} 收到来自 TG 的信息:{message.text}"
        )

    async def main():
        apps = loadClientsInFolder()
        for app in apps:
            try:
                await app.start()
                logger.success(f"{await user_info(client=app)} 登陆成功!已添加监听 TG")
                app.add_handler(
                    MessageHandler(handle_tg_code, filters=filters.chat(777000))
                )
            except Exception as exc:
                logger.error(f"{app.name} 登陆失败 {exc}")

        await idle()

        for app in apps:
            await app.stop()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())


cli.add_command(loopGet)
cli.add_command(listen)
cli.add_command(listenTGcode)


if __name__ == "__main__":
    # cli()
    asyncio.run(
        makeSessionString(
            bot_token="6399214671:AAHGXXYA-agrAewUQufvZJu2MQpdGGSjA4Y"
        )
    )
