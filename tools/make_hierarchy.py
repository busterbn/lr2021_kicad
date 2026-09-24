"""Turn the importer's two top-level sheets into a classic hierarchy (root sheet + accessories sub-sheet),
so kicad-cli (netlist, ERC, DRC parity) sees the whole design. Run with KiCad closed."""
import json, re, sys

KI = sys.argv[1]
NAME = 'LR2021_e788v01a_868_915_eval_module'
ROOT, SUB = f'{KI}/{NAME}.kicad_sch', f'{KI}/{NAME}_accessories.kicad_sch'
pro = json.load(open(f'{KI}/{NAME}.kicad_pro'))
tops = pro['schematic']['top_level_sheets']
root_id, sub_id = tops[0]['uuid'], tops[1]['uuid']
X, Y, W, H = 177.8, 340.36, 63.5, 20.32

sheet = f'''	(sheet
		(at {X} {Y})
		(size {W} {H})
		(exclude_from_sim no)
		(in_bom yes)
		(on_board yes)
		(dnp no)
		(fields_autoplaced yes)
		(stroke
			(width 0)
			(type solid)
		)
		(fill
			(color 0 0 0 0.0000)
		)
		(uuid "{sub_id}")
		(property "Sheetname" "Accessories"
			(at {X} {Y - 0.7112} 0)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
				(justify left bottom)
			)
		)
		(property "Sheetfile" "{NAME}_accessories.kicad_sch"
			(at {X} {Y + H + 0.5858} 0)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
				(justify left top)
			)
		)
		(instances
			(project "{NAME}"
				(path "/{root_id}"
					(page "2")
				)
			)
		)
	)
'''

t = open(ROOT).read()
if f'(uuid "{sub_id}")' not in t:
    i = t.index('\t(sheet_instances')
    t = t[:i] + sheet + t[i:]
    open(ROOT, 'w').write(t)

s = open(SUB).read()
s = s.replace(f'(path "/{sub_id}"', f'(path "/{root_id}/{sub_id}"')
s = re.sub(r'\t\(sheet_instances\n.*?\n\t\)\n', '', s, flags=re.S)
open(SUB, 'w').write(s)

pro['schematic']['top_level_sheets'] = tops[:1]
pro['schematic']['used_designators'] = ''
json.dump(pro, open(f'{KI}/{NAME}.kicad_pro', 'w'), indent=2)
print('hierarchy: root', root_id, 'sub', sub_id)
