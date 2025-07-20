# -*- coding: utf-8 -*-
import sys
import os
import json
import csv
import base64
import time
import asyncio
import requests
from urllib.parse import unquote
from cloudscraper import create_scraper
from Crypto.Hash import MD5
from Crypto.Cipher import AES
from telethon import TelegramClient, utils
from telethon.tl.functions.account import UpdateStatusRequest
from telethon.tl.functions.messages import RequestAppWebViewRequest
from telethon.tl.types import InputUser, InputBotAppShortName
from telethon.tl.functions.channels import JoinChannelRequest
from licensing.methods import Helpers
from colorama import Fore, init

init(autoreset=True)
print("Aktual codemi")
url = "https://raw.githubusercontent.com/Enshteyn40/crdevice/refs/heads/main/tonnel_3.csv"
machine_code = Helpers.GetMachineCode(v=2)

def evp_kdf(password: bytes, salt: bytes, key_len: int, iv_len: int):
    dtot, d = b"", b""
    while len(dtot) < key_len + iv_len:
        d = MD5.new(d + password + salt).digest()
        dtot += d
    return dtot[:key_len], dtot[key_len:key_len + iv_len]

def encrypt_timestamp(timestamp, secret_key):
    text = str(timestamp)
    salt = os.urandom(8)
    key, iv = evp_kdf(secret_key.encode(), salt, 32, 16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    pad_len = AES.block_size - len(text.encode()) % AES.block_size
    padded = text.encode() + bytes([pad_len] * pad_len)
    encrypted = cipher.encrypt(padded)
    return base64.b64encode(b"Salted__" + salt + encrypted).decode()

def ensure_path_and_file(path, filename):
    os.makedirs(path, exist_ok=True)
    filepath = os.path.join(path, filename)
    if not os.path.isfile(filepath):
        print(Fore.WHITE + f"{filename} fayli topilmadi. Yaratildi.")
        with open(filepath, 'w', encoding='utf-8') as f:
            pass
        sys.exit("Endi gividlarni yozib chiqing")
    return filepath

# ... yuqoridagi kod o‘zgarmaydi ...

async def process(tg_client: TelegramClient, phone_number: str):
    async with tg_client:
        await tg_client(UpdateStatusRequest(offline=False))
        bot_entity = await tg_client.get_entity("tonnel_network_bot")
        bot = InputUser(user_id=bot_entity.id, access_hash=bot_entity.access_hash)
        bot_app = InputBotAppShortName(bot_id=bot, short_name="gifts")
        web_view = await tg_client(
            RequestAppWebViewRequest(peer='me', app=bot_app, platform="android")
        )

        init_data = unquote(web_view.url.split('tgWebAppData=')[1].split('&')[0])
        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8",
            "content-type": "application/json",
            "origin": "https://marketplace.tonnel.network",
            "referer": "https://marketplace.tonnel.network",
            "user-agent": "Mozilla/5.0"
        }

        with create_scraper() as http_client:
            http_client.headers = headers
            iduser = (await tg_client.get_me()).id

            # balansni tekshirish
            resp = http_client.post(
                url="https://gifts3.tonnel.network/api/balance/info",
                json={"authData": init_data, "ref": None},
                headers=headers,
                timeout=10
            )
            if not resp.ok:
                print(Fore.RED + f"Xatolik (balance): {resp.status_code} {resp.text}")
                return

            data = resp.json()
            balance = data.get("balance", 0)
            print(Fore.YELLOW + f"💰 Balans: {balance}")

            # giftlarni olish
            psondata = {
                "page": 1,
                "limit": 30,
                "sort": json.dumps({"message_post_time": -1, "gift_id": -1}),
                "filter": json.dumps({
                    "seller": iduser,
                    "buyer": {"$exists": False},
                    "$or": [
                        {"price": {"$exists": True}},
                        {"auction_id": {"$exists": True}}
                    ]
                }),
                "ref": f"ref_{iduser}",
                "user_auth": init_data
            }

            resp = http_client.post(
                url="https://gifts2.tonnel.network/api/pageGifts",
                json=psondata,
                headers=headers,
                timeout=10
            )
            if not resp.ok:
                print(Fore.RED + f"Xatolik (gifts): {resp.status_code} {resp.text}")
                return

            gifts = resp.json()
            listed_gift_count = len(gifts)

            print(Fore.GREEN + f"🎁 Listed giftlar: {listed_gift_count}")

            # 🔷 Shart: balans >= 0.5 yoki listed giftlar mavjud bo‘lsa yoziladi
            if balance >= 0.5 or listed_gift_count > 0:
                print(Fore.CYAN + "✅ Raqam qidirilayotgan raqam shartlariga moz, yozilmoqda...")
                with open("tonnelichida.csv", "a", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        phone_number,
                        balance,
                        listed_gift_count
                    ])

                # giftlarni ham chiqarsin
                for gift in gifts:
                    print(f"Name: {gift.get('name','')}")
                    print(f"Model: {gift.get('model','')}")
                    print(f"Symbol: {gift.get('symbol','')}")
                    print(f"Backdrop: {gift.get('backdrop','')}")
                    print("-" * 30)

            else:
                print(Fore.LIGHTBLACK_EX + "⚠️ Shart bajarilmadi, yozilmadi.")

# ... qolgan main() va boshqa kodlar o‘sha-o‘sha ...


async def main():
    # CSV joylashgan path’ni aniqlash
    if os.path.exists('/storage/emulated/0/giv'):
        mrkt_file = ensure_path_and_file('/storage/emulated/0/giv', 'tonnelgivlar.csv')
    elif os.path.exists('C:\\join'):
        mrkt_file = ensure_path_and_file('C:\\join', 'tonnelgivlar.csv')
    else:
        sys.exit(Fore.YELLOW + "Mos papka topilmadi.")

    with open('phone.csv', 'r', encoding='utf-8') as f:
        phlist = [row[0] for row in csv.reader(f) if row]

    api_id, api_hash = 22962676, '543e9a4d695fe8c6aa4075c9525f7c57'

    for idx, phone in enumerate(phlist):
        print(Fore.CYAN + f"📲 Login: {phone}")
        print(Fore.MAGENTA + f"📶 Nechanchi raqam: {idx+1}")
        tg_client = TelegramClient(f"sessions/{utils.parse_phone(phone)}", api_id, api_hash)
        try:
            await process(tg_client, phone)
            await asyncio.sleep(2.5)
        except Exception as e:
            print(Fore.RED + f"❌ Xatolik ({phone}): {e}")

if __name__ == "__main__":
    asyncio.run(main())
