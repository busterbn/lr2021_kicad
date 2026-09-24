"""Write the board's footprints back to the project footprint library (like 'Export footprints to library')."""
import sys
import pcbnew

board_file, lib = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(board_file)
io = pcbnew.PCB_IO_KICAD_SEXPR()

done = set()
for fp in board.GetFootprints():
    name = fp.GetFPID().GetLibItemName().wx_str()
    if not name or name in done:
        continue
    done.add(name)
    c = pcbnew.FOOTPRINT(fp)
    if c.IsFlipped():
        c.SetParent(board)   # flipping needs the board's layer stack
        c.Flip(c.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
    c.SetParent(None)
    c.SetOrientation(pcbnew.ANGLE_0)
    c.SetPosition(pcbnew.VECTOR2I(0, 0))
    for pad in c.Pads():
        pad.SetNetCode(0)
    c.SetReference('REF**')
    io.FootprintSave(lib, c)
print(f'saved {len(done)} footprints to {lib}')
