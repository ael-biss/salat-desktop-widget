# ==============================================================================
# Sala Al Jadida Salat Desktop Widget
# Standalone GTK3 widget — zero sudo, zero GNOME Shell extension required
# ==============================================================================

BIN_DIR        := $(HOME)/.local/bin
INSTALL_BIN    := $(BIN_DIR)/salat-widget
DATA_DIR       := $(HOME)/.local/share/salat-widget
AUTOSTART_DIR  := $(HOME)/.config/autostart
AUTOSTART_FILE := $(AUTOSTART_DIR)/salat-desktop-widget.desktop
BUNDLE         := dist/salat-widget.pyz

.PHONY: all build install uninstall run stop autostart disable-autostart check test sim-adhan sim-iqama sim-jumaa help

all: run

# Build single-file bytecode-only executable bundle (no source code inside)
build:
	@python3 scripts/build_bundle.py

# Install standalone executable to ~/.local/bin/salat-widget + autostart (survives deleting source repo)
install: build
	@mkdir -p "$(BIN_DIR)" "$(AUTOSTART_DIR)"
	@cp -f "$(BUNDLE)" "$(INSTALL_BIN)"
	@chmod +x "$(INSTALL_BIN)"
	@printf '[Desktop Entry]\nType=Application\nName=Salat Desktop Widget\nComment=Sala Al Jadida Prayer Times & Iqama Widget\nExec=%s\nTerminal=false\nX-GNOME-Autostart-enabled=true\n' "$(INSTALL_BIN)" > "$(AUTOSTART_FILE)"
	@pkill -f "salat-desktop-widget/[r]un.py" 2>/dev/null || true
	@pkill -f "\.local/bin/[s]alat-widget" 2>/dev/null || true
	@nohup "$(INSTALL_BIN)" >/dev/null 2>&1 </dev/null &
	@echo "✔ Installed standalone app to $(INSTALL_BIN)"
	@echo "✔ Autostart enabled at $(AUTOSTART_FILE)"
	@echo "✔ Safe to delete source folder — app runs independently!"

uninstall:
	@pkill -f "\.local/bin/[s]alat-widget" 2>/dev/null || true
	@pkill -f "salat-desktop-widget/[r]un.py" 2>/dev/null || true
	@rm -f "$(INSTALL_BIN)" "$(AUTOSTART_FILE)"
	@rm -rf "$(DATA_DIR)"
	@echo "✔ Uninstalled Salat Desktop Widget."

run:
	@pkill -f "salat-desktop-widget/[r]un.py" 2>/dev/null || true
	@pkill -f "\.local/bin/[s]alat-widget" 2>/dev/null || true
	@nohup python3 "$(CURDIR)/run.py" >/dev/null 2>&1 </dev/null &
	@echo "✔ Salat Desktop Widget started from source! (Left-click: schedule, Right-click: settings, Drag: move)"

stop:
	@pkill -f "salat-desktop-widget/[r]un.py" 2>/dev/null || true
	@pkill -f "\.local/bin/[s]alat-widget" 2>/dev/null || true
	@echo "✔ Widget stopped."

autostart: install

disable-autostart:
	@rm -f "$(AUTOSTART_FILE)"
	@echo "✔ Autostart disabled."

check:
	@python3 -m compileall -q run.py salat_widget scripts/build_bundle.py
	@echo "✔ Syntax check passed."

test: check
	@python3 -m unittest discover -s tests -v

sim-adhan:
	@pkill -f "salat-desktop-widget/[r]un.py" 2>/dev/null || true
	@nohup python3 "$(CURDIR)/run.py" --simulate adhan >/dev/null 2>&1 </dev/null &
	@echo "✔ Simulating Adhan -> Iqama (red icon + audio in 3 seconds)..."

sim-iqama:
	@pkill -f "salat-desktop-widget/[r]un.py" 2>/dev/null || true
	@nohup python3 "$(CURDIR)/run.py" --simulate iqama >/dev/null 2>&1 </dev/null &
	@echo "✔ Simulating Iqama mode (red icon + 10s countdown)..."

sim-jumaa:
	@pkill -f "salat-desktop-widget/[r]un.py" 2>/dev/null || true
	@nohup python3 "$(CURDIR)/run.py" --simulate jumaa >/dev/null 2>&1 </dev/null &
	@echo "✔ Simulating Jumu'ah Friday reminder..."

help:
	@echo "Available commands:"
	@echo "  make build             - Build single-file bytecode-only dist/salat-widget.pyz"
	@echo "  make install           - Build & install to ~/.local/bin/salat-widget + autostart"
	@echo "  make uninstall         - Remove installed app, extracted assets, and autostart"
	@echo "  make run               - Run directly from source (dev mode)"
	@echo "  make stop              - Stop the running widget"
	@echo "  make test              - Run automated unit tests"
	@echo "  make sim-adhan         - Live test: Adhan -> Red Iqama mode"
	@echo "  make sim-iqama         - Live test: Red Iqama countdown"
	@echo "  make sim-jumaa         - Live test: Friday Jumu'ah reminder"
