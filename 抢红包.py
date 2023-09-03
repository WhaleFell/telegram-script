from pyrogram import Client, compose, filters, handlers, types as ptypes, errors
from pyrogram.raw import functions, types
import os
import asyncio
import sys
from loguru import logger

api_id = "28340368"
api_hash = "514cc2ec366cf8c59b7ad84560598660"

group_ids = [-1001797337928, -1001615949926]

debug = True

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

SERVICE_INFO = {
    "name": "ok红包脚本2",
}


async def main():
    session_files = [i for i in os.listdir(
        sys.path[0]) if i.endswith(".session")]
    apps = []
    for i in session_files:

        app = Client(i.split('.')[0], api_id=api_id,
                     api_hash=api_hash, workdir=sys.path[0], device_model="wf-tgbot")

        me = None
        #  try login
        try:
            async with app:
                # keep oneline
                await app.invoke(functions.account.UpdateStatus(offline=False))
                me = await app.get_me()
                logger.success(
                    f"login Account Success user:{me.first_name} phone_number:{me.phone_number}"
                )
        except:
            print(i, "失效")
            continue

        def mk_pocket_handler(me):
            async def pocket_handler(client: Client, message: types.message.Message):
                # 判断信息
                if message.text == None and message.caption == None and message.game == None:
                    return

                # 判断是否含有回复标记 即回复按钮
                if hasattr(message.reply_markup, "inline_keyboard"):
                    for i in message.reply_markup.inline_keyboard:
                        for i in i:
                            logger.info("bnt:%s" % i)
                            try:
                                # 请求机器人回拨答案。这相当于单击包含回调数据的内联按钮。
                                await client.request_callback_answer(
                                    chat_id=message.chat.id,
                                    message_id=message.id,
                                    callback_data=i.callback_data,
                                )
                                logger.success("抢红包触发，消息ID:", message.id)

                            except Exception as e:
                                logger.exception("error!")
                                # logger.error(message)
                                logger.critical(f"{e}")
            return pocket_handler

        # 监听自己签到红包的信息
        def mk_pocket_edited_handler(me):
            """closure is use to mk pocket_edited_handler"""
            async def pocket_edited_handler(client: Client, message: types.message.Message):
                if message.text == None:
                    return
                if "红包" in message.text and me.first_name in message.text:
                    for i in message.text.split("\n\n")[1].split("\n"):
                        if me.first_name in i:
                            print(me.first_name, "抢到", i.split(' ')[1].split(
                                '(')[0], message.text.split("💰")[0].split(" ")[-1])
            return pocket_edited_handler

        app.add_handler(handlers.MessageHandler(
            mk_pocket_handler(me), filters=filters.chat(group_ids)))
        app.add_handler(handlers.edited_message_handler.EditedMessageHandler(
            mk_pocket_edited_handler(me), filters=filters.chat(group_ids)))
        apps.append(app)

    print("全部用户登录完毕，开始运行。")
    print("监听以下群组")
    for i in group_ids:
        print(i)

    # 监听多个账号
    await compose(apps)


if __name__ == "__main__":
    if debug:
        asyncio.run(main())
    else:
        # close input error
        os.close(sys.stderr.fileno())
        try:
            asyncio.run(main())
        except:
            pass
