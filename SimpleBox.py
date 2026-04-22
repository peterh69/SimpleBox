# -*- coding: utf-8 -*-
"""
SimpleBox.py

Geometrie-Bibliothek fuer eine einfache, zweiteilige Box
(Grundkoerper + Deckel) fuer Elektronikprojekte (z.B. Arduino).

Wird aus FreeCAD heraus via exec() geladen und anschliessend mit
create_box(laenge, breite, hoehe, ...) aufgerufen.
"""

import os
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


def _find_template():
    """Sucht eine passende A4-Landscape-Vorlage; First-Angle (ISO) bevorzugt."""
    candidates = [
        "Mod/TechDraw/Templates/ISO/A4_Landscape_ISO5457_minimal.svg",
        "Mod/TechDraw/Templates/ISO/A4_Landscape_blank.svg",
        "Mod/TechDraw/Templates/A4_Landscape_TD.svg",
        "Mod/TechDraw/Templates/Default_Template_A4_Landscape.svg",
    ]
    for rel in candidates:
        path = os.path.join(App.getResourceDir(), rel)
        if os.path.isfile(path):
            return path
    return None


def _find_view_edge(view, expected_length, direction, tol=0.1):
    """Gibt den 0-basierten Index eines Edges in der Ansicht zurueck,
    der die gewuenschte Laenge und Richtung hat. direction='X' fuer
    horizontal, 'Y' fuer vertikal."""
    i = 0
    while i < 200:
        try:
            e = view.getEdgeByIndex(i)
        except Exception:
            return None
        if e is None:
            return None
        v1 = e.firstVertex()
        v2 = e.lastVertex()
        dx = v2.X - v1.X
        dy = v2.Y - v1.Y
        length = (dx * dx + dy * dy) ** 0.5
        is_horiz = abs(dx) > 10 * abs(dy)
        is_vert = abs(dy) > 10 * abs(dx)
        if abs(length - expected_length) < tol:
            if direction == "X" and is_horiz:
                return i
            if direction == "Y" and is_vert:
                return i
        i += 1
    return None


def _add_linear_dim(doc, page, view, edge_idx, dim_type, name):
    dim = doc.addObject("TechDraw::DrawViewDimension", name)
    dim.Type = dim_type
    dim.References2D = [(view, "Edge{}".format(edge_idx))]
    page.addView(dim)
    return dim


def _add_dims_for_part(doc, page, group, length, width, front_h, prefix):
    """Bemasst Laenge und Breite in der Draufsicht, Hoehe in der Frontansicht.
    Rueckgabe: Anzahl erfolgreicher Bemassungen."""
    views = {getattr(v, "Type", ""): v for v in group.Views}
    added = 0
    if "Top" in views:
        top = views["Top"]
        i_len = _find_view_edge(top, length, "X")
        if i_len is not None:
            _add_linear_dim(doc, page, top, i_len, "DistanceX", prefix + "_L")
            added += 1
        i_wid = _find_view_edge(top, width, "Y")
        if i_wid is not None:
            _add_linear_dim(doc, page, top, i_wid, "DistanceY", prefix + "_W")
            added += 1
    if "Front" in views:
        front = views["Front"]
        i_h = _find_view_edge(front, front_h, "Y")
        if i_h is not None:
            _add_linear_dim(doc, page, front, i_h, "DistanceY", prefix + "_H")
            added += 1
    return added


def build_drawings(doc, parts):
    """parts: Liste von (obj, label, length, width, front_height)-Tupeln.
    Erzeugt je eine TechDraw-Seite mit Front/Draufsicht/Seite + Iso und
    Bemassungen (L, B in Draufsicht; H in Front). First-Angle-Projektion."""
    try:
        import TechDraw  # noqa: F401
    except ImportError:
        App.Console.PrintWarning("TechDraw nicht verfuegbar, keine Zeichnungen erzeugt.\n")
        return []

    template_path = _find_template()
    pages = []

    for obj, label, length, width, front_h in parts:
        name = obj.Name + "_Page"
        page = doc.addObject("TechDraw::DrawPage", name)
        page.Label = "Zeichnung " + label

        if template_path:
            tpl = doc.addObject("TechDraw::DrawSVGTemplate", name + "_Template")
            tpl.Template = template_path
            page.Template = tpl

        group = doc.addObject("TechDraw::DrawProjGroup", name + "_Group")
        page.addView(group)
        group.Source = [obj]
        group.ProjectionType = "First angle"
        group.ScaleType = "Automatic"
        group.Anchor = group.addProjection("Front")
        group.addProjection("Top")
        group.addProjection("Right")
        group.addProjection("FrontTopRight")

        # Views muessen berechnet sein, bevor Edges referenziert werden koennen
        doc.recompute()

        _add_dims_for_part(doc, page, group, length, width, front_h, obj.Name)
        pages.append(page)

    doc.recompute()
    return pages


def create_box(length, width, height,
               wall=WALL_THICKNESS, lid_h=LID_HEIGHT,
               lip_h=LIP_HEIGHT, clearance=LIP_CLEARANCE,
               post_d=POST_DIAMETER, screw_d=SCREW_DIAMETER,
               post_gap=POST_GAP, explode=EXPLODE_GAP,
               with_drawings=True):
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

    if with_drawings:
        build_drawings(doc, [
            (base_obj, "Grundkoerper", length, width, height - lid_h),
            (lid_obj,  "Deckel",       length, width, lid_h),
        ])

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
