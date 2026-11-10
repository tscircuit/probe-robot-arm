# Modular flying probe — revision 24

Parametric theta / Z / radial arm with four modules covering a **100 × 100 mm PCB** and a **2 × 2 mm simultaneous probe cluster**. [Interactive assembly and downloads](https://modular-flying-probe-arm.seveibar.chatgpt.site) · [Source](https://github.com/tscircuit/probe-robot-arm).

## Rigid base experiment

A separate [Rigid base tab](https://modular-flying-probe-arm.seveibar.chatgpt.site/rigid-base.html) retains the internal-gear drive with a **module-1 264T/12T gear pair (22:1)**, 296 mm ring, supported pinion journal, thicker base/deck, wider support mounts and two printed rear trusses plus two front braces attached to the Z actuator lid. The lower Z-support flange reaches the full 148 mm ring radius. The existing main assembly and standalone base remain unchanged. This is a single-arm mechanical prototype; physical vibration, backlash and accuracy have not been measured. The fixed base and stand are 312 mm square; the rear extensions are shortened so all 27 prints fit the H2S dimensional envelope. The hollow-backbone experiment has been removed. See [design, hardware, rebuild instructions and validation scope](rigid_base/README.md).

## Printed-leadscrew actuators

The actuator geometry is pinned to [rack-actuator revision 24](https://github.com/tscircuit/rack-actuator/commit/cc86a8e20de12db4f5eda797278d3ff07537a772), source commit `cc86a8e20de12db4f5eda797278d3ff07537a772`. The unchanged upstream source lives in `upstream/leadscrew-grid31`; the arm adapters are `leadscrew_actuator.py` and `direct_mount.py`. This incorporates the current 31 mm mounting grid, short M3 mounting inserts, retained bearing axles and nut-clamped printed screws.

- **Z:** selectable 1× / 2× / 4× printed-screw actuator, default 4× (206 mm base width, 168 mm output flange), 40 mm travel, inverted with the output pointing down and motor above, full-depth NEMA17 reference (48 mm body).
- **Radial:** 1× printed-screw actuator, 80 mm base width, upright, with its lid attached directly to the inverted Z output. Full-depth NEMA14 reference (34 mm body) with a 26 mm motor bolt pitch.
- **Radial travel:** the upstream 120 mm printed-screw configuration. The radial motor body center is 105 mm behind Z. The extra 140 mm body extension from revision 21 is removed while stroke stays 120 mm: native bearing stations are X=143/217 mm, the home output face is X=235 mm and working screw length is 202 mm. Both threaded bands remain fully engaged and both bearing stations remain on the guide throughout travel.
- Both printed screws have an 8 mm lead. The radial motor stays centered laterally, with its body center at X=−105 mm relative to Z to counter the forward structure. The world-space probe reach remains 190–310 mm.

The compact layout places the arm pivots at **(±245, 0) and (0, ±245) mm**, requiring a **690 × 690 mm platform**. This preserves 120 mm radial travel and room for the narrow triangular probe extension. The base ring, spindle, stand and rotating deck remain shared with the standalone test fixture. The radial motor rear is X=−122 mm relative to the pivot; the 4× Z housing spans X=±103 mm.

The long Z-to-radial carrier is removed. The downward Z output flange seats directly on an integral **168 × 42 × 8 mm mounting pad** on the radial lid. It has twelve modeled **M3×0.5 threaded holes on a uniform 31 × 31 mm grid**. Its sixth longitudinal row matches all twelve holes of the 4× Z flange; the first five rows align with the standard upstream lid grid. The Z flange long dimension remains parallel to radial travel. The radial stage remains bottom-down.

The inverted layout lowers the **PCB surface to Z=79.2 mm**, from 284 mm in revision 22 (204.8 mm lower). The radial base is Z=118.2 mm at mid-travel; at its lowest pose it clears the support corner gussets by 6 mm. Z still has 40 mm travel and the PCB support posts are shortened accordingly.

## Balance, controller and support corner

The rearward motor offset is parameterized by `radial_setback_mm` (105 mm), independently of `radial_body_extension_mm` (0 mm). The fixed radial housing end is now X=147 mm from Z, **105 mm closer than revision 21's X=252 mm**. Its motor moves from X=−140 to −105 mm. The near bearing station is X=55 mm and the far station X=129 mm. Moving the arm pivots 105 mm inward preserves the short 43 mm triangular probe extension, 120 mm radial travel and the 100 × 100 mm PCB working area.

`check_balance.py` reports the current moving-stage center of gravity using motor masses of 140–250 g, effective printed densities of 0.2–0.65 g/cm³ and radial travel positions. The downloadable balance report contains the current mass and center-of-gravity estimates. These are sensitivity estimates, not measured balance or a structural qualification. Wiring and actual slicer toolpaths are not modeled.

The inverted Z motor face is **Z=369.2 mm**, with the full 48 mm motor and rear controller above it. Controller references retain the 42.3 × 42.32 × 1.6 mm PCB, 6 mm spacers, component and USB envelopes. At least 10 mm of clear space beyond those envelopes is reserved; the controller is no longer trapped above the rotating deck. These remain packaging allowances.

The support has **two mirrored, staggered three-hole braces**. Their deck mounts are (±42, −28), (±58, 8) and (±42, 44) mm; the middle pair is spread 32 mm farther apart than before. Two rear bolts at (±42, −54) and a front-center bolt at (0, 64) complete the symmetric nine-point pattern. Rounded flange ribs join the front-center mount to both braces. The flat outer print face remains at Y=−62 mm.

Each brace retains a 26 mm-wide, 28 × 28 mm, 45° corner gusset. Use **two M4×25 corner bolts** at (±42, −28) and **seven M4×16 bolts** elsewhere. All nine deck insert sockets have **Ø5.6 mm bores open through their full 10 mm bosses**, without a bottom. The shared deck has twelve smaller rounded openings, a 10 mm rim, a 28 mm-radius bearing hub and six 10 mm-wide primary spokes. CAD volume is 104,982 mm³: 16.2% below the unrelieved version and 2.4% below the previous four-window deck. These are geometric reductions, not slicer estimates or stiffness measurements.

## Mounting compatibility

The Z support mounts **only the actuator base face**. Five reinforced rows match the upstream 31 mm grid; seven rounded windows reduce volume between the rails. Four recessed **M3×20 screws** pass through 16 mm of support into the selected actuator's corner M3 inserts, with 4 mm engagement. There are no Z-base nuts or washers. The support provides clearance for every position of the 1×/2×/4× base grid, so additional fasteners can be fitted. The outer face remains flat for printing, with a 206 × 324 mm footprint and 135 mm print height.

Native actuator coordinates use X along travel, Y across the module and Z above its base. The motor face is X=0; the drive axis is Y=0, Z=42 mm.

| Width | Grid Y columns (mm) | Base/lid seats per face | Output holes | Output plate width |
|---|---|---|---|---|
| 1× | −15.5, 15.5 | 10 | 4 | 42 mm |
| 2× | −46.5, −15.5, 15.5, 46.5 | 20 | 8 | 104 mm |
| 4× | −77.5, −46.5, −15.5, 15.5, 46.5, 77.5 | 30 | 12 | 168 mm |

Base and stock lid rows are X=10.5, 41.5, 72.5, 103.5 and 134.5 mm. Output holes use the same width columns and Z=26.5/57.5 mm. Both current printed-screw and T8 families publish these grids; the former inferred 21 mm widening patterns are removed. Standard base/lid seats accept RX-M3S×4.0 inserts (4.6 mm OD, 4 mm long) in Ø4 mm printed pilots. Installed reference cavities include heat-set displacement.

The custom radial lid retains the direct mounting pad and adds the sixth X row at 165.5 mm. Relative to Z, its columns are X=±15.5, ±46.5 and ±77.5 mm, with Y=±15.5 mm. These twelve locations use integrated printed M3×0.5 threads instead of the stock lid's heat-set inserts. The original lid mounting pilot cavities are filled; the unused lid inserts are omitted. The radial base keeps the standard 31 mm M3 insert grid. A Ø22.2 × 2 mm center recess retains NEMA17 boss clearance. Chase the printed threads and test fit before loading.

The Z carriage has clearance holes, recessed head wells and side-open access slots. Use **M3×12 screws** through the Z flange into the radial lid: four for 1× and eight for 2×/4×. On 4×, the four middle-column holes at ±46.5 mm remain available as standard output pilots but are unused in this joint; omitting their deep head-access recesses preserves the lower bearing tracks. Nominal thread engagement is 7.2 mm and heads are recessed 0.2 mm below the flange back. Extend Z fully for access. The probe outrigger keeps four M3×12 screws on its 1× grid. `downloads/mounting-patterns.json` contains the coordinates.

## Rotary base and existing prints

The rotary base retains a 12T compliant pinion / 72T internal ring for **6:1 reduction**, direct full-depth NEMA17 mounting and rear RP2040-controller clearance envelopes. Four 625ZZ rollers tilt at 45° on one rounded integral block each. Their solid Ø5.1 mm printed axles use no bolts. The ring's 176 mm OD has a continuous 45° track, clear of its flat-seated M3 button heads. Bearings retain the requested 0.4 mm nominal normal overlap with the track.

Two 6002 bearings sit on the **Ø15.25 mm central spindle** with a 0.5 mm top chamfer. Its four 0.5 mm-wide relief cuts run 33.1 mm from the tip, leaving a 0.5 mm connected root. The module base retains its five rounded cutouts. The revised deck has twelve rounded openings around the spread mounting lands. Both retain flat print faces. The main assembly and base-test page use the same rotary-base source and canonical STL exports.

For revision 24, reprint the **rotating deck, Z support and updated actuator printed parts**, including the radial lid and Z carriage. The newer actuator hardware uses short M3 mounting inserts, four M5 adjustment inserts per actuator and an M3 clamp nut per printed screw. Use the new insert and fastener references in the model when assembling. The shared fixed base, ring, spindle and standalone stand retain their geometry. Reprint only the deck when updating the standalone rotary test fixture from v4.10. Its guide is `base_test_kit_v4/PRINT_AND_ASSEMBLY.md`.

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
