"""Centralized dark slate & emerald GTK3 stylesheet and icon helpers."""

import os
from typing import Optional

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gdk, GdkPixbuf, Gtk

from salat_widget.constants import DEFAULT_ICON_PATH, RED_ICON_PATH

APP_CSS = b"""
* {
    font-family: "Ubuntu", "Inter", "Cantarell", "DejaVu Sans", sans-serif;
}

window.salat-transparent {
    background-color: transparent;
}

window.salat-settings-window {
    background-color: #0f141b;
    color: #f1f5f9;
}

/* Floating Pill */
.salat-pill {
    background-color: #0e131a;
    border: 1px solid #1f3d33;
    border-radius: 999px;
    padding: 5px 14px;
    color: #f8fafc;
}

.salat-pill.topbar-mode {
    padding: 2px 11px;
    border-radius: 999px;
    background-color: #11161d;
}

.salat-pill:hover {
    background-color: #131b24;
    border-color: #10b981;
}

.salat-pill.iqama-mode {
    background-color: #261014;
    border: 1px solid #ef4444;
}

.salat-pill.iqama-mode:hover {
    background-color: #32141a;
    border-color: #f87171;
}

.salat-pill-name {
    font-weight: 700;
    font-size: 12.5px;
    color: #34d399;
}

.salat-pill.iqama-mode .salat-pill-name {
    color: #f87171;
}

.salat-pill-sep {
    color: #475569;
    font-size: 11px;
}

.salat-pill-time {
    font-family: "JetBrains Mono", "Ubuntu Mono", "DejaVu Sans Mono", monospace;
    font-weight: 700;
    font-size: 12.5px;
    color: #f8fafc;
}

/* Popup & Settings Surfaces */
.salat-card {
    background-color: #0f141b;
    border: 1px solid #243040;
    border-radius: 16px;
    padding: 16px;
    color: #f1f5f9;
}

.salat-section {
    background-color: #141b24;
    border: 1px solid #1e2938;
    border-radius: 12px;
    padding: 12px;
}

.salat-title {
    font-weight: 700;
    font-size: 15px;
    color: #f8fafc;
}

.salat-subtitle {
    font-size: 11.5px;
    color: #94a3b8;
}

.salat-section-title {
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 0.8px;
    color: #34d399;
}

.salat-field-label {
    font-size: 13px;
    font-weight: 600;
    color: #e2e8f0;
}

.salat-hint {
    font-size: 11px;
    color: #94a3b8;
}

/* Close Button */
.salat-close-btn {
    background-image: none;
    background-color: #18202c;
    color: #94a3b8;
    border: 1px solid #263244;
    border-radius: 8px;
    padding: 2px 8px;
    min-height: 24px;
    min-width: 24px;
    font-size: 12px;
    font-weight: 700;
    box-shadow: none;
}

.salat-close-btn:hover {
    background-color: #243042;
    color: #ffffff;
}

/* Hero Next-Prayer Banner */
.salat-hero-card {
    background-color: #132220;
    border: 1px solid #1f4d3f;
    border-radius: 12px;
    padding: 12px 14px;
}

.salat-hero-card.iqama-mode {
    background-color: #2a1216;
    border-color: #ef4444;
}

.salat-hero-badge {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.8px;
    color: #34d399;
}

.salat-hero-card.iqama-mode .salat-hero-badge {
    color: #f87171;
}

.salat-hero-name {
    font-size: 17px;
    font-weight: 700;
    color: #ffffff;
}

.salat-hero-countdown {
    font-family: "JetBrains Mono", "Ubuntu Mono", "DejaVu Sans Mono", monospace;
    font-size: 19px;
    font-weight: 700;
    color: #34d399;
}

.salat-hero-card.iqama-mode .salat-hero-countdown {
    color: #f87171;
}

progressbar.salat-progress trough {
    background-color: #1a2c29;
    border: none;
    border-radius: 999px;
    min-height: 5px;
}

progressbar.salat-progress progress {
    background-color: #10b981;
    border: none;
    border-radius: 999px;
    min-height: 5px;
}

.salat-hero-card.iqama-mode progressbar.salat-progress trough {
    background-color: #3b181e;
}

.salat-hero-card.iqama-mode progressbar.salat-progress progress {
    background-color: #ef4444;
}

/* Prayer Table */
.salat-table-box {
    background-color: #141b24;
    border: 1px solid #1e2938;
    border-radius: 12px;
    padding: 6px;
}

.salat-row {
    padding: 6px 10px;
    border-radius: 8px;
}

.salat-row-active {
    background-color: #132b24;
    border: 1px solid #1e5946;
}

.salat-row-active.iqama-mode {
    background-color: #2c1317;
    border: 1px solid #dc2626;
}

.salat-row-name {
    font-weight: 600;
    font-size: 13px;
    color: #cbd5e1;
}

.salat-row-active .salat-row-name {
    color: #34d399;
    font-weight: 700;
}

.salat-row-active.iqama-mode .salat-row-name {
    color: #f87171;
}

.salat-row-time {
    font-family: "JetBrains Mono", "Ubuntu Mono", "DejaVu Sans Mono", monospace;
    font-size: 13px;
    font-weight: 700;
    color: #f8fafc;
}

.salat-iqama-pill {
    background-color: #1d2633;
    color: #94a3b8;
    border-radius: 999px;
    padding: 1px 7px;
    font-family: "JetBrains Mono", "Ubuntu Mono", "DejaVu Sans Mono", monospace;
    font-size: 10.5px;
    font-weight: 600;
}

.salat-row-active .salat-iqama-pill {
    background-color: #10b981;
    color: #062118;
}

.salat-row-active.iqama-mode .salat-iqama-pill {
    background-color: #ef4444;
    color: #ffffff;
}

/* Inputs & Switches */
entry,
spinbutton,
spinbutton entry {
    background-image: none;
    background-color: #0f141b;
    color: #f8fafc;
    border: 1px solid #2b384a;
    border-radius: 8px;
    padding: 4px 8px;
    box-shadow: none;
    font-size: 12.5px;
}

spinbutton {
    padding: 0;
}

spinbutton entry {
    border: none;
    border-radius: 8px 0 0 8px;
}

spinbutton button {
    background-image: none;
    background-color: #182230;
    color: #e2e8f0;
    border: none;
    border-left: 1px solid #2b384a;
    box-shadow: none;
    padding: 4px 8px;
}

spinbutton button:hover {
    background-color: #223044;
    color: #34d399;
}

entry:focus,
spinbutton:focus {
    border-color: #10b981;
}

switch {
    background-color: #263244;
    border: 1px solid #334155;
    border-radius: 999px;
    color: transparent;
    min-width: 42px;
    min-height: 22px;
}

switch:checked {
    background-color: #10b981;
    border-color: #10b981;
}

switch slider {
    background-color: #f8fafc;
    border-radius: 999px;
    min-width: 16px;
    min-height: 16px;
    margin: 2px;
}

/* Action Buttons */
.salat-btn {
    background-image: none;
    background-color: #17202c;
    color: #e2e8f0;
    border: 1px solid #263244;
    border-radius: 9px;
    padding: 6px 12px;
    font-size: 12px;
    font-weight: 600;
    box-shadow: none;
}

.salat-btn:hover {
    background-color: #1e2d3d;
    border-color: #10b981;
    color: #ffffff;
}

.salat-btn-primary {
    background-image: none;
    background-color: #10b981;
    color: #062118;
    border: 1px solid #10b981;
    border-radius: 9px;
    padding: 6px 12px;
    font-size: 12px;
    font-weight: 700;
    box-shadow: none;
}

.salat-btn-primary:hover {
    background-color: #34d399;
    border-color: #34d399;
}

.salat-btn-danger:hover {
    background-color: #3b1820;
    border-color: #ef4444;
    color: #fca5a5;
}
"""


def install_css() -> None:
    provider = Gtk.CssProvider()
    provider.load_from_data(APP_CSS)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )


def enable_rgba(window: Gtk.Window) -> None:
    window.set_app_paintable(True)
    screen = window.get_screen()
    visual = screen.get_rgba_visual()
    if visual is not None and screen.is_composited():
        window.set_visual(visual)


def load_mosque_icon(size: int, red: bool = False) -> Optional[GdkPixbuf.Pixbuf]:
    path = RED_ICON_PATH if red else DEFAULT_ICON_PATH
    if os.path.exists(path):
        try:
            return GdkPixbuf.Pixbuf.new_from_file_at_scale(path, size, size, True)
        except Exception:
            pass
    return None
