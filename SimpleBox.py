# -*- coding: utf-8 -*-
"""
SimpleBox.py

Geometrie-Bibliothek fuer eine einfache, zweiteilige Box
(Grundkoerper + Deckel) fuer Elektronikprojekte (z.B. Arduino).

Wird aus FreeCAD heraus via exec() geladen und anschliessend mit
create_box(laenge, breite, hoehe, ...) aufgerufen.
"""

import FreeCAD as App
import Part


# ---------- Parameter-Vorgaben ----------
WALL_THICKNESS = 2.0     # Wandstaerke in mm
LID_HEIGHT = 5.0         # Hoehe des Deckels in mm
LIP_HEIGHT = 3.0         # Hoehe der Zentrierlippe am Deckel
LIP_CLEARANCE = 0.2      # Spiel zwischen Lippe und Innenwand (je Seite)
POST_DIAMETER = 5.0      # Aussendurchmesser der Schraubdome
SCREW_DIAMETER = 1.5     # Pilotloch-Durchmesser in den Domen
POST_GAP = 0.3           # Spalt zwischen Dom und Lippen-Innenkante
EXPLODE_GAP = 10.0       # Abstand Grundkoerper <-> Deckel in der Darstellung


def _post_positions(length, width, wall, clearance, post_d, post_gap):
    """XY-Mittelpunkte der 4 Schraubdome, innerhalb der Zentrierlippe."""
    inset = 2 * wall + clearance + post_d / 2 + post_gap
    return [
        (inset, inset),
        (length - inset, inset),
        (inset, width - inset),
        (length - inset, width - inset),
    ]


def build_base(length, width, height, wall, lid_h, clearance,
               post_d, screw_d, post_gap):
    """Grundkoerper: Quader abzueglich Innenausschnitt + 4 Schraubdome
    mit Pilotloechern."""
    base_outer_h = height - lid_h
    outer = Part.makeBox(length, width, base_outer_h)

    inner = Part.makeBox(
        length - 2 * wall,
        width - 2 * wall,
        base_outer_h - wall + 0.01
    )
    inner.translate(App.Vector(wall, wall, wall))

    base = outer.cut(inner)

    post_height = base_outer_h - wall
    positions = _post_positions(length, width, wall, clearance, post_d, post_gap)

    for (cx, cy) in positions:
        post = Part.makeCylinder(
            post_d / 2.0, post_height,
            App.Vector(cx, cy, wall), App.Vector(0, 0, 1)
        )
        base = base.fuse(post)

    # Pilotloecher: blind, von oben bis 1 mm ueber Dom-Unterkante
    hole_bottom_z = wall + 1.0
    hole_height = base_outer_h - hole_bottom_z + 0.01
    for (cx, cy) in positions:
        hole = Part.makeCylinder(
            screw_d / 2.0, hole_height,
            App.Vector(cx, cy, hole_bottom_z), App.Vector(0, 0, 1)
        )
        base = base.cut(hole)

    return base.removeSplitter()


def build_lid(length, width, wall, lid_h, lip_h, clearance,
              post_d, screw_d, post_gap):
    """Deckel: flacher Quader, Zentrierlippe unten, 4 Durchgangsloecher."""
    top = Part.makeBox(length, width, lid_h)

    lip_length = length - 2 * wall - 2 * clearance
    lip_width = width - 2 * wall - 2 * clearance
    lip_outer = Part.makeBox(lip_length, lip_width, lip_h)
    lip_outer.translate(App.Vector(wall + clearance, wall + clearance, -lip_h))

    lip_inner = Part.makeBox(
        lip_length - 2 * wall,
        lip_width - 2 * wall,
        lip_h + 0.01
    )
    lip_inner.translate(
        App.Vector(wall + clearance + wall, wall + clearance + wall, -lip_h)
    )
    lip = lip_outer.cut(lip_inner)

    lid = top.fuse(lip)

    for (cx, cy) in _post_positions(length, width, wall, clearance, post_d, post_gap):
        hole = Part.makeCylinder(
            screw_d / 2.0, lid_h + 0.02,
            App.Vector(cx, cy, -0.01),
            App.Vector(0, 0, 1)
        )
        lid = lid.cut(hole)

    return lid.removeSplitter()


def create_box(length, width, height,
               wall=WALL_THICKNESS, lid_h=LID_HEIGHT,
               lip_h=LIP_HEIGHT, clearance=LIP_CLEARANCE,
               post_d=POST_DIAMETER, screw_d=SCREW_DIAMETER,
               post_gap=POST_GAP, explode=EXPLODE_GAP):
    min_xy = 2 * (2 * wall + clearance + post_d + post_gap)
    if length < min_xy or width < min_xy:
        raise ValueError(
            "Laenge/Breite muessen mindestens {:.1f} mm betragen "
            "(fuer 4 Schraubdome).".format(min_xy)
        )
    if height < lid_h + wall + 3:
        raise ValueError(
            "Hoehe muss mindestens {:.1f} mm betragen.".format(lid_h + wall + 3)
        )

    doc = App.newDocument("SimpleBox")

    base_shape = build_base(length, width, height, wall, lid_h, clearance,
                            post_d, screw_d, post_gap)
    lid_shape = build_lid(length, width, wall, lid_h, lip_h, clearance,
                          post_d, screw_d, post_gap)

    lid_shape.translate(App.Vector(0, 0, (height - lid_h) + explode))

    base_obj = doc.addObject("Part::Feature", "Grundkoerper")
    base_obj.Shape = base_shape

    lid_obj = doc.addObject("Part::Feature", "Deckel")
    lid_obj.Shape = lid_shape

    doc.recompute()

    try:
        import FreeCADGui as Gui
        Gui.ActiveDocument.ActiveView.viewAxonometric()
        Gui.SendMsgToActiveView("ViewFit")
    except Exception:
        pass

    App.Console.PrintMessage(
        "SimpleBox erstellt: {} x {} x {} mm\n".format(length, width, height)
    )
    return doc
