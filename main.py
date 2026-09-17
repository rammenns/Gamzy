import sys
import subprocess
import psutil
from socket import socket, AF_INET, SOCK_STREAM, error
from PyQt5.QtWidgets import QApplication
from UI import MainWindow
import platform
from pathlib import Path

syst = platform.system()
oneinstance = None


def dr():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


def autostartx():
    if syst == "Linux":

        script = dr() / "GamzScript"

        if not script.exists():
            return None

        autostart = Path.home() / ".config" / "autostart"
        autostart.mkdir(parents=True, exist_ok=True)

        desktop = autostart / "GamzScript.desktop"

        template = dr() / "GamzScript.desktop.template"

        if not template.exists():
            return None

        content = template.read_text(encoding="utf-8")
        content = content.replace("scripth", str(script))

        if desktop.exists() and desktop.read_text(encoding="utf-8") == content:
            return None

        desktop.write_text(
            content,
            encoding="utf-8"
        )

    elif syst == "Darwin":

        if not Path("/Applications/Gamzy.app").exists():
            return False

        uid = subprocess.check_output(["id", "-u"], text=True).strip()
        service = f"gui/{uid}/com.gamzy.GamzScript"

        check = subprocess.run(
            ["launchctl", "print", service],
            capture_output=True
        )

        if check.returncode == 0:
            return False

        script = dr() / "GamzScript"

        if not script.exists():
            return False

        launchagents = Path.home() / "Library" / "LaunchAgents"
        launchagents.mkdir(parents=True, exist_ok=True)

        source_plist = dr().parent / "Resources" / "com.gamzy.GamzScript.plist"
        plist = launchagents / "com.gamzy.GamzScript.plist"

        try:
            content = source_plist.read_text(encoding="utf-8")
        except FileNotFoundError:
            return False

        content = content.replace(
            "GamzScriptPTH",
            str(script)
        )

        plist.write_text(content, encoding="utf-8")

        hooray = subprocess.run([
            "launchctl",
            "bootstrap",
            f"gui/{uid}",
            str(plist)
        ])

        return hooray.returncode == 0

    return None


def gamzscript():
    return "GamzScript.exe" if syst == "Windows" else "GamzScript"


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
        try:
            if p.info['name'] == gamzscript():
                return True
        except(psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False


def main():
    if uirun():
        sys.exit()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    if syst == "Windows" and not scriptrun():
        subprocess.Popen([str(dr() / gamzscript())])

    elif syst == "Linux":
        autostartx()
        if not scriptrun():
            subprocess.Popen([str(dr() / gamzscript())])

    elif syst == "Darwin":
        if not scriptrun() and not autostartx():
            subprocess.Popen([str(dr() / gamzscript())])

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
