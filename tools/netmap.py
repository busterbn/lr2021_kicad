"""Map Altium net names (board before relink.py) to KiCad net names (after), via shared pads.
Usage: python3 netmap.py <board before relink> <board after relink>  > netmap.json"""
import json, sys
sys.path.insert(0, sys.path[0])
exec(open(sys.path[0] + '/cmpnet.py').read().split('sch, pcb =')[0])

old, new = pcb_nets(sys.argv[1]), pin2net(pcb_nets(sys.argv[2]))
print(json.dumps({o: new[next(iter(p))] for o, p in old.items()}, indent=0))
