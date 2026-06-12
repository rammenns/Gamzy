from sys import argv, exit
from subprocess import Popen
import psutil
from socket import socket, AF_INET, SOCK_STREAM, error
from PyQt5.QtWidgets import QApplication
from UI import MainWindow

oneinstance = None

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
        if p.info['name'] == "GamzScript.exe":
            return True

    return False

def main():
    app = QApplication(argv)

    if uirun():
        return

    if not scriptrun():
        Popen(["GamzScript.exe"])

    window = MainWindow()
    window.show()

    exit(app.exec_())

if __name__ == "__main__":
    main()
