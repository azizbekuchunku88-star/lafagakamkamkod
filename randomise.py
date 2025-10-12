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
from io import BytesIO
from PIL import Image
import os
from typing import Optional

print("Oxirgi yangilanish vaqti 23:39")


# =============== Turnstile token olish ===============
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
    """
    enshteyn40.com dagi /turnstile va /turnstile/result API orqali token qaytaradi.
    READY bo'lsa token, bo'lmasa None.
    """
    try:
        r = await session.post(
            f"{server_url}/turnstile",
            json={
                "api_key": api_key,
                "website_url": website_url,
                "website_key": website_key,
                "wait": True,
                "server_wait": server_wait
            }
        )
        j = await r.json(content_type=None)
    except Exception as e:
        print(f"Create error: {e}")
        return None

    if j.get("success") and j.get("status") == "ready":
        tok = j.get("token")
        return tok if tok else None

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
                f"{server_url}/turnstile/result",
                json={"task_id": task_id, "block": False}
            )
            j2 = await r2.json(content_type=None)

            if j2.get("success") and j2.get("status") == "ready":
                tok = j2.get("token")
                return tok if tok else None

            if not j2.get("success"):
                print(j2.get("error", "error"))
                return None

            await asyncio.sleep(sleep_sec)
        except Exception:
            await asyncio.sleep(sleep_sec)
            continue

    print("Timeout: token olinmadi")
    return None


# =============== Foydali yordamchilar ===============
def image2base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


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
        status, code = response_data.split('|')
        if status != 'OK':
            return None
        return code


async def get_result(code):
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    params = {
        "key": XEVIL_API_KEY,
        "id": code,
        'action': 'get'
    }
    for _ in range(5):
        async with aiohttp.request("GET", "https://api.sctg.xyz/res.php", params=params, headers=headers) as response:
            response_data = await response.text()
            if '|' not in response_data:
                await asyncio.sleep(1)
                continue
            status, result = response_data.split('|')
            if status != 'OK':
                return None
            return result
    return None


# ================== KROSS-PLATTAFORMA CSV RESOLVER ==================
import os, sys, csv
from termcolor import colored

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
    """
    filename uchun birinchi mavjud yo'lni qaytaradi.
    Agar hech birida topilmasa, fallback sifatida ENV_ROOT ichida to'liq yo'lni beradi (lekin yaratmaydi).
    """
    for root in ROOTS:
        try:
            full = os.path.join(root, filename)
            if os.path.exists(full):
                return full
        except Exception:
            continue
    return os.path.join(ENV_ROOT, filename)

def ensure_path_and_file(root: str, filename: str, header: str | None = None, exit_after_create: bool = True) -> str:
    """
    root papkani (agar kerak bo'lsa) yaratadi, filename bo'sh bo'lsa yaratadi.
    header berilsa, yangi faylga yozib qo'yadi.
    """
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

# ================== BU YERDAN PASTDA CSV LARNI RESOLVE QILING ==================
# XEvil API key
xevil_file = resolve_path("xevilkey.csv")
if os.path.exists(xevil_file):
    XEVIL_API_KEY = read_first_cell_csv_file(xevil_file)
    print(colored(f"🔑 XEvil key: {xevil_file}", "cyan"))
else:
    # istasangiz avtomatik yaratib ham ketishingiz mumkin:
    xevil_file = ensure_path_and_file(ENV_ROOT, "xevilkey.csv", header="", exit_after_create=False)
    XEVIL_API_KEY = ""
    print(colored("⚠️ xevilkey.csv topilmadi. Bo'sh qiymat bilan davom etamiz (CAPTCHA ishlamasligi mumkin).", "yellow"))

# Proxy (birinchi katakda http(s)://user:pass@host:port yoki socks5://...)
proxy_file = resolve_path("proxy.csv")
ROTATED_PROXY = read_first_cell_csv_file(proxy_file) if os.path.exists(proxy_file) else ""
if ROTATED_PROXY:
    print(colored(f"🔌 Proxy: {proxy_file}", "cyan"))
else:
    print(colored("ℹ️ proxy.csv topilmadi yoki bo‘sh. Proxysiz ishlaymiz.", "yellow"))

# Turnstile server API key (enshteyn40.com)
captcha2_file = resolve_path("captcha2ensh.csv")
if os.path.exists(captcha2_file):
    captchapai = read_first_cell_csv_file(captcha2_file)
    print(colored(f"🧰 Turnstile API key: {captcha2_file}", "cyan"))
else:
    captchapai = ""
    print(colored("⚠️ captcha2ensh.csv topilmadi yoki bo‘sh. Turnstile token olinmasligi mumkin.", "yellow"))

# start_param -> bot_username (majburiy)
randogiv_file = resolve_path("randogiv.csv")
if not os.path.exists(randogiv_file):
    # Shablon sarlavhasiz bo'sh fayl yaratiladi va skript to'xtaydi — foydalanuvchi to‘ldiradi.
    randogiv_file = ensure_path_and_file(ENV_ROOT, "randogiv.csv", header="start_param,bot_username")
    # sys.exit bo'lgani uchun bu joydan pastga tushmaydi

bot_mapping, givs = {}, []
with open(randogiv_file, "r", encoding="utf-8", newline="") as f:
    for row in csv.reader(f):
        if len(row) >= 2 and row[0].strip() and row[1].strip():
            key = row[0].strip()
            val = row[1].strip()
            givs.append(key)
            bot_mapping[key] = val
print(colored(f"📌 randogiv.csv yuklandi: {len(givs)} ta start_param", "cyan"))

# kutish vaqti (soniya) — bo'lmasa 1
limit_file = resolve_path("randolimit.csv")
if os.path.exists(limit_file):
    try:
        limituzz = int(read_first_cell_csv_file(limit_file))
    except Exception:
        limituzz = 1
        print(colored("⚠️ randolimit.csv noto‘g‘ri format. default 1s.", "yellow"))
    print(colored(f"⏱️ Kutiladigan vaqt: {limituzz}s", "cyan"))
else:
    # istasangiz avtomatik yaratib qo‘yish
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
# ================== /CSV RESOLVER ==================







# =============== Asosiy ish oqimi ===============
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

        # --- PROXY connector tayyorlab qo'yamiz (randomgodbot uchun)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        proxy_conn = aiohttp_proxy.ProxyConnector(ssl_context=ssl_context).from_url(ROTATED_PROXY) if ROTATED_PROXY else None

        # yopiq kanallar
        for yopiq_link in yopiq_channels:
            try:
                await tg_client(ImportChatInviteRequest(yopiq_link))
                await asyncio.sleep(limituzz)
                print(colored(f"{name} | Kanalga a'zo bo'ldi {yopiq_link}", "green"))
            except Exception as e:
                print(colored(f"{name} | Kanalga qo'shilishda xatolik {yopiq_link}: {e}", "red"))

        # ochiq kanallar
        for ochiq_link in premium_channels:
            try:
                await tg_client(JoinChannelRequest(ochiq_link))
                await asyncio.sleep(limituzz)
                print(colored(f"{name} | Kanalga a'zo bo'ldi {ochiq_link}", "green"))
            except Exception as e:
                print(colored(f"{name} | Kanalga qo'shilishda xatolik {ochiq_link}: {e}", "red"))
                return

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

            # --- Turnstile token olish (PROXYSIZ sessiya!)
            SERVER_URL  = "https://enshteyn40.com"
            sitekey     = "0x4AAAAAAA2AVdjVXiMwY1g-"   # <-- sizda qanday bo‘lsa shuni qoldirdim
            website_url = "https://randomgodbot.com"    # kerak bo‘lsa, to‘liq join URL qilib qo‘ying

            if not captchapai:
                print(colored("⚠️ Turnstile API key topilmadi (captcha2ensh.csv).", "red"))
                # Token bo‘lmasa, keyingi start_param ga o‘tamiz
                continue

            turnstile_timeout = aiohttp.ClientTimeout(total=45)
            async with aiohttp.ClientSession(timeout=turnstile_timeout) as ts_session:  # PROXYSIZ
                tokenfrombot = await get_turnstile_token_async(
                    session=ts_session,
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

            # --- randomgodbot HTTP sessiya (PROXY bilan)
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
                    http_client.headers.add('Host', 'randomgodbot.com')
                    encoded_init_data = base64.b64encode(init_data.encode()).decode()

                    # 1-bosqich: captcha rasmini olish (IP orqali)
                    url = f"https://randomgodbot.com/lot_join?userId={me.id}&startParam={start_param}&id={encoded_init_data}&token=-"
                    response = await http_client.get(url=url, ssl=False)
                    response.raise_for_status()
                    response_json = await response.json()

                    try:
                        result_node = response_json.get("result")
                        if not isinstance(result_node, dict):
                            raise KeyError("result")
                        b64_data = result_node["base64"]
                        captcha_hash = result_node["hash"]
                    except Exception as err_inner:
                        print(colored(f"{name} | Giv uchun aynan so'rovda xatolik: {err_inner}", "yellow"))
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

                    # 2-bosqich: real join (domen orqali) + turnstile token
                    url = (
                        f"https://randomgodbot.com/lot_join"
                        f"?userId={me.id}"
                        f"&startParam={start_param}"
                        f"&id={encoded_init_data}"
                        f"&captcha_hash={captcha_hash}"
                        f"&captcha_value={captcha_input}"
                        f"&token={tokenfrombot}"
                    )
                    response = await http_client.get(url=url, ssl=False)
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


# =============== Runner ===============
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

    ban_file = "randobans.csv"
    banned = set()
    if os.path.exists(ban_file):
        with open(ban_file, "r", encoding="utf-8") as f:
            banned = set(line.strip() for line in f if line.strip())
        print(colored(f"🚫 Ban ro‘yxati topildi: {len(banned)} ta raqam", "yellow"))
    else:
        print(colored("ℹ️ randobans.csv topilmadi (ban ro‘yxati bo‘sh deb qabul qilinadi)", "cyan"))

    phones = [p for p in phones if p not in banned]
    print(colored(f"✅ Ban filtridan so‘ng qolgan raqamlar: {len(phones)}", "green"))

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

        filtered_phones = [phone for phone in phones if phone not in skipped_phones and phone not in banned]
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
