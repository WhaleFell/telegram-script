from pyrogram import Client
import sys, os, asyncio, random

api_id = "27383462"
api_hash = "4309430458dda9e90978961986c46041"

group = -1001050982793
group_access_session = 'test2'

uinfo_list = []

def uinlist(l, u):
  for i in l:
    if i.id == u.id:
      return True
  return False

async def main():
  session_files = [i for i in os.listdir(sys.path[0]) if i.endswith(".session") if not i.startswith(group_access_session)]
  app = Client(group_access_session, api_id=api_id, api_hash=api_hash, workdir=sys.path[0])
  user_list = []
  ulindex = 0
  tindex = 0
  async with app:
    await app.get_chat(group)
    try:
      await app.join_chat(group)
    except:
      pass
    async for i in app.get_chat_history(group):
      print(tindex)
      tindex += 1
      user = i.from_user
      if user == None:
        continue
      if user.photo == None:
        continue
      if uinlist(user_list, user):
        continue
      if user.is_bot == True:
        continue
      if user.username == None:
        continue
      user_list.append(user)
      ulindex += 1
      if ulindex >= len(session_files):
        break
    for u in user_list:
      uinfo_list.append([u.first_name, u.last_name, u.username, await app.download_media(u.photo.small_file_id, in_memory=True)])
  print(uinfo_list)
  for i in range(ulindex):
    app = Client(session_files[i].split('.')[0], api_id=api_id, api_hash=api_hash, workdir=sys.path[0])
    async with app:
      await app.update_profile(first_name=uinfo_list[i][0],last_name=uinfo_list[i][1])
      try:
        await app.set_username(uinfo_list[i][2] + ''.join(random.choices("1234567890", k=3)))
      except:
        pass
      await app.set_profile_photo(photo=uinfo_list[i][3])
      try:
        await app.enable_cloud_password("88")
      except:
        print("二级密码开启失败")
      print(await app.get_me())
    os.rename(sys.path[0] + '/' + session_files[i], sys.path[0] + '/' + uinfo_list[i][0] + '.session')
      

if __name__ == "__main__":
  asyncio.run(main())