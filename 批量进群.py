from pyrogram import Client
from pyrogram.raw import functions, types
from pyrogram.enums import ChatType
import os
import asyncio
import sys
from loguru import logger

logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:HH:mm:ss}</green> | {name}:{function} {level} | <level>{message}</level>",
    level="DEBUG",
    backtrace=True,
    diagnose=True
)

api_id = "27383462"
api_hash = "4309430458dda9e90978961986c46041"


async def main():

    session_files = [i for i in os.listdir() if i.endswith(".session")]
    print(session_files)
    for i in session_files:
        app = Client(i.split('.')[0], api_id=api_id,
                     api_hash=api_hash, workdir=sys.path[0])
        async with app:
            await app.invoke(functions.account.UpdateStatus(offline=False))
            me = await app.get_me()
            print(me.first_name, "登录成功")
            if os.path.exists(os.path.join(sys.path[0], "groups.txt")):
                with open("groups.txt", "r") as f:
                    content = f.readlines()
                    for i in content:
                        try:
                            if i.startswith("http"):
                                chat = await app.get_chat("@%s" % i.split("/")[-1])
                            else:
                                chat = await app.get_chat(i)
                            logger.success(
                                f"获取群成功名称:{chat.username} 群类型:{chat.type}")
                            if chat.type == ChatType.SUPERGROUP:
                                await app.join_chat(chat_id=chat.id)
                            await app.join_chat(chat_id=chat.id)
                            logger.success(me.first_name+"加入" +
                                           i.replace("\n", '')+"成功")
                        except:
                            # logger.exception("入群错误")
                            print(me.first_name, "已经发出申请了", "群:",
                                  i.replace("\n", ''))

            if os.path.exists(os.path.join(sys.path[0], "bots.txt")):
                with open("bots.txt", 'r') as f:
                    content = f.readlines()
                    for i in content:
                        try:
                            await app.send_message((await app.get_users(i.replace("\n", ''))).id, "/start")
                            print(me.first_name, "向", i.replace(
                                "\n", ''), "发送 /start 成功")
                        except:
                            print(me.first_name, "向", i.replace(
                                "\n", ''), "发送 /start 失败")


async def test():
    session_files = [i for i in os.listdir() if i.endswith(".session")]
    for i in session_files:
        app = Client(i.split('.')[0], api_id=api_id, api_hash=api_hash)
        async with app:
            print(await app.send_message((await app.get_users("@xiejiaoben6bot")).id, "/start"))

if __name__ == "__main__":
    asyncio.run(main())
