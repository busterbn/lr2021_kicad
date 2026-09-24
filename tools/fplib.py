"""Point symbols and board footprints at one project footprint library.

The board's footprints come from three Altium libraries (e783/e787/e788, with case-only name differences
such as C_201_SMD/c_201_smd); the schematic Footprint fields already use one name per footprint.
Board footprints get that name, and all references use the library nickname LIB.
Usage: python3 fplib.py <kicad project dir> <schematic netlist>"""
import re, sys
sys.path.insert(0, sys.path[0])
exec(open(sys.path[0] + '/cmpnet.py').read().split('sch, pcb =')[0])

KI, NET = sys.argv[1], sys.argv[2]
NAME, LIB, OLD = 'LR2021_e788v01a_868_915_eval_module', 'LR2021_e788v01a', 'LR2021_e788v01a_868_915_eval_module-import-fps:'

root = parse(open(NET).read())
fpname = {kids(c, 'ref')[0][1]: kids(c, 'footprint')[0][1].split(':')[-1]
          for c in kids(kids(root, 'components')[0], 'comp') if kids(c, 'footprint')}

pcb = f'{KI}/{NAME}.kicad_pcb'
out = []
for block in re.split(r'(?=\n\t\(footprint ")', open(pcb).read()):
    m = re.search(r'\(property "Reference" "([^"]*)"', block)
    if block.startswith('\n\t(footprint "') and m and m.group(1) in fpname:
        block = re.sub(r'^\n\t\(footprint "[^"]*"', f'\n\t(footprint "{LIB}:{fpname[m.group(1)]}"', block)
    out.append(block)
open(pcb, 'w').write(''.join(out))

for f in (f'{KI}/{NAME}.kicad_sch', f'{KI}/{NAME}_accessories.kicad_sch', f'{KI}/{LIB}.kicad_sym'):
    t = open(f).read()
    open(f, 'w').write(t.replace(OLD, f'{LIB}:'))

open(f'{KI}/fp-lib-table', 'w').write(
    f'(fp_lib_table\n\t(version 7)\n\t(lib (name "{LIB}") (type "KiCad") (uri "${{KIPRJMOD}}/{LIB}.pretty") (options "") (descr ""))\n)\n')
open(f'{KI}/sym-lib-table', 'w').write(
    f'(sym_lib_table\n\t(version 7)\n\t(lib (name "{LIB}") (type "KiCad") (uri "${{KIPRJMOD}}/{LIB}.kicad_sym") (options "") (descr ""))\n)\n')
print(f'{len(set(fpname.values()))} footprint names, {len(fpname)} parts -> {LIB}')
