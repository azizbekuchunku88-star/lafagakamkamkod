import csv, asyncio
from re import search
from telethon import functions, utils
from telethon.sync import TelegramClient
from telethon.tl.functions.account import UpdateStatusRequest
import time
def color(text, color_code):
    color_map = {
        "red": "91", "green": "92", "yellow": "93", "blue": "94",
        "magenta": "95", "cyan": "96", "white": "97", "bold_white": "1;97"
    }
    return f"\033[{color_map.get(color_code,'97')}m{text}\033[0m"

api_id = 6810439
api_hash = '66ac3b67cce1771ce129819a42efe02e'
new_id = 22962676
new_hash = '543e9a4d695fe8c6aa4075c9525f7c57'

phonecsv = 'phone'
kutishsoniya = int(input("Kutish soniyasini kiriting xabardan keyin: "))
a = input("Eski parolni yozing: ")
telegramid = 777000
bot = str(input("Qaysi botha sotish kerak: "))

with open('ozim.csv', 'r') as f:
    faxislist = [row[0] for row in csv.reader(f) if row]
if not faxislist:
    print(color("📄 ozim.csv bo'sh!", "red"))
    exit()
phoneozim = faxislist[0]

with open(f'{phonecsv}.csv', 'r') as f:
    phlist = [row[0] for row in csv.reader(f)]
print('\x1b[1;37m\nJami raqamlar: ' + str(len(phlist)))

async def ishlash(phone, indexx):
    print(f'\n    {indexx}-raqam: +{phone}')
    client = TelegramClient(f'sotiladigansessions/{phone}', api_id, api_hash)
    yangi = TelegramClient(f'ozim/{phoneozim}', api_id=new_id, api_hash=new_hash)

    async with client, yangi:
        if not await client.is_user_authorized():
            print('  ❗Sessiondan chiqib ketgan!')
            return

        await yangi(UpdateStatusRequest(offline=False))

        try:
            # Oxirgi xabarni eslab qolish
            old_msg = await client.get_messages(telegramid, limit=1)
            old_id = old_msg[0].id if old_msg else 0
            print(f"📨 Oxirgi xabar id: {old_id}")

            result = await client(functions.account.GetAuthorizationsRequest())
            for auth in result.authorizations:
                print(f" - Device: {auth.device_model}, Platform: {auth.platform}, IP: {auth.ip}, Active: {auth.current}")
                if auth.current:
                    print(f" - Ushbu sessiya qoldirildi: Device: {auth.device_model}")
                else:
                    try:
                        await client(functions.account.ResetAuthorizationRequest(hash=auth.hash))
                        print(f" - Sessiya chiqarildi: Device: {auth.device_model}")
                    except Exception as e:
                        print(f" - Sessiyani chiqarib bo‘lmadi: {e}")
                        with open('24soatlik.csv', 'a', encoding='utf-8') as f24:
                            f24.write(f'+{phone}\n')
                        print(f"❌ Raqam 24soatlik.csv ga yozildi: +{phone}")
                        return

            await client.edit_2fa(current_password=a, new_password="", hint="")
            print("✅ 2FA parol o‘chirildi")

            username = await yangi.get_entity(bot)
            await yangi.send_message(username, phone)
            await asyncio.sleep(kutishsoniya)

            # yangi xabar kelguncha kutish
            print("⌛ Yangi xabarni kutyapmiz...")
            new_msg = None
            while True:
                msgs = await client.get_messages(telegramid, limit=1)
                if msgs and msgs[0].id != old_id:
                    new_msg = msgs[0]
                    break
                await asyncio.sleep(5)

            mes = search(r'\d+', new_msg.message)
            if not mes:
                print(f"❌ Botdan kod topilmadi")
                return

            code_received = mes.group()
            print(f'  📩 Tasdiqlash kodi: {code_received}')
            await yangi.send_message(username, code_received)

            with open('sotilgannomerlar.csv', 'a', encoding='utf-8') as f:
                f.write(f'\n+{phone}')
            print(f"✅ Raqam sotildi va sotilgannomerlar.csv ga yozildi: +{phone}")
            time.sleep(5)

        except Exception as e:
            print(f"❗Xatolik yuz berdi ishlash() ichida: {e}")

async def main():
    for idx, number in enumerate(phlist, 1):
        phone = utils.parse_phone(number)
        await ishlash(phone, idx)

if __name__ == "__main__":
    asyncio.run(main())
