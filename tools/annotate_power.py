"""Number unannotated power symbols (#PWR?) across all sheets, like Annotate with 'Keep existing annotations'
(the GUI annotator would also renumber Altium designators without a trailing number, e.g. J7_SWD)."""
import re, sys

n = 0
for f in sys.argv[1:]:
    t = open(f).read()
    def num(m):
        global n
        n += 1
        return re.sub(r'"#PWR\?"', f'"#PWR{n:03d}"', m.group(0))
    t = re.sub(r'\n\t\(symbol\n.*?\n\t\)(?=\n)', lambda m: num(m) if '"#PWR?"' in m.group(0) else m.group(0), t, flags=re.S)
    open(f, 'w').write(t)
print(f'annotated {n} power symbols')
