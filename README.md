# Modular flying probe — revision 18

Parametric theta / Z / radial arm with four modules covering a **100 × 100 mm PCB** and a **2 × 2 mm simultaneous probe cluster**. [Interactive assembly and downloads](https://modular-flying-probe-arm.seveibar.chatgpt.site) · [Source](https://github.com/tscircuit/probe-robot-arm).

## Printed-leadscrew actuators

The actuator geometry is pinned to [FLEX printed-leadscrew Site version 61](https://flex17-compliant-linear-actuator.seveibar.chatgpt.site/experiments/printed-leadscrew/?width=1), source commit `417da079fe5da0ac1bed3edbbaef6dc2782e65f4`. The [rack-actuator GitHub repository](https://github.com/tscircuit/rack-actuator) did not yet contain these experiments when imported. A separate pinned copy lives in `upstream/leadscrew-r16`; the arm adapter is `leadscrew_actuator.py`.

- **Z:** 4× printed-screw actuator, 206 mm base width, 168 mm output flange, 40 mm travel, full-depth NEMA17 reference (48 mm body).
- **Radial:** 1× printed-screw actuator, 80 mm base width, inverted and mounted from below through its structural lid. Full-depth NEMA14 reference (34 mm body) with a 26 mm motor bolt pitch.
- **Radial travel:** 120 mm, extended from the upstream 40 mm design. Both bearing stations move forward by 80 mm, to X=143/217 mm. The output face moves to X=235 mm at home; working screw length grows to 202 mm. Both threaded bands remain fully engaged and both bearing stations remain on the guide throughout travel.
- Both printed screws have an 8 mm lead. Motor position is centered laterally; the radial motor body center is at X=0 above the vertical stage.

The larger mechanism moves the arm pivots to **(±350, 0) and (0, ±350) mm**, requiring a **900 × 900 mm platform**. This preserves 120 mm radial travel and room for the narrow triangular probe extension. The base ring, spindle, stand and rotating deck remain shared with the standalone test fixture.

The new output face replaces the old rack-pad U clamp with a broad carrier using **eight M3 screws** on the 4× flange. The carrier also has the 2× output pattern. The radial probe holder now bolts to the vertical output flange and narrows to the probe tip.

## Mounting compatibility

Coordinates below are in the actuator's native frame: X along travel, Y across the actuator, Z up from its base. Motor face is X=0 and screw axis is Y=0, Z=42 mm. All adapter M5 clearance holes are Ø5.5 mm.

| Z variant, 40 mm stroke | Base holes: X rows; Y columns | Lid holes: X rows; Y columns | Status |
|---|---|---|---|
| Printed 2× | −3, 149; ±55 | 36, 96; ±48 | Published geometry |
| Printed 4× | −3, 149; ±97 | 36, 96; ±90 | Published geometry; installed |
| T8 2× | −3, 115; ±55 | 36, 79; ±48 | Inferred |
| T8 4× | −3, 115; ±97 | 36, 79; ±90 | Inferred |

T8 2×/4× patterns are engineering projections of the published 1× T8 longitudinal positions using the printed family's **21 mm outward offset per multiplier step**. They are not released T8 designs. Confirm them against future T8 models before drilling or relying on a drop-in fit. Z side-face holes include the union of printed and T8 longitudinal positions. The centered base/lid mounting planes remain common across widths; the narrower 2× actuator does not contact the 4× side face.

The radial carrier accepts the **1× lid patterns for both printed and T8 designs**, at stock 40 mm stroke and the custom 120 mm length:

| Radial pattern | X rows | Y columns |
|---|---|---|
| Printed, stock 40 mm | 36, 96 | ±27 |
| T8, stock 40 mm | 36, 79 | ±27 |
| Printed, extended 120 mm | 36, 176 | ±27 |
| T8, inferred extended 120 mm | 36, 159 | ±27 |

Compatibility here means matching mounting holes and datums. A stock 40 mm radial actuator cannot cover the full PCB with this arm layout. The extended T8 pattern does not specify a purchased screw or establish its stiffness. `downloads/mounting-patterns.json` contains the complete machine-readable coordinates and inference labels.

The installed Z uses four lid-face and six side-face M5 screws. The radial actuator uses four underside M5 screws. Lid interfaces have 6 mm adapter walls with M5×14 screws (8 mm entry); the Z side wall is 8 mm with M5×16 screws (8 mm entry). Receiving pilots are 9 mm deep; do not bottom screws out. Output adapters use M3×12 screws through 6 mm material into the original M3 forming pilots. These are three-ridge printed pilots, not inserts or modeled machine threads. Physical installation and load capacity remain untested.

## Rotary base and existing prints

The unchanged base has a 12T compliant pinion / 72T internal ring for **6:1 reduction**, direct full-depth NEMA17 mounting and rear RP2040-controller clearance envelopes. Four 625ZZ rollers tilt at 45° on one rounded integral block each. Their solid Ø5.1 mm printed axles use no bolts. The ring's 176 mm OD has a continuous 45° track, clear of its flat-seated M3 button heads. Bearings retain the requested 0.4 mm nominal normal overlap with the track.

Two 6002 bearings sit on the **Ø15.25 mm central spindle** with a 0.5 mm top chamfer. Its four 0.5 mm-wide relief cuts run 33.1 mm from the tip, leaving a 0.5 mm connected root. The module base and rotating deck retain their large rounded cutouts and flat print faces. The main assembly and base-test page use the same rotary-base source and canonical STL exports.

The existing base/stand print package remains usable. For the actuator change, replace the **Z support, Z-to-radial carrier, probe outrigger and both actuator assemblies**. The standalone fixture guide remains in `base_test_kit_v4/PRINT_AND_ASSEMBLY.md`.

## Viewer

Left drag orbits; middle drag pans; the wheel zooms. Right-click offers Download, Isolate, Hide part, Show All and Show hidden edges. Show All works on empty space. The page links switch between the main assembly and the synchronized base test.

The explosion separates the radial carrier, both actuator modules and Z cradle. The screw drives stay assembled and threaded. Z output screws are first loosened 6 mm and retained in the carrier; remove them fully after separating the radial actuator. Axis animation pauses and returns to its neutral pose during explosion. In assembled mode, screw rotation follows the 8 mm lead. The four-arm view coordinates the probe cluster across the board.

## Build and checks

Install the pinned Python requirements and development dependencies, then run:

```sh
python model.py --check
python check_z_mount.py
python check_leadscrew.py
python check_arm_explosion.py
python check_platform.py
python check_base_sync.py
python check_base_drive.py
python check_deck_cutouts.py
```

The adapter caches exact BREP geometry using source and configuration hashes. Upstream source is retained unchanged; the integration applies full-depth motor envelopes, NEMA14 mounting and the radial extension locally. The STL downloads preserve the upstream free-state insert pilots. Rotation and travel checks distinguish intended fastener/pilot contact and bearing print-fit interference from unintended solid overlap.

Validation covers ideal CAD geometry and reference hardware. Printed screw friction, wear, backlash, axial motor loading, stiffness, creep, homing and probing accuracy still require physical testing. Microstepping is commanded resolution, not measured positioning accuracy. At 200 steps/revolution and 1/16 microstepping, the 8 mm-lead linear axes command 0.0025 mm per microstep.

The unchanged 6:1 base drive commands 0.01875° per 1/16 microstep. With the new 350 mm board-center reach, that corresponds to about 0.115 mm tangential tip motion (about 0.136 mm at the 415 mm reach limit). The linear screw resolution does not remove this rotary-axis limitation.
