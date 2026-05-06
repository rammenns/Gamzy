from sys import argv, exit
from sqlite3 import connect
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QScrollArea
from PyQt5.QtGui import QIcon, QPixmap, QFontDatabase, QFont
from PyQt5.QtCore import Qt, QTimer
from webbrowser import open_new_tab

class gamUI(QWidget):
    def __init__(self, link, image, name, platform, font):
        super().__init__()

        self.setObjectName("FreeGam")
        self.link = link
        self.setFixedHeight(120)
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
        platformmap = QPixmap(platform)
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
        self.setFixedSize(900, 415)
        self.move(510, 350)
        self.setWindowIcon(QIcon("gamzicon.png"))
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

        namefont = QFontDatabase.addApplicationFont("Minecraftia-Regular.ttf")
        fontfam = QFontDatabase.applicationFontFamilies(namefont)
        if fontfam:
            self.basefont = QFont(fontfam[0], 10)
        else:
            self.basefont = QFont("Arial", 10)

        p = self.creategamz()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.creategamz)

        if p:
            self.timer.start(300000)
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

        conn = connect("games.db", timeout = 10)
        cursor = conn.cursor()

        cursor.execute("SELECT link, image, name, platform FROM games")
        rows = cursor.fetchall()
        for link, image, name, platform in rows:
            card = gamUI(link, image, name, platform, self.basefont)
            self.scrolyout.addWidget(card)

        conn.close()

        return bool(rows)


def main():
    app = QApplication(argv)
    window = MainWindow()
    window.show()
    exit(app.exec_())

if __name__ == "__main__":
    main()
