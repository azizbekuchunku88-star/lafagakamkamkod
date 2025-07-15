import asyncio
import traceback
import csv
from telethon import utils
from telethon.sync import TelegramClient
from telethon.tl.functions.account import UpdateStatusRequest
import sys
from telethon import TelegramClient, functions
from licensing.methods import Helpers
import requests
from telethon.tl.functions.payments import GetUserStarGiftsRequest

url = "https://raw.githubusercontent.com/Enshteyn40/crdevice/refs/heads/main/giftsana.csv"
machine_code = Helpers.GetMachineCode(v=2)
if machine_code not in requests.get(url).text.splitlines():
    print(f"{machine_code}")
    print("Kodni aktivlashtirish uchun @Enshteyn40 ga murojat qiling")
    sys.exit()
print("✅ Kod aktiv. Oxirgi yangilanish: 16.07.2025")

phonecsv = "phone"
with open(f'{phonecsv}.csv', 'r') as f:
    phlist = [row[0] for row in csv.reader(f)]
print('Jami Nomerlar: ' + str(len(phlist)))

async def main():
    indexx = 0

    # CSVga yozish uchun tayyorlab qo‘yamiz
    with open('giftiborakkauntlar.csv', 'w', newline='', encoding='utf-8') as outcsv:
        writer = csv.writer(outcsv)
        writer.writerow(['phone', 'gift_count'])

        for phone in phlist:
            api_id = 22962676
            api_hash = '543e9a4d695fe8c6aa4075c9525f7c57'
            phone = utils.parse_phone(phone)
            indexx += 1
            print(f'Index : {indexx}')
            tg_client = TelegramClient(f'sessions/{phone}', api_id, api_hash)
            await tg_client.connect()
            if not await tg_client.is_user_authorized():
                print(f"Raqam ro'yxatdan o'tmagan yoki sessiya mavjud emas: {phone}")
                continue

            await tg_client.start()
            await tg_client(UpdateStatusRequest(offline=False))

            try:
                async with tg_client:
                    me = await tg_client.get_me()

                    result = await tg_client(functions.payments.GetUserStarGiftsRequest(
                        user_id=me.id,
                        offset='',
                        limit=100
                    ))

                    gift_count = result.count
                    print(f"Giftlar soni: {gift_count}")

                    # 🔷 Shart: agar giftlar > 0 bo‘lsa — CSVga yozamiz
                    if gift_count > 0:
                        writer.writerow([phone, gift_count])

            except Exception as e:
                traceback.print_exc()
                print(f"Telefon: {phone} ishlamadi. Xato: {e}")

if __name__ == '__main__':
    asyncio.run(main())
