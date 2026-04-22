#!/usr/bin/env bash
# Box.sh - Startet die SimpleBox-GUI.
# Beim ersten Aufruf wird ein .venv im Projektordner angelegt und
# - falls vorhanden - requirements.txt installiert. Danach wird
# simplebox_gui.py im venv ausgefuehrt.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$DIR/.venv"
REQ="$DIR/requirements.txt"
GUI="$DIR/simplebox_gui.py"

if ! command -v python3 >/dev/null 2>&1; then
    echo "Fehler: python3 ist nicht installiert." >&2
    exit 1
fi

if [ ! -d "$VENV" ]; then
    echo "Lege virtuelle Umgebung an: $VENV"
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install --quiet --upgrade pip
    if [ -f "$REQ" ]; then
        "$VENV/bin/pip" install --quiet -r "$REQ"
    fi
fi

# tkinter-Pruefung (stammt aus dem System-Python, nicht aus pip)
if ! "$VENV/bin/python" -c "import tkinter" >/dev/null 2>&1; then
    echo "Fehler: tkinter ist nicht verfuegbar." >&2
    echo "Unter Debian/Ubuntu:  sudo apt install python3-tk" >&2
    echo "Unter Fedora:         sudo dnf install python3-tkinter" >&2
    echo "Unter Arch:           sudo pacman -S tk" >&2
    exit 1
fi

# FreeCAD-Pruefung (nur Hinweis, kein Abbruch)
if ! command -v freecad >/dev/null 2>&1 && ! command -v FreeCAD >/dev/null 2>&1; then
    echo "Hinweis: FreeCAD wurde im PATH nicht gefunden." >&2
    echo "Die GUI oeffnet trotzdem, der 'FreeCAD starten'-Knopf wird aber fehlschlagen." >&2
fi

exec "$VENV/bin/python" "$GUI" "$@"
