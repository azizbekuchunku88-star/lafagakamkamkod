#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import ssl
import csv
import base64
import asyncio
from io import BytesIO
from typing import Optional
from urllib.parse import unquote

import aiohttp
from aiohttp_proxy import ProxyConnector
from PIL import Image
from termcolor import colored
from telethon import TelegramClient
from telethon.tl.types import InputUser, InputBotAppShortName
from telethon.tl.functions.messages import (
    RequestAppWebViewRequest,
    ImportChatInviteRequest,
)
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.account import UpdateStatusRequest

# ===================== UMUMIY YORDAMCHILAR =====================
SDCARD = "/storage/emulated/0"
GIVDIR = f"{SDCARD}/giv" if os.path.isdir(SDCARD) else os.path.abspath("./giv")
os.makedirs(GIVDIR, exist_ok=True)

def first_existing(paths):
    for p in paths:
        if p and os.path.exists(p):
            return p
    return ""

def read_first_cell_csv(path: str) -> str:
    try:
        if not path or not os.path.exists(path):
            return ""
        with open(path, "r", encoding="utf-8", newline="") as f:
            r = csv.reader(f)
            for row in r:
                if row and (row[0] or "").strip():
                    return row[0].strip()
    except Exception:
        pass
    return ""

def read_list_csv(path: str):
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            return [row[0].strip() for row in csv.reader(f) if row and row[0].strip()]
    except Exception:
        return []

def ensure_file(path: str):
    if not os.path.exists(path):
        open(path, "w", encoding="utf-8").close()

# ===================== KONFIG & FAYLLAR =====================
# 1) XEvil API key
XEKEY_CANDIDATES = [
    f"{GIVDIR}/xevilkey.csv",
    f"{SDCARD}/xevilkey.csv",
    r"C:\join\xevilkey.csv",
    "./xevilkey.csv",
]
xe_path = first_existing(XEKEY_CANDIDATES)
XEVIL_API_KEY = read_first_cell_csv(xe_path)
if XEVIL_API_KEY:
    print(colored(f"🔑 XEvil key: {xe_path}", "cyan"))
else:
    print(colored("⚠️ xevilkey.csv topilmadi yoki bo‘sh — CAPTCHA yechish ishlamasligi mumkin.", "yellow"))

# 2) Proxy
PROXY_CANDIDATES = [
    f"{GIVDIR}/proxy.csv",
    r"S:\join\proxy.csv",
    r"C:\join\proxy.csv",
    "./proxy.csv",
]
proxy_path = first_existing(PROXY_CANDIDATES)
ROTATED_PROXY = read_first_cell_csv(proxy_path)
if ROTATED_PROXY:
    print(colored(f"🔌 Proxy: {proxy_path}", "cyan"))
else:
    print(colored("ℹ️ proxy.csv topilmadi yoki bo‘sh. Proxysiz ishlaymiz.", "yellow"))

# 3) Turnstile API key
CAPTCHAKEY_CANDIDATES = [
    f"{GIVDIR}/captcha2ensh.csv",
    r"C:\join\captcha2ensh.csv",
    "./captcha2ensh.csv",
]
cap_path = first_existing(CAPTCHAKEY_CANDIDATES)
captchapai = read_first_cell_csv(cap_path)
if captchapai:
    print(colored(f"🔑 Turnstile API key: {cap_path}", "cyan"))
else:
    print(colored("⚠️ captcha2ensh.csv topilmadi yoki bo‘sh. Turnstile token olinmasligi mumkin.", "yellow"))

# 4) GIV ro‘yxatlari
randogiv_path    = first_existing([f"{GIVDIR}/randogiv.csv",    r"C:\join\randogiv.csv",    "./randogiv.csv"])
randolimit_path  = first_existing([f"{GIVDIR}/randolimit.csv",  r"C:\join\randolimit.csv",  "./randolimit.csv"])
ranochiq_path    = first_existing([f"{GIVDIR}/ranochiqkanal.csv",r"C:\join\ranochiqkanal.csv","./ranochiqkanal.csv"])
ranyopiq_path    = first_existing([f"{GIVDIR}/ranyopiqkanal.csv",r"C:\join\ranyopiqkanal.csv","./ranyopiqkanal.csv"])

givs = []
bot_mapping = {}
if randogiv_path:
    with open(randogiv_path, "r", encoding="utf-8", newline="") as f:
        for row in csv.reader(f):
            if len(row) >= 2:
                k, v = row[0].strip(), row[1].strip()
                if k and v:
                    givs.append(k)
                    bot_mapping[k] = v
else:
    print(colored("⚠️ randogiv.csv topilmadi — start_param lar bo‘sh bo‘lishi mumkin.", "yellow"))

limituzz = int(read_first_cell_csv(randolimit_path) or "1")
premium_channels = read_list_csv(ranochiq_path)
yopiq_channels   = read_list_csv(ranyopiq_path)
channels = premium_channels + yopiq_channels

print("📌 Yuklangan start_param ↔ botlar:")
for k, v in bot_mapping.items():
    print(f"   ➤ {k} => {v}")
print(f"⏱  Kutish (sek): {limituzz}")

# 5) Telefon ro‘yxati
PHONECSV_CANDIDATES = [
    f"{GIVDIR}/ochopish.csv",
    "../ochopish.csv",
    "./ochopish.csv",
]
phonecsv_path = first_existing(PHONECSV_CANDIDATES)

# 6) Sessions joyi
SESS_DIR = os.path.join(os.path.expanduser("~"), "sessions")
os.makedirs(SESS_DIR, exist_ok=True)

# ===================== TURNSTILE FUNKSIYALARI =====================
async def get_turnstile_token_async(
    session: aiohttp.ClientSession,
    server_url: str,
    api_key: str,
    website_url: str,
    website_key: str,
    server_wait: float = 2.0,
    attempts: int = 40,
    sleep_sec: float = 0.8,
) -> Optional[str]:
    """enshteyn40.com dagi /turnstile va /turnstile/result API orqali token qaytaradi."""
    try:
        r = await session.post(
            f"{server_url}/turnstile",
            json={
                "api_key": api_key,
                "website_url": website_url,
                "website_key": website_key,
                "wait": True,
                "server_wait": server_wait,
            },
        )
        j = await r.json(content_type=None)
    except Exception as e:
        print(f"Create error: {e}")
        return None

    if j.get("success") and j.get("status") == "ready":
        return j.get("token") or None

    if not (j.get("success") and j.get("status") == "pending"):
        print(j.get("error", "unknown_error"))
        return None

    task_id = j.get("task_id")
    if not task_id:
        print("Task ID not found")
        return None

    for _ in range(attempts):
        try:
            r2 = await session.post(
                f"{server_url}/turnstile/result", json={"task_id": task_id, "block": False}
            )
            j2 = await r2.json(content_type=None)
            if j2.get("success") and j2.get("status") == "ready":
                return j2.get("token") or None
            if not j2.get("success"):
                print(j2.get("error", "error"))
                return None
            await asyncio.sleep(sleep_sec)
        except Exception:
            await asyncio.sleep(sleep_sec)
            continue

    print("Timeout: token olinmadi")
    return None

# ===================== CAPTCHA (XEvil) =====================
def image2base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

async def img2txt(body):
    if not XEVIL_API_KEY:
        return None
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    form_data = {"key": XEVIL_API_KEY, "body": body, "method": "base64"}
    async with aiohttp.request("POST", "https://api.sctg.xyz/in.php", data=form_data, headers=headers) as response:
        response_data = await response.text()
        if "|" not in response_data:
            print(response_data)
            return None
        status, code = response_data.split("|", 1)
        if status != "OK":
            return None
        return code

async def get_result(code):
    if not XEVIL_API_KEY:
        return None
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    params = {"key": XEVIL_API_KEY, "id": code, "action": "get"}
    for _ in range(5):
        async with aiohttp.request("GET", "https://api.sctg.xyz/res.php", params=params, headers=headers) as response:
            response_data = await response.text()
            if "|" not in response_data:
                await asyncio.sleep(1)
                continue
            status, result = response_data.split("|", 1)
            if status != "OK":
                return None
            return result
    return None

# ===================== ISH OQIMI =====================
def add_to_bans(phone):
    try:
        with open("randobans.csv", "a", encoding="utf-8") as f:
            f.write(f"{phone}\n")
        print(colored(f"🚫 {phone} → randobans.csv ga yozildi", "yellow"))
    except Exception as e:
        print(colored(f"⚠️ Ban faylga yozishda xatolik: {e}", "red"))

async def run(phone, start_params, channels):
    api_id = 22962676
    api_hash = "543e9a4d695fe8c6aa4075c9525f7c57"

    tg_client = TelegramClient(os.path.join(SESS_DIR, f"{phone}"), api_id, api_hash)
    await tg_client.connect()
    if not await tg_client.is_user_authorized():
        print("Sessiyasi yo‘q raqam:", phone)
        return

    async with tg_client:
        me = await tg_client.get_me()
        await tg_client(UpdateStatusRequest(offline=False))
        name = (me.username or ((me.first_name or "") + (me.last_name or ""))).strip() or str(me.id)

        # PROXY (agar bor bo‘lsa)
        proxy_conn = ProxyConnector.from_url(ROTATED_PROXY) if ROTATED_PROXY else None

        # yopiq kanallar
        for yopiq_link in yopiq_channels:
            try:
                await tg_client(ImportChatInviteRequest(yopiq_link))
                await asyncio.sleep(limituzz)
                print(colored(f"{name} | Yopiq kanalga qo‘shildi: {yopiq_link}", "green"))
            except Exception as e:
                print(colored(f"{name} | Yopiq kanal xatolik {yopiq_link}: {e}", "red"))

        # ochiq kanallar
        for ochiq_link in premium_channels:
            try:
                await tg_client(JoinChannelRequest(o‘chiq_link))  # noqa: F821  (o‘ → o)
            except NameError:
                # Android klaviatura o‘zgarishi bo‘lishi mumkin, to‘g‘rilaymiz:
                try:
                    await tg_client(JoinChannelRequest(ochiq_link))
                except Exception as e:
                    print(colored(f"{name} | Ochiq kanal xatolik {ochiq_link}: {e}", "red"))
            else:
                await asyncio.sleep(limituzz)
                print(colored(f"{name} | Ochiq kanalga qo‘shildi: {ochiq_link}", "green"))

        for start_param in start_params:
            start_param = start_param.strip()
            bot_username = bot_mapping.get(start_param)
            if not bot_username:
                print(colored(f"🚫 Bot topilmadi: {start_param}", "red"))
                continue

            print(colored(f"✅ {start_param} → @{bot_username}", "green"))
            bot_entity = await tg_client.get_entity(bot_username)
            bot = InputUser(user_id=bot_entity.id, access_hash=bot_entity.access_hash)
            bot_app = InputBotAppShortName(bot_id=bot, short_name="JoinLot")

            web_view = await tg_client(
                RequestAppWebViewRequest(
                    peer=await tg_client.get_input_entity("me"),
                    app=bot_app,
                    platform="android",
                    write_allowed=True,
                    start_param=start_param,
                )
            )
            init_data = unquote(web_view.url.split("tgWebAppData=", 1)[1].split("&tgWebAppVersion")[0])

            # Turnstile token (PROXYsiz)
            SERVER_URL  = "https://enshteyn40.com"
            sitekey     = "0x4AAAAAAA2AVdjVXiMwY1g-"     # kerak bo‘lsa almashtiring
            website_url = "https://randomgodbot.com"

            if not captchapai:
                print(colored("⚠️ Turnstile API key yo‘q — ushbu start_param o‘tkazib yuborildi", "yellow"))
                continue

            ts_timeout = aiohttp.ClientTimeout(total=45)
            async with aiohttp.ClientSession(timeout=ts_timeout) as ts_session:
                tokenfrombot = await get_turnstile_token_async(
                    session=ts_session,
                    server_url=SERVER_URL,
                    api_key=captchapai,
                    website_url=website_url,
                    website_key=sitekey,
                    server_wait=2.0,
                    attempts=40,
                    sleep_sec=0.8,
                )

            if not tokenfrombot:
                print(colored(f"{name} | ⚠️ Turnstile token olinmadi, o‘tkazildi", "yellow"))
                continue

            # randomgodbot HTTP (PROXY bilan)
            headers = {
                "Host": "randomgodbot.com",
                "Accept": "*/*",
                "Accept-Language": "ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Pragma": "no-cache",
                "Referer": f"https://randomgodbot.com/join/?tgWebAppStartParam={start_param}",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Mobile Safari/537.36",
            }

            async with aiohttp.ClientSession(headers=headers, connector=proxy_conn) as http_client:
                try:
                    encoded_init_data = base64.b64encode(init_data.encode()).decode()

                    # 1) CAPTCHA rasmini (IP orqali) olish
                    url1 = f"https://185.203.72.14/lot_join?userId={me.id}&startParam={start_param}&id={encoded_init_data}&token=-"
                    r1 = await http_client.get(url=url1, ssl=False)
                    r1.raise_for_status()
                    j1 = await r1.json()

                    try:
                        result_node = j1.get("result")
                        if not isinstance(result_node, dict):
                            raise KeyError("result")
                        b64_data = result_node["base64"]
                        captcha_hash = result_node["hash"]
                    except Exception as err_inner:
                        if (isinstance(err_inner, KeyError) and err_inner.args and err_inner.args[0] == "result") or ("'result'" in str(err_inner)):
                            add_to_bans(phone)
                        print(colored(f"{name} | Giv so‘rov xatolik: {err_inner}", "yellow"))
                        continue

                    image_data = base64.b64decode(b64_data)
                    filename = f"{phone}_captcha.png"
                    Image.open(BytesIO(image_data)).save(filename)
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

                    # 2) Real join (domen orqali) + turnstile token
                    url2 = (
                        f"https://randomgodbot.com/lot_join"
                        f"?userId={me.id}"
                        f"&startParam={start_param}"
                        f"&id={encoded_init_data}"
                        f"&captcha_hash={captcha_hash}"
                        f"&captcha_value={captcha_input}"
                        f"&token={tokenfrombot}"
                    )
                    r2 = await http_client.get(url=url2, ssl=False)
                    j2 = await r2.json()

                    description = j2.get("description", "")
                    result = j2.get("result", "")
                    ok = j2.get("ok", False)

                    write_to_csv = False
                    if description == "ALREADY_JOINED":
                        print(colored(f"{name} | ❕ Allaqachon qatnashgan", "blue"))
                        write_to_csv = True
                    elif ok and result == "success":
                        print(colored(f"{name} | ✅ Givga muvaffaqiyatli qo‘shildi", "green"))
                        write_to_csv = True
                    else:
                        print(colored(f"{name} | ⚠️ Giv javobi: {j2}", "yellow"))

                    if write_to_csv:
                        log_file = f"{start_param}.csv"
                        ensure_file(log_file)
                        with open(log_file, "r", encoding="utf-8") as f:
                            existing = set(line.strip() for line in f if line.strip())
                        if phone not in existing:
                            with open(log_file, "a", newline="", encoding="utf-8") as f:
                                csv.writer(f).writerow([phone])
                                print(colored(f"📥 {phone} yozildi → {log_file}", "cyan"))

                    if os.path.exists(filename):
                        os.remove(filename)
                        print(colored(f"🗑️ CAPTCHA rasm o‘chirildi: {filename}", "grey"))

                except Exception as err:
                    print(colored(f"{name} | So‘rov xatolik: {err}", "yellow"))

# ===================== RUNNER =====================
from asyncio import Semaphore
sem = Semaphore(1)

async def sem_run(phone, givs, channels):
    async with sem:
        print(colored(f"🔵 {phone} uchun jarayon boshlandi...", "blue"))
        try:
            await run(phone, givs, channels)
        except Exception as e:
            print(colored(f"{phone} | run() ichida xatolik: {e}", "red"))
        print(colored(f"🟣 {phone} | Jarayon yakunlandi.", "magenta"))

async def main():
    # Telefonlar
    if not phonecsv_path:
        print(colored("❗ ochopish.csv topilmadi. Uni /storage/emulated/0/giv/ ichiga qo‘ying.", "red"))
        return

    try:
        with open(phonecsv_path, "r", encoding="utf-8") as f:
            phones = [line.strip() for line in f if line.strip()]
        print(f"📲 Umumiy raqamlar soni: {len(phones)}")
    except Exception as e:
        print(f"Telefon raqamlarini yuklashda xatolik: {e}")
        return

    # Banlar
    ban_file = "randobans.csv"
    if os.path.exists(ban_file):
        with open(ban_file, "r", encoding="utf-8") as f:
            banned = set(line.strip() for line in f if line.strip())
        print(colored(f"🚫 Ban ro‘yxati: {len(banned)} ta", "yellow"))
    else:
        banned = set()
        print(colored("ℹ️ randobans.csv topilmadi (bo‘sh deb qabul qilinadi)", "cyan"))

    phones = [p for p in phones if p not in banned]
    print(colored(f"✅ Ban filtridan so‘ng qolgan raqamlar: {len(phones)}", "green"))

    all_tasks = []
    if not givs:
        print(colored("⚠️ start_param (giv) ro‘yxati bo‘sh.", "yellow"))

    for start_param in givs:
        start_param = start_param.strip()
        skip_file = f"{start_param}.csv"

        if not os.path.exists(skip_file):
            print(f"🆕 Skip fayl hali yo‘q: {skip_file} (keyin yaratiladi)")
            skipped_phones = set()
        else:
            with open(skip_file, "r", encoding="utf-8") as f:
                skipped_phones = set(line.strip() for line in f if line.strip())
            print(f"⛔ Skip fayl: {skip_file} | Skip qilingan: {len(skipped_phones)}")

        filtered_phones = [ph for ph in phones if ph not in skipped_phones and ph not in banned]
        print(f"✅ {len(filtered_phones)} ta yangi raqam qolgan: {start_param}")

        for phone in filtered_phones:
            all_tasks.append(asyncio.create_task(sem_run(phone, [start_param], channels)))

    if not all_tasks:
        print("⚠️ Hech qanday topshiriq topilmadi (all_tasks bo‘sh).")
    else:
        await asyncio.gather(*all_tasks)
        print(colored("🏁 Barcha givlar uchun yakunlandi.", "green"))

if __name__ == "__main__":
    asyncio.run(main())
