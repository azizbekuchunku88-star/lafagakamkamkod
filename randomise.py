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


# =============== Fayl qidirish yordamchilari ===============
def find_path(candidates):
    """Berilgan yo'llar ichidan birinchi mavjudini qaytaradi."""
    for p in candidates:
        try:
            if p and os.path.exists(p):
                return p
        except Exception:
            continue
    return None

def read_first_cell_csv_file(path: str) -> str:
    """CSV faylning 1-qatordagi 1-ustun qiymatini qaytaradi (bo'sh bo'lsa '')."""
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if row and (row[0] or "").strip():
                    return row[0].strip()
    except Exception:
        pass
    return ""

def read_list_csv_first_col(path: str) -> list[str]:
    """Har bir qatordan 1-ustunni ro'yxat sifatida qaytaradi (bo'sh qatorlar tashlanadi)."""
    out = []
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            for row in csv.reader(f):
                if row and (row[0] or "").strip():
                    out.append(row[0].strip())
    except Exception:
        pass
    return out

def info_found(label: str, path: str):
    print(colored(f"📄 {label}: {path} dan olindi", "cyan"))

def warn_missing(label: str, hint: str = ""):
    msg = f"⚠️ {label} topilmadi yoki bo'sh."
    if hint:
        msg += f" {hint}"
    print(colored(msg, "yellow"))

# Root papkalar
WIN = r"C:\join"
ANDR = "/storage/emulated/0/giv"
CURR = "."

# =============== XEvil API key ===============
xevil_path = find_path([os.path.join(WIN, "xeviIkey.csv"),   # ba'zi fayl nomlari adashishi mumkin, ikkalasini qo'shdik
                        os.path.join(WIN, "xevilkey.csv"),
                        os.path.join(ANDR, "xevilkey.csv"),
                        os.path.join(CURR, "xevilkey.csv")])
if xevil_path:
    XEVIL_API_KEY = read_first_cell_csv_file(xevil_path)
    info_found("XEvil API key", xevil_path)
else:
    XEVIL_API_KEY = ""
    warn_missing("xevilkey.csv", "CAPTCHA servisi ishlamasligi mumkin.")

# =============== Proxy ===============
proxy_path = find_path([os.path.join(ANDR, "proxy.csv"),
                        os.path.join(WIN, "proxy.csv"),
                        os.path.join(CURR, "proxy.csv")])
ROTATED_PROXY = read_first_cell_csv_file(proxy_path) if proxy_path else ""
if ROTATED_PROXY:
    info_found("Proxy", proxy_path)
else:
    warn_missing("proxy.csv", "Proxysiz ishlaymiz.")

# =============== Turnstile server API key (enshteyn40.com) ===============
captcha2_path = find_path([os.path.join(WIN, "captcha2ensh.csv"),
                           os.path.join(ANDR, "captcha2ensh.csv"),
                           os.path.join(CURR, "captcha2ensh.csv")])
if captcha2_path:
    captchapai = read_first_cell_csv_file(captcha2_path)
    info_found("Turnstile API key", captcha2_path)
else:
    captchapai = ""
    warn_missing("captcha2ensh.csv", "Turnstile token olinmasligi mumkin.")

# =============== GIV mapping va boshqa CSVlar ===============
# randogiv.csv (start_param -> bot username) majburiy!
randogiv_path = find_path([os.path.join(WIN, "randogiv.csv"),
                           os.path.join(ANDR, "randogiv.csv"),
                           os.path.join(CURR, "randogiv.csv")])
bot_mapping, givs = {}, []
if randogiv_path:
    with open(randogiv_path, "r", encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) >= 2 and row[0].strip() and row[1].strip():
                key = row[0].strip()
                val = row[1].strip()
                givs.append(key)
                bot_mapping[key] = val
    info_found("randogiv.csv", randogiv_path)
else:
    warn_missing("randogiv.csv", "start_param -> bot mapping bo'sh bo'ladi.")

print("📌 Yuklangan start_param lar va botlar:")
for k, v in bot_mapping.items():
    print(f"   ➤ {k} => {v}")

# randolimit.csv (kutish vaqti, birinchi katak)
limit_path = find_path([os.path.join(WIN, "randolimit.csv"),
                        os.path.join(ANDR, "randolimit.csv"),
                        os.path.join(CURR, "randolimit.csv")])
try:
    limituzz = int(read_first_cell_csv_file(limit_path)) if limit_path else 1
    info_found("randolimit.csv", limit_path or "(topilmadi, default 1s)")
except Exception:
    limituzz = 1
    warn_missing("randolimit.csv", "default 1 soniya qo‘llanadi.")
print(f"Kutiladigan vaqt - {limituzz}")

# ochiq/yopiq kanallar ro'yxati
ranochiq_path = find_path([os.path.join(WIN, "ranochiqkanal.csv"),
                           os.path.join(ANDR, "ranochiqkanal.csv"),
                           os.path.join(CURR, "ranochiqkanal.csv")])
ranyopiq_path = find_path([os.path.join(WIN, "ranyopiqkanal.csv"),
                           os.path.join(ANDR, "ranyopiqkanal.csv"),
                           os.path.join(CURR, "ranyopiqkanal.csv")])

premium_channels = read_list_csv_first_col(ranochiq_path) if ranochiq_path else []
yopiq_channels    = read_list_csv_first_col(ranyopiq_path) if ranyopiq_path else []

if ranochiq_path: info_found("ranochiqkanal.csv", ranochiq_path)
else:             warn_missing("ranochiqkanal.csv")
if ranyopiq_path: info_found("ranyopiqkanal.csv", ranyopiq_path)
else:             warn_missing("ranyopiqkanal.csv")

channels = premium_channels + yopiq_channels




def add_to_bans(phone):
    try:
        with open("randobans.csv", "a", encoding="utf-8") as f:
            f.write(f"{phone}\n")
        print(colored(f"🚫 {phone} → randobans.csv ga yozildi", "yellow"))
    except Exception as e:
        print(colored(f"⚠️ Ban faylga yozishda xatolik: {e}", "red"))


def read_csv(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Sarlavha qatorini o'tkazib yuborish
        return [(row[0].strip(), row[1].strip()) for row in reader if len(row) == 2]


# GIV’lar va bot mapping
givs = []
bot_mapping = {}
with open(r"C:\join\randogiv.csv", 'r', encoding='utf-8') as f:
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

with open(r"C:\join\randolimit.csv", 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    limituzz = int((next(reader)[0] or "1").strip())
print(f"Kutiladigan vaqt - {limituzz}")

with open(r"C:\join\ranochiqkanal.csv", 'r', encoding='utf-8') as f:
    premium_channels = [row[0].strip() for row in csv.reader(f) if row]

with open(r"C:\join\ranyopiqkanal.csv", 'r', encoding='utf-8') as f:
    yopiq_channels = [row[0].strip() for row in csv.reader(f) if row]

channels = premium_channels + yopiq_channels


# =============== Asosiy ish oqimi ===============
async def run(phone, start_params, channels):
    api_id = 22962676
    api_hash = '543e9a4d695fe8c6aa4075c9525f7c57'

    tg_client = TelegramClient(f"../sessions/{phone}", api_id, api_hash)
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
                    url = f"https://185.203.72.14/lot_join?userId={me.id}&startParam={start_param}&id={encoded_init_data}&token=-"
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
                        if (isinstance(err_inner, KeyError) and err_inner.args and err_inner.args[0] == "result") or ("'result'" in str(err_inner)):
                            add_to_bans(phone)
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
        phonecsv = "../ochopish"
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
