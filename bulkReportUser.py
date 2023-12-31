# /usr/bin/python3
# 通过大量的 TG 账号举报 TG 用户到达封号的目的
# 使用方法：
# 添加用户账号,会保存 session 字符串到 session 目录
# python reportBlockUser.py dump_session 名字
# 更新: 在命令行传递需要举报的账号,并同时运行多个协程来加速举报
# python bulkReportUser.py start "@shenxian"
##########
# 需要举报的账号
import asyncio
from pyrogram.raw import functions, types
from pyrogram import Client, idle
from contextlib import closing, suppress
import functools
from pathlib import Path
import click
from typing import List
import glob
import os
from loguru import logger
import sys
report_user = "@shenxian"
# https://docs.pyrogram.org/topics/advanced-usage#invoking-functions
# https://click-docs-zh-cn.readthedocs.io/zh/latest/

API_ID = "28340368"
API_HASH = "514cc2ec366cf8c59b7ad84560598660"
ROOTPATH = Path(__file__).absolute().parent.as_posix()
DEBUG = True

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


@click.group()
def cli():
    pass


def make_sync(func):
    # https://github.com/pallets/click/issues/2033
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))
    return wrapper


@click.command(name="dump_session", help="导出字符串 session 并保存到目录下的 sessions 文件,需要一个名称参数")
@click.argument('name')
@make_sync
async def dumpTGStringSession(name: str):
    user = Client(name, api_id=API_ID, api_hash=API_HASH, in_memory=True)
    session_folder = Path(ROOTPATH, "sessions")
    session_folder.mkdir(exist_ok=True)

    async with user:
        me = await user.get_me()
        session_string = await user.export_session_string()
        save_path = Path(session_folder, f"{me.username}.txt")
        save_path.write_text(data=session_string, encoding="utf8")
        logger.success(
            f"Get Telegram user:@{me.username} session Success! to save session string in {save_path.as_posix()}"
        )


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
            name=name, session_string=session,
            api_id=API_ID, api_hash=API_HASH, in_memory=True
        )
        for name, session in file_content_list
    ]


def readSession(name: str) -> str:
    session_folder = Path(ROOTPATH, "sessions")
    if not Path(session_folder, f"{name}.txt").exists():
        raise FileNotFoundError(f"{name} 不存在")

    return Path(session_folder, f"{name}.txt").read_text(encoding="utf8")


async def reportUser(client: Client, username: str):
    while True:
        try:
            me = await client.get_me()
            logger.success(f"@{me.username} login success!")
            # Report a peer for violation of telegram’s Terms of Service.
            peer_id = await client.resolve_peer(username)
            logger.info(f"report peer type:{type(peer_id)})")
            await client.invoke(
                functions.account.report_peer.ReportPeer(
                    peer=peer_id,
                    reason=types.InputReportReasonSpam(),
                    message=f"""
    I am writing to report a user on Telegram by the username of @{username} for frequently sending spam messages. The user has been consistently sending unsolicited messages to several users, causing inconvenience and disturbance.
    I kindly request that immediate action be taken to address this issue and ensure that such behavior is not tolerated on the platform.
    Thank you for your attention to this matter.
    """
                )
            )
            logger.success(f"@{me.username} report {username} success!")

        except Exception as e:
            # logger.exception(e)
            logger.error(f"举报失败哦！{e}")
        finally:
            await asyncio.sleep(5)


async def main(username):
    global report_user
    clients = loadClientsInFolder()

    tasks = []

    for client in clients:
        try:
            await client.start()
            me = await client.get_me()
            logger.success(f"@{me.username} login success!")
        except Exception as e:
            logger.error(f"{client.name}登录失败了")
            continue

        tasks.append(
            reportUser(client, username=username)
        )

    print("s11s11", tasks)
    await asyncio.gather(*tasks)

    await idle()

    for client in clients:
        await client.stop()


@click.command(help="main runnning loop")
@click.argument("username")
def start(username: str):
    loop = asyncio.get_event_loop()
    with closing(loop):
        with suppress(asyncio.exceptions.CancelledError):
            loop.run_until_complete(main(username))

        loop.run_until_complete(asyncio.sleep(0.5))  # task cancel


cli.add_command(dumpTGStringSession)
cli.add_command(start)

if __name__ == "__main__":
    cli()
