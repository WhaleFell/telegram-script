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


async def makeSessionString(name: str, **kwargs) -> str:
    client = Client(
        name=name,
        api_id=API_ID,
        api_hash=API_HASH,
        in_memory=True,
        **kwargs
    )

    async with client as c:
        string = await c.export_session_string()
        logger.success(f"获取 {NAME} Session 成功！\n{string}")
        Path(SESSION_PATH, f"{NAME}.txt").write_text(
            data=string, encoding="utf8")

if __name__ == "__main__":
    NAME = input(">> 请输入保存的 Session 名字:")
    asyncio.run(makeSessionString(NAME))
