"""Re-link PCB footprints to schematic symbols by reference (like 'Update PCB from Schematic' re-link),
and rename PCB nets to the schematic net names (connectivity is already identical)."""
import re, sys, uuid
sys.path.insert(0, sys.path[0])
exec(open(sys.path[0] + '/cmpnet.py').read().split('sch, pcb =')[0])

net_file, pcb_file = sys.argv[1], sys.argv[2]
root = parse(open(net_file).read())

comps = {}
for c in kids(kids(root, 'components')[0], 'comp'):
    ref = kids(c, 'ref')[0][1]
    sp = kids(c, 'sheetpath')[0]
    props = {kids(p, 'name')[0][1]: kids(p, 'value')[0][1] for p in kids(c, 'property')}
    fields = {kids(f, 'name')[0][1]: (f[2] if len(f) > 2 else '') for f in kids(kids(c, 'fields')[0], 'field')}
    for k in ('Reference', 'Value', 'Footprint', 'Component Class'):
        fields.pop(k, None)
    comps[ref] = dict(path=kids(sp, 'tstamps')[0][1] + kids(c, 'tstamps')[0][1], fields=fields,
                      sheetname=kids(sp, 'names')[0][1], sheetfile=props.get('Sheetfile', ''))

esc = lambda s: s.replace('\\', '\\\\').replace('"', '\\"')

def sync_fields(block, fields):
    """Set footprint properties to the symbol field values, adding hidden ones that are missing."""
    added = []
    for name, value in fields.items():
        pat = re.compile(r'(\n\t\t\(property "%s" )"(?:[^"\\]|\\.)*"' % re.escape(esc(name)))
        if pat.search(block):
            block = pat.sub(lambda m: f'{m.group(1)}"{esc(value)}"', block, count=1)
        else:
            added.append(f'\n\t\t(property "{esc(name)}" "{esc(value)}"\n\t\t\t(at 0 0 0)\n\t\t\t(layer "F.Fab")'
                         f'\n\t\t\t(hide yes)\n\t\t\t(uuid "{uuid.uuid4()}")\n\t\t\t(effects\n\t\t\t\t(font\n'
                         f'\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)')
    if added:
        last = [m.end() for m in re.finditer(r'\n\t\t\(property "(?:[^"\\]|\\.)*" .*?\n\t\t\)', block, re.S)][-1]
        block = block[:last] + ''.join(added) + block[last:]
    return block

# PCB net name -> schematic net name via shared pins
sch, pcb = sch_nets(net_file), pcb_nets(pcb_file)
s_p = pin2net(sch)
rename = {}
for pn, pins in pcb.items():
    names = {s_p[p] for p in pins if p in s_p}
    if len(names) == 1:
        rename[pn] = names.pop()
    elif names:
        sys.exit(f'net {pn} maps to several schematic nets {names}')

t = open(pcb_file).read()
out, linked, missing, board_only = [], 0, [], 0
for block in re.split(r'(?=\n\t\(footprint ")', t):
    m = re.search(r'\(property "Reference" "([^"]*)"', block)
    if block.startswith('\n\t(footprint "') and m and m.group(1) in comps:
        c = comps[m.group(1)]
        block = sync_fields(block, c['fields'])
        new =(f'(path "{c["path"]}")\n\t\t(sheetname "{esc(c["sheetname"])}")\n\t\t(sheetfile "{esc(c["sheetfile"])}")')
        block, n = re.subn(r'\(path "[^"]*"\)\n\t\t\(sheetname "(?:[^"\\]|\\.)*"\)\n\t\t\(sheetfile "(?:[^"\\]|\\.)*"\)',
                           lambda _: new, block, count=1)
        if not n:
            block, n = re.subn(r'(\n\t\t\(uuid "[^"]*"\))', lambda u: u.group(1) + '\n\t\t' + new, block, count=1)
        linked += n
    elif block.startswith('\n\t(footprint "') and m and m.group(1):
        missing.append(m.group(1))
    elif block.startswith('\n\t(footprint "') and m and '(attr board_only' not in block:
        # Altium free pads become reference-less footprints; keep them out of schematic parity
        block, n = re.subn(r'\n\t\t\(attr ([^)]*)\)', r'\n\t\t(attr \1 board_only)', block, count=1)
        if not n:
            block = re.sub(r'(\n\t\t\(uuid "[^"]*"\))', r'\1\n\t\t(attr board_only)', block, count=1)
        board_only += 1
    out.append(block)
t = ''.join(out)

# net names appear as (net "NAME") on pads, tracks, vias, zones and in (net N "NAME") declarations
def sub(m):
    name = m.group(2).replace('\\"', '"')
    new = rename.get(name, name).replace('"', '\\"')
    return f'{m.group(1)}"{new}")'
t = re.sub(r'(\(net (?:\d+ )?)"((?:[^"\\]|\\.)*)"\)', sub, t)
t = re.sub(r'(\(net_name )"((?:[^"\\]|\\.)*)"\)', sub, t)
open(pcb_file, 'w').write(t)
print(f'linked {linked} footprints; {board_only} free-pad footprints -> board_only; not linked: {missing}; renamed {sum(1 for a, b in rename.items() if a != b)} nets')
