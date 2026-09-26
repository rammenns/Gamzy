import platform
import sys
syst = platform.system()
if syst not in {"Windows", "Linux", "Darwin"}:
    print(f"Unsupported operating system: {syst}")
    sys.exit(1)
from sqlite3 import connect, OperationalError
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from random import uniform
from time import sleep
from pathlib import Path
from desktop_notifier import DesktopNotifier, Button
from subprocess import Popen, run
import httpx
import asyncio
from requests import Session

def deleteshit(connsafe, conntmr, conngmz):

    for conn in (conngmz, conntmr, connsafe):
        if conn is not None:
            conn.close()

    appdata = (Path.home() / "Library" / "Application Support" / "Gamzy")

    if appdata.exists():

        for item in appdata.iterdir():

            if item.is_dir():

                for subitem in sorted(item.rglob("*"), reverse=True):
                    if subitem.is_file():
                        subitem.unlink()
                    elif subitem.is_dir():
                        subitem.rmdir()

                item.rmdir()

            else:
                item.unlink()

        appdata.rmdir()

    if int(platform.mac_ver()[0].split(".")[0]) >= 13:

        run([str(Path.home() / ".Trash" / "Gamzy.app" / "Contents" / "MacOS" / "Gamzy"), "--unregister-gamzscript"])

    else:

        launch_agent = (Path.home() / "Library" / "LaunchAgents" / "com.gamzy.GamzScript.plist")

        if launch_agent.exists():
            run([
                "/bin/launchctl",
                "unload",
                "-w",
                str(launch_agent),
            ])

            launch_agent.unlink()

    sys.exit(0)


def resourcepth(name):
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / name
    return Path(__file__).resolve().parent / name

def dr():
    if not getattr(sys, "frozen", False):
        return Path(__file__).resolve().parent
    elif syst == "Windows":
        stuffpth = Path.home() / "AppData" / "Roaming" / "Gamzy"
    elif syst == "Linux":
        stuffpth = Path.home() / ".local" / "share" / "Gamzy"
    else:
        stuffpth = Path.home() / "Library" / "Application Support" / "Gamzy"
    stuffpth.mkdir(parents=True, exist_ok=True)
    return stuffpth

def Gamzy():
    if syst != "Darwin":
        Popen([str((Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent) / ("Gamzy.exe" if syst == "Windows" else "Gamzy"))])
    else:
        Popen(["open", str(Path(sys.executable).parents[5])])

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

            conncheck = None
            chk = None
            try:
                checkpth = str(dr() / "check.db")
                conncheck = connect(checkpth, timeout = 10)
                chk = conncheck.cursor()
            except:
                pass

            thisissil = None
            if chk is not None:
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
                    if "ubilogo.png" in silencedones:
                        thisissil += silans["Ubisoft"]

                if conncheck is not None:
                    conncheck.close()


            if thisissil is None or thisissil < len(silencedones):

                notif = DesktopNotifier(app_name = " ")

                await notif.send(
                    title = "Gamz Found!",
                    icon = resourcepth("gamzylogo.png"),
                    message = "Hey, there are new games waiting for you! Check 'em now!",
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
                if file.name not in dbimgs and file.name not in {"steamlogo.png", "epiclogo.png", "goglogo.png", "itchlogo.png", "ubilogo.png"}:
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
                                if goggamn:
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

                    epicresponse = epic.get("https://store.epicgames.com/graphql?operationName=searchStoreQuery&variables=%7B%22allowCountries%22:%22RO%22,%22category%22:%22games%2Fedition%2Fbase%7Caddons%7Cbundles%2Fgames%7Cgames%2Fedition%7Csubscription%22,%22count%22:40,%22country%22:%22RO%22,%22effectiveDate%22:%22[,2026-09-14T16:18:45.558Z]%22,%22keywords%22:%22%22,%22locale%22:%22en-US%22,%22onSale%22:true,%22sortBy%22:%22currentPrice%22,%22sortDir%22:%22ASC%22,%22tag%22:%22%22,%22withPrice%22:true%7D&extensions=%7B%22persistedQuery%22:%7B%22version%22:1,%22sha256Hash%22:%227d58e12d9dd8cb14c84a3ff18d360bf9f0caa96bf218f2c5fda68ba88d68a437%22%7D%7D", timeout = 5)

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


        async def ubiscrap():

            print("\033[1m Requesting Ubisoft URL: \033[0m")

            try:

                async with httpx.AsyncClient(timeout=5, follow_redirects=True) as ubi:

                    ubiheaders = {
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Encoding": "gzip, deflate, br, zstd",
                        "Accept-Language": "en-US,en;q=0.9",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:153.0) Gecko/20100101 Firefox/153.0"
                    }

                    ubi.headers.update(ubiheaders)

                    ubiresponse = await ubi.get("https://store.ubisoft.com/ie/free-pc-games?lang=en-ZW")

                    ubiresponse.raise_for_status()

                    print("Ubisoft request     \033[92m SUCCESS \033[0m")

                    ubisoup = BeautifulSoup(ubiresponse.text, 'html.parser')

                    for ubigam in ubisoup.find_all('store-operability-focus-banner'):
                        ubibackgr = ubigam.get("background")
                        ubipara = ubigam.get("click-event-params")
                        if (ubibackgr and "giveaway" in ubibackgr.lower()) or (ubipara and "giveaway" in ubipara.lower()):
                            ubihrf = ubigam.get("main-cta-link")
                            if ubihrf:
                                ubinam = ubigam.get("title-text")
                                if ubinam:
                                    ubinam = BeautifulSoup(str(ubinam), "html.parser").get_text(strip=True).removeprefix("Get ").removesuffix(" for free!")
                                else:
                                    ubinam = ""
                                ubifile = ""
                                ubiurl = ubigam.get("logo")
                                if ubiurl:
                                    ubiext = Path(ubiurl.split("?")[0]).suffix
                                    ubifile = dr() / "gamzimgs" / f"{namecut(ubinam)}{ubiext}"
                                    if not ubifile.exists():
                                        ubiimgresp = await ubi.get(str(ubiurl))
                                        ubiimgresp.raise_for_status()
                                        with open(ubifile, "wb") as f:
                                            f.write(ubiimgresp.content)

                                links.append(ubihrf)
                                names.append(ubinam)
                                imgs.append(ubifile)
                                platforms.append("ubilogo.png")

                    print("Ubisoft scrapping   \033[92m SUCCESS \033[0m")

            except Exception as e:
                fail.append("ubilogo.png")
                print(f"Ubisoft scrapping   \033[91m FAILED \033[0m {e}")


        await asyncio.gather(
            steamscrap(),
            gogscrap(),
            itchscrap(),
            ubiscrap(),
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
        connsafe.execute("PRAGMA journal_mode=WAL")
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
            chk.execute("INSERT INTO checks(platform) VALUES (?)", ("Ubisoft",))

        ####################################################################
        chk.execute("INSERT OR IGNORE INTO checks(platform) VALUES (?)", ("Old",))
        chk.execute("INSERT OR IGNORE INTO checks(platform) VALUES (?)", ("Ubisoft",))
        ####################################################################

        conncheck.commit()
        conncheck.close()
        conncheck = None

        timerpth = str(dr() / "timer.db")
        conntmr = connect(timerpth)
        gamespth = str(dr() / "games.db")
        conngmz = connect(gamespth, timeout = 10)
        conngmz.execute("PRAGMA journal_mode=WAL")

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
            new BOOLEAN NOT NULL DEFAULT TRUE
        )
        """)

        ##############################################################################
        try:
            gmz.execute("ALTER TABLE games ADD COLUMN new BOOLEAN NOT NULL DEFAULT TRUE")
        except OperationalError:
            pass
        try:
            gmz.execute("ALTER TABLE games DROP COLUMN seen")
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
                    pause = timedelta(hours=uniform(2, 6))
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

                    if syst == "Darwin" and (Path.home() / ".Trash" / "Gamzy.app").exists() and not Path("/Applications/Gamzy.app").exists():
                        deleteshit(connsafe, conntmr, conngmz)

                    sleep(uniform(30, 60))


            except Exception as e:
                print(f"\033[1;91m ERROR: \033[0m {e}")
                print("")
                safe.execute("UPDATE safety SET safe = ?", (True,))
                connsafe.commit()
                tmr.execute("UPDATE timer SET nextupdate = ?", (now + uniform(600, 900),))
                conntmr.commit()

    except Exception as e:
        for conn in [connsafe, conntmr, conngmz]:
            if conn is not None:
                conn.close()
        print(f"\033[1;91m ERROR: \033[0;91m Main script FAILED \033[0m {e}")

if __name__ == "__main__":
    main()