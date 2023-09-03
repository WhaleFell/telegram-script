from pyrogram import Client
import pyrogram
import asyncio
phone = "19713190107"
api_id = 21341224
api_hash = "2d910cf3998019516d6d4bbb53713f20"


# pyrogram.raw.functions.auth.SignUp

# pyrogram.raw.functions.auth.SendCode(
#     api_hash="2d910cf3998019516d6d4bbb53713f20",
#     api_id=21341224,
#     phone_number=phone,
#     settings=pyrogram.raw.types.CodeSettings(

#     )
# )
app = Client(
    "bulk_register",
    in_memory=True,
    api_hash="2d910cf3998019516d6d4bbb53713f20",
    api_id=21341224
)


async def main():
    await app.start()
    await app.send_code(phone)


if __name__ == "__main__":
    asyncio.run(main())
