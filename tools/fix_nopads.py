"""Remove the two kinds of symbol pins that have no footprint pad (Update PCB from Schematic reports them as errors):
- Altium logo symbols carry a hidden zero-length dummy pin "0"; logo footprints have no pads. The pin is removed.
- ANT_HF1/ANT_LF1 use a 3-pin symbol (1 signal, 2 and 3 GND) on an SMA footprint with pads 1, 2, 2.
  The second GND pad becomes pad 3 (same copper, still GND).
Run with KiCad's bundled Python and KiCad closed. Usage: fix_nopads.py <kicad project dir>"""
import re, sys
import pcbnew

KI = sys.argv[1]
NAME, LIB = 'LR2021_e788v01a_868_915_eval_module', 'LR2021_e788v01a'
SMA = 'SMA_end_launch_1.2mm_6.35mm_female'
DUMMY = re.compile(r'\n(\t*)\(pin passive line\n\1\t\(at 0 0 180\)\n\1\t\(length 0\)\n\1\t\(name "L"\n.*?'
                   r'\n\1\t\(number "0"\n.*?\n\1\)(?=\n)', re.S)

def logo_blocks(t, head):
    """Apply DUMMY removal inside the lib symbol block starting with head."""
    i = t.find(head)
    if i < 0:
        return t
    indent = head[:len(head) - len(head.lstrip('\t'))]
    j = t.index(f'\n{indent})', i)
    return t[:i] + DUMMY.sub('', t[i:j]) + t[j:]

f = f'{KI}/{LIB}.kicad_sym'
t = open(f).read()
open(f, 'w').write(logo_blocks(t, '\t(symbol "Logo"\n'))

for f in (f'{KI}/{NAME}.kicad_sch', f'{KI}/{NAME}_accessories.kicad_sch'):
    t = logo_blocks(open(f).read(), f'\t\t(symbol "{LIB}:Logo"\n')
    t = re.sub(r'\n\t\(symbol\n\t\t\(lib_id "%s:Logo"\).*?\n\t\)(?=\n)' % LIB,
               lambda m: re.sub(r'\n\t\t\(pin "0"\n\t\t\t\(uuid "[^"]*"\)\n\t\t\)', '', m.group(0)), t, flags=re.S)
    open(f, 'w').write(t)

def renumber(pads):
    twos = [p for p in pads if p.GetNumber() == '2']
    if len(twos) == 2:
        twos[1].SetNumber('3')

f = f'{KI}/{LIB}.pretty/{SMA}.kicad_mod'
t = open(f).read()
i = t.index('(pad "2"', t.index('(pad "2"') + 1)
open(f, 'w').write(t[:i] + '(pad "3"' + t[i + 8:])

board = pcbnew.LoadBoard(f'{KI}/{NAME}.kicad_pcb')
for fp in board.GetFootprints():
    if fp.GetFPID().GetLibItemName() == SMA:
        renumber(list(fp.Pads()))
pcbnew.SaveBoard(f'{KI}/{NAME}.kicad_pcb', board)
print('done')
