#!/usr/bin/env python3
"""Generate the project-specific KiCad 7 library (symbols + footprint).

* ESP32-C6-MINI-1 footprint: converted from the official KiCad library
  (gitlab.com/kicad/libraries/kicad-footprints, KiCad 10 format) to KiCad 7
  format.  Pad geometry is copied 1:1.  The huge 43x20 mm antenna keep-out
  courtyard is replaced by the module outline; the antenna keep-out is drawn
  as a board-level rule area in the PCB instead.
* ESP32-C6-MINI-1 symbol: pin numbers/names/types taken from the official
  KiCad symbol (lib/upstream/ESP32-C6-MINI-1.kicad_sym), re-drawn.
* TP4056 symbol: from the TP4056 datasheet (ESOP-8):
  1 TEMP, 2 PROG, 3 GND, 4 VCC, 5 BAT, 6 STDBY, 7 CHRG, 8 CE, EP = GND.
"""
import os
import re
from sexp import parse, find, find_all, dump, Sym as S

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "kicad", "lib")
UP = os.path.join(LIB, "upstream")


def font(size=1.27):
    return [S("effects"), [S("font"), [S("size"), size, size]]]


def prop(name, value, x, y, hide=False, idx=None):
    p = [S("property"), name, value]
    if idx is not None:
        p += [[S("id"), idx]]
    p += [[S("at"), x, y, 0], font()]
    if hide:
        p[-1].append(S("hide"))
    return p


def pin(num, name, typ, x, y, ang, hide=False, length=2.54):
    p = [S("pin"), S(typ), S("line"), [S("at"), x, y, ang], [S("length"), length]]
    if hide:
        p.append(S("hide"))
    p += [[S("name"), name, font()], [S("number"), str(num), font()]]
    return p


def symbol(name, ref, value, fp, ds, desc, rect, pins, ref_y, val_y, kw=""):
    x1, y1, x2, y2 = rect
    return [S("symbol"), name, [S("pin_names"), [S("offset"), 1.016]],
            [S("in_bom"), S("yes")], [S("on_board"), S("yes")],
            prop("Reference", ref, x1, ref_y, idx=0),
            prop("Value", value, x1, val_y, idx=1),
            prop("Footprint", fp, 0, 0, True, idx=2),
            prop("Datasheet", ds, 0, 0, True, idx=3),
            prop("ki_keywords", kw, 0, 0, True, idx=4),
            prop("ki_description", desc, 0, 0, True, idx=5),
            [S("symbol"), f"{name}_0_1",
             [S("rectangle"), [S("start"), x1, y1], [S("end"), x2, y2],
              [S("stroke"), [S("width"), 0.254], [S("type"), S("default")]],
              [S("fill"), [S("type"), S("background")]]]],
            [S("symbol"), f"{name}_1_1"] + pins]


def esp32_symbol():
    up = parse(open(os.path.join(UP, "ESP32-C6-MINI-1.kicad_sym")).read())
    sym = find(up, "symbol")
    upins = {}

    def walk(n):
        for c in n:
            if isinstance(c, list) and c:
                if c[0] == "pin":
                    upins[find(c, "number")[1]] = (find(c, "name")[1], str(c[1]))
                else:
                    walk(c)
    walk(sym)
    assert len(upins) == 53, len(upins)
    byname = {}
    for n, (nm, t) in upins.items():
        byname.setdefault(nm, []).append(n)

    pins = []
    W = 15.24
    # left side
    left = ["3V3", "EN", None] + [f"IO{i}" for i in range(8)]
    y = 15.24
    for nm in left:
        if nm:
            n = byname[nm][0]
            pins.append(pin(n, nm, upins[n][1], -W - 2.54, y, 0))
        y -= 2.54
    right = ["IO8", "IO9", None, "IO12", "IO13", "IO14", "IO15", None] + \
            [f"IO{i}" for i in range(18, 24)] + [None, "RXD0", "TXD0"]
    y = 15.24
    for nm in right:
        if nm:
            n = byname[nm][0]
            pins.append(pin(n, nm, upins[n][1], W + 2.54, y, 180))
        y -= 2.54
    ybot = y + 2.54 - 5.08
    # NC pins along the top
    x = -7.62
    for n in sorted(byname["NC"], key=int):
        pins.append(pin(n, "NC", "no_connect", x, 20.32, 270, length=2.54))
        x += 2.54
    # GND: all stacked at one point, first visible power_in, rest hidden passive
    gnds = sorted(byname["GND"], key=int)
    for i, n in enumerate(gnds):
        pins.append(pin(n, "GND", "power_in" if i == 0 else "passive", 0, ybot - 2.54, 90, hide=i > 0))
    rect = (-W, 17.78, W, ybot)
    return symbol("ESP32-C6-MINI-1", "U", "ESP32-C6-MINI-1-N4", "vent-control:ESP32-C6-MINI-1",
                  "https://www.espressif.com/sites/default/files/documentation/esp32-c6-mini-1_mini-1u_datasheet_en.pdf",
                  "ESP32-C6 module, Wi-Fi 6, BLE, Thread/Zigbee, PCB antenna", rect, pins,
                  ref_y=19.05 + 3.81, val_y=ybot - 6.35, kw="ESP32 C6 Thread Zigbee")


def tp4056_symbol():
    pins = [
        pin(4, "VCC", "power_in", -12.7, 5.08, 0),
        pin(8, "CE", "input", -12.7, 2.54, 0),
        pin(1, "TEMP", "input", -12.7, -2.54, 0),
        pin(2, "PROG", "passive", -12.7, -5.08, 0),
        pin(5, "BAT", "power_out", 12.7, 5.08, 180),
        pin(7, "~{CHRG}", "open_collector", 12.7, 0, 180),
        pin(6, "~{STDBY}", "open_collector", 12.7, -2.54, 180),
        pin(3, "GND", "power_in", 0, -12.7, 90),
        pin(9, "EP", "passive", 2.54, -12.7, 90),
    ]
    return symbol("TP4056", "U", "TP4056", "Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.3mm",
                  "https://dlnmh9ip6v2uc.cloudfront.net/datasheets/Prototyping/TP4056.pdf",
                  "1A standalone linear Li-ion charger, ESOP-8", (-10.16, 7.62, 10.16, -10.16), pins,
                  ref_y=8.89, val_y=-15.24, kw="charger lithium")


def write_symlib():
    lib = [S("kicad_symbol_lib"), [S("version"), 20220914], [S("generator"), S("vent_control_gen")],
           esp32_symbol(), tp4056_symbol()]
    open(os.path.join(LIB, "vent-control.kicad_sym"), "w").write(dump(lib) + "\n")


# ---------------------------------------------------------------- footprint
def conv_stroke(n):
    st = find(n, "stroke")
    w = find(st, "width")[1]
    return [S("stroke"), [S("width"), float(w)], [S("type"), S("solid")]]


def esp32_footprint():
    up = parse(open(os.path.join(UP, "ESP32-C6-MINI-1.kicad_mod")).read())
    out = [S("footprint"), "ESP32-C6-MINI-1", [S("version"), 20221018], [S("generator"), S("vent_control_gen")],
           [S("layer"), "F.Cu"],
           [S("descr"), "ESP32-C6-MINI-1 module. Converted from the official KiCad library to KiCad 7 format. "
                        "https://www.espressif.com/sites/default/files/documentation/esp32-c6-mini-1_mini-1u_datasheet_en.pdf"],
           [S("tags"), "ESP32 C6 module"], [S("attr"), S("smd")],
           [S("fp_text"), S("reference"), "REF**", [S("at"), 0, 6.9], [S("layer"), "F.SilkS"],
            [S("effects"), [S("font"), [S("size"), 1, 1], [S("thickness"), 0.15]]]],
           [S("fp_text"), S("value"), "ESP32-C6-MINI-1", [S("at"), 0, 8.4], [S("layer"), "F.Fab"],
            [S("effects"), [S("font"), [S("size"), 1, 1], [S("thickness"), 0.15]]]],
           [S("fp_text"), S("user"), "${REFERENCE}", [S("at"), 0, 0], [S("layer"), "F.Fab"],
            [S("effects"), [S("font"), [S("size"), 1, 1], [S("thickness"), 0.15]]]],
           [S("fp_text"), S("user"), "Antenna", [S("at"), 0, -8.3], [S("layer"), "Cmts.User"],
            [S("effects"), [S("font"), [S("size"), 1, 1], [S("thickness"), 0.15]]]]]
    for n in up:
        if not isinstance(n, list):
            continue
        if n[0] == "fp_line":
            layer = find(n, "layer")[1]
            if layer == "F.CrtYd":
                continue
            out.append([S("fp_line"), [S("start")] + [float(v) for v in find(n, "start")[1:]],
                        [S("end")] + [float(v) for v in find(n, "end")[1:]], conv_stroke(n), [S("layer"), layer]])
        elif n[0] == "fp_poly":
            pts = [S("pts")] + [[S("xy"), float(p[1]), float(p[2])] for p in find_all(find(n, "pts"), "xy")]
            out.append([S("fp_poly"), pts, conv_stroke(n), [S("fill"), S("solid")], [S("layer"), find(n, "layer")[1]]])
        elif n[0] == "pad":
            at = find(n, "at")
            p = [S("pad"), n[1], S(n[2]), S(n[3]), [S("at")] + [float(v) for v in at[1:]],
                 [S("size")] + [float(v) for v in find(n, "size")[1:]]]
            pr = find(n, "property")
            if pr:
                p.append([S("property"), S(pr[1])])
            p.append([S("layers")] + list(find(n, "layers")[1:]))
            for k in ("roundrect_rratio", "chamfer_ratio"):
                v = find(n, k)
                if v:
                    p.append([S(k), float(v[1])])
            ch = find(n, "chamfer")
            if ch:
                p.append([S("chamfer")] + [S(x) for x in ch[1:]])
            zc = find(n, "zone_connect")
            if zc:
                p.append([S("zone_connect"), int(zc[1])])
            out.append(p)
    # courtyard = module outline + 0.25 mm
    c = [(-6.85, -11.25), (6.85, -11.25), (6.85, 5.85), (-6.85, 5.85)]
    for i in range(4):
        a, b = c[i], c[(i + 1) % 4]
        out.append([S("fp_line"), [S("start"), *a], [S("end"), *b],
                    [S("stroke"), [S("width"), 0.05], [S("type"), S("solid")]], [S("layer"), "F.CrtYd"]])
    npads = len([x for x in out if isinstance(x, list) and x and x[0] == "pad"])
    assert npads == 61, npads
    open(os.path.join(LIB, "vent-control.pretty", "ESP32-C6-MINI-1.kicad_mod"), "w").write(dump(out) + "\n")


if __name__ == "__main__":
    write_symlib()
    esp32_footprint()
    print("library written")
