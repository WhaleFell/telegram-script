# /bin/python3

# ====== pyrogram =======
import random
import pyromod
from pyromod.helpers import ikb, array_chunk  # inlinekeyboard
from pyrogram import Client, idle, filters  # type:ignore
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    BotCommand,
    CallbackQuery,
    User,
    ChatPreview,
    Chat,
)
from pyrogram.enums import ParseMode, ChatType
from pyrogram import errors

from pyrogram.raw import functions, types

# ====== pyrogram end =====

from contextlib import closing, suppress
from typing import List, Union, Any, Optional, BinaryIO, Callable
from pydantic import BaseModel, ByteSize
from pathlib import Path
import asyncio
from loguru import logger
import sys
import re
from functools import wraps
import os
import sys
import glob
import io


# ====== Config ========
ROOTPATH: Path = Path(__file__).parent.absolute()
DEBUG = True
# 信息号的名称
INFO_BOT = os.environ.get("NAME") or "cheryywk"
# 需要克隆的群,信息号加入的克隆群 -1001939161298
COPY_GROUP_ID = -1001939161298

API_ID = 21341224
API_HASH = "2d910cf3998019516d6d4bbb53713f20"
SESSION_PATH: Path = Path(ROOTPATH, "sessions")
if not SESSION_PATH.exists():
    logger.error("Not Found Session folder!")
    SESSION_PATH.mkdir()

__desc__ = """
TG 群用户克隆

1. 先有一个信息号,专门读取群聊中的用户头像、用户简洁、用户名
2. 遍历 session 登陆新号，修改新好的头像、用户讲解、和用户名，相当于克隆TG用户
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
    diagnose=True,
)

# ===== logger end =====

# ====== Helper Function ======


class BaseUser(BaseModel):
    first: str
    last: str
    username: str
    bio: str
    photo: Any

    def __repr__(self) -> str:
        return f"<BaseUser username={self.username}>"


def makeClient(path: Path) -> Client:
    session_string = path.read_text(encoding="utf8")
    return Client(
        name=path.stem,
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=session_string,
        in_memory=True,
    )


def loadClientsInFolder() -> List[Client]:
    session_folder = Path(ROOTPATH, "sessions")
    file_paths = glob.glob(os.path.join(session_folder.as_posix(), "*.txt"))

    file_content_list = []
    for file_path in file_paths:
        with open(file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
            file_name = Path(file_path).stem
            if file_name == INFO_BOT:
                continue
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


def filter(user: Union[Chat, ChatPreview]) -> bool:
    if (
        user.photo
        and user.username
        and user.last_name
        and user.first_name
        and user.bio
        and user.type == ChatType.PRIVATE
    ):
        return True
    return False


async def getGroupUser(
    client: Client, limit: int = 20
) -> Optional[List[BaseUser]]:
    """get group users
    directly get users list must be group Administrator
    but get history message is not need.
    """
    userObjs: List[BaseUser] = []
    skip_user: List[int] = []
    exists_user: List[int] = []

    try:
        await client.get_chat(COPY_GROUP_ID)
        await client.join_chat(COPY_GROUP_ID)
    except Exception as exc:
        logger.error("信息号未加入克隆群！", exc)
        raise exc

    logger.info(f"正在读取群的历史信息以便读取群用户")

    logger.info("获取中.....")
    async for i in client.get_chat_history(COPY_GROUP_ID):
        if isinstance(i, Message) and i.from_user:
            user_id: int = i.from_user.id
            if (user_id in exists_user) or (user_id in skip_user):
                # logger.debug(f"{user_id} 用户重复 skip")
                continue
            if i.from_user.is_bot:
                skip_user.append(user_id)
                logger.debug("是机器人 skip")
                continue

            try:
                rawUser = await client.get_chat(user_id)
                logger.info(f"get_chat:{user_id}")
                await asyncio.sleep(0.5)
            except Exception as exc:
                skip_user.append(user_id)
                logger.error(f"获取用户资料出现错误:{exc}")
                continue

            if not filter(rawUser):
                skip_user.append(user_id)
                logger.info(f"过滤掉没资料不全的用户{user_id}！")
                continue

            exists_user.append(rawUser.id)
            user: BaseUser = BaseUser(
                first=rawUser.first_name,
                last=rawUser.last_name,
                username=rawUser.username,
                bio=rawUser.bio,
                photo=await client.download_media(
                    rawUser.photo.small_file_id, in_memory=True
                ),
            )
            userObjs.append(user)
            logger.success(f"获取到用户:{user}")

        if len(userObjs) >= limit:
            logger.success(f"收集{len(userObjs)}条账号信息完成!")
            return userObjs


async def ATryInvoke(func: Callable):
    try:
        await func()
    except Exception as e:
        logger.error(f"setProfile Error:{e} {func.__name__}")
        logger.exception(f"setProfile Error:{e} {func.__name__}")


async def setProfile(client: Client, user: BaseUser):
    await ATryInvoke(
        lambda: client.update_profile(
            first_name=user.first, last_name=user.last, bio=user.bio
        )
    )

    await ATryInvoke(
        lambda: client.set_username(
            username=user.username + "".join(random.choices("1234567890", k=3))
        )
    )

    await ATryInvoke(lambda: client.set_profile_photo(photo=user.photo))

    await ATryInvoke(
        lambda: client.invoke(
            functions.account.SetPrivacy(
                types.InputPrivacyKeyPhoneNumber,
                types.InputPrivacyValueDisallowAll,
            )
        )
    )

    await ATryInvoke(
        lambda: client.invoke(
            functions.account.SetPrivacy(
                types.InputPrivacyKeyPhoneCall,
                types.InputPrivacyValueDisallowAll,
            )
        )
    )

    logger.success(f"{client.name} 修改信息成功!")


def renameTXT(path: Path, fileName: str):
    path.rename(Path(path.parent, f"{fileName}.txt"))


# ====== Helper Function End ====


async def main():
    accounts: List[Client] = loadClientsInFolder()
    infoBot = makeClient(Path(SESSION_PATH, f"{INFO_BOT}.txt"))

    async with infoBot:
        user = await infoBot.get_me()

        logger.success(
            f"""
    -------login success--------
    username: {user.first_name}
    type: {"Bot" if user.is_bot else "User"}
    @{user.username}
    ----------------------------
    """
        )
        userObjs = await getGroupUser(infoBot, limit=len(accounts))
        if not userObjs:
            return

    logger.success("正在批量登陆并修改信息")

    for k, app in enumerate(accounts):
        async with app:
            account_info = await app.get_me()
            logger.success(
                f"""
                -------改信息 login success--------
                username: {account_info.first_name}
                type: {"Bot" if account_info.is_bot else "User"}
                @{account_info.username}
                ----------------------------
                """
            )
            await setProfile(app, user=userObjs[k])
            renameTXT(
                Path(SESSION_PATH, f"{app.name}.txt"),
                fileName=userObjs[k].first,
            )
            await app.enable_cloud_password("888888")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    with closing(loop):
        with suppress(asyncio.exceptions.CancelledError):
            loop.run_until_complete(main())
        loop.run_until_complete(asyncio.sleep(3.0))  # task cancel wait 等待任务结束
    # asyncio.run(makeSessionString())
