# ==============================================================================
# Sala Al Jadida Salat Desktop Widget
# Standalone GTK3 widget — zero sudo, zero GNOME Shell extension required
# ==============================================================================

AUTOSTART_DIR  := $(HOME)/.config/autostart
AUTOSTART_FILE := $(AUTOSTART_DIR)/salat-desktop-widget.desktop

.PHONY: all run stop autostart disable-autostart check help

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

help:
	@echo "Available commands:"
	@echo "  make run               - Start (or restart) the desktop widget"
	@echo "  make stop              - Stop the running widget"
	@echo "  make autostart         - Auto-start widget on login (~/.config/autostart)"
	@echo "  make disable-autostart - Remove login autostart entry"
	@echo "  make check             - Verify Python syntax across all modules"
