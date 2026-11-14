#!/usr/bin/env python3
"""Step 4: production files for JLCPCB (Gerbers, drill, BOM, CPL) + schematic PDF.

Run with any python3 that can import design.py; needs kicad-cli on PATH.
"""
import csv
import os
import shutil
import subprocess
import zipfile
import design

HERE = os.path.dirname(os.path.abspath(__file__))
KI = os.path.join(HERE, "..", "kicad")
PROD = os.path.join(HERE, "..", "production")
PCB = os.path.join(KI, "vent-control.kicad_pcb")
SCH = os.path.join(KI, "vent-control.kicad_sch")
GERB = os.path.join(PROD, "gerbers")


def run(*args):
    subprocess.run(args, check=True, capture_output=True)


def gerbers():
    shutil.rmtree(GERB, ignore_errors=True)
    os.makedirs(GERB)
    layers = "F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"
    run("kicad-cli", "pcb", "export", "gerbers", "--layers", layers, "--subtract-soldermask",
        "--no-x2", "--use-drill-file-origin", "-o", GERB + "/", PCB)
    run("kicad-cli", "pcb", "export", "drill", "--format", "excellon", "--excellon-separate-th",
        "--generate-map", "--map-format", "gerberx2", "-o", GERB + "/", PCB)
    zpath = os.path.join(PROD, "vent-control-gerbers.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(GERB)):
            z.write(os.path.join(GERB, f), f)
    return zpath, sorted(os.listdir(GERB))


def bom():
    """JLCPCB BOM: Comment, Designator, Footprint, LCSC Part #  (SMT parts only)
    plus a full BOM including the hand-soldered parts."""
    groups = {}
    for ref, (lib_id, value, fp, mpn, lcsc, _p, asm) in design.PARTS.items():
        if asm == "none":
            continue
        key = (value, fp.split(":")[1], mpn, lcsc, asm)
        groups.setdefault(key, []).append(ref)

    def refkey(r):
        import re
        m = re.match(r"([A-Z]+)(\d+)", r)
        return m.group(1), int(m.group(2))
    rows = sorted(groups.items(), key=lambda kv: refkey(sorted(kv[1], key=refkey)[0]))
    with open(os.path.join(PROD, "bom-jlcpcb.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for (value, fp, mpn, lcsc, asm), refs in rows:
            if asm == "smt":
                w.writerow([f"{value} {mpn}".strip(), ",".join(sorted(refs, key=refkey)), fp, lcsc])
    with open(os.path.join(PROD, "bom-full.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Qty", "Designator", "Value", "MPN", "LCSC (verify)", "Footprint", "Assembly"])
        for (value, fp, mpn, lcsc, asm), refs in rows:
            w.writerow([len(refs), ",".join(sorted(refs, key=refkey)), value, mpn, lcsc, fp,
                        "JLCPCB SMT" if asm == "smt" else "hand solder"])


def cpl():
    tmp = os.path.join(PROD, "pos-kicad.csv")
    run("kicad-cli", "pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "front",
        "--use-drill-file-origin", "-o", tmp, PCB)
    smt = {r for r, v in design.PARTS.items() if v[6] == "smt"}
    with open(tmp) as f, open(os.path.join(PROD, "cpl-jlcpcb.csv"), "w", newline="") as g:
        w = csv.writer(g)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for row in csv.DictReader(f):
            if row["Ref"] in smt:
                w.writerow([row["Ref"], f'{float(row["PosX"]):.3f}mm', f'{float(row["PosY"]):.3f}mm',
                            "Top" if row["Side"] == "top" else "Bottom", f'{float(row["Rot"]):.0f}'])
    os.remove(tmp)


def docs():
    run("kicad-cli", "sch", "export", "pdf", "-o", os.path.join(PROD, "vent-control-schematic.pdf"), SCH)
    run("kicad-cli", "pcb", "export", "pdf", "--layers", "F.Cu,F.SilkS,F.Fab,Edge.Cuts", "--include-border-title",
        "-o", os.path.join(PROD, "vent-control-pcb-top.pdf"), PCB)
    run("kicad-cli", "pcb", "export", "pdf", "--layers", "B.Cu,B.SilkS,Edge.Cuts", "--mirror", "--include-border-title",
        "-o", os.path.join(PROD, "vent-control-pcb-bottom.pdf"), PCB)
    for side, layers, extra in (("top", "F.Cu,F.Mask,F.SilkS,Edge.Cuts", []),
                                ("bottom", "B.Cu,B.Mask,B.SilkS,Edge.Cuts", ["--mirror"])):
        run("kicad-cli", "pcb", "export", "svg", "--layers", layers, "--page-size-mode", "2",
            "--exclude-drawing-sheet", *extra, "-o", os.path.join(PROD, f"pcb-{side}.svg"), PCB)


if __name__ == "__main__":
    # the drill/place origin is set to the board's bottom-left corner by gen_pcb.py
    z, files = gerbers()
    bom()
    cpl()
    docs()
    print("gerbers:", files)
    print("written to", os.path.abspath(PROD))
