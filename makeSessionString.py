# 自动生成 session string 并保存到目录下的 session 文件夹
# 默认名字为账号的名字
# ====== pyrogram =======
import pyromod
from pyromod.helpers import ikb, array_chunk  # inlinekeyboard
from pyrogram import Client, idle, filters
from pyrogram.types import Message, InlineKeyboardMarkup, User
from pyrogram.enums import ParseMode
from pyrogram.raw import functions
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
        string = await c.export_session_string()
        user = await c.get_me()
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
            f"获取 {user.first_name+user.last_name} Session 成功！\n{string}")
        Path(SESSION_PATH, f"{user.first_name+user.last_name}.txt").write_text(
            data=string, encoding="utf8")

if __name__ == "__main__":
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
