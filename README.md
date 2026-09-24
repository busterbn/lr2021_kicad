# LR2021 868/915 MHz eval module in KiCad

KiCad 10 port of Semtech's LR2021 reference design, the 868/915 MHz evaluation module (e788v01a), converted from the original Altium project.

- `e788v01a/` KiCad project (schematic, board, design rules, symbol and footprint libraries with 3D models)
- `tools/` scripts used for the conversion

Open `e788v01a/LR2021_e788v01a_868_915_eval_module.kicad_pro` in KiCad 10 or newer.

## Verification

- Schematic and PCB connectivity match pin by pin (`tools/check.sh`). The Altium board was used as the reference.
- The board's 107 nets match the Altium PcbDoc, and footprint placement matches Semtech's pick and place file.
- Gerbers plotted from KiCad match Semtech's production Gerbers on all copper, solder mask and paste layers (`tools/gerber_diff.py`). Drill holes match in count and size.

## Notes

- Altium designators without a trailing number (`ANT_HF`, `J7_SWD`, `868M`, `K1_USER`, `Shield`, the logos and a few more) are kept, so the silkscreen matches the original. KiCad treats them as unannotated, so Update PCB from Schematic asks you to annotate first.
- The accessories sheet is a sub-sheet of the main sheet. The Altium project was flat, so labels shared by both sheets are global labels.
- `ANT_HF` and `ANT_LF` use a 3-pin symbol with a 2-pad SMA footprint (pads 1, 2, 2), as in the original. KiCad reports "No pad found for pin 3". Both GND pins are on GND.
- Semtech's Altium design rules are in the `.kicad_pro` board setup, the netclasses and `.kicad_dru`. The RF clearance rules used Altium's auto-generated net names (`NetL*`, `NetC*`, `NetA*`). These nets are in the `RF` netclass.
- 42 vias under U1 and next to the XIAO module are not tented on the bottom side, as in the original.
- DRC still shows warnings that come from the original design: solder mask openings on Q1 that bridge nets, a small VBAT_3V3 copper island on the bottom layer, silkscreen overlaps and a few dangling track stubs.
- ERC shows off-grid warnings (Altium grid) and "power input not driven" errors from Altium pin types.
- `kicad-cli pcb drc --schematic-parity` reports "No corresponding pin" for nets without labels. This looks like a CLI issue.

## Conversion

1. KiCad: File > Import Non-KiCad Project > Altium Project, then save the schematic.
2. `make_hierarchy.py`: turns the two top-level sheets into root sheet plus sub-sheet.
3. `fix_labels.py`, `annotate_power.py`, `fix_pads.py`, `relink.py`, `netmap.py`, `fplib.py`, `export_fps.py`, `rules.py`, `fix_tenting.py`.
4. After each step, `check.sh` compares schematic and PCB connectivity.

The KiCad Python scripts (`fix_pads.py`, `export_fps.py`) run with KiCad's bundled Python. `fix_tenting.py` and `gerber_diff.py` need `olefile`, `gerbonara`, `pillow` and `numpy`.

## License

The design is Semtech's. Semtech's download contains no license terms, so ask Semtech before you publish or redistribute it. This is not an official Semtech release.
