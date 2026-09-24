"""KiCad treats references without a trailing number (Altium's J7_SWD, 868M, Shield ...) as unannotated, which
blocks Update PCB from Schematic. Append "1" (as KiCad's annotator would) in schematic and board, and keep the
silkscreen as it was: the board's reference field is hidden and replaced by a plain footprint text with the old name.
Run with KiCad's bundled Python and KiCad closed. Usage: fix_refs.py <kicad project dir>"""
import re, sys
import pcbnew

KI = sys.argv[1]
NAME = 'LR2021_e788v01a_868_915_eval_module'
esc = re.escape
unannotated = lambda r: r and not r[-1].isdigit() and not r.startswith('#')

renamed = {}
for f in (f'{KI}/{NAME}.kicad_sch', f'{KI}/{NAME}_accessories.kicad_sch'):
    t = open(f).read()
    def fix(m):
        s = m.group(0)
        ref = re.search(r'\(property "Reference" "([^"]*)"', s).group(1)
        if not unannotated(ref):
            return s
        renamed[ref] = ref + '1'
        s = s.replace(f'(property "Reference" "{ref}"', f'(property "Reference" "{ref}1"', 1)
        return re.sub(r'\(reference "%s"\)' % esc(ref), f'(reference "{ref}1")', s)
    t = re.sub(r'\n\t\(symbol\n.*?\n\t\)(?=\n)', fix, t, flags=re.S)   # placed symbols only, not lib_symbols
    open(f, 'w').write(t)

board = pcbnew.LoadBoard(f'{KI}/{NAME}.kicad_pcb')
for fp in board.GetFootprints():
    old = fp.GetReference()
    if old not in renamed:
        continue
    field = fp.Reference()
    if field.IsVisible():
        text = pcbnew.PCB_TEXT(fp)
        text.SetAttributes(field)
        text.SetText(old)
        text.SetLayer(field.GetLayer())
        text.SetPosition(field.GetPosition())
        text.SetTextAngle(field.GetTextAngle())
        text.SetKeepUpright(field.IsKeepUpright())
        fp.Add(text)
        field.SetVisible(False)
    fp.SetReference(renamed[old])
pcbnew.SaveBoard(f'{KI}/{NAME}.kicad_pcb', board)
print('renamed', renamed)
