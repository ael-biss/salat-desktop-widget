# ==============================================================================
# Sala Al Jadida Salat Desktop Widget
# Standalone GTK3 widget — zero sudo, zero GNOME Shell extension required
# ==============================================================================

AUTOSTART_DIR  := $(HOME)/.config/autostart
AUTOSTART_FILE := $(AUTOSTART_DIR)/salat-desktop-widget.desktop

.PHONY: all run stop autostart disable-autostart check test sim-adhan sim-iqama sim-jumaa help

all: run

run:
	@pkill -f "salat-desktop-widget/[r]un.py" 2>/dev/null || true
	@pkill -f "[s]cripts/salat_widget.py" 2>/dev/null || true
	@nohup python3 "$(CURDIR)/run.py" >/dev/null 2>&1 </dev/null &
	@echo "✔ Salat Desktop Widget started! (Left-click: schedule, Right-click: settings, Drag: move)"

stop:
	@pkill -f "salat-desktop-widget/[r]un.py" 2>/dev/null && echo "✔ Widget stopped." || echo "ℹ Widget is not running."

autostart:
	@mkdir -p "$(AUTOSTART_DIR)"
	@printf '[Desktop Entry]\nType=Application\nName=Salat Desktop Widget\nComment=Sala Al Jadida Prayer Times & Iqama Widget\nExec=python3 %s/run.py\nTerminal=false\nX-GNOME-Autostart-enabled=true\n' "$(CURDIR)" > "$(AUTOSTART_FILE)"
	@echo "✔ Autostart enabled at $(AUTOSTART_FILE)"

disable-autostart:
	@rm -f "$(AUTOSTART_FILE)"
	@echo "✔ Autostart disabled."

check:
	@python3 -m compileall -q run.py salat_widget
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
	@echo "  make run               - Start (or restart) the desktop widget"
	@echo "  make stop              - Stop the running widget"
	@echo "  make autostart         - Auto-start widget on login (~/.config/autostart)"
	@echo "  make disable-autostart - Remove login autostart entry"
	@echo "  make test              - Run automated unit tests"
	@echo "  make sim-adhan         - Live test: Adhan notification + audio -> Red Iqama mode"
	@echo "  make sim-iqama         - Live test: Red Iqama icon + countdown to 00:00"
	@echo "  make sim-jumaa         - Live test: Friday Jumu'ah reminder"
	@echo "  make check             - Verify Python syntax across all modules"
