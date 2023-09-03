from pyrogram import Client, idle
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler
import pyrogram
import os
import sys
import asyncio
from loguru import logger

api_id = "28340368"
api_hash = "514cc2ec366cf8c59b7ad84560598660"


if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

loglevel = "DEBUG"

logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:HH:mm:ss}</green> | {name}:{function} {level} | <level>{message}</level>",
    level=loglevel,
    backtrace=True,
    diagnose=True
)

session_files = [i for i in os.listdir(
    sys.path[0]) if i.endswith(".session")]


async def messageHandle(client: pyrogram.client.Client, message: Message):
    logger.debug(f"rev: {message.text}")


async def main():
    global app
    app = Client(
        name=session_files[0].split('.')[0],
        api_id=api_id,
        api_hash=api_hash,
        device_model="wf-tgbot"
    )
    await app.start()  # 启动

    app.add_handler(
        MessageHandler(
            messageHandle,
            filters=None,
        )
    )

    user = await app.get_me()
    logger.success(
        f"login Account Success user:{user.first_name} phone_number:{user.phone_number}"
    )

    await idle()  # 堵塞

if __name__ == "__main__":
    asyncio.run(main())
