from sqlite3 import connect
from requests import get, Session
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from random import uniform
from time import sleep
import os
from os.path import exists
from winotify import Notification, audio
import sys

def dr():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def namecut(nam):
    inval = '<>:"/\\|?*'
    return ''.join(c for c in nam if c not in inval).strip()

def mainscript(gmz, conngmz):

    try:

        print("\033[1m Running script \033[0m")
        print("")

        links = []
        names = []
        imgs = []
        platforms = []
        fail = []

        def insertnremove():

            print("\033[1m Attempting to update database: \033[0m")
            print("")

            if len(fail) == 4:

                print("Database update   \033[91m FAILED \033[0m")
                print("")
                return

            elif fail:

                print("\033[1m Database won't update: \033[0m")
                print("")
                for fails in fail:
                    match fails:
                        case "steamlogo.png":
                            print("Steam")
                        case "epiclogo.png":
                            print("EpicGames")
                        case "goglogo.png":
                            print("GOG")
                        case _:
                            print("itch.io")
                    print("")

            if links:
                linklist = ",".join("?" for _ in links)
                if not fail:
                    gmz.execute(f"DELETE FROM games WHERE link NOT IN ({linklist})", links)
                else:
                    faillist = ",".join("?" for _ in fail)
                    gmz.execute(f"DELETE FROM games WHERE link NOT IN ({linklist}) AND platform NOT IN ({faillist})", links + fail)

            else:
                gmz.execute("DELETE FROM games")


            silencedones = []
            for test in range(len(links)):
                gmz.execute(
                    "INSERT OR IGNORE INTO games (link, name, image, platform) VALUES (?, ?, ?, ?)",
                    (links[test], names[test], imgs[test], platforms[test])
                )
                if gmz.rowcount > 0:
                    if platforms[test] not in silencedones:
                        silencedones.append(platforms[test])
            conngmz.commit()

            checkpth = None
            conncheck = None
            chk = None
            try:
                checkpth = os.path.join(dr(), "check.db")
                conncheck = connect(checkpth, timeout = 10)
                chk = conncheck.cursor()
            except:
                pass

            thisissil = None
            if chk:
                chk.execute(" SELECT 1 FROM sqlite_master WHERE type='table' AND name='checks' ")
                if chk.fetchone():

                    chk.execute("SELECT silence FROM checks")
                    rows = chk.fetchall()

                    thisissil = 0

                    if len(rows) == 4:
                        if "steamlogo.png" in silencedones:
                            thisissil += rows[0][0]
                        if "epiclogo.png" in silencedones:
                            thisissil += rows[1][0]
                        if "goglogo.png" in silencedones:
                            thisissil += rows[2][0]
                        if "itchlogo.png" in silencedones:
                            thisissil += rows[3][0]

                conncheck.close()


            if thisissil is None or thisissil < len(silencedones):
                if getattr(sys, "frozen", False):
                    base = sys._MEIPASS
                else:
                    base = os.path.dirname(os.path.abspath(__file__))

                notif = Notification(
                    app_id = "FreeGamz",
                    title = "🎮New Gamz!",
                    msg = "Hey! there are new games waiting for you!",
                    duration = "long",
                    icon = os.path.join(base,"AppLogo.png")
                )
                notif.add_actions(
                    label="Open",
                    launch=os.path.join(dr(), "FreeGamz.exe")
                )
                notif.set_audio(audio.Reminder, loop=False)
                notif.show()

            folder = os.path.join(dr(), "gamzimgs/")

            gmz.execute("SELECT image FROM games")
            dbimgs = {row[0] for row in gmz.fetchall()}

            for file in os.listdir(folder):
                file_path = os.path.join(folder, file)

                if file_path not in dbimgs and file not in {"steamlogo.png", "epiclogo.png", "goglogo.png", "itchlogo.png"}:
                    os.remove(file_path)

            print("Database updated    \033[92m SUCCESS \033[0m")
            print("")


        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0"
        }


        #Steam Search

        if True:

            print("\033[1m Requesting Steam URL: \033[0m")

            try:

                with Session() as steam:

                    steam.headers.update(headers)

                    response = steam.get("https://store.steampowered.com/search?maxprice=free&supportedlang=english&specials=1&ndl=1", timeout = 5)

                    print("Steam request       \033[92m SUCCESS \033[0m")

                    if response.status_code == 200:

                        soup = BeautifulSoup(response.text,'html.parser')

                        for gam in soup.find_all('a', class_="search_result_row ds_collapse_flag"):

                            price = gam
                            if price:
                                price = price.find('div', class_="responsive_search_name_combined")
                            if price:
                                price = price.find('div', class_="search_price_discount_combined responsive_secondrow")
                            if price:
                                price = price.find('div', class_="search_discount_and_price responsive_secondrow")
                            if price:
                                price = price.find('div', class_="discount_block search_discount_block")
                            if price:
                                price = price.find('div', class_="discount_prices generic_discount")
                            if price:
                                price = price.find('div', class_="discount_final_price")

                            if price and "0,00" in price.text:

                                links.append(gam['href'])
                                nam = gam['href'].split('/')[-2].replace('_', ' ')
                                names.append(nam)

                                try:
                                    gam = gam.find('div', class_= "search_capsule")
                                    if gam:
                                        gam = gam.find('img')
                                    url = gam.get('src')
                                    if not url:
                                        continue
                                    ext = os.path.splitext(url)[1].split("?")[0]
                                    file = os.path.join(dr(), f"gamzimgs/{namecut(nam)}{ext}")
                                    if not exists(file):
                                        gamimg = steam.get(url, timeout = 5).content
                                        with open(file, "wb") as f:
                                            f.write(gamimg)
                                    imgs.append(file)
                                except:
                                    imgs.append("steamlogo.png")

                                platforms.append("steamlogo.png")

                    print("Steam scrapping     \033[92m SUCCESS \033[0m")

            except Exception as e:

                fail.append("steamlogo.png")
                print(f"Steam scrapping \033[91m FAILED \033[0m {e}")


            print("")

        #GOG Search

        if True:

            print("\033[1m Requesting GOG URL: \033[0m")

            try:

                with Session() as gog:

                    gog.headers.update(headers)

                    response = gog.get("https://www.gog.com/en/", timeout=5)

                    print("GOG request         \033[92m SUCCESS \033[0m")

                    if response.status_code == 200:

                        soup = BeautifulSoup(response.text,'html.parser')

                        for link in soup.find_all('div', class_="giveaway ng-star-inserted"):

                            sure = True
                            if link.find('a', class_="giveaway__overlay-link"):
                                gam = link.find('a', class_="giveaway__overlay-link")
                                links.append(gam['href'])
                                gamn = gam
                                if gam:
                                    gam = gam.get('href')
                                if gam:
                                    gam = gam.rstrip('/').split('/')[-1]
                                if gam:
                                    nam = gam.replace('_', ' ').title()
                                names.append(nam)
                                gam = gamn.find('store-picture')
                                if gam:
                                    gam = gam.find('picture')
                                if gam:
                                    gam = gam.find('source')
                                url = gam['srcset'].split(", ")[1].rsplit(" ", 1)[0]
                                if not url:
                                    continue
                                ext = os.path.splitext(url)[1].split("?")[0]
                                file = os.path.join(dr(), f"gamzimgs/{namecut(nam)}{ext}")
                                if not exists(file):
                                    gamimg = gog.get(url, timeout = 5).content
                                    with open(file, "wb") as f:
                                        f.write(gamimg)
                                imgs.append(file)

                                platforms.append("goglogo.png")

                print("GOG scrapping       \033[92m SUCCESS \033[0m")

            except Exception as e:

                fail.append("goglogo.png")
                print(f"GOG scrapping \033[91m FAILED \033[0m {e}")


            print("")


        #Epic Search

        if True:

            print("\033[1m Requesting EpicGames URL: \033[0m")

            try:

                with Session() as epic:

                    headers = {
                        "Accept": "application/json, text/plain, */*",
                        "Accept-Encoding": "gzip, deflate, br, zstd",
                        "Accept-Language": "en-US,en;q=0.9",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0"
                    }

                    epic.headers.update(headers)

                    response = epic.get("https://store.epicgames.com/graphql?operationName=searchStoreQuery&variables={%22allowCountries%22:%22RO%22,%22category%22:%22games/edition/base|games/edition|bundles/games|addons%22,%22count%22:40,%22country%22:%22RO%22,%22effectiveDate%22:%22[,2026-06-23T13:14:01.462Z]%22,%22keywords%22:%22%22,%22locale%22:%22en-US%22,%22onSale%22:true,%22sortBy%22:%22currentPrice%22,%22sortDir%22:%22ASC%22,%22tag%22:%22%22,%22withPrice%22:true}&extensions={%22persistedQuery%22:{%22version%22:1,%22sha256Hash%22:%2229d49ab31d438cd90be2d554d2d54704951e4223a8fcd290fcf68308841a1979%22}}", timeout = 5)

                    print("EpicGames request   \033[92m SUCCESS \033[0m")

                    if response.status_code == 200:

                        data = response.json()

                        for gam in data["data"]["Catalog"]["searchStore"]["elements"]:

                            if gam["price"]:
                                gamn = gam["price"]
                                if gamn["totalPrice"]:
                                    gamn = gamn["totalPrice"]
                                    if gamn["discountPrice"] == gamn["voucherDiscount"] and gamn["originalPrice"] == gamn["discount"]:
                                        if gam["catalogNs"]:
                                            gamn = gam["catalogNs"]
                                            if gamn["mappings"][0]:
                                                gamn = gamn["mappings"][0]
                                                if gamn["pageSlug"]:
                                                    links.append(f"https://store.epicgames.com/en-US/p/{gamn['pageSlug']}")
                                                    if gam["title"]:
                                                        nam = gam["title"]
                                                        names.append(nam)
                                                        if gam["keyImages"][0]["url"]:
                                                            url = gam["keyImages"][0]["url"]
                                                            ext = os.path.splitext(url)[1].split("?")[0]
                                                            if not ext:
                                                                ext = ".png"
                                                            file = os.path.join(dr(), f"gamzimgs/{namecut(nam)}{ext}")
                                                            if not exists(file):
                                                                gamimg = epic.get(url, timeout=5).content
                                                                with open(file, "wb") as f:
                                                                    f.write(gamimg)
                                                            imgs.append(file)
                                                            platforms.append("epiclogo.png")
                                    else:
                                        break

                    print("EpicGames scrapping \033[92m SUCCESS \033[0m")

            except Exception as e:

                fail.append("epiclogo.png")
                print(f"EpicGames scrapping \033[91m FAILED \033[0m {e}")

            print("")


        #itch.io search

        if True:

            print("\033[1m Requesting itch.io URL: \033[0m")

            try:

                with Session() as itch:

                    headers = {
                        "Accept": "*/*",
                        "Accept-Encoding": "gzip, deflate, br, zstd",
                        "Accept-Language": "en-US,en;q=0.9",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0",
                        "X-Requested-With": "XMLHttpRequest"
                    }

                    itch.headers.update(headers)

                    p = 1

                    response = itch.get(f"https://itch.io/games/on-sale?page={p}&format=json", timeout = 5)

                    data = response.json()
                    soup = BeautifulSoup(data["content"], "html.parser")

                    if response.status_code == 200:

                        print("itch.io request     \033[92m SUCCESS \033[0m")

                        while data["content"]:

                            if response.status_code == 200:

                                for gam in soup.find_all('div', class_="game_cell"):

                                    if gam:
                                        gamn = gam.find('div', class_="game_thumb")
                                        gam = gam.find('div', class_="game_cell_data")
                                    if gam:
                                        gam = gam.find('div', class_="game_title")
                                    if gam:
                                        nam = gam.find('a' , class_="title game_link").text
                                        gam = gam.find('a', class_="price_tag meta_tag sale")
                                    if gam:
                                        price = gam.find('div', class_="price_value")
                                        sale = gam.find('div', class_="sale_tag")

                                    if (price and sale and price.text == "$0" and sale.text == "-100%"):
                                        if gamn:
                                            gamn = gamn.find('a', class_="thumb_link game_link")
                                        links.append(gamn['href'])
                                        names.append(nam)
                                        if gamn:
                                            gamn = gamn.find('img', class_="lazy_loaded")
                                        url = gamn.get("data-lazy_src")
                                        if not url:
                                            continue
                                        ext = os.path.splitext(url)[1].split("?")[0]
                                        file = os.path.join(dr(), f"gamzimgs/{namecut(nam)}{ext}")
                                        if not exists(file):
                                            gamimg = itch.get(url, timeout=5).content
                                            with open(file, "wb") as f:
                                                f.write(gamimg)
                                        imgs.append(file)
                                        platforms.append("itchlogo.png")

                            sleep(uniform(0.3, 0.8))
                            p += 1
                            response = itch.get(f"https://itch.io/games/on-sale?page={p}&format=json", timeout=5)
                            data = response.json()
                            soup = BeautifulSoup(data["content"], "html.parser")

                    print("itch.io scrapping   \033[92m SUCCESS \033[0m")

            except Exception as e:
                fail.append("itchlogo.png")
                print(f"itch.io scrapping   \033[91m FAILED \033[0m {e}")

            print("")

        insertnremove(links, names, imgs, platforms, fail)

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

    try:
        safepth = os.path.join(dr(), "safe.db")
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

        timerpth = os.path.join(dr(), "timer.db")
        conntmr = connect(timerpth)
        gamespth = os.path.join(dr(), "games.db")
        conngmz = connect(gamespth, timeout = 10)

        gimgpth = os.path.join(dr(), "gamzimgs")
        if not os.path.exists(gimgpth):
            os.makedirs(gimgpth)
            print("\033[1m Folder created \033[0m")
            print("")

        tmr = conntmr.cursor()
        gmz = conngmz.cursor()

        tmr.execute("CREATE TABLE IF NOT EXISTS timer (nextupdate REAL)")
        conntmr.commit()

        gmz.execute("""
        CREATE TABLE IF NOT EXISTS games(
            link TEXT UNIQUE PRIMARY KEY,
            image TEXT,
            name TEXT,
            platform TEXT
        )
        """)
        conngmz.commit()

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

                get("https://1.1.1.1", timeout = 5)

                if now >= row[0]:

                    try:

                        conngmz = connect(gamespth, timeout=10)
                        gmz = conngmz.cursor()

                        if mainscript(gmz, conngmz):

                            counting = 1
                            gmz.execute("SELECT link, image, name, platform FROM games")
                            for link, image, name, platform in gmz.fetchall():
                                print(f"{counting}. {link} {image} {name} {platform}")
                                counting += 1

                    finally:

                        conngmz.close()

                    pause = timedelta(hours=uniform(12, 24))
                    tmr.execute("UPDATE timer SET nextupdate = ?", (now + pause.total_seconds(),))
                    conntmr.commit()
                    tmr.execute("SELECT nextupdate FROM timer")
                    row = tmr.fetchone()

                if row[0] - now > 0:
                    print(" Entering sleep")
                    safe.execute("UPDATE safety SET safe = ?", (True,))
                    connsafe.commit()
                    sleep(row[0] - now)
                else:
                    print(" Entering quick sleep")
                    safe.execute("UPDATE safety SET safe = ?", (True,))
                    connsafe.commit()
                    sleep(30)
            except Exception as e:
                print(f"\033[1;91m ERROR: \033[0m {e}")
                print("")
                safe.execute("UPDATE safety SET safe = ?", (True,))
                connsafe.commit()
                sleep(600)

    except Exception as e:
        for conn in [connsafe, conntmr, conngmz]:
            try:
                conn.close()
            except:
                pass
        print(f"\033[1;91m ERROR: \033[0;91m Main script FAILED \033[0m {e}")

if __name__ == "__main__":
    main()
