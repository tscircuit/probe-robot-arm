# Modular flying probe — revision 22

Parametric theta / Z / radial arm with four modules covering a **100 × 100 mm PCB** and a **2 × 2 mm simultaneous probe cluster**. [Interactive assembly and downloads](https://modular-flying-probe-arm.seveibar.chatgpt.site) · [Source](https://github.com/tscircuit/probe-robot-arm).

## Printed-leadscrew actuators

The actuator geometry is pinned to [FLEX printed-leadscrew Site version 61](https://flex17-compliant-linear-actuator.seveibar.chatgpt.site/experiments/printed-leadscrew/?width=1), source commit `417da079fe5da0ac1bed3edbbaef6dc2782e65f4`. The [rack-actuator GitHub repository](https://github.com/tscircuit/rack-actuator) did not yet contain these experiments when imported. A separate pinned copy lives in `upstream/leadscrew-r16`; the arm adapter is `leadscrew_actuator.py`.

- **Z:** selectable 1× / 2× / 4× printed-screw actuator, default 4× (206 mm base width, 168 mm output flange), 40 mm travel, full-depth NEMA17 reference (48 mm body).
- **Radial:** 1× printed-screw actuator, 80 mm base width, upright with its bottom/base seated on the carrier. Full-depth NEMA14 reference (34 mm body) with a 26 mm motor bolt pitch.
- **Radial travel:** 120 mm, extended from the upstream 40 mm design. The radial motor body center is 105 mm behind Z. The extra 140 mm body extension from revision 21 is removed while stroke stays 120 mm: native bearing stations are X=143/217 mm, the home output face is X=235 mm and working screw length is 202 mm. Both threaded bands remain fully engaged and both bearing stations remain on the guide throughout travel.
- Both printed screws have an 8 mm lead. The radial motor stays centered laterally, with its body center at X=−105 mm relative to Z to counter the forward structure. The world-space probe reach remains 190–310 mm.

The compact layout places the arm pivots at **(±245, 0) and (0, ±245) mm**, requiring a **690 × 690 mm platform**. This preserves 120 mm radial travel and room for the narrow triangular probe extension. The base ring, spindle, stand and rotating deck remain shared with the standalone test fixture. The carrier extends 195 mm behind each pivot; at neutral yaw, upper parts reach about 440 mm from platform center (an 880 mm envelope), beyond the 690 mm frame.

The Z module is turned 90° about its vertical travel axis so the **long dimension of its output flange runs parallel to radial travel**. A 168 × 42 × 2 mm direct seat supports a 342 × 100 × 10 mm carrier plate. Two 8 × 16 mm raised edge ribs and a rear cross-rib reinforce it. The plate extends rearward to X=−195 mm and forward to X=147 mm. There is no narrow connecting stem. The common carrier accepts all three Z widths; 4× and 2× use eight output screws, 1× uses four. Increased stiffness is a design intent, not a measured result.

## Balance, controller and support corner

The rearward motor offset is parameterized by `radial_setback_mm` (105 mm), independently of `radial_body_extension_mm` (0 mm). The fixed radial housing end is now X=147 mm from Z, **105 mm closer than revision 21's X=252 mm**. Its motor moves from X=−140 to −105 mm. The near bearing station is X=55 mm and the far station X=129 mm. Moving the arm pivots 105 mm inward preserves the short 43 mm triangular probe extension, 120 mm radial travel and the 100 × 100 mm PCB working area.

`check_balance.py` compares the previous revision 21 long actuator layout with the compact layout. It varies assumed motor mass (140–250 g), effective printed density (0.2–0.65 g/cm³) and radial position. At the default 4× Z width, with a nominal 180 g motor and 0.45 g/cm³ effective print density, estimated moving mass falls from 1276 g to 1051 g. Mid-travel center of gravity changes from 22.7 mm forward of Z to 0.4 mm behind it; the new estimate ranges from 5.8 mm behind to 5.0 mm forward over full radial travel. These are sensitivity estimates, not measured masses or a physical balance qualification. Wiring and actual slicer toolpaths are not modeled.

Z is raised **27.6 mm** to provide rear controller space. The assembly includes a 42.3 × 42.32 × 1.6 mm PCB reference, 6 mm spacers, a 10 mm component envelope and a USB cable envelope extending 12 mm below the PCB. The lowest envelope is Z=68.4 mm, **10 mm above the central clamp**, with the space directly beneath it checked. The Z motor face is now Z=136 mm. Controller components and cable shape remain packaging allowances.

The support has **two mirrored three-hole braces**, with bolt rows at X=±42 mm and Y=−28, 8 and 44 mm. Each brace has a 26 mm-wide, 28 × 28 mm, 45° internal corner gusset and solid backing. Use **two M4×25 corner bolts** at (±42, −28) through flat recessed head seats, and **seven M4×16 bolts** at the remaining brace/rear mounting positions. Three original rear mounting points are retained, for nine deck inserts in total. The shared rotating deck gains the left-hand inserts and full bearing lands beneath both braces; its relief windows are adjusted around these lands.

## Mounting compatibility

The Z support mounts **only the actuator base face**. Its 206 mm-wide frame retains a coplanar outer print face at Y=−62 mm, inward reinforcement, five rounded relief windows (R4 corners), and small rear bolt withdrawal openings. The largest opening is 178 × 94 mm. Both braces are mirror-symmetric and retain all three mounting holes. Four M5×30 through-bolts, washers and nuts secure the selected Z base pattern. The downloadable support STL is oriented with its large flat outer face on Z=0, with a 206 × 236.8 mm footprint and 116 mm height. Assembly STEP files retain assembly coordinates. Print fit and stiffness remain unmeasured.

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

The rotary base retains a 12T compliant pinion / 72T internal ring for **6:1 reduction**, direct full-depth NEMA17 mounting and rear RP2040-controller clearance envelopes. Four 625ZZ rollers tilt at 45° on one rounded integral block each. Their solid Ø5.1 mm printed axles use no bolts. The ring's 176 mm OD has a continuous 45° track, clear of its flat-seated M3 button heads. Bearings retain the requested 0.4 mm nominal normal overlap with the track.

Two 6002 bearings sit on the **Ø15.25 mm central spindle** with a 0.5 mm top chamfer. Its four 0.5 mm-wide relief cuts run 33.1 mm from the tip, leaving a 0.5 mm connected root. The module base retains its five rounded cutouts. The revised deck has four rounded windows around the two brace mounting lands. Both retain flat print faces. The main assembly and base-test page use the same rotary-base source and canonical STL exports.

For revision 22, replace the **Z support, rotating deck, all five radial actuator printed parts (body, lid, screw, carriage and shared lower bearing carrier), Z-to-radial carrier and main platform**. The probe outrigger, Z actuator, fixed rotary base, ring, spindle and standalone stand retain their geometry. The standalone test fixture shares the revised deck; its updated guide is `base_test_kit_v4/PRINT_AND_ASSEMBLY.md`.

## Viewer

Left drag orbits; middle drag pans; the wheel zooms. Right-click offers Download, Isolate, Hide part, Show All and Show hidden edges. Show All works on empty space. The page links switch between the main assembly and the synchronized base test.

The bottom **Z actuator width** dropdown selects 1×, 2× or 4×, loading actual width-specific CAD, fasteners, checks, STEP assemblies and STL downloads. The radial stage remains 1×. The choice is retained in the `?width=` URL.

The 18-stage explosion withdraws radial base bolts, lifts the radial actuator, removes Z output screws, and separates the carrier and Z module from the single-face support. Captive radial nuts stay in the carrier. Internal drives stay assembled and threaded. Axis animation pauses at the neutral pose during explosion; assembled screw rotation follows the 8 mm lead. The four-arm view coordinates the probe cluster across the board.

## Build and checks

Install the pinned Python requirements and development dependencies, then run:

```sh
python model.py --check
python check_z_mount.py
python check_leadscrew.py
python check_balance.py
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

The unchanged 6:1 base drive commands 0.01875° per 1/16 microstep. At the 245 mm board-center reach, that corresponds to about 0.080 mm tangential tip motion (about 0.101 mm at the 310 mm reach limit). The linear screw resolution does not remove this rotary-axis limitation.
