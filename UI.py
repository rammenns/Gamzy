import sys
from sqlite3 import connect
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QScrollArea, QPushButton, QProgressBar
from PyQt5.QtGui import QIcon, QPixmap, QFontDatabase, QFont
from PyQt5.QtCore import Qt, QTimer
from webbrowser import open_new_tab
from requests import get
import subprocess
import os
from ctypes import windll
import tempfile

def pathfind(f):
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, f)

def dr():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def updatepth():
    return os.path.join(tempfile.gettempdir(), "update.exe")

class updatebutton(QPushButton):
    def __init__(self, font, newver):
        super().__init__()

        self.setObjectName("updatebutton")
        self.setText(f"Version {newver} available! Click to install.")
        self.setFixedHeight(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFont(font)
        self.progress = QProgressBar(self)
        self.progress.setGeometry(162, 75, 650, 25)
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

            try:
                os.remove(updatepth())
            except FileNotFoundError:
                pass
            except PermissionError:
                pass

            url = get("https://api.github.com/repos/rammenns/FreeGamz/releases/latest", timeout=5)
            if url.status_code != 200:
                self.setText("Update failed :( Try again")
                self.setEnabled(True)
                return

            new = url.json()
            downl= None

            for asset in new['assets']:
                if asset["name"].endswith(".exe"):
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

            with open(updatepth(), "wb") as f:
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

            safepth = os.path.join(dr(), "safe.db")
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
                updatepth(),
                "/VERYSILENT /NORESTART",
                None,
                1
            )
            if permission <= 32:
                self.setText("Update cancelled :( Try again?")
                self.progress.hide()
                self.setEnabled(True)
                subprocess.Popen(["GamzScript.exe"])
                return

            QApplication.quit()

        except:
            self.setText("Update failed :( Try again")
            self.progress.hide()
            self.setEnabled(True)
            return

class gamUI(QWidget):
    def __init__(self, link, image, name, platform, font):
        super().__init__()

        self.setObjectName("FreeGam")
        self.link = link
        self.setFixedHeight(145)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        datalayout = QVBoxLayout()

        self.imglabel = QLabel(self)
        imagemap = QPixmap(image)
        scale = imagemap.scaledToHeight(120, Qt.SmoothTransformation)
        self.imglabel.setPixmap(scale)

        self.namelabel = QLabel(name)
        self.namelabel.setFont(font)

        platformlabel = QLabel(self)
        platformmap = QPixmap(pathfind(platform))
        scale = platformmap.scaledToHeight(50, Qt.SmoothTransformation)
        platformlabel.setPixmap(scale)

        datalayout.addWidget(self.namelabel)
        datalayout.addWidget(platformlabel)

        layout.addWidget(self.imglabel)
        layout.addLayout(datalayout)

        layout.addStretch()

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

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            open_new_tab(self.link)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FreeGamz")
        self.setFixedSize(950, 415)
        self.move(510, 350)
        self.setWindowIcon(QIcon(pathfind("gamzicon.png")))
        self.setObjectName("window")

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

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

        namefont = QFontDatabase.addApplicationFont(pathfind("Minecraftia-Regular.ttf"))
        fontfam = QFontDatabase.applicationFontFamilies(namefont)
        if fontfam:
            self.basefont = QFont(fontfam[0], 10)
        else:
            self.basefont = QFont("Arial", 10)

        p = self.creategamz()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.creategamz)

        if p:
            self.timer.start(3600000)
        else:
            self.timer.start(5000)

        self.setStyleSheet ("""
            #window {background-color: #424242;}
        """)

        scrollgamz.setStyleSheet("background-color: #424242;")

    def creategamz(self):

        while self.scrolyout.count():
            item = self.scrolyout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "FreeGamz"
        }
        url = get("https://api.github.com/repos/rammenns/FreeGamz/releases/latest",headers = headers, timeout=5)
        if url.status_code == 200:
            ver = url.json()
            if ver["tag_name"] != "1.3.1":
                self.scrolyout.addWidget(updatebutton(self.basefont, ver["tag_name"]))

        conn = None
        cursor = None
        try:
            gamespth = os.path.join(dr(), "games.db")
            conn = connect(gamespth, timeout = 10)
            cursor = conn.cursor()
        except:
            return False

        try:
            cursor.execute("SELECT link, image, name, platform FROM games")
            rows = cursor.fetchall()
        except:
            rows = []

        for link, image, name, platform in rows:
            card = gamUI(link, image, name, platform, self.basefont)
            self.scrolyout.addWidget(card)

        conn.close()

        return bool(rows)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
