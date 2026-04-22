# SimpleBox

Tkinter-GUI fuer FreeCAD, die ein einfaches, zweiteiliges Gehaeuse
(Grundkoerper + Deckel) fuer Elektronikprojekte (z.B. Arduino)
parametrisch erzeugt.

## Features

- Aeussere Abmessungen (L x B x H) frei einstellbar
- Wandstaerke, Deckelhoehe, Zentrierlippe mit Spiel
- 4 Schraubdome an den Innenecken mit 1,5 mm Pilotloch
- Passende Durchgangsloecher im Deckel
- Explosionsdarstellung (Deckel abgehoben) im Modell

## Dateien

| Datei | Zweck |
|-------|-------|
| `SimpleBox.py` | Geometrie-Bibliothek, in FreeCAD ausgefuehrt |
| `simplebox_gui.py` | Tkinter-Oberflaeche, startet FreeCAD mit Werten |
| `SimpleBox.desktop` | Klickbarer Starter fuer das Anwendungsmenue |

## Nutzung

```bash
./Box.sh
```

`Box.sh` legt beim ersten Aufruf ein `.venv` an, prueft `tkinter`
und startet dann die GUI. Werte eintragen, **FreeCAD starten** klicken.

Alternativ direkt:

```bash
python3 simplebox_gui.py
```

Die GUI erzeugt eine temporaere FCMacro-Datei (neben dem Script,
da Snap-FreeCAD keinen Zugriff auf `/tmp` hat) und startet FreeCAD damit.

### Starter installieren (optional)

```bash
cp SimpleBox.desktop ~/.local/share/applications/
```

Danach erscheint **SimpleBox** im Anwendungsmenue. Falls das Projekt
nicht unter dem hart kodierten Pfad liegt, die `Exec=`-Zeile in
`SimpleBox.desktop` auf den eigenen `Box.sh`-Pfad anpassen.

## Abhaengigkeiten

- Python 3 mit Tkinter (Linux: `python3-tk`)
- FreeCAD (getestet mit 1.1 aus dem Snap)
- Keine pip-Pakete noetig (`requirements.txt` ist leer)

## Auf anderem Rechner einrichten

```bash
git clone https://github.com/peterh69/SimpleBox.git
cd SimpleBox
./Box.sh
```
