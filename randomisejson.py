# -*- coding: utf-8 -*-  # captchalik kod (accounts.json versiya)
import requests
from licensing.methods import Helpers
import sys
import os
import csv
import json
import time
from urllib.parse import unquote
from datetime import datetime, timezone, timedelta
import asyncio

from telethon.tl.functions.channels import JoinChannelRequest
from telethon import types, utils, errors
from telethon.tl.functions.account import UpdateStatusRequest
from telethon.tl.types import InputUser
from telethon.tl.functions.messages import RequestAppWebViewRequest
from telethon.tl.types import InputBotAppShortName

def color(text, color_code):
    color_map = {
        "red": "91", "green": "92", "yellow": "93", "blue": "94",
        "magenta": "95", "cyan": "96", "white": "97", "bold_white": "1;97"
    }
    code = color_map.get(color_code, "97")
    return f"\033[{code}m{text}\033[0m"

# --- License ro'yxati ---
url = "https://raw.githubusercontent.com/Enshteyn40/crdevice/refs/heads/main/randomize_3.csv"
response = requests.get(url)
lines = response.text.splitlines()
hash_values_list = [line.strip() for line in lines]

def GetMachineCode():
    return Helpers.GetMachineCode(v=2)

machine_code = GetMachineCode()
print(color(machine_code, "white"))

if machine_code in hash_values_list:
    import ssl
    import base64
    from urllib.parse import unquote
    from telethon.tl.functions.messages import ImportChatInviteRequest
    import aiohttp
    import aiohttp_proxy
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from termcolor import colored
    from io import BytesIO
    from PIL import Image

    # ===== Muhitni aniqlash va fayl yo'llari =====
    import sys, os

    def detect_env():
        phone_dir = "/storage/emulated/0/giv"
        pc_dir = "C:/join"
        if os.path.exists(phone_dir):
            print("📱 Telefon (Termux) muhitida ishlayapti")
            return phone_dir
        elif os.path.exists(pc_dir):
            print("💻 Kompyuter (Windows) muhitida ishlayapti")
            return pc_dir
        else:
            try:
                os.makedirs(phone_dir, exist_ok=True)
                print(f"📁 {phone_dir} papkasi yaratildi. Fayllarni shu yerga joylashtiring.")
                sys.exit("📥 Ma'lumotlar yo'q. Fayllarni to‘ldirib qayta urinib ko‘ring.")
            except:
                try:
                    os.makedirs(pc_dir, exist_ok=True)
                    print(f"📁 {pc_dir} papkasi yaratildi. Fayllarni shu yerga joylashtiring.")
                    sys.exit("📥 Ma'lumotlar yo'q. Fayllarni to‘ldirib qayta urinib ko‘ring.")
                except Exception as e:
                    print("❌ Papkalarni yaratib bo‘lmadi:", e)
                    sys.exit("⛔ Dastur to‘xtatildi.")

    BASE_DIR = detect_env()

    def get_path(filename: str) -> str:
        return os.path.join(BASE_DIR, filename)

    def image2base64(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    # ===== XEVIL API =====
    async def img2txt(body):
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        form_data = {
            "key": XEVIL_API_KEY,
            "body": body,
            "method": "base64"
        }
        async with aiohttp.request("POST", "https://api.sctg.xyz/in.php", data=form_data, headers=headers) as response:
            response_data = await response.text()
            if '|' not in response_data:
                print(response_data)
                return None
            status, code = response_data.split('|', 1)
            if status != 'OK':
                return None
            return code

    async def get_result(code):
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        params = {"key": XEVIL_API_KEY, "id": code, 'action': 'get'}
        for _ in range(5):
            async with aiohttp.request("GET", "https://api.sctg.xyz/res.php", params=params, headers=headers) as response:
                response_data = await response.text()
                if '|' not in response_data:
                    await asyncio.sleep(1)
                    continue
                status, result = response_data.split('|', 1)
                if status != 'OK':
                    return None
                return result
        return None

    # ===== Konfiguratsiyalarni o‘qish =====
    try:
        with open(get_path("xevilkey.csv"), 'r') as f:
            XEVIL_API_KEY = str(next(csv.reader(f))[0]).strip()
    except Exception as e:
        print(colored(f"XEVIL kalitini o‘qishda xatolik: {e}", "red"))
        sys.exit(1)

    try:
        with open(get_path("proxy.csv"), 'r') as f:
            reader = csv.reader(f)
            ROTATED_PROXY = next(reader)[0].strip()
    except Exception:
        ROTATED_PROXY = ""

    # start_param ↔ bot_username
    givs = []
    bot_mapping = {}
    with open(get_path("randogiv.csv"), 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2:
                key = row[0].strip()
                val = row[1].strip()
                if key:
                    givs.append(key)
                    bot_mapping[key] = val

    print("📌 Yuklangan start_param lar va botlar:")
    for k, v in bot_mapping.items():
        print(f"   ➤ {k} => {v}")

    with open(get_path("randolimit.csv"), 'r') as f:
        limituzz = int(next(csv.reader(f))[0])
    print(f"Kutiladigan vaqt - {limituzz} sekund")

    with open(get_path("ranochiqkanal.csv"), 'r') as f:
        premium_channels = [row[0].strip() for row in csv.reader(f) if row and row[0].strip()]

    with open(get_path("ranyopiqkanal.csv"), 'r') as f:
        yopiq_channels = [row[0].strip() for row in csv.reader(f) if row and row[0].strip()]

    channels = premium_channels + yopiq_channels

    # ===== Asosiy ish: endi accounts.json dan o‘qiymiz =====
    def load_accounts():
        acc_path = get_path("accounts.json")
        if not os.path.exists(acc_path):
            print(colored(f"accounts.json topilmadi: {acc_path}", "red"))
            sys.exit(1)
        try:
            with open(acc_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                # {"phone": "StringSession", ...}
                pairs = [(p.strip(), s.strip()) for p, s in data.items() if p and s]
            elif isinstance(data, list):
                # [{"phone":"...","session":"..."}] bo‘lishi mumkin bo‘lsa
                pairs = []
                for item in data:
                    p = str(item.get("phone", "")).strip()
                    s = str(item.get("session", "")).strip()
                    if p and s:
                        pairs.append((p, s))
            else:
                raise ValueError("accounts.json noto‘g‘ri formatda")
            if not pairs:
                raise ValueError("accounts.json bo‘sh yoki noto‘g‘ri")
            return pairs
        except Exception as e:
            print(colored(f"accounts.json o‘qishda xatolik: {e}", "red"))
            sys.exit(1)

    # ===== Telegram ish funksiyasi (StringSession bilan) =====
    async def run(phone: str, session_str: str, start_params, channels):
        api_id = 22962676
        api_hash = '543e9a4d695fe8c6aa4075c9525f7c57'

        tg_client = TelegramClient(StringSession(session_str), api_id, api_hash)
        await tg_client.connect()

        if not await tg_client.is_user_authorized():
            print(colored(f'{phone} | Sessiya avtorizatsiya qilinmagan', 'red'))
            await tg_client.disconnect()
            return

        async with tg_client:
            me = await tg_client.get_me()
            await tg_client(UpdateStatusRequest(offline=False))
            name = (me.username or ((me.first_name or '') + ' ' + (me.last_name or '' ))).strip()

            # Yopiq kanallar
            for yopiq_link in yopiq_channels:
                try:
                    await tg_client(ImportChatInviteRequest(yopiq_link))
                    await asyncio.sleep(limituzz)
                    print(colored(f"{name} | Kanalga a'zo bo'ldi {yopiq_link}", "green"))
                except Exception as e:
                    print(colored(f"{name} | Kanalga qo'shilishda xatolik {yopiq_link}: {e}", "red"))

            # Ochiq/premium kanallar
            for ochiq_link in premium_channels:
                try:
                    await tg_client(JoinChannelRequest(ochiq_link))
                    await asyncio.sleep(limituzz)
                    print(colored(f"{name} | Kanalga a'zo bo'ldi {ochiq_link}", "green"))
                except Exception as e:
                    print(colored(f"{name} | Kanalga qo'shilishda xatolik {ochiq_link}: {e}", "red"))

            # Givlar
            for start_param in start_params:
                start_param = start_param.strip()
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

                ssl_ctx = ssl.create_default_context()
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.CERT_NONE

                # ✅ ProxyConnector to‘g‘ri ulanishi
                proxy_conn = None
                if ROTATED_PROXY:
                    try:
                        proxy_conn = aiohttp_proxy.ProxyConnector.from_url(ROTATED_PROXY, ssl=ssl_ctx)
                    except Exception as pe:
                        print(colored(f"Proxy ulanishida xatolik: {pe}", "yellow"))
                        proxy_conn = None

                async with aiohttp.ClientSession(headers=headers, connector=proxy_conn) as http_client:
                    try:
                        encoded_init_data = base64.b64encode(init_data.encode()).decode()
                        # ⚠️ birinchi bosqich (captcha rasm)
                        url1 = f"https://185.203.72.14/lot_join?userId={me.id}&startParam={start_param}&id={encoded_init_data}"
                        resp1 = await http_client.get(url=url1, ssl=False)
                        resp1.raise_for_status()
                        response_json = await resp1.json()
                        b64_data = response_json["result"]["base64"]
                        captcha_hash = response_json["result"]["hash"]

                        image_data = base64.b64decode(b64_data)
                        image = Image.open(BytesIO(image_data))
                        filename = f"{phone}_captcha.png"
                        image.save(filename)
                        print(f"✅ Rasm saqlandi: {filename}")

                        base64_body = image2base64(filename)
                        result_code = await img2txt(base64_body)
                        if not result_code:
                            print("| CAPTCHA kodini olishda xatolik")
                            if os.path.exists(filename):
                                os.remove(filename)
                            continue

                        await asyncio.sleep(2)
                        captcha_input = await get_result(code=result_code)
                        print("CAPTCHA javobi:", captcha_input)

                        # ✅ ikkinchi bosqich (jo‘in qilish)
                        url2 = (
                            f"https://randomgodbot.com/lot_join?userId={me.id}"
                            f"&startParam={start_param}&id={encoded_init_data}"
                            f"&captcha_hash={captcha_hash}&captcha_value={captcha_input}"
                        )
                        resp2 = await http_client.get(url=url2, ssl=False)
                        resp2_json = await resp2.json()

                        description = resp2_json.get("description", "")
                        result = resp2_json.get("result", "")
                        ok = resp2_json.get("ok", False)

                        if description == "ALREADY_JOINED":
                            print(colored(f"{name} | ❕ Allaqachon qatnashgan", "blue"))
                            write_to_csv = True
                        elif ok and result == "success":
                            print(colored(f"{name} | ✅ Givga muvaffaqiyatli qo‘shildi", "green"))
                            write_to_csv = True
                        else:
                            print(colored(f"{name} | ⚠️ Giv javobi: {resp2_json}", "yellow"))
                            write_to_csv = False

                        # ✅ faqat kerak bo‘lsa yozamiz
                        if write_to_csv:
                            log_file = f"{start_param}.csv"
                            if not os.path.exists(log_file):
                                print(colored(f"📄 Fayl yaratilmoqda: {log_file}", "cyan"))
                                open(log_file, 'w', encoding='utf-8').close()

                            with open(log_file, 'r', encoding='utf-8') as f:
                                existing = set(line.strip() for line in f if line.strip())

                            if phone not in existing:
                                with open(log_file, 'a', newline='', encoding='utf-8') as f:
                                    csv.writer(f).writerow([phone])
                                    print(colored(f"📥 {phone} yozildi → {log_file}", "cyan"))

                        if os.path.exists(filename):
                            os.remove(filename)
                            print(colored(f"🗑️ CAPTCHA rasm o‘chirildi: {filename}", "grey"))

                    except Exception as err:
                        print(colored(f"{name} | Giv uchun aynan so'rovda xatolik: {err}", "yellow"))

    # ===== Parallel yuguruvchi o‘ram =====
    from asyncio import Semaphore
    sem = Semaphore(2)

    async def sem_run(phone, session_str, givs, channels):
        async with sem:
            print(colored(f"🔵 {phone} uchun jarayon boshlanmoqda...", "blue"))
            try:
                await run(phone, session_str, givs, channels)
            except Exception as e:
                print(colored(f"{phone} | run() ichida xatolik: {e}", "red"))
            print(colored(f"🟣 {phone} | Jarayon yakunlandi.", "magenta"))

    async def main():
        # accounts.json -> [(phone, session_str), ...]
        account_pairs = load_accounts()
        print(f"📲 Umumiy raqamlar soni: {len(account_pairs)}")

        all_tasks = []
        for start_param in givs:
            start_param = start_param.strip()
            skip_file = f"{start_param}.csv"

            if not os.path.exists(skip_file):
                print(f"🆕 Fayl mavjud emas, keyinchalik run() yaratadi: {skip_file}")
                skipped_phones = set()
            else:
                with open(skip_file, 'r', encoding='utf-8') as f:
                    skipped_phones = set(line.strip() for line in f if line.strip())
                print(f"⛔ Skip fayl: {skip_file} | Skip qilingan raqamlar: {len(skipped_phones)}")

            # phone bo‘yicha filter
            filtered_pairs = [(p, s) for (p, s) in account_pairs if p not in skipped_phones]
            print(f"✅ {len(filtered_pairs)} ta yangi raqam qolgan: {start_param}")

            for phone, session_str in filtered_pairs:
                task = asyncio.create_task(sem_run(phone, session_str, [start_param], channels))
                all_tasks.append(task)

        if not all_tasks:
            print("⚠️ Hech qanday topshiriq topilmadi (all_tasks bo‘sh)")
        else:
            await asyncio.gather(*all_tasks)
            print(colored(f"🏁 Barcha givlar uchun yakunlandi.", "green"))

    if __name__ == '__main__':
        asyncio.run(main())
else:
    print(color("Kodni aktivlashtirish uchun @Enshteyn40 ga murojat qiling", "magenta"))
