# -*- coding: utf-8 -*- captchasiz randomize
import requests
from licensing.methods import Helpers
import sys
import os
import csv
import json
from telethon.tl.functions.channels import JoinChannelRequest
from telethon import types, utils, errors
import time
from urllib.parse import unquote
from telethon.sync import TelegramClient
from telethon.tl.functions.account import UpdateStatusRequest
from telethon.tl.types import InputUser
from telethon.tl.functions.messages import RequestAppWebViewRequest
from telethon.tl.types import InputBotAppShortName
from datetime import datetime, timezone, timedelta
import asyncio

def color(text, color_code):
    color_map = {
        "red": "91",
        "green": "92",
        "yellow": "93",
        "blue": "94",
        "magenta": "95",
        "cyan": "96",
        "white": "97",
        "bold_white": "1;97"
    }
    code = color_map.get(color_code, "97")
    return f"\033[{code}m{text}\033[0m"

url = "https://raw.githubusercontent.com/Enshteyn40/crdevice/refs/heads/main/randomize_3.csv"
response = requests.get(url)
lines = response.text.splitlines()
hash_values_list = [line.strip() for line in lines]

def GetMachineCode():
    return Helpers.GetMachineCode(v=2)

machine_code = GetMachineCode()
print(color(machine_code, "white"))

if machine_code in hash_values_list:
    #captchasiz kod
    import ssl
    import base64
    import asyncio
    from urllib.parse import unquote
    from telethon.tl.functions.messages import ImportChatInviteRequest
    import aiohttp
    import time
    import aiohttp_proxy
    import fake_useragent
    from telethon import TelegramClient
    from telethon.tl.functions.channels import JoinChannelRequest
    from telethon.sessions import StringSession
    from telethon.tl.types import InputUser, InputBotAppShortName
    from telethon.tl.functions.messages import RequestAppWebViewRequest
    import csv
    from termcolor import colored
    from telethon.tl.functions.account import UpdateStatusRequest
    
    import os
    import sys
    
    def detect_environment():
        phone_path = "/storage/emulated/0/giv"
        pc_path = "C:/join"
    
        if os.path.exists(phone_path):
            print("📱 Telefon muhitida ishga tushdi")
            return phone_path
        elif os.path.exists(pc_path):
            print("💻 Kompyuter muhitida ishga tushdi")
            return pc_path
        else:
            try:
                os.makedirs(phone_path)
                print(f"📂 {phone_path} papkasi yaratildi (telefon muhit deb qabul qilindi)")
                return phone_path
            except:
                try:
                    os.makedirs(pc_path)
                    print(f"📂 {pc_path} papkasi yaratildi (kompyuter muhit deb qabul qilindi)")
                    return pc_path
                except Exception as e:
                    print("❌ Hech bir muhit aniqlanmadi va papka yaratilolmadi")
                    print(f"Xatolik: {e}")
                    sys.exit("⛔ Dastur to‘xtatildi. Papkalarni qo‘lda yarating va qayta urinib ko‘ring.")
    
    # 🔁 Hamma fayllarni shu asosiy yo‘l orqali boshqaramiz
    BASE_PATH = detect_environment()
    
    def file_path(filename):
        return os.path.join(BASE_PATH, filename)
    with open(file_path("proxy.csv"), 'r') as f:
        reader = csv.reader(f)
        ROTATED_PROXY = next(reader)[0]
        
        
    def read_csv(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Sarlavha qatorini o'tkazib yuborish
            return [(row[0].strip(), row[1].strip()) for row in reader if len(row) == 2]
    
    givs = []
    bot_mapping = {}
    with open(file_path("randogiv.csv"), 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2:
                key = row[0].strip()
                val = row[1].strip()
                givs.append(key)
                bot_mapping[key] = val
                
    print("📌 Yuklangan start_param lar va botlar:")
    for k, v in bot_mapping.items():
        print(f"   ➤ {k} => {v}")
    
    with open(file_path("randolimit.csv"), 'r') as f:
        reader = csv.reader(f)
        limituzz = int(next(reader)[0])
    print(f"Kutiladigan vaqt - {limituzz}")
    with open(file_path("ranochiqkanal.csv"), 'r') as f:
        premium_channels = [row[0] for row in csv.reader(f)]
    
    with open(file_path("ranyopiqkanal.csv"), 'r') as f:
        yopiq_channels = [row[0] for row in csv.reader(f)]
    
    channels = premium_channels + yopiq_channels
    
    async def run(phone, start_params, channels):
        api_id = 22962676
        api_hash = '543e9a4d695fe8c6aa4075c9525f7c57'
    
        tg_client = TelegramClient(f"sessions/{phone}", api_id, api_hash)
        await tg_client.connect()
        if not await tg_client.is_user_authorized():
            print('Sessiyasi yoq raqam ')
        else:
            async with tg_client:
                me = await tg_client.get_me()
                await tg_client(UpdateStatusRequest(offline=False))
                name = me.username or me.first_name + (me.last_name or '')
                for yopiq_link in yopiq_channels:
                    try:
                        await tg_client(ImportChatInviteRequest(yopiq_link)) 
                        time.sleep(limituzz)
                        print(colored(f"{name} | Kanalga a'zo bo'ldi {yopiq_link}", "green"))
                    except Exception as e:
                        print(colored(f"{name} | Kanalga qo'shilishda xatolik {yopiq_link}: {e}", "red")) 
    
                for ochiq_link in premium_channels:
                    try:
                        await tg_client(JoinChannelRequest(ochiq_link)) 
                        time.sleep(limituzz)
                        print(colored(f"{name} | Kanalga a'zo bo'ldi {ochiq_link}", "green"))
                    except Exception as e:
                        print(colored(f"{name} | Kanalga qo'shilishda xatolik {ochiq_link}: {e}", "red"))   
    
                for start_param in start_params:
                    start_param = start_param.strip()  # 👈 bu MUHIM
                    bot_username = bot_mapping.get(start_param)
                    if not bot_username:
                        print(colored(f"🚫 Giv uchun bot topilmadi: {start_param}", "red"))
                        continue
                    print(colored(f"✅ Giv uchun bot topildi: {start_param} → {bot_username}", "green"))
    
                    bot_entity = await tg_client.get_entity(bot_username)
                    bot = InputUser(user_id=bot_entity.id, access_hash=bot_entity.access_hash)
                    bot_app = InputBotAppShortName(bot_id=bot, short_name="JoinLot")
    
                    web_view = await tg_client(
                        RequestAppWebViewRequest(
                            peer=await tg_client.get_input_entity('me'),
                            app=bot_app,
                            platform="android",
                            write_allowed=True,
                            start_param=start_param
                        )
                    )
    
                    init_data = unquote(web_view.url.split('tgWebAppData=', 1)[1].split('&tgWebAppVersion')[0])
    
                    headers = {
                        'Host': 'randomgodbot.com',
                        'Accept': '*/*',
                        'Accept-Language': 'ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7',
                        'Cache-Control': 'no-cache',
                        'Connection': 'keep-alive',
                        'Pragma': 'no-cache',
                        'Referer': f'https://randomgodbot.com/join/?tgWebAppStartParam={start_param}',
                        'Sec-Fetch-Dest': 'empty',
                        'Sec-Fetch-Mode': 'cors',
                        'Sec-Fetch-Site': 'same-origin',
                        "User-Agent": "Mozilla/5.0 (Linux; Android 13; SAMSUNG SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/21.0 Chrome/114.0.5735.131 Mobile Safari/537.36"
                    }
    
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    proxy_conn = aiohttp_proxy.ProxyConnector(ssl_context=ssl_context).from_url(ROTATED_PROXY) if ROTATED_PROXY else None
                    async with aiohttp.ClientSession(headers=headers, connector=proxy_conn) as http_client:
                        try:
                            http_client.headers.add('Host', 'randomgodbot.com')
                            encoded_init_data = base64.b64encode(init_data.encode()).decode()
                            url = f"https://185.203.72.14/lot_join?userId={me.id}&startParam={start_param}&id={encoded_init_data}"
                            response = await http_client.get(url=url, ssl=False)
                            response.raise_for_status()
                            response_json = await response.json()
                            description = response_json.get("description", "")
                            result = response_json.get("result", "")
                            ok = response_json.get("ok", False)
    
                            if description == "ALREADY_JOINED":
                                print(colored(f"{name} | ❕ Allaqachon qatnashgan", "blue"))
                                write_to_csv = True
    
                            elif ok and result == "success":
                                print(colored(f"{name} | ✅ Givga muvaffaqiyatli qo‘shildi", "green"))
                                write_to_csv = True
    
                            else:
                                print(colored(f"{name} | ⚠️ Giv javobi: {response_json}", "yellow"))
                                write_to_csv = False
    
                            # ✅ Faqat yuqoridagi shartlar bajarilganda yoziladi
                            if write_to_csv:
                                log_file = f"{start_param}.csv"
    
                                # 🔐 Fayl mavjud bo‘lmasa yaratadi, mavjud bo‘lsa yozadi
                                if not os.path.exists(log_file):
                                    print(colored(f"📄 Fayl yaratilmoqda: {log_file}", "cyan"))
                                    open(log_file, 'w', encoding='utf-8').close()
    
                                # 🔁 Takroriy yozishni oldini olish
                                with open(log_file, 'r', encoding='utf-8') as f:
                                    existing = set(line.strip() for line in f if line.strip())
    
                                if phone not in existing:
                                    with open(log_file, 'a', newline='', encoding='utf-8') as f:
                                        csv.writer(f).writerow([phone])
                                        print(colored(f"📥 {phone} yozildi → {log_file}", "cyan"))
    
    
                        except Exception as err:
                                print(colored(f"{name} | Giv uchun aynan so'rovda xatolik: {err}", "yellow"))
    
    import asyncio
    from asyncio import Semaphore
    import os
    
    sem = Semaphore(3)  # Maksimal 5 ta parallel vazifa
    
    async def sem_run(phone, givs, channels):
        async with sem:
            print(colored(f"🔵 {phone} uchun jarayon boshlanmoqda...", "blue"))
            await run(phone, givs, channels)
            print(colored(f"🟣 {phone} | Jarayon yakunlandi.", "magenta"))
    
    async def main():
        try:
            with open('phone.csv', 'r') as f:
                phones = [line.strip() for line in f if line.strip()]
            print(f"📲 Umumiy raqamlar soni: {len(phones)}")
        except Exception as e:
            print(f"Telefon raqamlarini yuklashda xatolik: {e}")
            return
    
        all_tasks = []
    
        for start_param in givs:
            start_param = start_param.strip()
            skip_file = f"{start_param}.csv"
    
            # Fayl mavjud bo‘lmasa — yaratamiz
            if not os.path.exists(skip_file):
                print(f"🆕 Fayl mavjud emas, keyinchalik run() yaratadi: {skip_file}")
                skipped_phones = set()
            else:
                with open(skip_file, 'r', encoding='utf-8') as f:
                    skipped_phones = set(line.strip() for line in f if line.strip())
                print(f"⛔ Skip fayl: {skip_file} | Skip qilingan raqamlar: {len(skipped_phones)}")
    
    
            filtered_phones = [phone for phone in phones if phone not in skipped_phones]
            print(f"✅ {len(filtered_phones)} ta yangi raqam qolgan: {start_param}")
    
            for phone in filtered_phones:
                all_tasks.append(sem_run(phone, [start_param], channels))
    
        if not all_tasks:
            print("⚠️ Hech qanday topshiriq topilmadi (all_tasks bo‘sh)")
        else:
            await asyncio.gather(*all_tasks)
            print(colored(f"🏁 Barcha givlar uchun yakunlandi.", "green"))
    if __name__ == '__main__':
        asyncio.run(main())
else:
    print(color("Kodni aktivlashtirish uchun @Enshteyn40 ga murojat qiling", "magenta"))
