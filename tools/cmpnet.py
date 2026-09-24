"""Compare connectivity between a KiCad schematic netlist and a .kicad_pcb (name-independent)."""
import re, sys
from collections import defaultdict

TOK = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+')

def parse(text):
    stack, cur = [], []
    for t in TOK.findall(text):
        if t == '(':
            stack.append(cur); cur = []
        elif t == ')':
            done = cur; cur = stack.pop(); cur.append(done)
        else:
            cur.append(t[1:-1].replace('\\"', '"') if t[0] == '"' else t)
    return cur[0]

def kids(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]

def sch_nets(path):
    root = parse(open(path).read())
    nets = {}
    for n in kids(kids(root, 'nets')[0], 'net'):
        name = kids(n, 'name')[0][1]
        pins = {(kids(x, 'ref')[0][1], kids(x, 'pin')[0][1]) for x in kids(n, 'node')}
        nets[name] = pins
    return nets

def pcb_nets(path):
    root = parse(open(path).read())
    nets = defaultdict(set)
    for fp in kids(root, 'footprint'):
        ref = next((p[2] for p in kids(fp, 'property') if p[1] == 'Reference'), '')
        if not ref:
            continue
        for pad in kids(fp, 'pad'):
            net = kids(pad, 'net')
            if pad[1] and net and net[0][-1]:
                nets[net[0][-1]].add((ref, pad[1]))
    return dict(nets)

def pin2net(nets):
    return {p: n for n, ps in nets.items() for p in ps}

sch, pcb = sch_nets(sys.argv[1]), pcb_nets(sys.argv[2])
s_p, p_p = pin2net(sch), pin2net(pcb)
common = set(s_p) & set(p_p)
sch_only_refs = sorted({r for r, _ in set(s_p) - set(p_p)})
pcb_only_refs = sorted({r for r, _ in set(p_p) - set(s_p)})
print(f'sch nets {len(sch)}, pcb nets {len(pcb)}, common pins {len(common)}')
print(f'pins only in sch (refs): {sch_only_refs[:40]}')
print(f'pins only in pcb (refs): {pcb_only_refs[:40]}')

# Group common pins by (sch net, pcb net); a clean 1:1 mapping means identical connectivity.
s2p, p2s = defaultdict(set), defaultdict(set)
for pin in common:
    s2p[s_p[pin]].add(p_p[pin]); p2s[p_p[pin]].add(s_p[pin])
merged = {p: s for p, s in p2s.items() if len(s) > 1}   # schematic split what PCB joins
split = {s: p for s, p in s2p.items() if len(p) > 1}    # schematic joins what PCB splits
print(f'\nPCB nets that are SPLIT into several schematic nets ({len(merged)}):')
for p, s in sorted(merged.items()):
    print(f'  PCB {p!r} <- sch {sorted(s)}')
print(f'\nSchematic nets that SHORT several PCB nets ({len(split)}):')
for s, p in sorted(split.items()):
    print(f'  sch {s!r} -> PCB {sorted(p)}')
