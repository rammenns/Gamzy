#!/bin/sh

APP="/Applications/Gamzy.app"
PLIST="$HOME/Library/LaunchAgents/com.gamzy.GamzScript.plist"
DATA="$HOME/Library/Application Support/Gamzy"
SERVICE="gui/$(id -u)/com.gamzy.GamzScript"

ANSWER=$(osascript <<'APPLESCRIPT'
display dialog "Are you sure you want to uninstall Gamzy?" \
buttons {"Cancel", "Uninstall"} \
default button "Cancel" \
cancel button "Cancel" \
with title "Uninstall Gamzy"
APPLESCRIPT
)

case "$ANSWER" in
    *Uninstall*)
        ;;
    *)
        exit 0
        ;;
esac

launchctl bootout "$SERVICE" 2>/dev/null || true

pkill -9 -f "$APP/Contents/MacOS/GamzScript" 2>/dev/null || true

rm -f "$PLIST"

rm -rf "$DATA"

DOCK_PLIST="/tmp/gamzy-dock.plist"

defaults export com.apple.dock "$DOCK_PLIST" 2>/dev/null || true

if [ -f "$DOCK_PLIST" ]; then
    INDEX=$( /usr/libexec/PlistBuddy -c "Print :persistent-apps" "$DOCK_PLIST" 2>/dev/null |
        awk '
        /Dict {/ { depth++; start=NR }
        /file-label/ && /Gamzy/ { print start-1 }
        /}/ { if (depth > 0) depth-- }
        ' | tail -1 )

    if [ -n "$INDEX" ]; then
        /usr/libexec/PlistBuddy -c "Delete :persistent-apps:$INDEX" "$DOCK_PLIST" 2>/dev/null || true
        defaults import com.apple.dock "$DOCK_PLIST" 2>/dev/null || true
    fi

    rm -f "$DOCK_PLIST"
fi

killall Dock 2>/dev/null || true

rm -rf "$APP"

rm -f "$0"
