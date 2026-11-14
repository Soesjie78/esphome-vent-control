#!/usr/bin/env python3
"""ERC-like verification of the generated schematic (KiCad 7's kicad-cli has no ERC).

1. Exports the netlist with kicad-cli and checks it matches design.NETS exactly.
2. Checks every multi-pin net, no net with only one pin, no two power outputs on
   one net, every power-input net is driven by a power output or PWR_FLAG.
"""
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
import design

HERE = os.path.dirname(os.path.abspath(__file__))
SCH = os.path.join(HERE, "..", "kicad", "vent-control.kicad_sch")
OUT = "/tmp/vent-control-netlist.xml"

subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", OUT, SCH], check=True,
               capture_output=True)
root = ET.parse(OUT).getroot()
errors = []
got = {}
types = {}
for net in root.iter("net"):
    name = net.get("name").lstrip("/")
    nodes = [(n.get("ref"), n.get("pin"), n.get("pintype")) for n in net.iter("node")]
    real = [(r, p, t) for r, p, t in nodes if not r.startswith("#")]
    if name.startswith("unconnected-"):
        for r, p, t in real:
            if f"{r}.{p}" not in design.NO_CONNECT and "no_connect" not in t:
                errors.append(f"unconnected pin {r}.{p} ({t})")
        continue
    got[name] = sorted(f"{r}.{p}" for r, p, t in real)
    types[name] = [t for r, p, t in nodes]

exp = {k: sorted(v) for k, v in design.NETS.items()}
for k in sorted(set(exp) | set(got)):
    if exp.get(k) != got.get(k):
        errors.append(f"net {k}: expected {exp.get(k)} got {got.get(k)}")
for k, t in types.items():
    pout = sum(x.startswith("power_out") for x in t)
    if pout > 1:
        errors.append(f"net {k}: {pout} power outputs")
    flagged = any(net == k for net, _ in design.PWR_FLAGS.values())  # PWR_FLAGs are not exported
    if any(x.startswith("power_in") for x in t) and pout == 0 and not flagged:
        errors.append(f"net {k}: power input not driven")
    if len(t) < 2:
        errors.append(f"net {k}: single pin")
comps = {c.get("ref") for c in root.iter("comp")}
for ref in design.PARTS:
    if ref not in comps:
        errors.append(f"missing component {ref}")
if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"schematic check OK: {len(got)} nets, {len(comps)} components match design.py")
