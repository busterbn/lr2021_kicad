"""Give Altium's unnumbered footprint pads their electrical meaning (run with KiCad's bundled python).

- overlaps numbered pads of one number  -> takes that number (and net), like KiCad's own library importer
- overlaps numbered pads of 2+ numbers  -> net-tie copper: becomes a copper polygon, footprint gets a net-tie group
- overlaps board copper of a single net  -> takes the number of the footprint pad on that net (if any)
"""
import sys
import pcbnew

board = pcbnew.LoadBoard(sys.argv[1])
cu = [l for l in board.GetEnabledLayers().CuStack()]
tracks = list(board.GetTracks())

def collide(a, b):
    for layer in cu:
        if a.IsOnLayer(layer) and b.IsOnLayer(layer) and \
                a.GetEffectiveShape(layer).Collide(b.GetEffectiveShape(layer)):
            return True
    return False

report, ties = [], set()
for fp in board.GetFootprints():
    pads = list(fp.Pads())
    named = [p for p in pads if p.GetNumber()]
    for u in [p for p in pads if not p.GetNumber() and p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH]:
        ref = fp.GetReference()
        hits = {}
        for n in named:
            if collide(u, n):
                hits.setdefault(n.GetNumber(), n)
        if len({n.GetNetname() for n in hits.values()}) == 1:
            n = next(iter(hits.values()))
            u.SetNumber(n.GetNumber()); u.SetNet(n.GetNet())
            report.append(f'{ref}: pad -> {n.GetNumber()} ({n.GetNetname()})')
        elif len(hits) > 1:
            for layer in cu:
                if not u.IsOnLayer(layer):
                    continue
                shape = pcbnew.PCB_SHAPE(fp, pcbnew.SHAPE_T_POLY)
                shape.SetPolyShape(u.GetEffectivePolygon(layer, pcbnew.ERROR_INSIDE))
                shape.SetLayer(layer); shape.SetFilled(True); shape.SetWidth(0)
                fp.Add(shape)
            fp.Remove(u)
            group = ', '.join(sorted(hits))
            if (ref, group) not in ties:
                ties.add((ref, group)); fp.AddNetTiePadGroup(group)
            report.append(f'{ref}: jumper copper -> net tie "{group}"')
        else:
            box = u.GetBoundingBox()
            nets = {t.GetNetname() for t in tracks
                    if t.GetNetname() and t.GetBoundingBox().Intersects(box) and collide(u, t)}
            match = [n for n in named if n.GetNetname() in nets]
            if len(nets) == 1 and match:
                u.SetNumber(match[0].GetNumber()); u.SetNet(match[0].GetNet())
                report.append(f'{ref}: mechanical pad on {nets} -> {match[0].GetNumber()}')
            elif nets:
                report.append(f'{ref}: UNRESOLVED pad touching {nets}')

pcbnew.SaveBoard(sys.argv[1], board)
print('\n'.join(report))
