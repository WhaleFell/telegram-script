import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# 替换成你的 API ID 和 API Hash
api_id = YOUR_API_ID
api_hash = 'YOUR_API_HASH'

# 创建一个 Pyrogram 客户端
app = Client("my_account", api_id=api_id, api_hash=api_hash)

# 定义管理员私聊过滤器
admin_filter = filters.create(
    lambda _, __, message: message.from_user.id == ADMIN_ID)

# 处理管理员发送的 "/join" 命令


@app.on_message(admin_filter & filters.command("join", prefixes="/"))
async def join_chat(client, message):
    chat_id = message.text.split()[1]  # 获取要加入的群聊 ID
    await client.join_chat(chat_id)  # 加入群聊
    await message.reply_text(f"已加入群聊 {chat_id}")

# 处理管理员发送的 "/leave" 命令


@app.on_message(admin_filter & filters.command("leave", prefixes="/"))
async def leave_chat(client, message):
    joined_groups = await client.get_chat_members_count().result  # 获取机器人当前所加入的群聊数量

    if joined_groups == 0:
        await message.reply_text("没有加入任何群聊")
        return

    keyboard = []
    for group_id in joined_groups:
        chat_info = await client.get_chat(group_id).result  # 获取群聊的详细信息
        chat_title = chat_info.title  # 获取群聊的名称
        keyboard.append([InlineKeyboardButton(
            f"{chat_title} ({group_id})", callback_data=f"leave_{group_id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text("请选择要退出的群聊：", reply_markup=reply_markup)

# 处理用户点击行内键盘按钮


@app.on_callback_query()
async def callback_handler(client, callback_query):
    query = callback_query.data.split("_")
    action = query[0]  # 获取操作类型（加入或退出）
    group_id = query[1]  # 获取群聊 ID

    if action == "leave":
        await client.leave_chat(group_id)  # 退出群聊
        await callback_query.answer("已退出群聊")
        await callback_query.message.delete()  # 删除选择群聊的消息

# 异步运行客户端


async def main():
    await app.start()
    await app.idle()

asyncio.run(main())
