#!/usr/bin/env bash
# Regenerate the complete KiCad project + production files from design.py.
# Requires KiCad 7 (kicad-cli + pcbnew python module, e.g. Ubuntu: apt install kicad).
set -euo pipefail
cd "$(dirname "$0")"
KPY=/usr/bin/python3                       # python that can 'import pcbnew'
$KPY gen_lib.py                            # project symbols + ESP32-C6-MINI-1 footprint
$KPY gen_sch.py                            # schematic
$KPY check_sch.py                          # netlist check (kicad-cli 7 has no ERC)
$KPY route.py 2> >(grep -v "swig/python detected" >&2)      # placement + routing
$KPY finish_pcb.py 2> >(grep -v "swig/python detected" >&2) # GND pours + DRC (fails on errors)
$KPY export.py                             # gerbers, drill, BOM, CPL, PDFs
