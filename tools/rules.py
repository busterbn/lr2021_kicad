"""Altium design rules (PcbDoc Rules6) -> KiCad board minimums, netclasses and .kicad_dru. Run with KiCad closed.
Usage: python3 rules.py <kicad project dir> <netmap.json: Altium net name -> KiCad net name>"""
import fnmatch, json, re, sys

KI, NETMAP = sys.argv[1], sys.argv[2]
NAME = 'LR2021_e788v01a_868_915_eval_module'
netmap = json.load(open(NETMAP))
rf_top = sorted(n for a, n in netmap.items() if any(fnmatch.fnmatchcase(a, p) for p in ('NetL*', 'NetC*', 'NetU*', 'NetA*')))
rf_bot = sorted(n for a, n in netmap.items() if fnmatch.fnmatchcase(a, 'NetA*'))
vcc = sorted(n for a, n in netmap.items() if a in ('VDD', 'VDCC', 'VIN', 'VBAT', 'VDD_RADIO', 'VDD_3V3'))

pro_file = f'{KI}/{NAME}.kicad_pro'
pro = json.load(open(pro_file))
ds = pro['board']['design_settings']
ds['rules'].update({
    'min_clearance': 0.125,               # Clearance 4.9213 mil
    'min_track_width': 0.127,             # Width All min 5 mil
    'min_via_diameter': 0.4,              # RoutingVias 15.748 mil
    'min_through_hole_diameter': 0.2,     # HoleSize min 7.874 mil
    'min_via_annular_width': 0.095,       # MinimumAnnularRing 3.7402 mil
    'min_hole_to_hole': 0.3,              # HoleToHoleClearance 11.811 mil
    'min_hole_clearance': 0.0,            # no Altium equivalent
    'min_copper_edge_clearance': 0.0,     # Altium's only outline rule is scoped to GND on Mechanical 14
    'min_silk_clearance': 0.05,           # SilkToSilk / SilkToSolderMask 1.9685 mil
    'min_text_height': 0.0,               # no Altium equivalent (silk text down to 0.5 mm)
    'min_resolved_spokes': 1,             # Altium accepts single-spoke relief connections
})
ds['track_widths'] = [0.0, 0.15, 0.2, 0.3, 0.8]
ds['via_dimensions'] = [{'diameter': 0.0, 'drill': 0.0}, {'diameter': 0.4, 'drill': 0.2}]
classes = [c for c in pro['net_settings']['classes'] if c['name'] == 'Default']
classes[0].update(clearance=0.125, track_width=0.15, via_diameter=0.4, via_drill=0.2,
                  diff_pair_width=0.381, diff_pair_gap=0.254)
rf = dict(classes[0], name='RF', priority=0)
pro['net_settings']['classes'] = classes + [rf]
pro['net_settings']['netclass_patterns'] = [{'netclass': 'RF', 'pattern': n} for n in rf_top]
json.dump(pro, open(pro_file, 'w'), indent=2)

pcb_file = f'{KI}/{NAME}.kicad_pcb'
t = open(pcb_file).read()
if '(solder_mask_min_width' not in t:   # MinimumSolderMaskSliver 1.9685 mil
    t = t.replace('\t\t(pad_to_mask_clearance 0.05)\n', '\t\t(pad_to_mask_clearance 0.05)\n\t\t(solder_mask_min_width 0.05)\n', 1)
# Altium polygons have no clearance of their own; the importer gave them 0.2 mm, which overrides the rules
t = t.replace('(connect_pads yes\n\t\t\t(clearance 0.2)\n', '(connect_pads yes\n\t\t\t(clearance 0.125)\n')
open(pcb_file, 'w').write(t)

names = lambda ns: ' || '.join(f"B.NetName == '{n}'" for n in ns)
fps = lambda ns: ' || '.join(f"A.memberOfFootprint('LR2021_e788v01a:{n}')" for n in ns)
dru = f'''(version 1)
# Translated from the Altium PcbDoc rules (Rules6). Later rules take precedence, as lower Altium priority numbers did.
# Netclass Default: Clearance 4.9213 mil, Width All pref 5.9 mil, RoutingVias 15.748/7.874 mil, DiffPairs 15/10 mil.
# Netclass RF: the Altium auto-named nets NetL*, NetC*, NetU*, NetA* used by Clearance_RF_GND_Top.

(rule "Width_All"
	(constraint track_width (min 0.127mm) (opt 0.15mm) (max 2mm)))

(rule "Width_VCC"
	(condition "{names(vcc).replace('B.', 'A.')}")
	(constraint track_width (min 0.2mm) (opt 0.8mm) (max 2mm)))

(rule "Width_GND"
	(condition "A.NetName == 'GND'")
	(constraint track_width (min 0.2mm) (opt 0.3mm) (max 3mm)))

(rule "HoleSize"
	(constraint hole_size (min 0.2mm) (max 3.6mm)))

(rule "RoutingVias"
	(condition "A.Type == 'Via'")
	(constraint via_diameter (min 0.4mm) (opt 0.4mm) (max 0.5mm))
	(constraint hole_size (min 0.2mm) (opt 0.2mm) (max 0.25mm)))

(rule "Clearance_RF_GND_Top"
	(layer F.Cu)
	(condition "A.Type == 'Zone' && A.NetName == 'GND' && B.hasNetclass('RF')")
	(constraint clearance (min 0.2mm)))

(rule "Clearance_RF_GND_Bot"
	(layer B.Cu)
	(condition "A.Type == 'Zone' && A.NetName == 'GND' && ({names(rf_bot)})")
	(constraint clearance (min 0.2mm)))

(rule "PolygonConnect_all"
	(constraint zone_connection solid))

(rule "PolygonConnect_header"
	(condition "A.NetName == 'GND' && ({fps(['H2X4-SMD-2.54', 'HDR*', 'MODULE14P*', 'HW4-2.0-00D'])})")
	(constraint zone_connection thermal_reliefs)
	(constraint thermal_spoke_width (min 0.8mm))
	(constraint thermal_relief_gap (min 0.25mm)))

(rule "PolygonConnect_SMD"
	(condition "A.NetName == 'GND' && ({fps(['c_402_smd', 'r_402_smd', 'lqw_402_smd', 'DFN8_3X3-0P65_506DB-A_OSI'])})")
	(constraint zone_connection thermal_reliefs)
	(constraint thermal_spoke_width (min 0.55mm))
	(constraint thermal_relief_gap (min 0.15mm)))

(rule "PolygonConnect_SMD_0201"
	(condition "A.NetName == 'GND' && ({fps(['LQP_201_smd', 'r_201_smd', 'c_201_smd', 'LQW_201_smd', 'SLP0603P2X3F', 'Ferrite_201_smd', 'SW4-SMD-4.5X3.8X1.8MM-90D', 'OLED30P-0.7-24.74X16.9MM'])})")
	(constraint zone_connection thermal_reliefs)
	(constraint thermal_spoke_width (min 0.35mm))
	(constraint thermal_relief_gap (min 0.15mm)))
'''
open(f'{KI}/{NAME}.kicad_dru', 'w').write(dru)
print(f'RF nets {len(rf_top)} (bottom {rf_bot}), VCC nets {vcc}')
