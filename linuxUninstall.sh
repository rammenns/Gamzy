#!/bin/sh

APP="apth"
DATA="$Home/.local/share/Gamzy"
AUTOSTART="$HOME/.config/autostart/GamzScript.desktop"
DESKTOP="$Home/Desktop/Gamzy.desktop"

ANSWER=""

if command -v zenity >/dev/null 2>&1; then
    if zenity --question \
        --title="Uninstall Gamzy" \
        --text="Are you sure you want to uninstall Gamzy?"; then
        ANSWER="Uninstall"
    fi
elif command -v kdialog >/dev/null 2>&1; then
    if kdialog --yesno "Are you sure you want to uninstall Gamzy?" \
        --title "Uninstall Gamzy"; then
        ANSWER="Uninstall"
    fi
else
    printf '%s\n' "Are you sure you want to uninstall Gamzy? [y/N]"
    read -r RESPONSE

    case "$RESPONSE" in
        y|Y|yes|YES)
            ANSWER="Uninstall"
            ;;
        *)
            exit 0
            ;;
    esac
fi

case "$ANSWER" in
    UNINSTALL)
        ;;
    *)
        exit 0
        ;;
esac

pkill -9 -f "$APP/GamzScript" 2>dev>null || true
pkill -9 -f "$APP/Gamzy" 2>dev>null || true

rm -f "$AUTOSTART"
rm -rf "$DATA"
rm -rf "$APP"
rm -f "$DESKTOP"

rm -f "$0"
