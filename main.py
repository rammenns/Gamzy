import platform
import sys
syst = platform.system()
if syst == "Darwin":
    macver = int(platform.mac_ver()[0].split(".")[0])
    if macver >= 13:
        from ServiceManagement import SMAppService, SMAppServiceStatusEnabled, SMAppServiceStatusRequiresApproval, SMAppServiceStatusNotRegistered, SMAppServiceStatusNotFound
        if "--unregister-gamzscript" in sys.argv:
            service = SMAppService.agentServiceWithPlistName_(
                "com.gamzy.GamzScript.plist"
            )
            success, error = service.unregisterAndReturnError_(None)
            print("Unregister success:", success)
            print("Unregister error:", error)
            sys.exit(0)
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

    if not getattr(sys, "frozen", False):
        return None if syst == "Linux" else False

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

        if dr().parents[1] != Path("/Applications/Gamzy.app"):
            return False

        if macver >= 13:

            service = SMAppService.agentServiceWithPlistName_(
                "com.gamzy.GamzScript.plist"
            )

            status = service.status()

            print("Launch Agent status:", status)
            print("Launch Agent status type:", type(status))
            try:
                print("Launch Agent status int:", int(status))
            except:
                print("Launch Agent status int: FAILED")

            if status == SMAppServiceStatusEnabled:
                print("Launch Agent: ENABLED")
                return True

            elif status == SMAppServiceStatusRequiresApproval:
                print("Launch Agent: REQUIRES APPROVAL")
                SMAppService.openSystemSettingsLoginItems()
                return False

            elif status == SMAppServiceStatusNotRegistered or status == SMAppServiceStatusNotFound:
                try:
                    success, error = service.registerAndReturnError_(None)
                    print("Register success:", success)
                    print("Register error:", error)
                    return bool(success)
                except Exception as e:
                    print("Register exception:", repr(e))
                    return False

            return False

        else:

            try:
                launch_agents = Path.home() / "Library" / "LaunchAgents"
                launch_agents.mkdir(parents=True, exist_ok=True)

                legacy_source = (dr().parent / "Library" / "LaunchAgents" / "com.gamzy.GamzScript.legacy.plist")

                legacy_target = (launch_agents / "com.gamzy.GamzScript.plist")

                if not legacy_source.exists():
                    return False

                legacy_target.write_bytes(legacy_source.read_bytes())

                result = subprocess.run(
                    [
                        "/bin/launchctl",
                        "load",
                        "-w",
                        str(legacy_target),
                    ],
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    return True

                check = subprocess.run(
                    [
                        "/bin/launchctl",
                        "list",
                        "com.gamzy.GamzScript",
                    ],
                    capture_output=True,
                    text=True,
                )

                return check.returncode == 0

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
        if not autostartx() and not scriptrun():
            subprocess.Popen([str(dr().parent / "Resources" / "GamzScript.app" / "Contents" / "MacOS" / gamzscript())]) if getattr(sys, "frozen", False) else subprocess.Popen([str(dr() / gamzscript())])

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()