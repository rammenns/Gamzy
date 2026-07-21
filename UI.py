import sys
from sqlite3 import connect
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QScrollArea, QPushButton, QProgressBar, QCheckBox, QToolButton, QMenu, QWidgetAction, QMessageBox
from PyQt5.QtGui import QIcon, QPixmap, QFontDatabase, QFont, QGuiApplication, QCursor
from PyQt5.QtCore import Qt, QTimer
from webbrowser import open_new_tab
from requests import get
import subprocess
from pathlib import Path
import tempfile
import os
import platform
syst = platform.system()
if syst == "Windows":
    from ctypes import windll
elif syst not in {"Darwin", "Linux"}:
    app = QApplication(sys.argv)
    QMessageBox.critical(
        None,
        "Gamzy",
        f"Unsupported operating system: {syst}\n\nBut I can fix this if you ask nicely :3"
    )
    sys.exit(1)

def pathfind(f):
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent
    return base / f

def dr():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

def updatepth():
    if syst == "Windows":
        return Path(tempfile.gettempdir()) / "update.exe"
    elif syst == "Darwin":
        return Path(tempfile.gettempdir()) / "update.app"

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

        try:

            if syst != "Linux":
                try:
                    updatepth().unlink()
                except FileNotFoundError:
                    pass
                except PermissionError:
                    pass

            url = get("https://api.github.com/repos/rammenns/Gamzy/releases/latest", timeout=5)
            if url.status_code != 200:
                self.setText("Connection lost :( Try again")
                self.setEnabled(True)
                return

            new = url.json()
            downl= None

            for asset in new['assets']:
                if (syst == "Windows" and asset["name"].endswith(".exe")) or (syst == "Darwin" and asset["name"].endswith(".dmg")) or (syst == "Linux" and asset["name"].endswith(".AppImage")):
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

            elif syst == "Linux":
                old = Path(os.environ["APPIMAGE"])
                scriptpth = old.with_name("Linux Gamzy.AppImage")
                shellpth = old.with_name("update.sh")

            with open(scriptpth, "wb") as f:
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

            safepth = str(dr() / "safe.db")
            connsafe = connect(safepth, timeout=10)
            safe = connsafe.cursor()
            safe.execute("SELECT safe FROM safety")
            row = safe.fetchone()
            if not row or not row[0]:
                connsafe.close()
                self.setText("Woops, small error :( Try again in a few seconds")
                self.progress.hide()
                self.setEnabled(True)
                return

            connsafe.close()

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
                    self.setText("Update canceled :( Try again?")
                    self.progress.hide()
                    self.setEnabled(True)
                    subprocess.Popen([str(dr() / "GamzScript.exe")])
                    return

            elif syst == "Darwin":

                subprocess.run(
                    [
                        "pkill",
                        "-f",
                        "GamzScript"
                    ],
                    capture_output=True
                )

                permission = subprocess.run(
                    [
                        "osascript",
                        "-e",
                        f'do shell script "{str(updatepth())} --silent" with administrator privileges'
                    ],
                    capture_output=True
                )
                if permission.returncode != 0:
                    self.setText("Update canceled :( Try again")
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

                rm -f "{old}"
                mv "{scriptpth}" "{old}"

                chmod +x "{old}"

                exec "{old}"
                """
                with open(shellpth, "w") as f:
                    f.write(script)

                subprocess.run(["chmod", "+x", str(shellpth)])

                subprocess.Popen(["pkexec", str(shellpth)])

            QApplication.quit()

        except:
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
        newlayout = QVBoxLayout()

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
        self.setWindowIcon(QIcon(str(pathfind("AppLogo.png"))))
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
            checkpth = str(dr() / "check.db")
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

            chk.execute("SELECT platform, hide, silence FROM checks")
            rows = chk.fetchall()

        ####################################################################
        try:
            chk.execute("INSERT INTO checks(platform) VALUES (?)", ("Old",))
            conncheck.commit()
            chk.execute("SELECT platform, hide, silence FROM checks")
            rows = chk.fetchall()
        except:
            pass
        ####################################################################

        conncheck.commit()

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

        p = self.creategamz(updt)

        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: self.creategamz(True))

        if p:
            self.timer.start(3600000)
        else:
            self.timer.start(5000)

        self.applyScale()

        scrollgamz.setStyleSheet("background-color: #424242;")

        if syst == "Linux":
            appimage = os.environ.get("APPIMAGE")
            if appimage:
                Path(appimage).with_name("update.sh").unlink(missing_ok=True)


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

        silitch = QCheckBox("itch.io")
        silitch.setChecked(presets.get("itch.io", {}).get("silence", False))
        itchsil_action = QWidgetAction(self)
        itchsil_action.setDefaultWidget(silitch)
        self.silmenu.addAction(itchsil_action)
        silitch.toggled.connect(lambda checked: self.togg("itch.io", False, checked))


    def togg(self, plat, wh, ch):
        checkpth = str(dr() / "check.db")
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
                url = get("https://api.github.com/repos/rammenns/Gamzy/releases/latest",headers = headers, timeout = 5)
                url.raise_for_status()
                ver = url.json()
                if ver["tag_name"] != "1.9":
                    tag_name = ver["tag_name"]
                    for asset in ver['assets']:
                        if (syst == "Windows" and asset["name"].endswith(".exe")) or (syst == "Darwin" and asset["name"].endswith(".dmg")) or (syst == "Linux" and asset["name"].endswith(".AppImage")):
                            self.scrolyout.addWidget(updatebutton(self.basefont, tag_name))
                            break
            except:
                pass

        checkpth = str(dr() / "check.db")
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


        conn = None
        cursor = None
        try:
            gamespth = str(dr() / "games.db")
            conn = connect(gamespth, timeout = 10)
            cursor = conn.cursor()
        except:
            return False

        try:
            cursor.execute("""
                SELECT link, image, name, platform, new FROM games
                ORDER BY CASE platform
                    WHEN 'goglogo.png' THEN 1
                    WHEN 'steamlogo.png' THEN 2
                    WHEN 'epiclogo.png' THEN 3
                    WHEN 'itchlogo.png' THEN 4
                END,
                new DESC,
                name
            """)
            rows = cursor.fetchall()
        except:
            rows = []


        for link, image, name, platform, new in rows:
            if len(name) > 43:
                name = name[:40] + "..."
            if oldhide and not new:
                continue
            if goghide and platform == "goglogo.png":
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

        try:
            conn = connect(gamespth, timeout=10)
            cursor = conn.cursor()

            cursor.execute("UPDATE games SET seen = ?", (True,))

            conn.close()
        except:
            pass


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()