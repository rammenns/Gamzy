import sys
from subprocess import Popen
import psutil
from socket import socket, AF_INET, SOCK_STREAM, error
from PyQt5.QtWidgets import QApplication
from UI import MainWindow
import platform
from pathlib import Path

oneinstance = None

def dr():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

def GamzScript():

    syst = platform.system()
    if syst == "Windows":
        return "GamzScript.exe"
    elif syst == "Darwin" or syst == "Linux":
        return "GamzScript"

def uirun():
    global oneinstance
    oneinstance = socket(AF_INET, SOCK_STREAM)
    try:
        oneinstance.bind(("127.0.0.1", 65432))
        return False
    except error:
        return True

def scriptrun():

    for p in psutil.process_iter(['name']):
        if p.info['name'] == GamzScript():
            return True

    return False

def main():
    app = QApplication(sys.argv)

    if uirun():
        return

    if not scriptrun():
        Popen([str(dr() / GamzScript())])

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()