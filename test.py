from pyrogram import Client, idle
import asyncio
from contextlib import closing, suppress
from opentele.td import TDesktop
from telethon import TelegramClient
API_ID = 21341224
API_HASH = "2d910cf3998019516d6d4bbb53713f20"


# bot = Client("17825240276", api_id=API_ID, api_hash=API_HASH)


async def main():
    async with TelegramClient("17825240276", api_id=API_ID, api_hash=API_HASH) as client:
        client.

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    with closing(loop):
        with suppress(asyncio.exceptions.CancelledError):
            loop.run_until_complete(main())

        loop.run_until_complete(asyncio.sleep(3.0))  # task cancel wait 等待任务结束
