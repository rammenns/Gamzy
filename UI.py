import platform
from PyQt5.QtWidgets import QApplication, QMessageBox
import sys
from pathlib import Path
syst = platform.system()
if syst == "Windows":
    from ctypes import windll
elif syst == "Linux":
    from shutil import which
elif syst == "Darwin":
    from PyQt5.QtCore import QSize
else:
    app = QApplication(sys.argv)
    QMessageBox.critical(
        None,
        "Gamzy",
        f"Unsupported operating system: {syst}\n\nBut I can fix this if you ask nicely :3"
    )
    sys.exit(1)
archit = platform.machine().lower()
if archit == "amd64": archit = "x86_64"
elif archit in ("aarch64", "arm64"): archit = "ARM64"
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QScrollArea, QPushButton, QProgressBar, QCheckBox, QToolButton, QMenu, QWidgetAction, QMessageBox
from PyQt5.QtGui import QIcon, QPixmap, QFontDatabase, QFont
from PyQt5.QtCore import Qt, QTimer
from webbrowser import open_new_tab
from requests import get
import subprocess
import tempfile
from sqlite3 import connect

def pathfind(f):
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent
    return base / f

def dbdr():
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

def dr():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

def updatepth():
    if syst == "Windows":
        return Path(tempfile.gettempdir()) / "update.exe"
    elif syst == "Darwin":
        return Path(tempfile.gettempdir()) / "update.dmg"
    return None

class updatebutton(QPushButton):
    def __init__(self, font, newver):
        super().__init__()

        self.setObjectName("updatebutton")
        self.setText(f"Version {newver} available! Click to install.")
        self.setFixedHeight(120)
        self.setFixedWidth(930)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFont(font)
        self.baseFont = QFont(font)
        self.progress = QProgressBar(self)
        self.progress.setGeometry(125, 75, 650, 25)
        self.progress.setTextVisible(False)
        self.progress.hide()

        if not getattr(sys, "frozen", False):
            self.setEnabled(False)

        self.setStyleSheet("""
            QPushButton{
                background-color: green;
                color: white;
                text-align: center;
                border: 2px solid white;
                border-radius: 5px;
            }
            QPushButton:hover{
                background-color: darkgreen;
            }
            QPushButton:disabled{
                background-color: darkgreen;
            }
            QProgressBar{
                background-color: darkgreen;
            }
            QProgressBar::chunk{
                background-color: white;
            }
        """)

        self.clicked.connect(self.update)

    def update(self):

        self.setEnabled(False)

        scriptpth = None
        shellpth = None

        if syst == "Darwin" and not Path("/Applications/Gamzy.app").exists():
            QMessageBox.information(
                self,
                "Function Denied",
                "Gamzy needs to be in the Applications folder"
            )
            return

        try:

            if syst != "Linux":
                try:
                    updatepth().unlink()
                except FileNotFoundError:
                    pass
                except PermissionError:
                    pass
            elif which("pkexec") is None:
                self.setText("pkexec is required for updates")
                self.setEnabled(True)
                return

            url = get("https://api.github.com/repos/rammenns/Gamzy/releases/latest", timeout=5)
            if url.status_code != 200:
                self.setText("Connection lost :( Try again")
                self.setEnabled(True)
                return

            new = url.json()
            downl= None

            for asset in new['assets']:
                if (syst == "Windows" and asset["name"].endswith(".exe")) or (syst == "Darwin" and asset["name"].endswith(".dmg")) or (syst == "Linux" and asset["name"].endswith(".tar.gz")):
                    downl = asset["browser_download_url"]
                    break

            if downl is None:
                self.setText("Update failed :( Try again")
                self.setEnabled(True)
                return

            file = get(downl, stream = True, timeout = 10)
            if file.status_code != 200:
                self.setText("Update failed :( Try again")
                self.setEnabled(True)
                return

            self.progress.show()
            total = int(file.headers.get("content-length", 0))
            downloaded = 0

            if syst == "Windows":
                scriptpth = updatepth()

            elif syst == "Darwin":
                scriptpth = updatepth()
                shellpth = dbdr() / "update.sh"

            elif syst == "Linux":
                scriptpth = dbdr() / "update.tar.gz"
                shellpth = dbdr() / "update.sh"

            with open(str(scriptpth), "wb") as f:
                for chunk in file.iter_content(8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total > 0:
                            percent = int(downloaded * 100 / total)
                            self.progress.setValue(percent)
                            self.setText(f"Updating... {percent}%")

                            QApplication.processEvents()

            self.progress.setValue(100)
            self.setText("Installing...")
            QApplication.processEvents()

            safepth = str(dbdr() / "safe.db")
            connsafe = connect(f"file:{safepth}?mode=ro", uri=True, timeout=10)
            safe = connsafe.cursor()
            safe.execute("SELECT safe FROM safety")
            row = safe.fetchone()
            if row:
                while not row[0]:
                    sleep(10)
                    try:
                        safe.execute("SELECT safe FROM safety")
                        row = safe.fetchone()
                    except:
                        pass
            else:
                connsafe.close()
                self.setText("Woops, small error :( Try again in a few seconds")
                self.progress.hide()
                self.setEnabled(True)
                return

            connsafe.close()

            safepth = None
            connsafe = None
            safe = None
            row = None

            if syst == "Windows":

                subprocess.run(
                    [
                        "taskkill",
                        "/F",
                        "/IM",
                        "GamzScript.exe"
                    ],
                    capture_output=True
                )

                permission = windll.shell32.ShellExecuteW(
                    None,
                    "runas",
                    scriptpth,
                    "/SILENT /NORESTART",
                    None,
                    1
                )
                if permission <= 32:
                    try:
                        updatepth().unlink()
                    except FileNotFoundError:
                        pass
                    except PermissionError:
                        pass
                    self.setText("Update canceled :( Try again?")
                    self.progress.hide()
                    self.setEnabled(True)
                    subprocess.Popen([str(dr() / "GamzScript.exe")])
                    return

            elif syst == "Darwin":

                check = subprocess.run(
                    [
                        "hdiutil",
                        "verify",
                        str(updatepth())
                    ],
                    capture_output=True
                )

                if check.returncode != 0:
                    self.setText("Update failed :( Try again?")
                    self.progress.hide()
                    self.setEnabled(True)
                    return

                subprocess.run(
                    [
                        "pkill",
                        "-f",
                        "GamzScript"
                    ],
                    capture_output=True
                )

                script = f"""#!/bin/sh
(
sleep 5

MOUNT="/tmp/GamzyUpdateMount"

mkdir -p "$MOUNT"

if ! hdiutil attach "{updatepth()}" -mountpoint "$MOUNT" -nobrowse; then
    exit 1
fi

rm -rf "/Applications/Gamzy.app"
if ! cp -R "$MOUNT/Gamzy.app" "/Applications/Gamzy.app"; then
    hdiutil detach "$MOUNT"
    exit 1
fi

hdiutil detach "$MOUNT"

rm -f "{updatepth()}"

open "/Applications/Gamzy.app"

) >/dev/null 2>&1 &

exit 0
"""
                with open(shellpth, "w") as f:
                    f.write(script)

                subprocess.run(["chmod", "+x", str(shellpth)])

                applescript = '''
on run argv
    do shell script quoted form of (item 1 of argv) with administrator privileges
end run
'''

                permission = subprocess.run(
                    [
                        "osascript",
                        "-e",
                        applescript,
                        str(shellpth)
                    ],
                    capture_output=True,
                    text=True
                )

                if permission.returncode != 0:
                    try:
                        updatepth().unlink()
                    except FileNotFoundError:
                        pass
                    except PermissionError:
                        pass
                    self.setText("Update canceled :( Try again?")
                    self.progress.hide()
                    self.setEnabled(True)
                    subprocess.Popen([str(dr() / "GamzScript")])
                    return

            elif syst == "Linux":

                subprocess.run(
                    [
                        "pkill",
                        "-f",
                        "GamzScript"
                    ],
                    capture_output=True
                )

                script = f"""#!/bin/sh
sleep 2

cd "{dr()}"

mkdir -p .update

tar -xzf update.tar.gz -C .update

cp -rf .update/Gamzy/* .

chmod +x Gamzy
chmod +x GamzScript
chmod +x "Create Shortcut.sh"

rm update.tar.gz
rm -rf .update

exec ./Gamzy
"""
                with open(shellpth, "w") as f:
                    f.write(script)

                subprocess.run(["chmod", "+x", str(shellpth)])

                permission = subprocess.run(["pkexec", str(shellpth)], capture_output = True, text = True)

                if permission.returncode != 0:
                    try:
                        scriptpth.unlink()
                    except FileNotFoundError:
                        pass
                    except PermissionError:
                        pass
                    self.setText("Update canceled :( Try again?")
                    self.progress.hide()
                    self.setEnabled(True)
                    subprocess.Popen([str(dr() / "GamzScript")])
                    return

            QApplication.quit()

        except Exception:
            self.setText("Update failed :( Try again")
            self.progress.hide()
            self.setEnabled(True)
            return

    def applyScaleAgain(self, dpi):

        font = QFont(self.baseFont)
        font.setPointSize(round(10 * (144 / dpi)))
        self.setFont(font)



class gamUI(QWidget):
    def __init__(self, link, image, name, platform, new, font, dpi):
        super().__init__()

        self.setObjectName("FreeGam")
        self.link = link
        self.setFixedHeight(145)
        self.setFixedWidth(930)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignVCenter)
        datalayout = QVBoxLayout()

        self.imglabel = QLabel(self)
        imagemap = QPixmap(image)
        scale = imagemap.scaledToHeight(120, Qt.SmoothTransformation)
        self.imglabel.setPixmap(scale)

        self.namelabel = QLabel(name)
        self.namelabel.setFont(font)
        self.namelabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.namelabel.setMinimumWidth(0)

        self.baseFont = QFont(font)
        self.baseFont.setPointSize(10)

        platformlabel = QLabel(self)
        platformmap = QPixmap(str(pathfind(platform)))
        scale = platformmap.scaledToHeight(50, Qt.SmoothTransformation)
        platformlabel.setPixmap(scale)

        self.newlabel = QLabel("NEW" if new else "")
        fuontus = QFont(font)
        fuontus.setPointSize(round(12 * (144 / dpi)))
        fuontus.setBold(True)
        self.newlabel.setFont(fuontus)
        self.newlabel.setFixedWidth(60)
        self.newlabel.setAlignment(Qt.AlignRight | Qt.AlignBottom)

        datalayout.addWidget(self.namelabel)
        datalayout.addWidget(platformlabel)

        layout.addWidget(self.imglabel)
        layout.addLayout(datalayout)
        layout.addStretch()
        layout.addWidget(
            self.newlabel,
            alignment=Qt.AlignRight | Qt.AlignBottom
        )

        self.setStyleSheet("""
            #FreeGam {
                background-color: lightgray;
                border-radius: 5px;
                border: 2px solid white;
            }
            #FreeGam:hover {background-color: white;}
        """)

        self.namelabel.setStyleSheet("background: transparent; color: black;")

        platformlabel.setStyleSheet("background: transparent;")

        self.newlabel.setStyleSheet("background: transparent; color: DeepSkyBlue;")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            open_new_tab(self.link)

    def applyScaleAgain(self, dpi):

        font = QFont(self.baseFont)
        font.setPointSize(round(10 * (144 / dpi)))

        self.namelabel.setFont(font)

        newfont = QFont(self.baseFont)
        newfont.setBold(True)
        newfont.setPointSize(round(12 * (144 / dpi)))

        self.newlabel.setFont(newfont)

class MainWindow(QMainWindow):
    def __init__(self, updt = True):
        super().__init__()

        self.currdpi = 144

        self.setWindowTitle("Gamzy")
        self.setFixedSize(1000, 415)
        self.move(510, 350)
        if syst != "Darwin":
            self.setWindowIcon(QIcon(str(pathfind("gamzylogo.png"))))
        self.setObjectName("window")

        central = QWidget()
        self.setCentralWidget(central)

        namefont = QFontDatabase.addApplicationFont(str(pathfind("Minecraftia-Regular.ttf")))
        fontfam = QFontDatabase.applicationFontFamilies(namefont)
        if fontfam:
            self.basefont = QFont(fontfam[0], 10)
        else:
            self.basefont = QFont("Arial", 10)

        layout = QVBoxLayout(central)

        checkpth = None
        conncheck = None
        try:
            checkpth = str(dbdr() / "check.db")
            conncheck = connect(checkpth, timeout = 180)
            chk = conncheck.cursor()
        except:
            return

        chk.execute("""
        CREATE TABLE IF NOT EXISTS checks(
            platform TEXT UNIQUE PRIMARY KEY,
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

        ##############################################################################
        chk.execute("INSERT OR IGNORE INTO checks(platform) VALUES (?)", ("Old",))
        chk.execute("INSERT OR IGNORE INTO checks(platform) VALUES (?)", ("Ubisoft",))
        ##############################################################################

        conncheck.commit()

        chk.execute("SELECT platform, hide, silence FROM checks")
        rows = chk.fetchall()

        if syst == "Darwin":
            if not Path("/Applications/Gamzy.app").exists():
                QMessageBox.critical(
                    None,
                    "Attention!",
                    "Move Gamzy into the Applications folder in order to function properly."
                )
            self.biutuon = QPushButton()
            self.biutuon.setIcon(QIcon(str(Path(sys.executable).parent.parent / "Resources" / "uninstall.png")))
            self.biutuon.setIconSize(QSize(36, 36))
            self.biutuon.setFixedSize(36, 36)
            self.biutuon.setStyleSheet("""
                QPushButton {
                    border: none;
                    background: transparent;
                }
            """)
            self.biutuon.clicked.connect(self.uninstallconfirm)
            delbut = QHBoxLayout()
            delbut.addWidget(self.biutuon)
            delbut.setAlignment(Qt.AlignRight)
            layout.addLayout(delbut)

        self.hidedropdown = QToolButton()
        self.hidedropdown.setText("Hide    >")

        self.sildropdown = QToolButton()
        self.sildropdown.setText("Silence  >")

        checks = QHBoxLayout()
        checks.addWidget(self.hidedropdown)
        checks.addWidget(self.sildropdown)
        layout.addLayout(checks)

        self.presets = {}

        for platform, hide, silence in rows:
            self.presets[platform] = {
                "hide": hide,
                "silence": silence
            }

        self.createmenus()

        conncheck.close()

        self.hidedropdown.setMenu(self.hidemenu)
        self.hidedropdown.setPopupMode(QToolButton.InstantPopup)

        self.sildropdown.setMenu(self.silmenu)
        self.sildropdown.setPopupMode(QToolButton.InstantPopup)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.NoFrame)

        scrollgamz = QWidget()
        self.scrolyout = QVBoxLayout(scrollgamz)
        self.scrolyout.setAlignment(Qt.AlignTop)

        scroll.setWidget(scrollgamz)
        layout.addWidget(scroll)

        self.storedgamz = []

        p = self.creategamz(updt)

        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: self.creategamz(True))

        if p:
            self.timer.start(3600000)
        else:
            self.timer.start(5000)

        self.applyScale()

        scrollgamz.setStyleSheet("background-color: #424242;")

    def uninstallconfirm(self):

        if Path("/Applications/Gamzy.app").exists():

            msg = QMessageBox(self)
            msg.setWindowTitle("Uninstall Gamzy")
            msg.setText("Do you want to uninstall Gamzy?")

            yes = msg.addButton("Yes", QMessageBox.YesRole)
            cancel = msg.addButton("Cancel", QMessageBox.NoRole)

            msg.exec_()

            if msg.clickedButton() == yes:
                source = Path(sys.executable).parent.parent / "Resources" / "uninstall.sh"
                uninstall = Path(tempfile.gettempdir()) / "gamzy-uninstall.sh"

                try:
                    uninstall.write_bytes(source.read_bytes())
                    subprocess.run(["chmod", "+x", str(uninstall)], check=True)
                    subprocess.Popen([str(uninstall)])
                    QApplication.quit()
                except Exception:
                    QMessageBox.critical(
                        self,
                        "Uninstall failed",
                        "Gamzy could not start the uninstall process. :("
                    )

        else:

            QMessageBox.information(
                self,
                "Function Denied",
                "Gamzy needs to be in the Applications folder"
            )

    def createmenus(self):

        presets = self.presets

        self.hidemenu = QMenu(self)

        self.hidemenu.aboutToShow.connect(lambda: self.hidedropdown.setText("Hide    v"))
        self.hidemenu.aboutToHide.connect(lambda: self.hidedropdown.setText("Hide    >"))

        hidesteam = QCheckBox("Steam")
        hidesteam.setChecked(presets.get("Steam", {}).get("hide", False))
        steamhide_action = QWidgetAction(self)
        steamhide_action.setDefaultWidget(hidesteam)
        self.hidemenu.addAction(steamhide_action)
        hidesteam.toggled.connect(lambda checked: self.togg("Steam", True, checked))

        hideepic = QCheckBox("Epic")
        hideepic.setChecked(presets.get("Epic", {}).get("hide", False))
        epichide_action = QWidgetAction(self)
        epichide_action.setDefaultWidget(hideepic)
        self.hidemenu.addAction(epichide_action)
        hideepic.toggled.connect(lambda checked: self.togg("Epic", True, checked))

        hidegog = QCheckBox("GOG")
        hidegog.setChecked(presets.get("GOG", {}).get("hide", False))
        goghide_action = QWidgetAction(self)
        goghide_action.setDefaultWidget(hidegog)
        self.hidemenu.addAction(goghide_action)
        hidegog.toggled.connect(lambda checked: self.togg("GOG", True, checked))

        hideubi = QCheckBox("Ubisoft")
        hideubi.setChecked(presets.get("Ubisoft", {}).get("hide", False))
        ubihide_action = QWidgetAction(self)
        ubihide_action.setDefaultWidget(hideubi)
        self.hidemenu.addAction(ubihide_action)
        hideubi.toggled.connect(lambda checked: self.togg("Ubisoft", True, checked))

        hideitch = QCheckBox("itch.io")
        hideitch.setChecked(presets.get("itch.io", {}).get("hide", False))
        itchhide_action = QWidgetAction(self)
        itchhide_action.setDefaultWidget(hideitch)
        self.hidemenu.addAction(itchhide_action)
        hideitch.toggled.connect(lambda checked: self.togg("itch.io", True, checked))

        hideolds = QCheckBox("Old")
        hideolds.setChecked(presets.get("Old", {}).get("hide", False))
        oldshide_action = QWidgetAction(self)
        oldshide_action.setDefaultWidget(hideolds)
        self.hidemenu.addAction(oldshide_action)
        hideolds.toggled.connect(lambda checked: self.togg("Old", True, checked))

        self.silmenu = QMenu(self)

        self.silmenu.aboutToShow.connect(lambda: self.sildropdown.setText("Silence  v"))
        self.silmenu.aboutToHide.connect(lambda: self.sildropdown.setText("Silence  >"))

        silsteam = QCheckBox("Steam")
        silsteam.setChecked(presets.get("Steam", {}).get("silence", False))
        steamsil_action = QWidgetAction(self)
        steamsil_action.setDefaultWidget(silsteam)
        self.silmenu.addAction(steamsil_action)
        silsteam.toggled.connect(lambda checked: self.togg("Steam", False, checked))

        silepic = QCheckBox("Epic")
        silepic.setChecked(presets.get("Epic", {}).get("silence", False))
        epicsil_action = QWidgetAction(self)
        epicsil_action.setDefaultWidget(silepic)
        self.silmenu.addAction(epicsil_action)
        silepic.toggled.connect(lambda checked: self.togg("Epic", False, checked))

        silgog = QCheckBox("GOG")
        silgog.setChecked(presets.get("GOG", {}).get("silence", False))
        gogsil_action = QWidgetAction(self)
        gogsil_action.setDefaultWidget(silgog)
        self.silmenu.addAction(gogsil_action)
        silgog.toggled.connect(lambda checked: self.togg("GOG", False, checked))

        silubi = QCheckBox("Ubisoft")
        silubi.setChecked(presets.get("Ubisoft", {}).get("silence", False))
        ubisil_action = QWidgetAction(self)
        ubisil_action.setDefaultWidget(silubi)
        self.silmenu.addAction(ubisil_action)
        silubi.toggled.connect(lambda checked: self.togg("Ubisoft", False, checked))

        silitch = QCheckBox("itch.io")
        silitch.setChecked(presets.get("itch.io", {}).get("silence", False))
        itchsil_action = QWidgetAction(self)
        itchsil_action.setDefaultWidget(silitch)
        self.silmenu.addAction(itchsil_action)
        silitch.toggled.connect(lambda checked: self.togg("itch.io", False, checked))


    def togg(self, plat, wh, ch):
        checkpth = str(dbdr() / "check.db")
        conncheck = connect(checkpth, timeout = 180)
        chk = conncheck.cursor()
        if wh:
            chk.execute("UPDATE checks SET hide = ? WHERE platform = ?", (ch, plat))
            self.presets[plat]["hide"] = ch
        else:
            chk.execute("UPDATE checks SET silence = ? WHERE platform = ?", (ch, plat))
            self.presets[plat]["silence"] = ch
        conncheck.commit()
        conncheck.close()

        if wh:
            self.creategamz(False)

    def creategamz(self, refr):

        readd = None
        while self.scrolyout.count():
            item = self.scrolyout.takeAt(0)
            widget = item.widget()
            if widget:
                if isinstance(widget, updatebutton):
                    readd = widget
                    continue
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
        if readd:
            self.scrolyout.addWidget(readd)

        if refr and readd is None:
            headers = {
                "Accept": "application/vnd.github+json",
                "User-Agent": "Gamzy"
            }
            try:
                url = get("https://api.github.com/repos/rammenns/Gamzy/releases", headers = headers, timeout = 5)
                url.raise_for_status()
                releases = url.json()
                upstop = False
                for ver in releases:
                    if upstop:
                        break
                    if ver["tag_name"] != "1.9":
                        if ver["draft"] or ver["prerelease"]:
                            continue
                        tag_name = ver["tag_name"]
                        for asset in ver['assets']:
                            if (
                                (
                                    (syst == "Windows" and asset["name"].endswith(".exe"))
                                    or
                                    (syst == "Darwin" and asset["name"].endswith(".dmg"))
                                    or
                                    (syst == "Linux" and asset["name"].endswith(".tar.gz"))
                                )
                                and
                                (archit in asset["name"])
                            ):
                                self.scrolyout.addWidget(updatebutton(self.basefont, tag_name))
                                upstop = True
                                break
                    else:
                        upstop = True
            except:
                pass

        checkpth = str(dbdr() / "check.db")
        conncheck = connect(checkpth, timeout = 180)
        chk = conncheck.cursor()

        chk.execute("SELECT hide FROM checks")
        rows = chk.fetchall()
        conncheck.close()

        sthide = rows[0][0]
        ephide = rows[1][0]
        goghide = rows[2][0]
        ithide = rows[3][0]
        oldhide = rows[4][0]
        ubihide = rows[5][0]


        conn = None
        cursor = None
        try:
            gamespth = str(dbdr() / "games.db")
            conn = connect(f"file:{gamespth}?mode=ro", uri=True, timeout = 10)
            cursor = conn.cursor()
        except:
            return False

        try:
            cursor.execute("""
                SELECT link, image, name, platform, new FROM games
                ORDER BY CASE platform
                    WHEN 'ubilogo.png' THEN 1
                    WHEN 'goglogo.png' THEN 2
                    WHEN 'steamlogo.png' THEN 3
                    WHEN 'epiclogo.png' THEN 4
                    WHEN 'itchlogo.png' THEN 5
                END,
                new DESC,
                name
            """)
            rows = cursor.fetchall()
        except:
            rows = []

        self.storedgamz = []

        for link, image, name, platform, new in rows:
            if len(name) > 43:
                name = name[:40] + "..."
            if oldhide and not new:
                continue
            if ubihide and platform == "ubilogo.png":
                continue
            elif goghide and platform == "goglogo.png":
                continue
            elif sthide and platform == "steamlogo.png":
                continue
            elif ephide and platform == "epiclogo.png":
                continue
            elif ithide and platform == "itchlogo.png":
                break
            font = QFont(self.basefont)
            font.setPointSize(self.uiscale(10))
            card = gamUI(link, image, name, platform, new, font, self.currdpi)
            self.scrolyout.addWidget(card)
            self.storedgamz.append(link)


        conn.close()

        return bool(rows)

    def uiscale(self, value):
        dpi = self.currdpi
        return round(value * (144 / dpi))

    def applyScale(self):

        tensize = self.uiscale(10)
        lvsize = self.uiscale(11)

        self.setStyleSheet(f"""
            #window {{background-color: #424242;}}

            QToolButton {{
                width: 140px;
                height: 40px;
                font-family: Minecraftia;
                font-size: {lvsize}pt;
                background-color: transparent;
                border: none;
                color: white;
            }}

            QToolButton:hover {{
                background-color: transparent;
                border: none;
                color: white;
            }}

            QToolButton::menu-indicator {{
                image: none;
            }}

            QCheckBox {{
                font-family: Minecraftia;
                font-size: {tensize}pt;
                margin-left: 10px;
            }}

            QCheckBox::indicator {{
                width: 24px;
                height: 24px;
            }}

            QMenu {{
                font-family: Minecraftia;
                font-size: {lvsize}pt;
                width: 140px;
            }}
        """)

        self.hidedropdown.adjustSize()
        self.sildropdown.adjustSize()

        self.centralWidget().layout().invalidate()
        self.centralWidget().layout().activate()

        for checkbox in self.findChildren(QCheckBox):
            checkbox.adjustSize()

        for menu in self.findChildren(QMenu):
            menu.adjustSize()

        self.centralWidget().repaint()


    def showEvent(self, event):

        super().showEvent(event)

        if not hasattr(self, "_screen_connected"):
            handle = self.windowHandle()
            if handle:
                self.currdpi = handle.screen().logicalDotsPerInch()

                self.applyScale()
                self.rescaleCards()

                self.updateGeometry()
                self.update()
                QApplication.processEvents()

                handle.screenChanged.connect(self.adaptscreen)
                self._screen_connected = True

    def adaptscreen(self, screen):

        newdpi = screen.logicalDotsPerInch()

        if newdpi == self.currdpi:
            return

        self.currdpi = newdpi

        QTimer.singleShot(0, self.finishScale)

    def finishScale(self):

        self.hidedropdown.setMenu(None)
        self.sildropdown.setMenu(None)

        self.hidemenu.deleteLater()
        self.silmenu.deleteLater()

        self.createmenus()

        self.hidedropdown.setMenu(self.hidemenu)
        self.sildropdown.setMenu(self.silmenu)

        self.applyScale()
        self.rescaleCards()

        self.updateGeometry()
        self.update()
        QApplication.processEvents()

    def rescaleCards(self):

        for card in self.findChildren(gamUI):
            card.applyScaleAgain(self.currdpi)

        for button in self.findChildren(updatebutton):
            button.applyScaleAgain(self.currdpi)

    def closeEvent(self, event):

        if not self.storedgamz: return

        safepth = str(dbdr() / "safe.db")
        connsafe = connect(f"file:{safepth}?mode=ro", uri=True, timeout=10)
        safe = connsafe.cursor()
        safe.execute("SELECT safe FROM safety")
        row = safe.fetchone()
        if row:
            while not row[0]:
                sleep(10)
                try:
                    safe.execute("SELECT safe FROM safety")
                    row = safe.fetchone()
                except:
                    pass
        else:
            connsafe.close()
            return
        connsafe.close()

        gamespth = str(dbdr() / "games.db")
        conn = connect(gamespth, timeout = 10)
        cursor = conn.cursor()

        pholder = ",".join("?" for _ in self.storedgamz)

        cursor.execute(f"UPDATE games SET new = ? WHERE link IN ({pholder})", (False, *self.storedgamz))
        conn.commit()

        conn.close()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
