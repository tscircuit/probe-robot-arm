# Modular flying probe — revision 23

Parametric theta / Z / radial arm with four modules covering a **100 × 100 mm PCB** and a **2 × 2 mm simultaneous probe cluster**. [Interactive assembly and downloads](https://modular-flying-probe-arm.seveibar.chatgpt.site) · [Source](https://github.com/tscircuit/probe-robot-arm).

## Printed-leadscrew actuators

The actuator geometry is pinned to [FLEX printed-leadscrew Site version 61](https://flex17-compliant-linear-actuator.seveibar.chatgpt.site/experiments/printed-leadscrew/?width=1), source commit `417da079fe5da0ac1bed3edbbaef6dc2782e65f4`. The [rack-actuator GitHub repository](https://github.com/tscircuit/rack-actuator) did not yet contain these experiments when imported. A separate pinned copy lives in `upstream/leadscrew-r16`; the arm adapters are `leadscrew_actuator.py` and `direct_mount.py`.

- **Z:** selectable 1× / 2× / 4× printed-screw actuator, default 4× (206 mm base width, 168 mm output flange), 40 mm travel, inverted with the output pointing down and motor above, full-depth NEMA17 reference (48 mm body).
- **Radial:** 1× printed-screw actuator, 80 mm base width, upright, with its lid attached directly to the inverted Z output. Full-depth NEMA14 reference (34 mm body) with a 26 mm motor bolt pitch.
- **Radial travel:** 120 mm, extended from the upstream 40 mm design. The radial motor body center is 105 mm behind Z. The extra 140 mm body extension from revision 21 is removed while stroke stays 120 mm: native bearing stations are X=143/217 mm, the home output face is X=235 mm and working screw length is 202 mm. Both threaded bands remain fully engaged and both bearing stations remain on the guide throughout travel.
- Both printed screws have an 8 mm lead. The radial motor stays centered laterally, with its body center at X=−105 mm relative to Z to counter the forward structure. The world-space probe reach remains 190–310 mm.

The compact layout places the arm pivots at **(±245, 0) and (0, ±245) mm**, requiring a **690 × 690 mm platform**. This preserves 120 mm radial travel and room for the narrow triangular probe extension. The base ring, spindle, stand and rotating deck remain shared with the standalone test fixture. The radial motor rear is X=−122 mm relative to the pivot; the 4× Z housing spans X=±103 mm.

The long Z-to-radial carrier is removed. The downward Z output flange seats directly on an integral **168 × 42 × 8 mm mounting pad** on the radial lid. It has twelve modeled **M3×0.5 threaded holes**: a **31 × 31 mm NEMA17 grid**, plus the 2× and 4× output-flange patterns. The Z flange long dimension remains parallel to radial travel. The radial stage remains bottom-down.

The inverted layout lowers the **PCB surface to Z=79.2 mm**, from 284 mm in revision 22 (204.8 mm lower). The radial base is Z=118.2 mm at mid-travel; at its lowest pose it clears the support corner gussets by 6 mm. Z still has 40 mm travel and the PCB support posts are shortened accordingly.

## Balance, controller and support corner

The rearward motor offset is parameterized by `radial_setback_mm` (105 mm), independently of `radial_body_extension_mm` (0 mm). The fixed radial housing end is now X=147 mm from Z, **105 mm closer than revision 21's X=252 mm**. Its motor moves from X=−140 to −105 mm. The near bearing station is X=55 mm and the far station X=129 mm. Moving the arm pivots 105 mm inward preserves the short 43 mm triangular probe extension, 120 mm radial travel and the 100 × 100 mm PCB working area.

`check_balance.py` reports the current moving-stage center of gravity using motor masses of 140–250 g, effective printed densities of 0.2–0.65 g/cm³ and radial travel positions. At the nominal 180 g motor and 0.45 g/cm³ effective print density, the lifted assembly is estimated at 848 g, with its mid-travel center of gravity 5.5 mm forward of Z (−1.2 to +12.1 mm over radial travel). These are sensitivity estimates, not measured balance or a structural qualification. Wiring and actual slicer toolpaths are not modeled.

The inverted Z motor face is **Z=369.2 mm**, with the full 48 mm motor and rear controller above it. Controller references retain the 42.3 × 42.32 × 1.6 mm PCB, 6 mm spacers, component and USB envelopes. At least 10 mm of clear space beyond those envelopes is reserved; the controller is no longer trapped above the rotating deck. These remain packaging allowances.

The support has **two mirrored three-hole braces**, with bolt rows at X=±42 mm and Y=−28, 8 and 44 mm. Each brace has a 26 mm-wide, 28 × 28 mm, 45° internal corner gusset and solid backing. Use **two M4×25 corner bolts** at (±42, −28) through flat recessed head seats, and **seven M4×16 bolts** at the remaining brace/rear mounting positions. Three original rear mounting points are retained, for nine deck inserts in total. The shared rotating deck retains the matching inserts and supported lands from revision 22.

## Mounting compatibility

The Z support mounts **only the actuator base face**. Its 206 mm-wide frame retains a coplanar outer print face at Y=−62 mm, inward reinforcement, five rounded relief windows (R4 corners), and small rear bolt withdrawal openings. The largest opening is 178 × 94 mm. Both braces are mirror-symmetric and retain all three mounting holes. Four M5×30 through-bolts, washers and nuts secure the selected Z base pattern. The downloadable support STL is oriented with its large flat outer face on Z=0, with a 206 × 324 mm footprint and 116 mm height. Assembly STEP files retain assembly coordinates. Print fit and stiffness remain unmeasured.

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

The direct lid mounting coordinates, relative to the Z axis, are X=±15.5, ±36.5 and ±78.5 mm, each with Y=±15.5 mm. The inner four holes form the NEMA17/1× pattern; 2× and 4× each use their corresponding outer four holes as well. A shallow Ø22.2 × 2 mm center recess preserves boss clearance. Thread engagement is 7.2 mm; chase printed M3 threads with a tap and test fit before loading.

The modified Z carriage has Ø3.4 clearance holes, recessed head wells and side-open service slots. Use **M3×12 screws**, eight for 2×/4× or four for 1×, through the Z flange into the radial lid. Extend Z fully to expose the slots for installation. Heads sit 0.2 mm below the flange's back surface. The lid retains access openings for its original fasteners and shaft-clamp bolt. The separate carrier, four M5 radial mounting bolts and captive nuts are removed. Probe outrigger fasteners remain M3×12.

`downloads/mounting-patterns.json` contains all support and lid coordinates. The support retains inferred T8 base compatibility; a T8 radial enclosure would need a corresponding modified lid, and is not supplied as interchangeable CAD in this release. The current 120 mm printed-screw radial stage is the checked configuration. Physical fastener access, printed fit and load capacity still need bench testing.

## Rotary base and existing prints

The rotary base retains a 12T compliant pinion / 72T internal ring for **6:1 reduction**, direct full-depth NEMA17 mounting and rear RP2040-controller clearance envelopes. Four 625ZZ rollers tilt at 45° on one rounded integral block each. Their solid Ø5.1 mm printed axles use no bolts. The ring's 176 mm OD has a continuous 45° track, clear of its flat-seated M3 button heads. Bearings retain the requested 0.4 mm nominal normal overlap with the track.

Two 6002 bearings sit on the **Ø15.25 mm central spindle** with a 0.5 mm top chamfer. Its four 0.5 mm-wide relief cuts run 33.1 mm from the tip, leaving a 0.5 mm connected root. The module base retains its five rounded cutouts. The revised deck has four rounded windows around the two brace mounting lands. Both retain flat print faces. The main assembly and base-test page use the same rotary-base source and canonical STL exports.

For revision 23, replace the **Z support, radial lid and Z carriage** and shorten the PCB support posts. Remove the old Z-to-radial carrier and its M5 hardware. The shared rotary base, rotating deck and standalone stand retain their geometry. The Z support remains a single print with a flat outer face, but now requires a **206 × 324 mm bed footprint** (116 mm height). Check your printer's usable area before slicing. The standalone guide remains `base_test_kit_v4/PRINT_AND_ASSEMBLY.md`.

## Viewer

Left drag orbits; middle drag pans; the wheel zooms. Right-click offers Download, Isolate, Hide part, Show All and Show hidden edges. Show All works on empty space. The page links switch between the main assembly and the synchronized base test.

The bottom **Z actuator width** dropdown selects 1×, 2× or 4×, loading actual width-specific CAD, fasteners, checks, STEP assemblies and STL downloads. The radial stage remains 1×. The choice is retained in the `?width=` URL.

The module explosion withdraws the direct-lid screws into the Z flange service wells, separates the radial module sideways, and removes the Z module and support. Internal drives stay assembled and threaded. Axis animation pauses at the neutral pose during explosion; the inverted Z screw's rotation direction follows its 8 mm lead. The four-arm view coordinates the probe cluster across the board.

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
