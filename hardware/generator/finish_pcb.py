#!/usr/bin/env python3
"""Step 3: GND pours on both layers, zone fill and KiCad DRC (KiCad python).

Writes the DRC report to hardware/production/drc-report.txt and exits non-zero
when there are DRC errors or unconnected items.
"""
import os
import re
import sys
import pcbnew
from gen_pcb import OUT, W, H, ANT_Y, rect_poly, mm

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(HERE, "..", "production", "drc-report.txt")


def add_pours(board):
    for z in list(board.Zones()):
        if not z.GetIsRuleArea():
            board.Remove(z)
    gnd = board.FindNet("GND")
    for layer, prio in ((pcbnew.F_Cu, 0), (pcbnew.B_Cu, 0)):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(gnd)
        z.SetZoneName(f"GND {board.GetLayerName(layer)}")
        z.SetAssignedPriority(prio)
        z.SetLocalClearance(mm(0.25))
        z.SetMinThickness(mm(0.2))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        z.Outline().AddOutline(rect_poly(0, ANT_Y, W, H))
        board.Add(z)
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())


def drc(board):
    """Returns (errors, warnings, report_text); severities as written by KiCad."""
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    pcbnew.WriteDRCReport(board, REPORT, pcbnew.EDA_UNITS_MILLIMETRES, True)
    txt = open(REPORT).read()
    errs, warns = {}, {}
    for m in re.finditer(r"^\[(\w+)\]: .*\n.*Severity: (\w+)", txt, re.M):
        d = errs if m.group(2) == "error" else warns
        d[m.group(1)] = d.get(m.group(1), 0) + 1
    return errs, warns, txt


if __name__ == "__main__":
    board = pcbnew.LoadBoard(OUT)
    add_pours(board)
    board.Save(OUT)
    board = pcbnew.LoadBoard(OUT)
    errs, warns, txt = drc(board)
    print(f"DRC errors: {sum(errs.values())} {errs}")
    print(f"DRC warnings: {sum(warns.values())} {warns}")
    sys.exit(1 if errs else 0)
