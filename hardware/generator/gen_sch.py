#!/usr/bin/env python3
"""Generate vent-control.kicad_sch (KiCad 7) from design.py.

Connections are made with net labels placed on every pin end, so the
schematic is guaranteed to match design.NETS.
"""
import copy
import os
import uuid as _uuid
from sexp import parse, find, find_all, dump, Sym as S
import design

HERE = os.path.dirname(os.path.abspath(__file__))
KI = os.path.join(HERE, "..", "kicad")
SYSLIB = "/usr/share/kicad/symbols"
G = 2.54
NS = _uuid.UUID("6f1c2a52-5b0e-4b7e-9a51-9c1d3e0a7e11")


def uid(*key):
    return str(_uuid.uuid5(NS, "/".join(map(str, key))))


ROOT = uid("root")
_libcache = {}


def lib_file(lib):
    if lib == "vent-control":
        return os.path.join(KI, "lib", "vent-control.kicad_sym")
    return os.path.join(SYSLIB, lib + ".kicad_sym")


def load_symbol(lib_id):
    lib, name = lib_id.split(":")
    if lib not in _libcache:
        _libcache[lib] = {s[1]: s for s in find_all(parse(open(lib_file(lib)).read()), "symbol")}
    syms = _libcache[lib]
    s = copy.deepcopy(syms[name])
    ext = find(s, "extends")
    if ext:
        parent = copy.deepcopy(syms[ext[1]])
        pname = parent[1]
        props = find_all(s, "property")
        out = [S("symbol"), lib_id]
        for c in parent[2:]:
            if isinstance(c, list) and c[0] == "property":
                continue
            if isinstance(c, list) and c[0] == "symbol":
                c[1] = c[1].replace(pname + "_", name + "_", 1)
            out.append(c)
        # insert child properties after in_bom/on_board
        idx = max(i for i, c in enumerate(out) if isinstance(c, list) and c[0] in ("in_bom", "on_board", "pin_names", "pin_numbers")) + 1
        out[idx:idx] = props
        s = out
    else:
        s[1] = lib_id
    return s


def sym_pins(s):
    pins = []
    for sub in find_all(s, "symbol"):
        unit = int(sub[1].split("_")[-2])
        for p in find_all(sub, "pin"):
            at = find(p, "at")
            pins.append(dict(num=find(p, "number")[1], name=find(p, "name")[1], type=str(p[1]),
                             x=float(at[1]), y=float(at[2]), ang=int(float(at[3])),
                             hidden=S("hide") in p, unit=unit))
    return pins


def font_eff(justify=None, hide=False):
    e = [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]
    if justify:
        e.append([S("justify")] + [S(j) for j in justify])
    if hide:
        e.append(S("hide"))
    return e


LABEL_ANG = {0: 180, 180: 0, 90: 270, 270: 90}
LABEL_JUST = {0: ["left", "bottom"], 180: ["right", "bottom"], 90: ["left", "bottom"], 270: ["right", "bottom"]}


def main():
    lib_symbols = {}
    items = []
    labels = {}       # (x,y) -> net
    ncs = set()

    def place(ref, lib_id, value, fp, pos, extra_props, in_bom=True):
        if lib_id not in lib_symbols:
            lib_symbols[lib_id] = load_symbol(lib_id)
        ls = lib_symbols[lib_id]
        x0, y0 = pos[0] * G, pos[1] * G
        inst = [S("symbol"), [S("lib_id"), lib_id], [S("at"), x0, y0, 0], [S("unit"), 1],
                [S("in_bom"), S("yes" if in_bom else "no")], [S("on_board"), S("yes" if not ref.startswith("#") else "no")],
                [S("dnp"), S("no")], [S("uuid"), uid("sym", ref)]]
        for i, p in enumerate(find_all(ls, "property")):
            name = p[1]
            if name.startswith("ki_"):
                continue
            val = {"Reference": ref, "Value": value, "Footprint": fp}.get(name, p[2])
            at = find(p, "at")
            eff = find(p, "effects")
            hide = S("hide") in eff
            just = find(eff, "justify")
            inst.append([S("property"), name, val, [S("at"), x0 + float(at[1]), y0 - float(at[2]), 0],
                         font_eff(list(just[1:]) if just else None, hide)])
        for k, v in extra_props.items():
            inst.append([S("property"), k, v, [S("at"), x0, y0, 0], font_eff(None, True)])
        pins = sym_pins(ls)
        for p in pins:
            inst.append([S("pin"), p["num"], [S("uuid"), uid("pin", ref, p["num"])]])
        inst.append([S("instances"), [S("project"), "vent-control",
                                      [S("path"), "/" + ROOT, [S("reference"), ref], [S("unit"), 1]]]])
        items.append(inst)
        return x0, y0, pins

    # parts
    handled = set()
    for ref, (lib_id, value, fp, mpn, lcsc, pos, asm) in design.PARTS.items():
        extra = {}
        if mpn:
            extra["MPN"] = mpn
        if lcsc:
            extra["LCSC"] = lcsc
        x0, y0, pins = place(ref, lib_id, value, fp, pos, extra, in_bom=asm != "none")
        for p in pins:
            key = f"{ref}.{p['num']}"
            ex, ey = round(x0 + p["x"], 3), round(y0 - p["y"], 3)
            net = design.PIN_NET.get(key)
            if net:
                old = labels.get((ex, ey))
                assert old in (None, net), f"{key}: {net} vs {old} at {ex},{ey}"
                if old is None:
                    labels[(ex, ey)] = net
                    # short wire stub pointing away from the body, label at its end
                    L = 5.08 if p["ang"] in (0, 180) else 2.54
                    dx, dy = {0: (-L, 0), 180: (L, 0), 90: (0, L), 270: (0, -L)}[p["ang"]]
                    lx, ly = round(ex + dx, 3), round(ey + dy, 3)
                    items.append([S("wire"), [S("pts"), [S("xy"), ex, ey], [S("xy"), lx, ly]],
                                  [S("stroke"), [S("width"), 0], [S("type"), S("default")]],
                                  [S("uuid"), uid("wire", key)]])
                    items.append([S("label"), net, [S("at"), lx, ly, LABEL_ANG[p["ang"]]],
                                  font_eff(LABEL_JUST[p["ang"]]), [S("uuid"), uid("lbl", key)]])
                handled.add(key)
            elif key in design.NO_CONNECT:
                ncs.add((ex, ey))
                items.append([S("no_connect"), [S("at"), ex, ey], [S("uuid"), uid("nc", key)]])
                handled.add(key)
            elif p["type"] == "no_connect":
                handled.add(key)
            else:
                raise SystemExit(f"pin {key} ({p['name']}) not connected in design.py")
    missing = set(design.PIN_NET) - handled
    assert not missing, missing

    # power flags
    for ref, (net, pos) in design.PWR_FLAGS.items():
        x0, y0, pins = place(ref, "power:PWR_FLAG", "PWR_FLAG", "", pos, {}, in_bom=False)
        p = pins[0]
        items.append([S("label"), net, [S("at"), x0, y0, 270], font_eff(["right", "bottom"]),
                      [S("uuid"), uid("lbl", ref)]])

    # block titles
    notes = [((4, 4), "USB-C (5V) + ESD"), ((58, 4), "Zonnepaneel + LiPo lader (TP4056, 500 mA)"),
             ((130, 4), "3.3V LDO + batterijmeting (GPIO0, factor 2)"),
             ((4, 52), "ESP32-C6-MINI-1 (Thread/WiFi)  -  RESET / BOOT"),
             ((110, 52), "Servo voeding schakelaar (GPIO2) + servo signaal (GPIO1)"),
             ((126, 96), "Montagegaten M2")]
    for (gx, gy), t in notes:
        items.append([S("text"), t, [S("at"), gx * G, gy * G, 0],
                      [S("effects"), [S("font"), [S("size"), 2, 2], S("bold")], [S("justify"), S("left"), S("bottom")]],
                      [S("uuid"), uid("txt", t)]])
    info = ("Servo: continuous rotation (SG90/MG90 360) direct op VBAT 3.0-4.2V.\n"
            "Q1 (P-FET) schakelt de servovoeding volledig uit in deep sleep; R13/C9 geven een soft-start (~1 ms).\n"
            "R14 houdt Q2 (en dus de servo) uit tijdens reset en deep sleep.\n"
            "D1/D2: Schottky OR van USB en zonnepaneel naar de lader. R3 = 2.4k -> laadstroom 500 mA.")
    items.append([S("text"), info, [S("at"), 4 * G, 100 * G, 0], font_eff(["left", "bottom"]), [S("uuid"), uid("txt", "info")]])

    sch = [S("kicad_sch"), [S("version"), 20230121], [S("generator"), S("eeschema")],
           [S("uuid"), ROOT], [S("paper"), "A3"],
           [S("title_block"), [S("title"), design.TITLE], [S("date"), "2026-11-14"], [S("rev"), design.REV],
            [S("comment"), 1, "Gegenereerd door hardware/generator/gen_sch.py uit design.py - niet met de hand aanpassen"],
            [S("comment"), 2, "Netten zijn verbonden via labels op de pinnen"]],
           [S("lib_symbols")] + list(lib_symbols.values())] + items + \
          [[S("sheet_instances"), [S("path"), "/", [S("page"), "1"]]]]
    open(os.path.join(KI, "vent-control.kicad_sch"), "w").write(dump(sch) + "\n")
    print(f"schematic: {len(design.PARTS)} parts, {len(labels)} labels, {len(ncs)} no-connects")


if __name__ == "__main__":
    main()
