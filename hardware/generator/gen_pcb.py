#!/usr/bin/env python3
"""Step 1 of the PCB: create vent-control.kicad_pcb with outline, placed footprints,
nets, net classes and the antenna keep-out.  Routing is done by route.py,
copper pours + DRC by finish_pcb.py.

Run with the KiCad python: /usr/bin/python3 gen_pcb.py
"""
import os
import pcbnew
import design
from gen_sch import uid, ROOT

HERE = os.path.dirname(os.path.abspath(__file__))
KI = os.path.join(HERE, "..", "kicad")
OUT = os.path.join(KI, "vent-control.kicad_pcb")
FPDIR = "/usr/share/kicad/footprints"

OX, OY = 100.0, 100.0        # board origin on the KiCad page
W, H = 36.0, 50.0            # board size (mm)
ANT_Y = 5.6                  # antenna keep-out band 0..ANT_Y (module antenna is 5.4 mm)

# ref: (x, y, rotation_deg)  - board coordinates, origin = top-left corner
PLACE = {
    "U1": (18.0, 11.0, 0),
    "H1": (2.6, 2.6, 0), "H2": (33.4, 2.6, 0), "H3": (2.6, 47.4, 0), "H4": (33.4, 47.4, 0),
    # left of the module: reset button + decoupling
    "SW1": (5.0, 11.0, 90),
    "C5": (10.0, 8.4, 90), "C6": (10.0, 11.8, 90), "C7": (10.0, 15.0, 90),
    # right of the module: boot button
    "SW2": (31.0, 11.0, 90),
    # under the module, left: LDO
    "U3": (5.0, 21.0, 0), "C3": (1.9, 21.0, 90), "C4": (8.4, 21.0, 90), "R8": (11.0, 19.6, 90),
    # under the module, centre: battery divider, status LED, strap resistors
    "R6": (13.6, 19.6, 90), "R7": (13.6, 22.8, 90), "C8": (15.4, 22.8, 90),
    "R11": (19.8, 19.6, 90), "D5": (19.8, 22.8, 90),
    "R10": (22.6, 19.6, 90), "R9": (24.6, 19.6, 90),
    # servo switch, left side
    "J4": (2.4, 30.0, 0),
    "Q1": (7.0, 28.0, 0), "C10": (6.5, 24.8, 0), "C11": (2.2, 25.2, 90),
    "R12": (10.6, 27.4, 90), "C9": (12.4, 27.4, 90), "R13": (10.6, 31.0, 90),
    "Q2": (7.0, 34.0, 0), "R14": (10.6, 35.0, 90), "R15": (6.6, 38.5, 0),
    # USB-C + ESD, bottom centre
    "J1": (18.0, 46.3, 0), "U4": (18.0, 37.0, 0), "R1": (11.8, 39.6, 90), "R2": (24.2, 39.6, 90),
    "D1": (22.2, 35.6, 90),
    # charger + connectors, right side
    "U2": (23.8, 28.0, 0), "C1": (19.0, 26.2, 90), "R3": (19.0, 29.8, 90), "C2": (25.4, 33.0, 0),
    "R4": (27.2, 18.8, 90), "D3": (27.2, 21.9, 90), "R5": (29.4, 18.8, 90), "D4": (29.4, 21.9, 90),
    "J2": (29.6, 28.2, 90), "J3": (29.6, 38.6, 90), "D2": (26.8, 44.4, 0),
}


def mm(v):
    return pcbnew.FromMM(v)


def pt(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


def load_fp(fpid):
    lib, name = fpid.split(":")
    path = os.path.join(KI, "lib", "vent-control.pretty") if lib == "vent-control" else os.path.join(FPDIR, lib + ".pretty")
    fp = pcbnew.FootprintLoad(path, name)
    assert fp, fpid
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


def add_line(board, a, b, layer=pcbnew.Edge_Cuts, w=0.1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pt(*a))
    s.SetEnd(pt(*b))
    s.SetLayer(layer)
    s.SetWidth(mm(w))
    board.Add(s)


def add_text(board, txt, x, y, layer, size=1.0, rot=0):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txt)
    t.SetPosition(pt(x, y))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(size * 0.15))
    t.SetTextAngleDegrees(rot)
    if layer == pcbnew.B_SilkS:
        t.SetMirrored(True)
    board.Add(t)


def rect_poly(x1, y1, x2, y2):
    chain = pcbnew.SHAPE_LINE_CHAIN()
    for x, y in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
        chain.Append(mm(OX + x), mm(OY + y))
    chain.SetClosed(True)
    return chain


def build():
    board = pcbnew.BOARD()
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    ds.SetAuxOrigin(pt(0, H))     # drill/place origin = bottom-left corner (CPL coordinates)
    # JLCPCB-friendly rules
    ds.m_TrackMinWidth = mm(0.15)
    ds.m_ViasMinSize = mm(0.5)
    ds.m_MinThroughDrill = mm(0.3)
    ds.m_CopperEdgeClearance = mm(0.3)
    ds.m_MinClearance = mm(0.15)
    ds.m_HoleClearance = mm(0.25)
    ds.m_SolderMaskMinWidth = 0
    ns = ds.m_NetSettings
    dflt = ns.m_DefaultNetClass
    dflt.SetClearance(mm(0.2))
    dflt.SetTrackWidth(mm(0.25))
    dflt.SetViaDiameter(mm(0.6))
    dflt.SetViaDrill(mm(0.3))
    pwr = pcbnew.NETCLASS("Power")
    pwr.SetClearance(mm(0.2))
    pwr.SetTrackWidth(mm(0.4))
    pwr.SetViaDiameter(mm(0.6))
    pwr.SetViaDrill(mm(0.3))
    ns.m_NetClasses["Power"] = pwr

    # nets
    nets = {}
    for i, name in enumerate(design.NETS, start=1):
        n = pcbnew.NETINFO_ITEM(board, name, i)
        board.Add(n)
        nets[name] = n
    for name in design.POWER_NETS:
        nets[name].SetNetClass(pwr)

    # outline with 1 mm corner radius approximated by chamfer-free rectangle
    for a, b in (((0, 0), (W, 0)), ((W, 0), (W, H)), ((W, H), (0, H)), ((0, H), (0, 0))):
        add_line(board, a, b)

    # footprints
    for ref, (lib_id, value, fpid, mpn, lcsc, _pos, asm) in design.PARTS.items():
        fp = load_fp(fpid)
        fp.SetReference(ref)
        fp.SetValue(value)
        fp.SetPath(pcbnew.KIID_PATH(f"/{uid('sym', ref)}"))
        x, y, rot = PLACE[ref]
        fp.SetPosition(pt(x, y))
        fp.SetOrientationDegrees(rot)
        if mpn:
            fp.SetField("MPN", mpn) if hasattr(fp, "SetField") else None
        if lcsc:
            fp.SetField("LCSC", lcsc) if hasattr(fp, "SetField") else None
        if asm == "tht":
            fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_THROUGH_HOLE)
        for pad in fp.Pads():
            key = f"{ref}.{pad.GetNumber()}"
            if key in design.PIN_NET:
                pad.SetNet(nets[design.PIN_NET[key]])
        # small, tidy reference text
        rt = fp.Reference()
        rt.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
        rt.SetTextThickness(mm(0.13))
        fp.Value().SetVisible(False)
        board.Add(fp)
        if ref in ("J2", "J3"):   # polarity mark next to pin 1 (+)
            p1 = [p for p in fp.Pads() if p.GetNumber() == "1"][0].GetPosition()
            add_text(board, "+", pcbnew.ToMM(p1.x) - OX - 1.9, pcbnew.ToMM(p1.y) - OY, pcbnew.F_SilkS, 1.0)

    # antenna keep-out (no copper at all under/near the PCB antenna), both layers
    ko = pcbnew.ZONE(board)
    ko.SetIsRuleArea(True)
    ko.SetDoNotAllowTracks(True)
    ko.SetDoNotAllowVias(True)
    ko.SetDoNotAllowCopperPour(True)
    ko.SetDoNotAllowPads(False)
    ko.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET()
    ls.AddLayer(pcbnew.F_Cu)
    ls.AddLayer(pcbnew.B_Cu)
    ko.SetLayerSet(ls)
    ko.Outline().AddOutline(rect_poly(0, 0, W, ANT_Y))
    ko.SetZoneName("Antenna keepout")
    board.Add(ko)

    # silkscreen
    add_text(board, "ANTENNA - geen koper", W / 2, 2.6, pcbnew.F_Fab, 0.8)
    add_text(board, "VENT CONTROL", W / 2, 44.0, pcbnew.B_SilkS, 1.2)
    add_text(board, f"ESP32-C6  rev {design.REV}", W / 2, 46.0, pcbnew.B_SilkS, 0.9)
    add_text(board, "SERVO", 2.4, 37.0, pcbnew.F_SilkS, 0.8)
    add_text(board, "G V S", 4.6, 32.5, pcbnew.F_SilkS, 0.8, 90)
    add_text(board, "BAT", 32.6, 32.8, pcbnew.F_SilkS, 0.8)
    add_text(board, "SOLAR", 30.4, 43.4, pcbnew.F_SilkS, 0.8)
    add_text(board, "RST", 5.0, 15.6, pcbnew.F_SilkS, 0.8)
    add_text(board, "BOOT", 31.0, 15.6, pcbnew.F_SilkS, 0.8)
    return board


def write_project():
    """Net classes and design rules live in the .kicad_pro in KiCad 7."""
    import json
    pro = {
        "board": {"design_settings": {
            "defaults": {"board_outline_line_width": 0.1, "copper_line_width": 0.2},
            "rules": {"min_clearance": 0.15, "min_track_width": 0.15, "min_via_diameter": 0.5,
                      "min_through_hole_diameter": 0.3, "min_copper_edge_clearance": 0.3,
                      "min_hole_clearance": 0.25, "min_hole_to_hole": 0.25, "min_via_annular_width": 0.1,
                      "solder_mask_to_copper_clearance": 0.0, "min_silk_clearance": 0.0,
                      "min_text_height": 0.6, "min_text_thickness": 0.08},
            "rule_severities": {"lib_footprint_issues": "ignore", "lib_footprint_mismatch": "ignore",
                                "silk_edge_clearance": "warning", "silk_over_copper": "warning",
                                "silk_overlap": "warning", "holes_co_located": "error"},
            "track_widths": [0.0, 0.25, 0.4, 0.6], "via_dimensions": [{"diameter": 0.0, "drill": 0.0},
                                                                       {"diameter": 0.6, "drill": 0.3}]}},
        "meta": {"filename": "vent-control.kicad_pro", "version": 1},
        "net_settings": {
            "classes": [
                {"name": "Default", "clearance": 0.2, "track_width": 0.25, "via_diameter": 0.6, "via_drill": 0.3,
                 "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_gap": 0.25, "diff_pair_width": 0.2,
                 "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12, "line_style": 0, "pcb_color": "rgba(0, 0, 0, 0.000)",
                 "schematic_color": "rgba(0, 0, 0, 0.000)"},
                {"name": "Power", "clearance": 0.2, "track_width": 0.4, "via_diameter": 0.6, "via_drill": 0.3,
                 "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_gap": 0.25, "diff_pair_width": 0.2,
                 "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12, "line_style": 0, "pcb_color": "rgba(0, 0, 0, 0.000)",
                 "schematic_color": "rgba(0, 0, 0, 0.000)"}],
            "meta": {"version": 3},
            "netclass_patterns": [{"netclass": "Power", "pattern": n} for n in design.POWER_NETS]},
        "sheets": [[ROOT, ""]],
        "text_variables": {},
    }
    open(os.path.join(KI, "vent-control.kicad_pro"), "w").write(json.dumps(pro, indent=2) + "\n")


if __name__ == "__main__":
    write_project()
    b = build()
    b.Save(OUT)
    print("placed", len(b.GetFootprints()), "footprints ->", OUT)
