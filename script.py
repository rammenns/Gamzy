from sqlite3 import connect, OperationalError
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from random import uniform
from time import sleep
from pathlib import Path
from desktop_notifier import DesktopNotifier, Button
import sys
import httpx
import asyncio
from requests import Session, get
import json
import platform
syst = platform.system()
if syst not in {"Windows", "Darwin", "Linux"}:
    print(f"Unsupported operating system: {syst}")
    sys.exit(1)

def dr():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

def Gamzy():

    if syst == "Windows":
        exec = "Gamzy.exe"
    else:
        exec = "Gamzy"
    Popen([str(dr() / exec)])

def namecut(nam):
    inval = '<>:"/\\|?*'
    return ''.join(c for c in nam if c not in inval).strip()

async def mainscript(gmz, conngmz):

    try:

        print("\033[1m Running script \033[0m")
        print("")

        links = []
        names = []
        imgs = []
        platforms = []
        fail = []

        async def insertnremove():

            print("\033[1m Attempting to update database: \033[0m")
            print("")

            if links:
                linklist = ",".join("?" for _ in links)
                if not fail:
                    gmz.execute(f"DELETE FROM games WHERE link NOT IN ({linklist})", links)
                else:
                    faillist = ",".join("?" for _ in fail)
                    gmz.execute(f"DELETE FROM games WHERE link NOT IN ({linklist}) AND platform NOT IN ({faillist})",
                                links + fail)
                gmz.execute("UPDATE games SET new = ? WHERE seen = ?", (False, True))
                gmz.execute("SELECT link, image FROM games")
                linki = {link: i for i, link in enumerate(links)}
                for link, image in gmz.fetchall():
                    i = linki.get(link)
                    if i is None:
                        continue
                    if image == "" and imgs[i] != "":
                        gmz.execute("UPDATE games SET image = ? WHERE link = ?", (str(imgs[i]), link))
            else:
                gmz.execute("DELETE FROM games")
            conngmz.commit()

            silencedones = []
            for test in range(len(links)):
                gmz.execute(
                    "INSERT OR IGNORE INTO games (link, name, image, platform) VALUES (?, ?, ?, ?)",
                    (links[test], names[test], str(imgs[test]), platforms[test])
                )
                if gmz.rowcount > 0:
                    if platforms[test] not in silencedones:
                        print(f"{platforms[test]} is scrap source")
                        silencedones.append(platforms[test])

            conngmz.commit()

            try:
                checkpth = str(dr() / "check.db")
                conncheck = connect(checkpth, timeout = 10)
                chk = conncheck.cursor()
            except:
                pass

            thisissil = None
            if chk:
                chk.execute(" SELECT 1 FROM sqlite_master WHERE type='table' AND name='checks' ")
                if chk.fetchone():

                    chk.execute("SELECT platform, silence FROM checks")

                    silans = dict(chk.fetchall())

                    thisissil = 0

                    if "steamlogo.png" in silencedones:
                        thisissil += silans["Steam"]
                    if "epiclogo.png" in silencedones:
                        thisissil += silans["Epic"]
                    if "goglogo.png" in silencedones:
                        thisissil += silans["GOG"]
                    if "itchlogo.png" in silencedones:
                        thisissil += silans["itch.io"]

                conncheck.close()


            if thisissil is None or thisissil < len(silencedones):
                if getattr(sys, "frozen", False):
                    base = Path(sys._MEIPASS)
                else:
                    base = Path(__file__).resolve().parent

                notif = DesktopNotifier()

                await notif.send(
                    title = "Gamzy",
                    message = "Hey! There are new games waiting for you!",
                    icon = dr() / "AppLogo.png",
                    buttons = [
                        Button(
                            title = "Open",
                            on_pressed = Gamzy,
                        )
                    ]
                )

            folder = dr() / "gamzimgs"

            gmz.execute("SELECT image FROM games")
            dbimgs = {Path(rowaw[0]).name for rowaw in gmz.fetchall()}

            for file in folder.iterdir():
                if file.name not in dbimgs and file.name not in {"steamlogo.png", "epiclogo.png", "goglogo.png", "itchlogo.png"}:
                    file.unlink()

            print("Database updated    \033[92m SUCCESS \033[0m")
            print("")

            await asyncio.sleep(10)



        async def steamscrap():

            print("\033[1m Requesting Steam URL: \033[0m")

            try:

                async with httpx.AsyncClient(timeout = 5, follow_redirects = True) as steam:

                    steamheaders = {
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Encoding": "gzip, deflate, br, zstd",
                        "Accept-Language": "en-US,en;q=0.9",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0"
                    }

                    steam.headers.update(steamheaders)

                    steamresponse = await steam.get("https://store.steampowered.com/search?maxprice=free&supportedlang=english&specials=1&ndl=1")

                    steamresponse.raise_for_status()

                    print("Steam request       \033[92m SUCCESS \033[0m")

                    steamsoup = BeautifulSoup(steamresponse.text,'html.parser')

                    for steamgam in steamsoup.find_all('a', class_="search_result_row ds_collapse_flag"):

                        steamprice = steamgam
                        steamprice = steamprice.find('div', class_="responsive_search_name_combined")
                        if steamprice:
                            steamprice = steamprice.find('div', class_="search_price_discount_combined responsive_secondrow")
                            if steamprice:
                                steamprice = steamprice.find('div', class_="search_discount_and_price responsive_secondrow")
                                if steamprice:
                                    steamprice = steamprice.find('div', class_="discount_block search_discount_block")
                                    if steamprice:
                                        steampriceS = steamprice.find('div', class_="discount_prices generic_discount")
                                        if not steampriceS:
                                            steampriceS = steamprice.find('div', class_="discount_prices")
                                        if steampriceS:
                                            steamprice = steampriceS.find('div', class_="discount_final_price")

                                            if steamprice and "0,00" in steamprice.text:

                                                steamhrf = steamgam.get('href')
                                                if steamhrf:
                                                    steamnam = steamhrf.split('/')[-2].replace('_', ' ')
                                                    steamfile = ""
                                                    steamgam = steamgam.find('div', class_= "search_capsule")
                                                    if steamgam:
                                                        steamgam = steamgam.find('img')
                                                        if steamgam:
                                                            steamurl = steamgam.get('src')
                                                            if steamurl:
                                                                steamext = Path(steamurl.split("?")[0]).suffix
                                                                steamfile = dr() / "gamzimgs" / f"{namecut(steamnam)}{steamext}"
                                                                if not steamfile.exists():
                                                                    steamimgresp = await steam.get(steamurl)
                                                                    steamimgresp.raise_for_status()
                                                                    with open(steamfile, "wb") as f:
                                                                        f.write(steamimgresp.content)

                                                    links.append(steamhrf)
                                                    names.append(steamnam)
                                                    imgs.append(steamfile)
                                                    platforms.append("steamlogo.png")

                    print("Steam scrapping     \033[92m SUCCESS \033[0m")

            except Exception as e:

                fail.append("steamlogo.png")
                print(f"Steam scrapping \033[91m FAILED \033[0m {e}")




        async def gogscrap():

            print("\033[1m Requesting GOG URL: \033[0m")

            try:

                async with httpx.AsyncClient( timeout = 5, follow_redirects = True) as gog:

                    gogheaders = {
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Encoding": "gzip, deflate, br, zstd",
                        "Accept-Language": "en-US,en;q=0.9",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0"
                    }

                    gog.headers.update(gogheaders)

                    gogresponse = await gog.get("https://www.gog.com/en/")

                    gogresponse.raise_for_status()

                    print("GOG request         \033[92m SUCCESS \033[0m")

                    gogsoup = BeautifulSoup(gogresponse.text,'html.parser')

                    for goglink in gogsoup.find_all('div', class_="giveaway"):

                        goggam = goglink.find('a', class_="giveaway__overlay-link")
                        goggamn = goglink.find('div', class_="giveaway__image")
                        if goggam:
                            goghrf = goggam.get('href')
                            if goghrf:
                                goggam = goghrf.rstrip('/').split('/')[-1]
                                gognam = goggam.replace('_', ' ').title()
                                goggam = goggamn.find('store-picture')
                                gogfile = ""
                                if goggam:
                                    goggam = goggam.find('picture')
                                    if goggam:
                                        goggam = goggam.find('source')
                                        if goggam:
                                            goggam = goggam.get("srcset")
                                            if goggam:
                                                gogurl = goggam.split(", ")[1].rsplit(" ", 1)[0]
                                                if gogurl:
                                                    gogext = Path(gogurl.split("?")[0]).suffix
                                                    gogfile = dr() / "gamzimgs" / f"{namecut(gognam)}{gogext}"
                                                    if not gogfile.exists():
                                                        gogimgresp = await gog.get(gogurl)
                                                        gogimgresp.raise_for_status()
                                                        with open(gogfile, "wb") as f:
                                                            f.write(gogimgresp.content)

                                links.append(goghrf)
                                names.append(gognam)
                                imgs.append(gogfile)
                                platforms.append("goglogo.png")

                print("GOG scrapping       \033[92m SUCCESS \033[0m")

            except Exception as e:

                fail.append("goglogo.png")
                print(f"GOG scrapping \033[91m FAILED \033[0m {e}")




        def epicscrap():

            print("\033[1m Requesting EpicGames URL: \033[0m")

            try:

                with Session() as epic:

                    epicheaders = {
                        "Accept": "application/json, text/plain, */*",
                        "Accept-Encoding": "gzip, deflate, br, zstd",
                        "Accept-Language": "en-US,en;q=0.9",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0"
                    }

                    epic.headers.update(epicheaders)

                    epicparams = {
                        "operationName": "searchStoreQuery",
                        "variables": json.dumps({
                            "allowCountries": "RO",
                            "category": "games/edition/base|addons|bundles/games|games/demo|games/edition",
                            "count": 40,
                            "country": "RO",
                            "effectiveDate": "[,2026-07-04T02:04:47.335Z]",
                            "keywords": "",
                            "locale": "en-US",
                            "onSale": True,
                            "sortBy": "currentPrice",
                            "sortDir": "ASC",
                            "start": 0,
                            "tag": "",
                            "withPrice": True
                        }),
                        "extensions": json.dumps({
                            "persistedQuery": {
                                "version": 1,
                                "sha256Hash": "29d49ab31d438cd90be2d554d2d54704951e4223a8fcd290fcf68308841a1979"
                            }
                        })
                    }

                    epicresponse = epic.get("https://store.epicgames.com/graphql", params = epicparams, timeout = 5)

                    epicresponse.raise_for_status()

                    print("EpicGames request   \033[92m SUCCESS \033[0m")

                    epicdata = epicresponse.json()

                    for epicgam in epicdata["data"]["Catalog"]["searchStore"]["elements"]:

                        if epicgam["price"]:
                            epicgamn = epicgam["price"]
                            if epicgamn["totalPrice"]:
                                epicgamn = epicgamn["totalPrice"]
                                if epicgamn["discountPrice"] == epicgamn["voucherDiscount"] and epicgamn["originalPrice"] == epicgamn["discount"]:
                                    if epicgam["catalogNs"]:
                                        epicgamn = epicgam["catalogNs"]
                                        if epicgamn["mappings"][0]:
                                            epicgamn = epicgamn["mappings"][0]
                                            if epicgamn["pageSlug"]:
                                                epicslug = epicgamn["pageSlug"]
                                                epicnam = epicgam.get("title", "")
                                                epicfile = ""
                                                if epicgam["keyImages"][0]["url"]:
                                                    epicurl = epicgam["keyImages"][0]["url"]
                                                    epicext = Path(epicurl.split("?")[0]).suffix
                                                    if not epicext:
                                                        epicext = ".png"
                                                    epicfile = dr() / "gamzimgs" / f"{namecut(epicnam)}{epicext}"
                                                    if not epicfile.exists():
                                                        epicimgresp = epic.get(epicurl)
                                                        epicimgresp.raise_for_status()
                                                        with open(epicfile, "wb") as f:
                                                            f.write(epicimgresp.content)

                                                links.append(f"https://store.epicgames.com/en-US/p/{epicslug}")
                                                names.append(epicnam)
                                                imgs.append(epicfile)
                                                platforms.append("epiclogo.png")
                                else:
                                    break

                    print("EpicGames scrapping \033[92m SUCCESS \033[0m")

            except Exception as e:

                fail.append("epiclogo.png")
                print(f"EpicGames scrapping \033[91m FAILED \033[0m {e}")




        async def itchscrap():

            print("\033[1m Requesting itch.io URL: \033[0m")

            try:

                async with httpx.AsyncClient(timeout = 5, follow_redirects = True) as itch:

                    itchheaders = {
                        "Accept": "*/*",
                        "Accept-Encoding": "gzip, deflate, br, zstd",
                        "Accept-Language": "en-US,en;q=0.9",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0",
                        "X-Requested-With": "XMLHttpRequest"
                    }

                    itch.headers.update(itchheaders)

                    p = 1

                    itchresponse = await itch.get(f"https://itch.io/games/on-sale?page={p}&format=json")

                    itchresponse.raise_for_status()

                    itchdata = itchresponse.json()
                    itchsoup = BeautifulSoup(itchdata["content"], "html.parser")

                    print("itch.io request     \033[92m SUCCESS \033[0m")

                    while itchdata["content"]:

                        for itchgam in itchsoup.find_all('div', class_="game_cell"):

                            itchgamn = itchgam.find('div', class_="game_thumb")
                            itchgam = itchgam.find('div', class_="game_cell_data")
                            if itchgam and itchgamn:
                                itchgam = itchgam.find('div', class_="game_title")
                                if itchgam:
                                    itchnam = itchgam.find('a' , class_="title game_link")
                                    if itchnam:
                                        itchnam = itchnam.text
                                    else:
                                        itchnam = ""
                                    itchgam = itchgam.find('a', class_="price_tag meta_tag sale")
                                    if itchgam:
                                        itchprice = itchgam.find('div', class_="price_value")
                                        itchsale = itchgam.find('div', class_="sale_tag")

                                        if (itchprice and itchsale and itchprice.text == "$0" and itchsale.text == "-100%"):
                                            itchgamn = itchgamn.find('a', class_="thumb_link game_link")
                                            if itchgamn:
                                                itchhrf = itchgamn.get("href")
                                                if itchhrf:
                                                    itchfile = ""
                                                    itchgamn = itchgamn.find('img', class_="lazy_loaded")
                                                    if itchgamn:
                                                        itchurl = itchgamn.get("data-lazy_src")
                                                        if itchurl:
                                                            itchext = Path(itchurl.split("?")[0]).suffix
                                                            itchfile = dr() / "gamzimgs" / f"{namecut(itchnam)}{itchext}"
                                                            if not itchfile.exists():
                                                                itchimgresp = await itch.get(itchurl)
                                                                itchimgresp.raise_for_status()
                                                                with open(itchfile, "wb") as f:
                                                                    f.write(itchimgresp.content)

                                                    links.append(itchhrf)
                                                    names.append(itchnam)
                                                    imgs.append(itchfile)
                                                    platforms.append("itchlogo.png")

                        await asyncio.sleep(uniform(0.3, 0.8))
                        p += 1
                        itchresponse = await itch.get(f"https://itch.io/games/on-sale?page={p}&format=json")
                        itchresponse.raise_for_status()
                        itchdata = itchresponse.json()
                        itchsoup = BeautifulSoup(itchdata["content"], "html.parser")

                print("itch.io scrapping   \033[92m SUCCESS \033[0m")

            except Exception as e:
                fail.append("itchlogo.png")
                print(f"itch.io scrapping   \033[91m FAILED \033[0m {e}")


        await asyncio.gather(
            steamscrap(),
            gogscrap(),
            itchscrap(),
            asyncio.to_thread(epicscrap)
        )

        assert len(links) == len(names) == len(imgs) == len(platforms)

        await insertnremove()

        return True

    except Exception as e:

        print(f"\033[1;91m ERROR: \033[0;91m script FAILED on running \033[0m {e}")
        print("")

        return False


def main():

    print("\033[1m Running: \033[0m")
    print("")
    connsafe = None
    conntmr = None
    conngmz = None
    checkpth = None
    conncheck = None
    chk = None

    try:
        safepth = str(dr() / "safe.db")
        connsafe = connect(safepth)
        safe = connsafe.cursor()
        safe.execute("CREATE TABLE IF NOT EXISTS safety (safe BOOLEAN)")
        safe.execute("SELECT safe FROM safety")
        rowz = safe.fetchone()
        if rowz is None:
            safe.execute("INSERT INTO safety VALUES (?)", (False,))
        else:
            safe.execute("UPDATE safety SET safe = ?", (False,))
        connsafe.commit()

        checkpth = str(dr() / "check.db")
        conncheck = connect(checkpth)
        chk = conncheck.cursor()

        chk.execute("""
        CREATE TABLE IF NOT EXISTS checks(
            platform TEXT PRIMARY KEY,
            hide BOOLEAN DEFAULT FALSE,
            silence BOOLEAN DEFAULT FALSE
        )
        """)

        chk.execute("SELECT platform, hide, silence FROM checks")
        rows = chk.fetchall()

        if not rows:
            chk.execute("INSERT INTO checks(platform) VALUES (?)", ("Steam",))
            chk.execute("INSERT INTO checks(platform) VALUES (?)", ("Epic",))
            chk.execute("INSERT INTO checks(platform) VALUES (?)", ("GOG",))
            chk.execute("INSERT INTO checks(platform) VALUES (?)", ("itch.io",))
            chk.execute("INSERT INTO checks(platform) VALUES (?)", ("Old",))

        ####################################################################
        try:
            chk.execute("INSERT INTO checks(platform) VALUES (?)", ("Old",))
        except:
            pass
        ####################################################################

        conncheck.commit()
        conncheck.close()
        conncheck = None

        timerpth = str(dr() / "timer.db")
        conntmr = connect(timerpth)
        gamespth = str(dr() / "games.db")
        conngmz = connect(gamespth, timeout = 10)

        gimgpth = dr() / "gamzimgs"
        if not gimgpth.exists():
            gimgpth.mkdir()
            print("\033[1m Folder created \033[0m")
            print("")

        tmr = conntmr.cursor()
        gmz = conngmz.cursor()

        tmr.execute("CREATE TABLE IF NOT EXISTS timer (nextupdate REAL)")
        conntmr.commit()

        gmz.execute("""
        CREATE TABLE IF NOT EXISTS games(
            link TEXT PRIMARY KEY,
            image TEXT,
            name TEXT,
            platform TEXT NOT NULL,
            new BOOLEAN NOT NULL DEFAULT TRUE,
            seen BOOLEAN NOT NULL DEFAULT FALSE
        )
        """)

        ##############################################################################
        try:
            gmz.execute("ALTER TABLE games ADD COLUMN new BOOLEAN NOT NULL DEFAULT TRUE")
        except OperationalError:
            pass
        try:
            gmz.execute("ALTER TABLE games ADD COLUMN seen BOOLEAN NOT NULL DEFAULT FALSE")
        except OperationalError:
            pass
        ##############################################################################

        conngmz.commit()
        conngmz.close()
        conngmz = None

        tmr.execute("SELECT nextupdate FROM timer")
        row = tmr.fetchone()
        if row is None:
            tmr.execute("INSERT INTO timer VALUES (?)", (datetime.now().timestamp(),))
            conntmr.commit()

        while True:

            print("\033[1m Entered loop \033[0m")
            print("")

            safe.execute("UPDATE safety SET safe = ?", (False,))
            connsafe.commit()

            tmr.execute("SELECT nextupdate FROM timer")
            row = tmr.fetchone()

            now = datetime.now().timestamp()

            try:

                internettest = httpx.get("https://www.google.com/generate_204", timeout=5)

                internettest.raise_for_status()

                if now >= row[0]:

                    try:

                        conngmz = connect(gamespth, timeout=10)
                        gmz = conngmz.cursor()

                        if asyncio.run(mainscript(gmz, conngmz)):

                            counting = 1
                            gmz.execute("SELECT link, image, name, platform, new FROM games")
                            for link, image, name, platform, new in gmz.fetchall():
                                print(f"{counting}. {link} {image} {name} {platform} {'NEW' if new else ''}")
                                counting += 1

                    finally:

                        if conngmz:
                            conngmz.close()
                            conngmz = None

                    now = datetime.now().timestamp()
                    pause = timedelta(hours=uniform(12, 24))
                    tmr.execute("UPDATE timer SET nextupdate = ?", (now + pause.total_seconds(),))
                    conntmr.commit()
                    tmr.execute("SELECT nextupdate FROM timer")
                    row = tmr.fetchone()

                print(" Entering sleep")
                safe.execute("UPDATE safety SET safe = ?", (True,))
                connsafe.commit()

                while True:

                    now = datetime.now().timestamp()

                    if now >= row[0]:
                        break

                    sleep(uniform(30, 60))


            except Exception as e:
                print(f"\033[1;91m ERROR: \033[0m {e}")
                print("")
                safe.execute("UPDATE safety SET safe = ?", (True,))
                connsafe.commit()
                tmr.execute("UPDATE timer SET nextupdate = ?", (now + uniform(600, 780),))
                conntmr.commit()

    except Exception as e:
        for conn in [connsafe, conntmr, conngmz]:
            try:
                conn.close()
            except:
                pass
        print(f"\033[1;91m ERROR: \033[0;91m Main script FAILED \033[0m {e}")

if __name__ == "__main__":
    main()