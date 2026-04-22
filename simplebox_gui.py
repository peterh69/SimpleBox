#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simplebox_gui.py

Tkinter-Oberflaeche fuer SimpleBox. Fragt die Abmessungen ab und
startet FreeCAD mit einer generierten Macro-Datei, die SimpleBox.py
laedt und create_box() mit den eingegebenen Werten aufruft.
"""

import os
import shutil
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SIMPLEBOX_PY = os.path.join(SCRIPT_DIR, "SimpleBox.py")
# Macro muss im Home-Verzeichnis liegen, nicht in /tmp:
# Snap-FreeCAD hat wegen Confinement keinen Zugriff auf /tmp.
MACRO_PATH = os.path.join(SCRIPT_DIR, ".simplebox_run.FCMacro")


def find_freecad():
    """Sucht das FreeCAD-Executable im PATH."""
    for name in ("freecad", "FreeCAD"):
        path = shutil.which(name)
        if path:
            return path
    return None


def generate_macro(params):
    """Schreibt die .FCMacro-Datei, die SimpleBox.py laedt und
    create_box() mit den Parametern aufruft. Liegt bewusst im
    Home-Verzeichnis (Snap-Confinement blockiert /tmp)."""
    content = (
        "# -*- coding: utf-8 -*-\n"
        "# Automatisch erzeugt von simplebox_gui.py\n"
        "with open({script!r}, 'r') as _f:\n"
        "    exec(_f.read())\n"
        "create_box(\n"
        "    length={length}, width={width}, height={height},\n"
        "    wall={wall}, lid_h={lid_h},\n"
        "    lip_h={lip_h}, clearance={clearance},\n"
        "    post_d={post_d}, screw_d={screw_d}\n"
        ")\n"
    ).format(script=SIMPLEBOX_PY, **params)

    with open(MACRO_PATH, "w") as f:
        f.write(content)
    return MACRO_PATH


class SimpleBoxGUI(tk.Tk):
    FIELDS = [
        ("length",    "Laenge (X) [mm]",   "100.0"),
        ("width",     "Breite (Y) [mm]",    "70.0"),
        ("height",    "Hoehe (Z) [mm]",     "30.0"),
        ("wall",      "Wandstaerke [mm]",    "2.0"),
        ("lid_h",     "Deckelhoehe [mm]",    "5.0"),
        ("lip_h",     "Lippenhoehe [mm]",    "3.0"),
        ("clearance", "Spiel Lippe [mm]",    "0.2"),
        ("post_d",    "Dom-Durchmesser [mm]", "5.0"),
        ("screw_d",   "Deckelloch [mm]",     "1.5"),
    ]

    def __init__(self):
        super().__init__()
        self.title("SimpleBox - Elektronikgehaeuse")
        self.resizable(False, False)

        self.entries = {}
        frm = ttk.Frame(self, padding=12)
        frm.grid(row=0, column=0)

        ttk.Label(
            frm, text="Aeussere Abmessungen der Box",
            font=("TkDefaultFont", 11, "bold")
        ).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")

        for i, (key, label, default) in enumerate(self.FIELDS, start=1):
            ttk.Label(frm, text=label).grid(row=i, column=0, sticky="w", padx=(0, 8), pady=2)
            var = tk.StringVar(value=default)
            entry = ttk.Entry(frm, textvariable=var, width=10, justify="right")
            entry.grid(row=i, column=1, sticky="e", pady=2)
            self.entries[key] = var

        btn_row = ttk.Frame(frm)
        btn_row.grid(row=len(self.FIELDS) + 1, column=0, columnspan=2, pady=(14, 0), sticky="ew")
        btn_row.columnconfigure(0, weight=1)
        btn_row.columnconfigure(1, weight=1)

        ttk.Button(btn_row, text="FreeCAD starten", command=self.on_start).grid(
            row=0, column=0, sticky="ew", padx=(0, 4)
        )
        ttk.Button(btn_row, text="Beenden", command=self.destroy).grid(
            row=0, column=1, sticky="ew", padx=(4, 0)
        )

        self.status = ttk.Label(frm, text="", foreground="#555")
        self.status.grid(row=len(self.FIELDS) + 2, column=0, columnspan=2, pady=(10, 0), sticky="w")

        self.entries["length"].trace_add("write", lambda *_: None)
        self.bind("<Return>", lambda _e: self.on_start())

    def collect_params(self):
        params = {}
        for key, _, _ in self.FIELDS:
            raw = self.entries[key].get().strip().replace(",", ".")
            if not raw:
                raise ValueError("Feld '{}' ist leer.".format(key))
            try:
                val = float(raw)
            except ValueError:
                raise ValueError("Feld '{}': '{}' ist keine Zahl.".format(key, raw))
            if val <= 0:
                raise ValueError("Feld '{}' muss groesser 0 sein.".format(key))
            params[key] = val

        # Plausibilitaet (entspricht den Checks in create_box)
        post_gap = 0.3  # muss mit POST_GAP in SimpleBox.py uebereinstimmen
        min_xy = 2 * (2 * params["wall"] + params["clearance"]
                      + params["post_d"] + post_gap)
        if params["length"] < min_xy or params["width"] < min_xy:
            raise ValueError(
                "Laenge/Breite muessen mindestens {:.1f} mm betragen "
                "(fuer 4 Schraubdome).".format(min_xy)
            )
        if params["height"] < params["lid_h"] + params["wall"] + 3:
            raise ValueError(
                "Hoehe muss mindestens {:.1f} mm betragen.".format(
                    params["lid_h"] + params["wall"] + 3
                )
            )
        if params["screw_d"] >= params["post_d"]:
            raise ValueError(
                "Deckelloch muss kleiner als Dom-Durchmesser sein."
            )
        return params

    def on_start(self):
        try:
            params = self.collect_params()
        except ValueError as e:
            messagebox.showerror("Ungueltige Eingabe", str(e), parent=self)
            return

        freecad = find_freecad()
        if not freecad:
            messagebox.showerror(
                "FreeCAD nicht gefunden",
                "Das Programm 'freecad' wurde im PATH nicht gefunden.\n"
                "Bitte FreeCAD installieren oder den Pfad ergaenzen.",
                parent=self,
            )
            return

        if not os.path.isfile(SIMPLEBOX_PY):
            messagebox.showerror(
                "SimpleBox.py fehlt",
                "Die Datei wurde nicht gefunden:\n{}".format(SIMPLEBOX_PY),
                parent=self,
            )
            return

        try:
            macro_path = generate_macro(params)
        except OSError as e:
            messagebox.showerror("Fehler", "Macro konnte nicht erzeugt werden:\n{}".format(e), parent=self)
            return

        try:
            subprocess.Popen(
                [freecad, macro_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError as e:
            messagebox.showerror("Fehler", "FreeCAD konnte nicht gestartet werden:\n{}".format(e), parent=self)
            return

        self.status.config(
            text="FreeCAD gestartet: {:g} x {:g} x {:g} mm".format(
                params["length"], params["width"], params["height"]
            )
        )


def main():
    app = SimpleBoxGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
