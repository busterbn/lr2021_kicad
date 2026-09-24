#!/bin/sh
# Export schematic netlist and compare connectivity with the PCB
P=${1:-e788v01a/LR2021_e788v01a_868_915_eval_module}
OUT=${TMPDIR:-/tmp}/lr2021.net
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli sch export netlist -o $OUT $P.kicad_sch | grep -v -E '^Done|^$'
python3 "$(dirname $0)/cmpnet.py" $OUT $P.kicad_pcb
