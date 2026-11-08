# Modular flying probe — revision 19

Parametric theta / Z / radial arm with four modules covering a **100 × 100 mm PCB** and a **2 × 2 mm simultaneous probe cluster**. [Interactive assembly and downloads](https://modular-flying-probe-arm.seveibar.chatgpt.site) · [Source](https://github.com/tscircuit/probe-robot-arm).

## Printed-leadscrew actuators

The actuator geometry is pinned to [FLEX printed-leadscrew Site version 61](https://flex17-compliant-linear-actuator.seveibar.chatgpt.site/experiments/printed-leadscrew/?width=1), source commit `417da079fe5da0ac1bed3edbbaef6dc2782e65f4`. The [rack-actuator GitHub repository](https://github.com/tscircuit/rack-actuator) did not yet contain these experiments when imported. A separate pinned copy lives in `upstream/leadscrew-r16`; the arm adapter is `leadscrew_actuator.py`.

- **Z:** selectable 1× / 2× / 4× printed-screw actuator, default 4× (206 mm base width, 168 mm output flange), 40 mm travel, full-depth NEMA17 reference (48 mm body).
- **Radial:** 1× printed-screw actuator, 80 mm base width, upright with its bottom/base seated on the carrier. Full-depth NEMA14 reference (34 mm body) with a 26 mm motor bolt pitch.
- **Radial travel:** 120 mm, extended from the upstream 40 mm design. Both bearing stations move forward by 80 mm, to X=143/217 mm. The output face moves to X=235 mm at home; working screw length grows to 202 mm. Both threaded bands remain fully engaged and both bearing stations remain on the guide throughout travel.
- Both printed screws have an 8 mm lead. Motor position is centered laterally; the radial motor body center is at X=0 above the vertical stage.

The larger mechanism moves the arm pivots to **(±350, 0) and (0, ±350) mm**, requiring a **900 × 900 mm platform**. This preserves 120 mm radial travel and room for the narrow triangular probe extension. The base ring, spindle, stand and rotating deck remain shared with the standalone test fixture.

The Z module is turned 90° about its vertical travel axis so the **long dimension of its output flange runs parallel to radial travel**. A 168 × 42 × 2 mm direct seat supports a 342 × 100 × 10 mm carrier plate. Two 8 × 16 mm raised edge ribs and a rear cross-rib reinforce it. There is no narrow connecting stem. The common carrier accepts all three Z widths; 4× and 2× use eight output screws, 1× uses four. Increased stiffness is a design intent, not a measured result.

## Mounting compatibility

The Z support mounts **only the actuator base face**. Its single 206 mm-wide plate has rear gussets and retains the existing six deck bolts and deck inserts. It does not attach to the actuator lid or sides. Four M5×30 through-bolts, washers and nuts secure the active Z base pattern. Rear clearance pockets keep the 1× hardware clear of the gussets.

Coordinates below are in the actuator's native frame: X along travel, Y across the actuator, Z up from its base. Motor face is X=0 and screw axis is Y=0, Z=42 mm. All adapter M5 clearance holes are Ø5.5 mm.

| Z variant, 40 mm stroke | Base X rows | Base Y columns | Status |
|---|---|---|---|
| Printed 1× | −3, 149 | ±34 | Published geometry |
| Printed 2× | −3, 149 | ±55 | Published geometry |
| Printed 4× | −3, 149 | ±97 | Published geometry; default |
| T8 1× | −3, 115 | ±34 | Published geometry |
| T8 2× | −3, 115 | ±55 | Inferred |
| T8 4× | −3, 115 | ±97 | Inferred |

T8 2×/4× patterns project the published 1× T8 longitudinal positions using the printed family's 21 mm outward offset per multiplier step. They are not released T8 designs; confirm against future models before relying on fit. All base patterns are present in the common support.

The upright radial actuator uses four M5×20 bolts through its base into **side-loaded captive M5 nuts** in the carrier. The carrier accepts these 1× base patterns:

| Radial pattern | X rows | Y columns |
|---|---|---|
| Printed, stock 40 mm | −3, 149 | ±34 |
| T8, stock 40 mm | −3, 115 | ±34 |
| Printed, extended 120 mm | −3, 229 | ±34 |
| T8, inferred extended 120 mm | −3, 195 | ±34 |

Compatibility means matching mounting holes and datums. A stock 40 mm radial actuator cannot cover the full PCB with this layout. The extended T8 pattern does not specify a purchased screw or establish stiffness. `downloads/mounting-patterns.json` contains the complete coordinates and inference labels.

Fit the Z-to-carrier M3×16 screws first. Their heads are recessed 0.2 mm below the carrier mounting surface, clear of the radial base. They enter the original three-ridge printed pilots, not inserts or modeled machine threads. Then slide the four M5 nuts into the carrier's side pockets, seat the radial actuator bottom-down and install its four base bolts. The probe outrigger retains its M3×12 mounting screws. Physical installation and load capacity remain untested.

## Rotary base and existing prints

The unchanged base has a 12T compliant pinion / 72T internal ring for **6:1 reduction**, direct full-depth NEMA17 mounting and rear RP2040-controller clearance envelopes. Four 625ZZ rollers tilt at 45° on one rounded integral block each. Their solid Ø5.1 mm printed axles use no bolts. The ring's 176 mm OD has a continuous 45° track, clear of its flat-seated M3 button heads. Bearings retain the requested 0.4 mm nominal normal overlap with the track.

Two 6002 bearings sit on the **Ø15.25 mm central spindle** with a 0.5 mm top chamfer. Its four 0.5 mm-wide relief cuts run 33.1 mm from the tip, leaving a 0.5 mm connected root. The module base and rotating deck retain their large rounded cutouts and flat print faces. The main assembly and base-test page use the same rotary-base source and canonical STL exports.

The existing base/stand print package remains usable. For the actuator change, replace the **Z support, Z-to-radial carrier, probe outrigger and both actuator assemblies**. The standalone fixture guide remains in `base_test_kit_v4/PRINT_AND_ASSEMBLY.md`.

## Viewer

Left drag orbits; middle drag pans; the wheel zooms. Right-click offers Download, Isolate, Hide part, Show All and Show hidden edges. Show All works on empty space. The page links switch between the main assembly and the synchronized base test.

The bottom **Z actuator width** dropdown selects 1×, 2× or 4×, loading actual width-specific CAD, fasteners, checks, STEP assemblies and STL downloads. The radial stage remains 1×. The choice is retained in the `?width=` URL.

The 17-stage explosion withdraws radial base bolts, lifts the radial actuator, removes Z output screws, and separates the carrier and Z module from the single-face support. Captive radial nuts stay in the carrier. Internal drives stay assembled and threaded. Axis animation pauses at the neutral pose during explosion; assembled screw rotation follows the 8 mm lead. The four-arm view coordinates the probe cluster across the board.

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
# Repeat the CAD, mounting, explosion and platform checks for each alternative:
python model.py --config configs/z-1x.json --out output/widths/z-1x --check
python model.py --config configs/z-2x.json --out output/widths/z-2x --check
# check_z_mount.py, check_arm_explosion.py and check_platform.py accept the same flags.
python prepare_site.py
python prepare_width_variants.py
```

The adapter caches exact BREP geometry using source and configuration hashes. Upstream source is retained unchanged; the integration applies full-depth motor envelopes, NEMA14 mounting and the radial extension locally. The STL downloads preserve the upstream free-state insert pilots. Rotation and travel checks distinguish intended fastener/pilot contact and bearing print-fit interference from unintended solid overlap.

Validation covers ideal CAD geometry and reference hardware. Printed screw friction, wear, backlash, axial motor loading, stiffness, creep, homing and probing accuracy still require physical testing. Microstepping is commanded resolution, not measured positioning accuracy. At 200 steps/revolution and 1/16 microstepping, the 8 mm-lead linear axes command 0.0025 mm per microstep.

The unchanged 6:1 base drive commands 0.01875° per 1/16 microstep. With the new 350 mm board-center reach, that corresponds to about 0.115 mm tangential tip motion (about 0.136 mm at the 415 mm reach limit). The linear screw resolution does not remove this rotary-axis limitation.
