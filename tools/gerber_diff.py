"""Compare KiCad-plotted Gerbers with Semtech's original Altium Gerbers by rasterizing each layer (macOS qlmanage)
and XOR-ing the images. Layers are aligned on the board outline. Needs gerbonara, pillow, numpy.
Usage: python gerber_diff.py <altium gerber dir> <kicad gerber dir> <work dir>"""
import glob, os, subprocess, sys
import numpy as np
from PIL import Image
from gerbonara import GerberFile

ALT, KI, WORK = sys.argv[1:4]
PAIRS = {'GTL': 'F_Cu', 'G1': 'In1_Cu', 'G2': 'In2_Cu', 'GBL': 'B_Cu', 'GTS': 'F_Mask', 'GBS': 'B_Mask',
         'GTP': 'F_Paste', 'GBP': 'B_Paste'}
PX = 4000       # raster size of the longer side
os.makedirs(WORK, exist_ok=True)

alt = lambda ext: glob.glob(f'{ALT}/*.{ext}')[0]
ki = lambda ext: glob.glob(f'{KI}/*.{ext.lower()}')[0]   # KiCad uses the same extensions

(ax0, ay0), (ax1, ay1) = GerberFile.open(alt('GM14')).bounding_box()
(kx0, ky0), (kx1, ky1) = GerberFile.open(ki('GM1')).bounding_box()
dx, dy = ax0 - kx0, ay0 - ky0
print(f'outline altium {ax1 - ax0:.4f} x {ay1 - ay0:.4f} mm, kicad {kx1 - kx0:.4f} x {ky1 - ky0:.4f} mm')
M = 1.0
bounds = ((ax0 - M, ay0 - M), (ax1 + M, ay1 + M))
scale = PX / max(bounds[1][0] - bounds[0][0], bounds[1][1] - bounds[0][1])   # px per mm

def raster(g, name):
    svg = f'{WORK}/{name}.svg'
    open(svg, 'w').write(str(g.to_svg(force_bounds=bounds, fg='black', bg='white')))
    subprocess.run(['qlmanage', '-t', '-s', str(PX), '-o', WORK, svg], capture_output=True)
    return np.array(Image.open(svg + '.png').convert('L')) < 128

def erode(a, n):
    for _ in range(n):
        a = a & np.roll(a, 1, 0) & np.roll(a, -1, 0) & np.roll(a, 1, 1) & np.roll(a, -1, 1)
    return a

for ext, layer in PAIRS.items():
    a = raster(GerberFile.open(alt(ext)), f'alt_{layer}')
    k = GerberFile.open(ki(ext)); k.offset(dx, dy)
    k = raster(k, f'ki_{layer}')
    diff = erode(a ^ k, 2)          # ignore anti-aliasing on edges
    Image.fromarray(((a ^ k) * 255).astype(np.uint8)).save(f'{WORK}/diff_{layer}.png')
    ys, xs = np.nonzero(diff)
    area = len(xs) / scale ** 2
    print(f'{layer:8s} {ext:4s} copper {a.sum() / scale ** 2:8.1f} / {k.sum() / scale ** 2:8.1f} mm2   diff {area:7.3f} mm2')
    if len(xs):
        # report differing spots in KiCad board coordinates
        spots = {}
        for x, y in zip(xs, ys):
            gx, gy = bounds[0][0] + x / scale - dx, bounds[1][1] - y / scale - dy
            spots.setdefault((round(gx), round(-gy)), 0)
            spots[(round(gx), round(-gy))] += 1
        top = sorted(spots.items(), key=lambda s: -s[1])[:8]
        print('   at KiCad (x, y) mm:', [(p, round(n / scale ** 2, 3)) for p, n in top])
