#!/bin/bash

APPDIR="$(cd "$(dirname "$0")" && pwd)"
DESKTOP="$(xdg-user-dir DESKTOP)"

cat > "$DESKTOP/Gamzy.desktop" << EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=Gamzy
Comment=Gamzy Launcher
Exec=$APPDIR/Gamzy
Icon=$APPDIR/AppLogo.png
Terminal=false
Categories=Game;
EOF

chmod +x "$DESKTOP/Gamzy.desktop"

echo "Gamzy shortcut created on Desktop"
