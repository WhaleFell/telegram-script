# coding: utf-8

from pyrogram import Client, compose, filters, handlers, types as ptypes, errors
from pyrogram.raw import functions, types
import os
import uvloop, asyncio
import sys, xlrd

SERVICE_INFO = {
  'name': '批量发消息'
}

api_id = "27383462"
api_hash = "4309430458dda9e90978961986c46041"

group_ids = [-1001949022163]

debug = False

def get_msg():
  book = xlrd.open_workbook(os.path.join(sys.path[0], "msg.xls"))
  sheet = book.sheet_by_index(0)
  res = {}
  for i in zip(sheet.col(colx=0), sheet.col(colx=1)):
    res[i[0].value] = i[1].value
  return res

async def main():
  session_files = [i for i in os.listdir(sys.path[0]) if i.endswith(".session")]
  apps = []
  msgs = get_msg()
  for i in session_files:
    session_name = i.split('.')[0]
    if not session_name in list(msgs.keys()):
      print(i, "没有配置消息")
      continue
    app = Client(session_name, api_id=api_id, api_hash=api_hash, workdir=sys.path[0])
    banned_group = []
    me = None
    async with app:
      await app.invoke(functions.account.UpdateStatus(offline=False))
      me = await app.get_me()
      if debug:
        print(me)
      print(me.first_name, "登录成功")
    
      for i in group_ids:
        if debug:
          print("测试", i)
        try:
          await app.send_message(i, msgs[session_name])
          print(session_name, "发送成功")
        except errors.exceptions.forbidden_403.Forbidden as e:
          if debug:
              print(i, e)
          if "CHAT_SEND_PLAIN_FORBIDDEN" in str(e) or "CHAT_WRITE_FORBIDDEN" in str(e):
            banned_group.append(i)
        except Exception as e:
          if debug:
            print(e)
          print(session_name, "发送消息失败")     
    if debug:
      print(banned_group)
    def mk_改禁言_handler(me: ptypes.User, message, gp):
      async def raw_update_handler(client: Client, update: ptypes.Update, users, chats):
        if "UpdateChatDefaultBannedRights" in str(type(update)):
          if debug:
            print(update)
          if not update.default_banned_rights.send_messages:
            if hasattr(update.peer, "chat_id"):
              if debug: 
                print(-1*update.peer.chat_id ,gp)
              if -1*update.peer.chat_id in gp:
                if debug:
                  print(await client.send_message(-1*update.peer.chat_id, message))
                else:
                  await client.send_message(-1*update.peer.chat_id, message)
                  print(me.first_name, "发送成功")
                gp.remove(-1*update.peer.chat_id)
            if hasattr(update.peer, "channel_id"):
              cid = int("-100" + str(update.peer.channel_id))
              print(cid, gp)
              if cid in gp:
                if debug:
                  print(await client.send_message(cid, message))
                else:
                  await client.send_message(cid, message)
                  print(me.first_name, "发送成功")
                gp.remove(cid)
            #await send_message()
      return raw_update_handler
    app.add_handler(handlers.raw_update_handler.RawUpdateHandler(mk_改禁言_handler(me, msgs[session_name], banned_group)))
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
    try:
      asyncio.run(main())
    except:
      pass
  #main()