import platform
import sys
syst = platform.system()
if syst == "Darwin":
    macver = int(platform.mac_ver()[0].split(".")[0])
    if macver >= 13:
        from ServiceManagement import SMAppService, SMAppServiceStatusEnabled, SMAppServiceStatusRequiresApproval, SMAppServiceStatusNotRegistered, SMAppServiceStatusNotFound
    else:
        from ServiceManagement import SMLoginItemSetEnabled
elif syst not in {"Windows", "Linux"}:
    print(f"Unsupported operating system: {syst}")
    sys.exit(1)
import subprocess
import psutil
from socket import socket, AF_INET, SOCK_STREAM, error
from PyQt5.QtWidgets import QApplication
from UI import MainWindow
from pathlib import Path

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

        if not getattr(sys, "frozen", False):
            return False

        elif not Path("/Applications/Gamzy.app").exists():
            return False

        if macver >= 13:

            service = SMAppService.loginItemServiceWithIdentifier_(
                "com.gamzy.GamzScript"
            )

            status = service.status

            if status == SMAppServiceStatusEnabled:
                return True

            elif status == SMAppServiceStatusRequiresApproval:
                return False

            elif status == SMAppServiceStatusNotRegistered or status == SMAppServiceStatusNotFound:
                try:
                    success, error = service.registerAndReturnError_(None)
                    return bool(success)
                except Exception:
                    return False

            return False

        else:

            try:
                return bool(
                    SMLoginItemSetEnabled(
                        "com.gamzy.GamzScript",
                        True
                    )
                )
            except Exception:
                return False

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
            subprocess.Popen([str(dr().parent / "Library" / "LoginItems" / "GamzScript.app" / "Contents" / "MacOS" / gamzscript())]) if getattr(sys, "frozen", False) else subprocess.Popen([str(dr() / gamzscript())])

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
