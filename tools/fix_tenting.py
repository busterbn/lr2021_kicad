"""Copy per-via solder mask tenting from the Altium PcbDoc (Vias6) to the KiCad board; the importer tents all vias.
Needs olefile. Usage: python fix_tenting.py <PcbDoc> <kicad_pcb>"""
import re, struct, sys
import olefile

MM = 2.54e-6   # Altium internal unit (1e-4 mil) -> mm
d = olefile.OleFileIO(sys.argv[1]).openstream('Vias6/Data').read()
alt, i = [], 0
while i < len(d):
    n = struct.unpack('<I', d[i + 1:i + 5])[0]
    b = d[i + 5:i + 5 + n]
    i += 5 + n
    x, y = struct.unpack('<ii', b[13:21])
    alt.append((x * MM, y * MM, bool(b[1] & 0x20), bool(b[1] & 0x40)))   # tented front, back

pcb = sys.argv[2]
t = open(pcb).read()
VIA = re.compile(r'\t\(via\n\t\t\(at ([-\d.]+) ([-\d.]+)\)\n(?:(?!\t\(via\n).)*?\t\t\(tenting\n\t\t\t\(front (yes|no)\)\n\t\t\t\(back (yes|no)\)\n\t\t\)', re.S)
ki = {(round(float(m.group(1)), 3), round(float(m.group(2)), 3)): m for m in VIA.finditer(t)}

# calibrate: KiCad x = x + dx, KiCad y = cy - y (pick the offset that matches the most vias)
key = lambda x, y, dx, cy: (round(x + dx, 3), round(cy - y, 3))
x0, y0 = alt[0][:2]
dx, cy = max(((kx - x0, ky + y0) for kx, ky in ki), key=lambda o: sum(key(x, y, *o) in ki for x, y, *_ in alt[::50]))
edits, missing = {}, 0
for x, y, front, back in alt:
    m = ki.get(key(x, y, dx, cy))
    if not m:
        missing += 1
        continue
    yn = lambda v: 'yes' if v else 'no'
    if (m.group(3), m.group(4)) != (yn(front), yn(back)):
        s = m.group(0)
        edits[m.span()] = s[:s.rindex('(front')] + f'(front {yn(front)})\n\t\t\t(back {yn(back)})\n\t\t)'
for span in sorted(edits, reverse=True):
    t = t[:span[0]] + edits[span] + t[span[1]:]
open(pcb, 'w').write(t)
print(f'offset ({dx:.4f}, {cy:.4f}); {len(alt)} Altium vias, {missing} not found; changed tenting on {len(edits)}')
