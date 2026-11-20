#!/usr/bin/env bash
# Zero-sudo, zero-source-code installer for Salat Desktop Widget.
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/ael-biss/salat-desktop-widget/main/install.sh | bash
# Or override the release download URL:
#   SALAT_BUNDLE_URL="https://..." bash install.sh

set -euo pipefail

BUNDLE_URL="${SALAT_BUNDLE_URL:-https://github.com/ael-biss/salat-desktop-widget/releases/latest/download/salat-widget.pyz}"
BIN_DIR="$HOME/.local/bin"
BIN_PATH="$BIN_DIR/salat-widget"
AUTOSTART_DIR="$HOME/.config/autostart"
AUTOSTART_FILE="$AUTOSTART_DIR/salat-desktop-widget.desktop"

echo "Installing Salat Desktop Widget (no sudo required)..."
mkdir -p "$BIN_DIR" "$AUTOSTART_DIR"

TMP_FILE="${BIN_PATH}.tmp"
curl -fsSL "$BUNDLE_URL" -o "$TMP_FILE"
chmod +x "$TMP_FILE"
mv -f "$TMP_FILE" "$BIN_PATH"

cat > "$AUTOSTART_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Salat Desktop Widget
Comment=Sala Al Jadida Prayer Times & Iqama Widget
Exec=$BIN_PATH
Terminal=false
X-GNOME-Autostart-enabled=true
EOF

pkill -f "[s]alat-widget" 2>/dev/null || true
nohup "$BIN_PATH" >/dev/null 2>&1 </dev/null &

echo "✔ Installed to $BIN_PATH"
echo "✔ Autostart enabled at $AUTOSTART_FILE"
echo "✔ Widget is running!"
