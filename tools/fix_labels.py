"""Altium's flat project (HierarchyMode=0) joins same-named net labels across sheets; KiCad labels are
sheet-local. Labels whose name occurs on more than one sheet become global labels, turned so the label body
points away from the wire they end. Safe to run again (existing global labels are re-oriented)."""
import re, sys
from collections import defaultdict

files = sys.argv[1:]
LABEL = re.compile(r'\t\((label|global_label) "((?:[^"\\]|\\.)*)"\n(?:\t\t\(shape \w+\)\n)?\t\t\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)\n'
                   r'.*?\n\t\t\(uuid "([^"]+)"\)(?:\n\t\t.*?)?\n\t\)(?=\n)', re.S)
WIRE = re.compile(r'\t\(wire\n\t\t\(pts\n\t\t\t\(xy ([-\d.]+) ([-\d.]+)\) \(xy ([-\d.]+) ([-\d.]+)\)')

texts = {f: open(f).read() for f in files}
sheets = defaultdict(set)
for f, t in texts.items():
    for m in LABEL.finditer(t):
        sheets[m.group(2)].add(f)
shared = {n for n, fs in sheets.items() if len(fs) > 1}

def angle(x, y, a, wires):
    """Point the label body away from a wire that ends at (x, y)."""
    for x1, y1, x2, y2 in wires:
        for (px, py), (qx, qy) in (((x1, y1), (x2, y2)), ((x2, y2), (x1, y1))):
            if abs(px - x) < 1e-3 and abs(py - y) < 1e-3:
                if qx > px: return 180
                if qx < px: return 0
                return 90 if qy > py else 270
    return int(float(a)) % 360

for f, t in texts.items():
    wires = [tuple(map(float, m.groups())) for m in WIRE.finditer(t)]
    def glabel(m):
        kind, name, x, y, a, uid = m.groups()
        if name not in shared:
            return m.group(0)
        a = angle(float(x), float(y), a, wires)
        just = 'left' if a in (0, 90) else 'right'
        return f'''\t(global_label "{name}"
\t\t(shape passive)
\t\t(at {x} {y} {a})
\t\t(fields_autoplaced yes)
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1.27 1.27)
\t\t\t)
\t\t\t(justify {just})
\t\t)
\t\t(uuid "{uid}")
\t\t(property "Intersheetrefs" "${{INTERSHEET_REFS}}"
\t\t\t(at {x} {y} {a})
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(justify {just})
\t\t\t\t(hide yes)
\t\t\t)
\t\t)
\t)'''
    open(f, 'w').write(LABEL.sub(glabel, t))
print('global labels:', sorted(shared))
