# T8×8 — 100 and 300 mm screw lengths

Select the purchased rod length independently of 1×, 2× and 4× width. The 100 mm screw gives 70 mm usable travel; the 300 mm screw gives 270 mm. Both bearing stations stay 40 mm apart and support the carriage throughout travel. The rod engages a rigid 5-to-8 mm coupling by 8 mm, with a bolted brass flange nut in the hollow carriage.

| Screw length | Travel | Bearing X stations | Base length | Overall retracted | Overall extended |
|---|---|---|---|---|---|
| 100 mm | 70 mm | 93 / 133 mm | 159 mm | 191 mm | 261 mm |
| 300 mm | 270 mm | 293 / 333 mm | 359 mm | 391 mm | 661 mm |

The screw starts at X=26 mm. The 15 mm nut remains fully engaged, with 4.5 mm of screw beyond its front face at full extension. The tip stays 25 mm inside the retracted output face. T8 threads use smooth fit envelopes in the viewer; actual helical engagement, backlash and friction are not simulated. The 300 mm rod is the lab-stock length. Long components are single-piece STLs, so check print-bed dimensions.

## Width and external mounting patterns

Widths 1×, 2× and 4× use output plates 42, 104 and 168 mm wide and bases 80, 122 and 206 mm wide. The motor and screw remain centered. Four upper bearings move outward; 1× has two lower bearings, while 2× and 4× have four. One carrier and four M5 adjustment bolts tighten the lower bearings together. Its ruthex RX-M5x9.5 inserts use Ø6.4 mm printed pilots, 10.5 mm deep. Heat-set these before assembly.

All external mounting interfaces now use a **31 mm square hole grid**. Every adjacent pair of columns and rows forms a complete NEMA17 pattern. The 1×, 2× and 4× output plates are **42, 104 and 168 mm wide**, respectively. The 2× plate was widened from 84 mm to keep a centered NEMA17 pattern while adding columns at the same 31 mm pitch; the carriage running section, bearings and base widths are unchanged.

The output plate has two rows 31 mm apart and 2, 4 or 6 columns: Y=±15.5 mm for 1×; add ±46.5 mm for 2×; add ±77.5 mm for 4×. This gives 4, 8 or 12 M3 three-ridge holes. All three retain the centered 31×31 mm NEMA17 square.

The lid and base have matching grids with five X rows at **10.5, 41.5, 72.5, 103.5 and 134.5 mm**, measured forward from the motor front. Their Y columns match the output plate. There are **10, 20 or 30 short M3 insert seats on each face** for 1×, 2× or 4×. The first NEMA17 square stays centered at X=26, Y=0 mm, just ahead of the motor. Continuous ribs connect the insert seats around the cutouts. The two front structural lid screws move outward to clear the grid.

A wider actuator plate can also be mounted with its width along the host length (X), including on a narrow 1× host:

| Mounted plate | Center X | Supported X rows (at Y=±15.5) | Bolts |
|---|---|---|---|
| 1× | 26 mm | 10.5, 41.5 | 4 |
| 2× | 57 or 88 mm | First four or last four grid rows | All 8 |
| 4×, rear overhang | 57 mm | All five grid rows | 10 of 12 |
| 4×, front overhang | 88 mm | All five grid rows | 10 of 12 |

The unused 4× outer pair is at X=−20.5 mm or X=165.5 mm, outside this five-row grid. These are alternative mounting positions, not a simultaneous two-actuator arrangement. An overhanging plate and its attached mechanism still require a load and clearance check for the actual application. The CAD report verifies matching holes and screw access, not attached-actuator strength.

Use [ruthex RX-M3Sx4.0 short inserts](https://www.ruthex.de/en/collections/gewindeeinsatze/products/ruthex-gewindeeinsatz-m3s-100stuck-rx-m3x4-0-short-messing-gewindebuchsen-fur-3d-druck), nominal Ø4.6×4 mm. Printed pilots are Ø4 mm with a Ø4.8 mm entry taper; the pilot diameter is a prototype fit to calibrate on the actual PETG print. Install lid inserts from above and base inserts from below. Lid seats are open-bottomed. Base pilots are 5 mm deep, leaving 1 mm beyond the 4 mm insert; where a grid hole lies below a structural foot, backing is retained above the pilot instead of drilling through the foot. Other base seats pass through the floor. Limit external screw entry to 4 mm from the lid top or 5 mm from the base underside. External mounting screws are not included because their length depends on the attached structure. The viewer shows installed Ø4.64 mm cavities around the insert references; STLs retain undersized pilots.

External side mounting bosses and side holes are removed. The former perimeter M5 floor pads and external M5 lid receivers are replaced by the matched M3 patterns. These mounts do not preserve the previous external hole locations.

## Windowed structural lid

The lid stays at Z=64–68 mm and does not increase the 68 mm assembly height. Rounded through-windows remove material between a continuous 8 mm perimeter and transverse fixing/mounting ribs. Mounting rows retain full-width bands of material; intermediate ribs divide long windows. The geometry report records the exact CAD volume reduction for the selected configuration, not printed mass or a stiffness rating.

Six recessed M3×12 button-head screws fasten the lid into the base's 12 mm-deep three-ridge pilots. These structural fasteners are separate from the external M3 insert patterns. Driver access remains for the four carrier-adjustment bolts and motor bolts; extend the carriage to reach the motor bolts.

## Bearings and running faces

The carriage runs on smooth flats with no raised side rails. The CAD checks include nominal bearing alignment and ±1 mm axial displacement relative to the carriage. The base and carrier retain their existing clearance channels. Solid Ø4.8 mm axles keep the 6.4 mm-wide retaining shoulders and extended 30° bent tips, without relief slots. The Ø7.4 mm inner-race lands and surrounding Ø17 mm face relief keep the outer rings and shields clear.

The bearings must be forced over the solid heads. The assembly report records these head/bore contacts separately; it does not validate insertion force, PETG strain or the ability to force the bearing on without damage. The viewer does not simulate bending. Tilt, preload, friction, wear and print fit need physical testing.

## Assembly and downloads

Individual STL downloads and each configuration's ZIP contain the matching printable geometry. The bundle includes CAD source, configuration, bill of materials and validation report. Heat-set the mounting inserts while the lid and base are accessible; mount the base from below. Install the adjustable carrier, bearings and drive before closing the lid. The exploded view removes lid screws, lid (with its inserts), carriage, drive and bearing packs, then the carrier. M5 inserts remain attached to the carrier. The printed screw rotates during carriage withdrawal.

This is a geometry prototype, not a strength, stiffness or fatigue rating. No external screw-support bearings are fitted. Bought motor and hardware meshes are fit references. Printed threads, insert pilots and three-ridge holes require calibration for the actual print process.

## Rebuilding

Install `python -m pip install -r experiments/t8-leadscrew/requirements.txt`, then run `python experiments/t8-leadscrew/model.py --screw-length 300 --width 1 --check`. The site offers 100 and 300 mm screws, each at widths 1, 2 and 4.

The 100 mm, 1× assets stay at the experiment root; wider models use `widths/2x/` and `widths/4x/`. The 300 mm models use `lengths/300mm/` with the same width subdirectories. Each configuration has matching STL files, source and a validation report. `--quick` produces an unvalidated preview only.

