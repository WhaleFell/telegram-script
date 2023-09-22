from pyrogram import Client, compose, filters, handlers, types as ptypes, errors
from pyrogram.raw import functions, types
import os
import asyncio
import sys

api_id = "27383462"
api_hash = "4309430458dda9e90978961986c46041"

group_ids = [-1001979255590,-1001811589217,-1001919310248]

debug = False

SERVICE_INFO = {
  "name": "ok红包脚本2",
}

async def main():
  session_files = [i for i in os.listdir(sys.path[0]) if i.endswith(".session")]
  apps = []
  for i in session_files:
    
    app = Client(i.split('.')[0], api_id=api_id, api_hash=api_hash, workdir=sys.path[0])
    
    me = None
    try:
      async with app:
        await app.invoke(functions.account.UpdateStatus(offline=False))
        me = await app.get_me()
        print(me.first_name, "登录成功")
    except:
        print(i, "失效")
        continue
    def mk_pocket_handler(me):
      async def pocket_handler(client:Client, message: types.message.Message):
        if debug:
          print(message)
        if message.text == None and message.caption == None and message.game == None:
          return 
        if hasattr(message.reply_markup, "inline_keyboard"):
          for i in message.reply_markup.inline_keyboard:
            for i in i:
              try:
                await client.request_callback_answer(
                    chat_id=message.chat.id,
                    message_id=message.id,
                    callback_data=i.callback_data
                )
              except errors.exceptions.bad_request_400.DataInvalid:
                pass
              except Exception as e:
                if debug:
                  print(e)
              if debug:
                print("抢红包触发，消息ID:", message.id)
      return pocket_handler
            #await client
    def mk_pocket_edited_handler(me):
      async def pocket_edited_handler(client:Client, message: types.message.Message):
        if message.text == None:
          return 
        if "红包" in message.text and me.first_name in message.text:
          for i in message.text.split("\n\n")[1].split("\n"):
            if me.first_name in i:
              print(me.first_name, "抢到", i.split(' ')[1].split('(')[0], message.text.split("💰")[0].split(" ")[-1])
      return pocket_edited_handler
    
    app.add_handler(handlers.MessageHandler(mk_pocket_handler(me), filters=filters.chat(group_ids)))
    app.add_handler(handlers.edited_message_handler.EditedMessageHandler(mk_pocket_edited_handler(me), filters=filters.chat(group_ids)))
    apps.append(app)
  print("全部用户登录完毕，开始运行。")
  print("监听以下群组")
  for i in group_ids:
    print(i)
  await compose(apps)
  

if __name__ == "__main__":
  uvloop.install()
  if debug:
    asyncio.run(main())
  else:
    os.close(sys.stderr.fileno())
    try:
      asyncio.run(main())
    except:
      pass
  #main()
