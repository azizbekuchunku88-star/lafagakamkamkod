import csv
import asyncio, csv, os, sys, requests, traceback
import asyncio
from licensing.methods import Helpers
from telethon import utils, errors
from telethon.sync import TelegramClient
from telethon.tl.functions.account import UpdateStatusRequest
from telethon.tl.functions.channels import (
    CreateChannelRequest, EditAdminRequest, InviteToChannelRequest
)
from termcolor import colored
from telethon.tl.functions.messages import ExportChatInviteRequest
from datetime import datetime
import pytz


url = "https://raw.githubusercontent.com/Enshteyn40/crdevice/refs/heads/main/guruhyarat.csv"
machine_code = Helpers.GetMachineCode(v=2)
if machine_code not in requests.get(url).text.splitlines():
    print(colored(f"{machine_code}", "magenta"))
    print(colored("Kodni aktivlashtirish uchun @Enshteyn40 ga murojat qiling", "magenta"))
    sys.exit()
print(colored("✅ Kod aktiv. Oxirgi yangilanish: 13.07.2025", "magenta"))

# Toshkent time-zone
tashkent_tz = pytz.timezone("Asia/Tashkent")
from telethon.tl.types import ChatAdminRights

# 🔷 API ma'lumotlari
api_id = 22962676
api_hash = '543e9a4d695fe8c6aa4075c9525f7c57'

# 🔷 Linklar yuboriladigan guruh ID
DESTINATION_CHAT_ID = -4975770375

# 🔷 Admin qilinadigan botlar
bots = [
    '@reklamatarqat_bot',
    '@Tozala_bot',
    '@TaronaBot'
]

# 🔷 Glavniy raqamni o‘qish
with open('glavniyraqam.csv', 'r') as f:
    faxislist = [row[0] for row in csv.reader(f) if row]
if not faxislist:
    print("📄 glaniyraqam.csv bo'sh!")
    exit()
phoneozim = faxislist[0]

# 🔷 Raqamlarni o‘qish
with open('phone.csv', 'r') as f:
    phlist = [row[0] for row in csv.reader(f) if row]

# 🔷 Guruh sonini bir marta so‘raymiz
while True:
    try:
        count = int(input("❓ Nechta superguruh yaratmoqchisiz (har bir raqam uchun)? "))
        break
    except ValueError:
        print("🚫 Noto'g'ri son. Raqam kiriting.")
# 🔷 Guruh sonini bir marta so‘raymiz
while True:
    try:
        sleeptime = int(input("❓ Guruhlar yaratish orasida necha sekunddan kutish kerak)? "))
        break
    except ValueError:
        print("🚫 Noto'g'ri son. Raqam kiriting.")

async def add_bots_as_admin(client, chat):
    """Botlarni guruhga qo‘shib, admin qilib belgilaydi"""
    rights = ChatAdminRights(
        change_info=True, post_messages=True, edit_messages=True,
        delete_messages=True, ban_users=True, invite_users=True,
        pin_messages=True, add_admins=True, manage_call=True, other=True
    )

    for bot_username in bots:
        try:
            print(f"➕ {bot_username} ni qo‘shyapman...")
            await client(InviteToChannelRequest(channel=chat, users=[bot_username]))
            await asyncio.sleep(1)

            bot_entity = await client.get_entity(bot_username)
            await client(EditAdminRequest(
                channel=chat,
                user_id=bot_entity,
                admin_rights=rights,
                rank="Admin"
            ))
            print(f"✅ {bot_username} admin bo‘ldi.")
            await asyncio.sleep(1)

        except errors.UserAlreadyParticipantError:
            print(f"ℹ️ {bot_username} allaqachon guruhda.")
        except Exception as e:
            print(f"❌ Bot {bot_username} bilan muammo: {e}")

async def get_group_link(client, chat_id, retries=3):
    """Guruh uchun linkni olishga 3 marta urinadi"""
    for attempt in range(retries):
        try:
            invite = await client(ExportChatInviteRequest(chat_id))
            return invite.link
        except Exception as e:
            print(f"⚠️ Link olish urinish {attempt+1}: xato: {e}")
            await asyncio.sleep(1)
    return "Linkni olishda xato"

async def create_supergroup(client, phone, yangi_client):
    for i in range(count):
        print(f"Kutish vaqti kutayabman {sleeptime} - sekund")
        await asyncio.sleep(sleeptime)
        title = f'SUPERGROUP__{i + 1}'
        about = f'{title} haqida ma’lumot'
        try:
            result = await asyncio.wait_for(
                client(CreateChannelRequest(title=title, about=about, megagroup=True)),
                timeout=30
            )

            chat = result.chats[0]
            print(f"✅ Yaratildi: {title}")
            await client.send_message(chat.id, "Salom")

            await add_bots_as_admin(client, chat)

            link = await get_group_link(client, chat.id)
            now_tashkent = datetime.now(tashkent_tz).strftime("%Y-%m-%d %H:%M:%S")

            msg = (
                f"📄 Raqam: {phone}\n"
                f"🔗 Guruh: {title}\n"
                f"➡️ Link: {link}\n"
                f"🕒 Yaratilgan: {now_tashkent}"
            )
            print(msg)

            await yangi_client.send_message(DESTINATION_CHAT_ID, msg)

        except asyncio.TimeoutError:
            print(f"⚠️ Timeout: {title} yaratilmadi")

async def main():
    # 🔷 Glavniy clientni ochib olamiz
    yangi_client = TelegramClient(f'glavniy/{phoneozim}', api_id=api_id, api_hash=api_hash)
    await yangi_client.start()
    await yangi_client(UpdateStatusRequest(offline=False))

    for index, phone_number in enumerate(phlist):
        try:
            phone = utils.parse_phone(phone_number)
            print(f'\n📱 {index + 1}-akkaunt: {phone}')

            client = TelegramClient(f"sessions/{phone}", api_id, api_hash)
            await client.start()
            await client(UpdateStatusRequest(offline=False))

            await create_supergroup(client, phone, yangi_client)

            await client.disconnect()

        except Exception as e:
            print(f"❌ ERROR: {e} (akkaunt {index + 1})")
            print("⏩ Davom etamiz...")
            continue

    await yangi_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
