#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ssl
import base64
import asyncio
from urllib.parse import unquote
from telethon.tl.functions.messages import ImportChatInviteRequest
import aiohttp
import aiohttp_proxy
from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import InputUser, InputBotAppShortName
from telethon.tl.functions.messages import RequestAppWebViewRequest
import csv
from termcolor import colored
from telethon.tl.functions.account import UpdateStatusRequest
import os
from typing import Optional

print("Oxirgi yangilanish vaqti 23:39")

# ===================== Turnstile token olish (PROXYSIZ) =====================

import json
from aiohttp import ClientError, ClientConnectorError, ServerTimeoutError

async def get_turnstile_token_async(
    session: Optional[aiohttp.ClientSession] = None,  # orqaga moslik uchun qabul qilamiz, lekin ishlatmaymiz
    server_url: str = "",
    api_key: str = "",
    website_url: str = "",
    website_key: str = "",
    server_wait: float = 2.0,
    attempts: int = 40,
    sleep_sec: float = 0.8,
) -> Optional[str]:
    """
    Soddalashtirilgan loglar bilan Turnstile token olish.
    - Konsolga uzun JSON yoki token chop etilmaydi.
    - Faoliyat haqida qisqa holat xabarlari beriladi.
    """
    create_payload = {
        "api_key": api_key,
        "website_url": website_url,
        "website_key": website_key,
        "wait": True,
        "server_wait": server_wait,
    }

    timeout = aiohttp.ClientTimeout(total=45)

    async with aiohttp.ClientSession(timeout=timeout, trust_env=False) as s:
        # CREATE
        try:
            r = await s.post(f"{server_url}/turnstile", json=create_payload)
            raw = await r.text()
            try:
                j = json.loads(raw)
            except json.JSONDecodeError:
                print(colored(f"[turnstile][create] non-JSON response, status={r.status}", "yellow"))
                return None
        except (ClientConnectorError, ServerTimeoutError) as e:
            print(colored(f"[turnstile][create] transport error: {type(e).__name__}", "red"))
            return None
        except ClientError as e:
            print(colored(f"[turnstile][create] aiohttp error: {type(e).__name__}", "red"))
            return None
        except Exception as e:
            print(colored(f"[turnstile][create] unexpected: {type(e).__name__}", "red"))
            return None

        # Endi j mavjud bo'lishi kerak
        if j.get("success") and j.get("status") == "ready":
            # Token mavjud — QIYMATNI CHOP ETMAYMIZ, faqat xabar beramiz
            print(colored(f"[turnstile] Token olindi (create ready).", "green"))
            return j.get("token") or None

        if not (j.get("success") and j.get("status") == "pending"):
            print(colored(f"[turnstile][create] failed: {j.get('error') or 'unknown'}", "yellow"))
            return None

        task_id = j.get("task_id")
        if not task_id:
            print(colored("[turnstile][create] pending lekin task_id yo'q", "yellow"))
            return None

        # POLLING
        for i in range(1, attempts + 1):
            try:
                r2 = await s.post(f"{server_url}/turnstile/result", json={"task_id": task_id, "block": False})
                raw2 = await r2.text()
                try:
                    j2 = json.loads(raw2)
                except json.JSONDecodeError:
                    # non-JSON javob — qisqacha xabar va davom et
                    print(colored(f"[turnstile][poll] try {i}/{attempts}: no-json reply", "yellow"))
                    await asyncio.sleep(sleep_sec)
                    continue

                # Agar token tayyor bo'lsa — tokenni CHOP ETMAYMIZ, faqat xabar
                if j2.get("success") and j2.get("status") == "ready":
                    print(colored(f"[turnstile] Token olindi (task_id={task_id}) try={i}/{attempts}", "green"))
                    return j2.get("token") or None

                # Agar javob muvaffaqiyatsiz bo'lsa — chiqib ketamiz
                if not j2.get("success"):
                    print(colored(f"[turnstile][poll] try {i}/{attempts}: server returned error", "yellow"))
                    return None

                # Agar hali pending bo'lsa — qisqacha holat xabarlarini chiqaramiz.
                # Juda ko'p chiqa boshlamasligi uchun har bir urinishni ham chiqarish mumkin,
                # lekin agar siz juda tiqilib qolmasin desangiz, quyidagi kodni i%N sharti bilan o'zgartiring.
                print(colored(f"[turnstile][poll] try {i}/{attempts}: token ishlanyapti...", "cyan"))

                await asyncio.sleep(sleep_sec)

            except (ClientConnectorError, ServerTimeoutError) as e:
                print(colored(f"[turnstile][poll] try {i}/{attempts}: transport error ({type(e).__name__})", "red"))
                await asyncio.sleep(sleep_sec)
            except ClientError as e:
                print(colored(f"[turnstile][poll] try {i}/{attempts}: aiohttp error ({type(e).__name__})", "red"))
                await asyncio.sleep(sleep_sec)
            except Exception as e:
                print(colored(f"[turnstile][poll] try {i}/{attempts}: unexpected ({type(e).__name__})", "red"))
                await asyncio.sleep(sleep_sec)

        print(colored(f"[turnstile] Timeout: token olinmadi (task_id={task_id})", "yellow"))
        return None


# ========================= CSV / sozlamalar =========================

import sys

ANDROID_ROOT = "/storage/emulated/0/giv"
WIN_ROOT     = r"C:\join"
CURR_ROOT    = "."

ROOTS = [ANDROID_ROOT, WIN_ROOT, CURR_ROOT]  # ustuvorlik tartibi

def detect_env() -> str:
    for root in ROOTS:
        try:
            if os.path.exists(root):
                return root
        except Exception:
            continue
    return CURR_ROOT

ENV_ROOT = detect_env()
print(colored(f"🗂️ Ishchi ROOT: {ENV_ROOT}", "cyan"))

def resolve_path(filename: str) -> str:
    for root in ROOTS:
        try:
            full = os.path.join(root, filename)
            if os.path.exists(full):
                return full
        except Exception:
            continue
    return os.path.join(ENV_ROOT, filename)

def ensure_path_and_file(root: str, filename: str, header: str | None = None, exit_after_create: bool = True) -> str:
    if not os.path.exists(root):
        print(colored(f"{root} papkasi mavjud emas. Yaratilmoqda...", "yellow"))
        os.makedirs(root, exist_ok=True)
    fp = os.path.join(root, filename)
    if not os.path.isfile(fp):
        print(colored(f"{filename} topilmadi. Yaratildi: {fp}", "yellow"))
        with open(fp, "w", encoding="utf-8", newline="") as f:
            if header:
                f.write(header.rstrip() + "\n")
        if exit_after_create:
            print(colored("→ Iltimos, faylni to‘ldiring va skriptni qayta ishga tushiring.", "yellow"))
            sys.exit(0)
    else:
        print(colored(f"{filename} mavjud: {fp}", "cyan"))
    return fp

def read_first_cell_csv_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            for row in csv.reader(f):
                if row and (row[0] or "").strip():
                    return row[0].strip()
    except Exception:
        pass
    return ""

def read_first_col_list(path: str) -> list[str]:
    out = []
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            for row in csv.reader(f):
                if row and (row[0] or "").strip():
                    out.append(row[0].strip())
    except Exception:
        pass
    return out

# XEvil API (ixtiyoriy)
xevil_file = resolve_path("xevilkey.csv")
if os.path.exists(xevil_file):
    XEVIL_API_KEY = read_first_cell_csv_file(xevil_file)
    print(colored(f"🔑 XEvil key: {xevil_file}", "cyan"))
else:
    xevil_file = ensure_path_and_file(ENV_ROOT, "xevilkey.csv", header="", exit_after_create=False)
    XEVIL_API_KEY = ""
    print(colored("⚠️ xevilkey.csv topilmadi. Bo'sh qiymat bilan davom (CAPTCHA ishlamasligi mumkin).", "yellow"))

# Proxy
proxy_file = resolve_path("proxy.csv")
ROTATED_PROXY = read_first_cell_csv_file(proxy_file) if os.path.exists(proxy_file) else ""
if ROTATED_PROXY:
    print(colored(f"🔌 Proxy: {proxy_file}", "cyan"))
else:
    print(colored("ℹ️ proxy.csv topilmadi yoki bo‘sh. Proxysiz HTTP bajariladi.", "yellow"))

# Turnstile server API key (enshteyn40.com)
captcha2_file = resolve_path("captcha2ensh.csv")
if os.path.exists(captcha2_file):
    captchapai = read_first_cell_csv_file(captcha2_file)
    print(colored(f"🧰 Turnstile API key: {captcha2_file}", "cyan"))
else:
    captchapai = ""
    print(colored("⚠️ captcha2ensh.csv topilmadi. Turnstile token olinmasligi mumkin.", "yellow"))

# start_param -> bot_username
randogiv_file = resolve_path("randogiv.csv")
if not os.path.exists(randogiv_file):
    randogiv_file = ensure_path_and_file(ENV_ROOT, "randogiv.csv", header="start_param,bot_username")

bot_mapping, givs = {}, []
with open(randogiv_file, "r", encoding="utf-8", newline="") as f:
    for row in csv.reader(f):
        if len(row) >= 2 and row[0].strip() and row[1].strip():
            key = row[0].strip()
            val = row[1].strip()
            givs.append(key)
            bot_mapping[key] = val
print(colored(f"📌 randogiv.csv yuklandi: {len(givs)} ta start_param", "cyan"))

# kutish
limit_file = resolve_path("randolimit.csv")
if os.path.exists(limit_file):
    try:
        limituzz = int(read_first_cell_csv_file(limit_file))
    except Exception:
        limituzz = 1
        print(colored("⚠️ randolimit.csv noto‘g‘ri format. default 1s.", "yellow"))
    print(colored(f"⏱️ Kutiladigan vaqt: {limituzz}s", "cyan"))
else:
    ensure_path_and_file(ENV_ROOT, "randolimit.csv", header="1", exit_after_create=False)
    limituzz = 1
    print(colored("ℹ️ randolimit.csv topilmadi. default 1s.", "yellow"))

# kanallar ro‘yxati
ranochiq_file = resolve_path("ranochiqkanal.csv")
ranyopiq_file = resolve_path("ranyopiqkanal.csv")
premium_channels = read_first_col_list(ranochiq_file) if os.path.exists(ranochiq_file) else []
yopiq_channels  = read_first_col_list(ranyopiq_file) if os.path.exists(ranyopiq_file) else []
if not os.path.exists(ranochiq_file):
    ensure_path_and_file(ENV_ROOT, "ranochiqkanal.csv", header="", exit_after_create=False)
if not os.path.exists(ranyopiq_file):
    ensure_path_and_file(ENV_ROOT, "ranyopiqkanal.csv", header="", exit_after_create=False)
channels = premium_channels + yopiq_channels
print(colored(f"📡 Ochiq: {len(premium_channels)} | Yopiq: {len(yopiq_channels)}", "cyan"))

# ========================= Asosiy ish oqimi =========================

async def run(phone, start_params, channels):
    api_id = 22962676
    api_hash = '543e9a4d695fe8c6aa4075c9525f7c57'

    tg_client = TelegramClient(f"sessions/{phone}", api_id, api_hash)
    await tg_client.connect()
    if not await tg_client.is_user_authorized():
        print('Sessiyasi yoq raqam ')
        return

    async with tg_client:
        me = await tg_client.get_me()
        await tg_client(UpdateStatusRequest(offline=False))
        name = (me.username or ((me.first_name or "") + (me.last_name or ""))).strip() or str(me.id)

        # randomgodbot uchun HTTP (PROXY ishlatiladi, lekin TOKEN OLISH emas!)
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        proxy_conn = aiohttp_proxy.ProxyConnector(ssl_context=ssl_ctx).from_url(ROTATED_PROXY) if ROTATED_PROXY else None

        # yopiq/ochiq kanallar
        for yopiq_link in yopiq_channels:
            try:
                await tg_client(ImportChatInviteRequest(yopiq_link))
                await asyncio.sleep(limituzz)
                print(colored(f"{name} | Kanalga a'zo bo'ldi {yopiq_link}", "green"))
            except Exception as e:
                print(colored(f"{name} | Kanalga qo'shilishda xatolik {yopiq_link}: {e}", "red"))

        for ochiq_link in premium_channels:
            try:
                await tg_client(JoinChannelRequest(ochiq_link))
                await asyncio.sleep(limituzz)
                print(colored(f"{name} | Kanalga a'zo bo'ldi {ochiq_link}", "green"))
            except Exception as e:
                print(colored(f"{name} | Kanalga qo'shilishda xatolik {ochiq_link}: {e}", "red"))
                return

        SERVER_URL  = "https://enshteyn40.com"
        sitekey     = "0x4AAAAAAA2AVdjVXiMwY1g-"
        website_url = "https://randomgodbot.com"

        for start_param in start_params:
            start_param = start_param.strip()
            bot_username = bot_mapping.get(start_param)
            if not bot_username:
                print(colored(f"🚫 Giv uchun bot topilmadi: {start_param}", "red"))
                continue
            print(colored(f"✅ Giv uchun bot topildi: {start_param} → {bot_username}", "green"))

            # Telegram WebView init_data
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

            if not captchapai:
                print(colored("⚠️ Turnstile API key topilmadi (captcha2ensh.csv).", "red"))
                continue

            # TOKEN — HAR DOIM PROXYSIZ SIZNING SERVERINGIZGA!
            tokenfrombot = await get_turnstile_token_async(
                session=None,
                server_url=SERVER_URL,
                api_key=captchapai,
                website_url=website_url,
                website_key=sitekey,
                server_wait=2.0,
                attempts=40,
                sleep_sec=0.8
            )

            if not tokenfrombot:
                print(colored(f"{name} | ⚠️ Turnstile token olinmadi, ushbu start_param o‘tkazib yuborildi", "yellow"))
                continue

            # randomgodbot HTTP — bu yerda PROXY bo‘lishi mumkin (token allaqachon bor)
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

            async with aiohttp.ClientSession(headers=headers, connector=proxy_conn) as http_client:
                try:
                    encoded_init = base64.b64encode(init_data.encode()).decode()
                    url = (
                        f"https://randomgodbot.com/lot_join"
                        f"?userId={me.id}"
                        f"&startParam={start_param}"
                        f"&id={encoded_init}"
                        f"&token={tokenfrombot}"
                    )
                    resp = await http_client.get(url=url, ssl=False)
                    data = await resp.json()
                    description = data.get("description", "")
                    result = data.get("result", "")
                    ok = data.get("ok", False)

                    if description == "ALREADY_JOINED":
                        print(colored(f"{name} | ❕ Allaqachon qatnashgan", "blue"))
                        write_to_csv = True
                    elif ok and result == "success":
                        print(colored(f"{name} | ✅ Givga muvaffaqiyatli qo‘shildi", "green"))
                        write_to_csv = True
                    else:
                        print(colored(f"{name} | ⚠️ Giv javobi: {data}", "yellow"))
                        write_to_csv = False

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

                except Exception as err:
                    print(colored(f"{name} | Giv uchun aynan so'rovda xatolik: {err}", "yellow"))

# ========================= Runner =========================

from asyncio import Semaphore
sem = Semaphore(1)

async def sem_run(phone, givs, channels):
    async with sem:
        print(colored(f"🔵 {phone} uchun jarayon boshlanmoqda...", "blue"))
        try:
            await run(phone, givs, channels)
        except Exception as e:
            print(colored(f"{phone} | run() ichida xatolik: {e}", "red"))
        print(colored(f"🟣 {phone} | Jarayon yakunlandi.", "magenta"))

async def main():
    try:
        phonecsv = "phone"
        with open(f"{phonecsv}.csv", 'r', encoding="utf-8") as f:
            phones = [line.strip() for line in f if line.strip()]
        print(f"📲 Umumiy raqamlar soni: {len(phones)}")
    except Exception as e:
        print(f"Telefon raqamlarini yuklashda xatolik: {e}")
        return

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

        filtered_phones = [phone for phone in phones if phone not in skipped_phones]
        print(f"✅ {len(filtered_phones)} ta yangi raqam qolgan: {start_param}")

        for phone in filtered_phones:
            task = asyncio.create_task(sem_run(phone, [start_param], channels))
            all_tasks.append(task)

    if not all_tasks:
        print("⚠️ Hech qanday topshiriq topilmadi (all_tasks bo‘sh)")
    else:
        await asyncio.gather(*all_tasks)
        print(colored(f"🏁 Barcha givlar uchun yakunlandi.", "green"))

if __name__ == '__main__':
    asyncio.run(main())
