from sqlite3 import connect
from requests import get
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from random import uniform
from time import sleep
import os
from os.path import exists
from winotify import Notification, audio
import sys


def mainscript(gmz, conngmz):

    try:

        print("\033[1m Running script \033[0m")
        print("")

        links = []
        names = []
        imgs = []
        platforms = []
        fail = []

        def insertnremove(links, names, imgs, platforms):

            print("\033[1m Attempting to update database: \033[0m")
            print("")

            if len(fail) == 3:

                print("Database update   \033[91m FAILED \033[0m")
                print("")
                return

            else:

                print("\033[1m Database won't update: \033[0m")
                print("")
                for fails in fail:
                    match fails:
                        case "steamlogo.png":
                            print("Steam")
                        case "epiclogo.png":
                            print("EpicGames")
                        case _:
                            print("GOG")
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

            added = False
            for test in range(len(links)):
                gmz.execute(
                    "INSERT OR IGNORE INTO games (link, name, image, platform) VALUES (?, ?, ?, ?)",
                    (links[test], names[test], imgs[test], platforms[test])
                )
                if gmz.rowcount > 0:
                    added = True
            conngmz.commit()

            if added:
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
                notif.set_audio(audio.Reminder, loop=False)
                notif.show()

            folder = "gamzimgs/"

            gmz.execute("SELECT image FROM games")
            dbimgs = {row[0] for row in gmz.fetchall()}

            for file in os.listdir(folder):
                file_path = os.path.join(folder, file)

                if file_path not in dbimgs and file not in {"steamlogo.png", "epiclogo.png", "goglogo.png"}:
                    os.remove(file_path)

            print("Database updated   \033[92m SUCCESS \033[0m")
            print("")


        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

        #Steam Search

        print("\033[1m Requesting Steam URL: \033[0m")

        try:

            response = get("https://store.steampowered.com/search?maxprice=free&supportedlang=english&specials=1&ndl=1", headers=headers, timeout = 5)

            print("Steam request      \033[92m SUCCESS \033[0m")

            if response.status_code == 200:

                soup = BeautifulSoup(response.text,'html.parser')

                for gam in soup.find_all('a', class_="search_result_row ds_collapse_flag"):

                    links.append(gam['href'])
                    names.append(gam['href'].split('/')[-2])
                    gamm = gam['href']

                    try:
                        gam = gam.find('div', class_= "search_capsule")
                        gam = gam.find('img')
                        url = gam.get('src')
                        file = f"gamzimgs/{gamm.split('/')[4]}.jpg"
                        if not exists(file):
                            gamimg = get(url, timeout = 5).content
                            with open(file, "wb") as f:
                                f.write(gamimg)
                        imgs.append(file)
                    except:
                        imgs.append("steamlogo.png")

                    platforms.append("steamlogo.png")

            print("Database insertion \033[92m SUCCESS \033[0m")

        except Exception as e:

            fail.append("steamlogo.png")
            print(f"Steam scrapping \033[91m FAILED \033[0m {e}")


        print("")

        #GOG Search

        print("\033[1m Requesting GOG URL: \033[0m")

        try:

            response = get("https://www.gog.com/en/", headers=headers, timeout = 5)

            print("GOG request        \033[92m SUCCESS \033[0m")

            if response.status_code == 200:

                soup = BeautifulSoup(response.text,'html.parser')

                for link in soup.find_all('div', class_="giveaway ng-star-inserted"):

                    sure = True
                    if link.find('a', class_="giveaway__overlay-link"):
                        gam = link.find('a', class_="giveaway__overlay-link")
                        links.append(gam['href'])

                        gam = gam.get('href')
                        gam = gam.rstrip('/').split('/')[-1]
                        names.append(gam.replace('_', ' ').title())
                        gamnam = gam
                    else:
                        sure = False

                    if sure:
                        try:
                            gam = link.find('div', class_="giveaway__image")
                            gam = gam.find('store-picture')
                            gam = gam.find('picture')
                            gam = gam.find('source')
                            url = gam['srcset'].split(", ")[1].rsplit(" ", 1)[0]
                            file = f"gamzimgs/{gamnam}.webp"
                            if not exists(file):
                                gamimg = get(url, timeout = 5).content
                                with open(file, "wb") as f:
                                    f.write(gamimg)
                            imgs.append(file)
                        except Exception as e:
                            print(e)
                            imgs.append("goglogo.png")

                        platforms.append("goglogo.png")

            print("Database insertion \033[92m SUCCESS \033[0m")

        except Exception as e:

            fail.append("goglogo.png")
            print(f"GOG scrapping \033[91m FAILED \033[0m {e}")


        print("")


        #Epic Search

        print("\033[1m Requesting EpicGames URL: \033[0m")

        try:

            response = get("https://store-site-backend-static-ipv4.ak.epicgames.com/freeGamesPromotions?locale=en-US&country=RO&allowCountries=RO", headers=headers, timeout = 5)

            print("EpicGames request  \033[92m SUCCESS \033[0m")

            if response.status_code == 200:

                data = response.json()

                for gam in data["data"]["Catalog"]["searchStore"]["elements"]:
                    if gam["isCodeRedemptionOnly"] == True and gam["effectiveDate"]:
                        offertime = datetime.strptime(gam["effectiveDate"], "%Y-%m-%dT%H:%M:%S.%fZ")
                        offertime = offertime.replace(tzinfo=timezone.utc)
                        now = datetime.now(timezone.utc)
                        if offertime <= now:
                            links.append(f"https://store.epicgames.com/en-US/p/{gam['productSlug']}")
                            names.append(gam["title"])
                            url = gam["keyImages"][0]["url"]
                            file = f"gamzimgs/{gam['id']}.jpg"
                            if not exists(file):
                                gamimg = get(url, timeout=5).content
                                with open(file, "wb") as f:
                                    f.write(gamimg)
                            imgs.append(file)
                            platforms.append("epiclogo.png")

            print("Database insertion \033[92m SUCCESS \033[0m")

        except Exception as e:

            fail.append("epiclogo.png")
            print(f"EpicGames scrapping \033[91m FAILED \033[0m {e}")

        print("")

        insertnremove(links, names, imgs, platforms)

        return True

    except Exception as e:

        print(f"\033[1;91m ERROR: \033[0;91m script FAILED on running \033[0m {e}")
        print("")

        return False


def main():

    print("\033[1m Running: \033[0m")
    print("")

    try:
        connsafe = connect("safe.db")
        safe = connsafe.cursor()
        safe.execute("CREATE TABLE IF NOT EXISTS safety (safe BOOLEAN)")
        safe.execute("SELECT safe FROM safety")
        rowz = safe.fetchone()
        if rowz is None:
            safe.execute("INSERT INTO safety VALUES (?)", (False,))
        else:
            safe.execute("UPDATE safety SET safe = ?", (False,))
        connsafe.commit()

        conntmr = connect("timer.db")
        conngmz = connect("games.db", timeout = 10)

        if not os.path.exists("gamzimgs"):
            os.makedirs("gamzimgs")
            print("\033[1m Folder created \033[0m")
            print("")

        tmr = conntmr.cursor()
        gmz = conngmz.cursor()

        #tmr.execute("DROP TABLE IF EXISTS timer")
        tmr.execute("CREATE TABLE IF NOT EXISTS timer (nextupdate REAL)")
        conntmr.commit()

        #gmz.execute("DROP TABLE IF EXISTS games")
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

                    if mainscript(gmz, conngmz):

                        counting = 1
                        gmz.execute("SELECT link, image, name, platform FROM games")
                        for link, image, name, platform in gmz.fetchall():
                            print(f"{counting}. {link} {image} {name} {platform}")
                            counting += 1

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
        print("\033[1;91m ERROR: \033[0;91m Main script FAILED \033[0m {e}")

if __name__ == "__main__":
    main()
