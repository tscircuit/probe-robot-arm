# Modular flying probe — revision 14

Source: https://github.com/tscircuit/probe-robot-arm

Parametric CadQuery assembly and public viewer: https://modular-flying-probe-arm.seveibar.chatgpt.site

Four removable theta/Z/radial modules serve a 100 × 100 mm PCB, with simultaneous probe contacts on a 2 × 2 mm square. The NEMA17 Z stage and NEMA14 radial stage use the actual **R24 rear pass-through mounting enclosure** from [tscircuit/rack-actuator](https://github.com/tscircuit/rack-actuator/tree/a0ccaf201d6f6f5f988ca64dc1a9f5e7aba931b5). This is a geometry prototype; physical print fit, stiffness, accuracy and load capacity remain untested.

## Lighter rotating deck

Five rounded through-windows remove **25.2% of the rotating deck's solid CAD volume**. The deck retains its 6 mm plate thickness, 10 mm continuous outer rim, 28 mm-radius bearing hub, six 14 mm-wide radial ribs, all six Z-insert seats and the full Z-cradle flange footprints. Corners are R3. The original top face remains the flat printing face. **Only part 10 (rotating deck) needs reprinting when upgrading from revision 13**; the other parts and hardware are unchanged. The main arm and standalone fixture use the same shared deck. CAD volume reduction does not establish physical stiffness or exact filament savings.

## Lighter module base (revision 13)

Five large through-cutouts with **R6 rounded corners** reduce the module base's solid CAD volume by approximately **37%**. A 10 mm perimeter and 28.3 mm diagonal webs retain the motor pad, spindle hub, all mounting lands and the four bearing-block footprints. The 11 mm thickness and flat printing underside are retained. Revision 13 changed only the module base; revision 14 also lightens the rotating deck. Volume reduction describes the CAD solid, not an exact slicer filament saving or a measured stiffness rating.

## Spindle fit update

The bearing journal is now **Ø15.25 mm**, reduced from the tight Ø15.5 print. A **0.5 mm × 45° chamfer** on the outer top edge makes a Ø14.25 mm lead-in. Shaft height, flange, centre bolt bore and the Ø15.8 spacer bore are unchanged. This update also changes the module plate and ring for the four tilted roller supports; reprint all three parts when upgrading from revision 10. The print kit also includes a matching fit coupon. The nominal 6002 bore remains 15 mm; print-fit interference is 0.25 mm diametrically.

## Shared rotary base

The main arm and bench fixture now call **the same generator and configuration**, `rotary_base/core.py` and `rotary_base/parameters.json`. `check_base_sync.py` compares every common component, including the motor, controller, bearings, plate, ring and deck, and checks motion groups. Base settings belong in that shared configuration; `parameters.json` contains the arm/PCB settings.

The base has **four 625ZZ rollers**, at 45°, 135°, 225° and 315° around the base. Each bearing tilts 45° and presses onto an **integral Ø5.1 mm printed axle** on **one block**, with an R6 rounded crown. A 0.3 mm lead-in chamfer guides the bearing; an 8 mm OD shoulder supports its inner race. No roller bolts, nuts or separate spacers are used.

The 72T ring is now **176 mm OD** (88 mm outer radius). Its lower outer edge has a **6 × 6 mm, 45° continuous track**. The bearing contact line is centered at radius 85, Z31. Six **M3×30 button-head screws with flat seats** retain the ring; no countersinks are present. The bearings stay at least 2.38 mm radially outside every head, so no screw head is part of the rolling track. The teeth, bolt positions and deck spacers are retained.

The plate is 11 mm thick with a broad flat underside at Z0; its recessed spindle seat retains a 4 mm floor. The NEMA17 mounts directly below it at Z0. The ring bottom stays at Z28, 17 mm above the plate. The Ø15.25 spindle, 0.5 mm top chamfer, Ø15.8 spacer and two 6002 bearings are shared. Reprint the **module plate, ring and spindle** when upgrading from the published flat-base version. The integrated stand and structural deck remain unchanged.

The **same structural rotating deck** serves both views, with the six reinforced Z-cradle insert seats. Its top is Z54.2, 5.8 mm below the former main-arm deck. This replaces the older open-spoke test deck. Reprint the base plate and shared deck when updating from the first roller-supported kit. The integrated bench stand is unchanged. When upgrading the previous main arm, also replace the resized Z support and use the revised platform hole pattern and clearance openings. The main platform instead uses four M5×30 bolts per module on the 150 mm square pattern, with washers and nuts below its 10 mm plate. The platform now has central clearance openings for the spindle and clamp fasteners, plus the motor openings.

The four printed axles are fixed, with no height slots. Check all four roller contacts and free rotation after printing. The base kit includes tilted 4.9, 5.0 and 5.1 mm axle coupons. The CAD separately verifies the intended 0.1 mm diametral axle/bore interference, with no other block/bearing overlap. Motor screws remain M3×16; stand screws are M5×25 and main-platform bolts M5×30. The motor shaft engages the pinion by 7 mm.

The complete arm contains **22 printed designs**; the bench fixture contains ten. The main arm's module-service explosion keeps the rotary base assembled; the Base test view provides the detailed rotary-base disassembly using identical geometry. [Shared base print kit and guide](https://modular-flying-probe-arm.seveibar.chatgpt.site/downloads/armature-base-test-v4.zip).

## Base reduction update

The inner motor pinion now has **12 teeth**, down from 20, while the ring retains 72. The reduction is **6:1**, and the motor/shaft/controller and platform opening move from X=52 to **X=60 mm**. Pitch diameter is 24 mm; tip diameter is 28 mm. Use the new pinion with the shared fixed-base motor opening; it does not mesh at the old motor position.

For the current unshifted, full-depth 25° profile, the standard rack-generation undercut limit is `ceil(2 / sin(25°)^2) = 12`. This follows [SDP/SI equation 4-3](https://sdp-si.com/D805/D805_PDFS/sections/technical.pdf) with zero profile shift. Smaller tooth counts would require a different tooth design. Nominal internal-mesh transverse contact ratio is about 1.55. The open tooth slots occupy 25% of the tooth half-angle instead of 55%, leaving approximately 0.418 mm tangential walls and a 0.278 mm opening at the tooth tips. Inspect these narrow slots in the slicer and after printing; narrower slots change spring stiffness, which remains untested. There are no small finger caps.

With 1.8° motors and 1/16 microstepping, base movement is 0.0818 mm per microstep at 250 mm reach and 0.1031 mm at 315 mm reach, 40% smaller than the previous drive. These are command-resolution figures, not measured accuracy.

## Actuator integration

- Z actuator: **NEMA17, 48 mm motor depth**, 40 mm stroke, 125 × 90.8 × 76.9 mm housing. The upstream 18T, 20° pressure-angle drive replaces the previous NEMA14 14T drive; Z rotation uses an 18 mm pitch radius.
- Horizontal actuator: **NEMA14, 34 mm motor depth**, 120 mm stroke, 198 × 84.8 × 62.9 mm housing, **rotated 180° about its travel axis**. The motor faces upward and the reinforced top mounting posts face downward. The 14T drive uses a 14 mm pitch radius; its world-space rotation sign reverses after the flip. The 120 mm stroke is generated directly within the upstream 20–150 mm range.
- Both use `--enclosure pass-through`. The rack can project through the rear portal. At full retraction, rear projection beyond the case is 17 mm for Z and 97 mm for the horizontal axis.
- The original tray, lid, chassis, pinion, six 625ZZ guide bearings and internal fasteners are retained. The Z rack output pad is adapted locally to four straight 3.4 mm through-bores with no output inserts; the radial output keeps its inserts. No housing approximation or cut-down enclosure is substituted. The relaxed chassis is used for its printable STL.
- The Z support now has a **solid 6 mm-thick top mounting face**, 96.8 mm wide and 148.2 mm high, with four mounting bores and no windows. It overlaps the side wall by 6 mm along the entire corner, eliminating the previous 1.5 mm gap above the flange. The support remains one printed solid.
- A single lower Z cradle bolts to both the enclosure's **four top-face and four side-face M3 inserts**. Its wider **10 mm-thick flanges** fasten to six M4 heat-set inserts in reinforced rotating-deck bosses using **M4×16 through-bolts**. No extra printed support pieces are added. A one-piece U-shaped carrier wraps over the top and both faces of the Z output pad. Four M3×35 through-bolts, four M3 nuts and eight washers fasten the two 6 mm carrier legs around the 18 mm pad: eight carrier contact points, four on each side. The 9 × 9 mm bolt pattern is retained. The bridge covers the pad top, and the shelf connects to the horizontal enclosure's four downward-facing reinforced top posts. Its flat 6 mm shelf replaces the tall side-mount bracket. Screws enter upward from underneath the shelf; no new holes are cut in the actuator housing.
- The tapered triangular probe holder mounts beneath the inverted output pad using all four M3 inserts on the 9 × 9 mm pattern. Its fastening direction is reversed to match the pad. Its tip remains 54.5 mm forward of the output-pad center and narrows toward a 6 mm nose. The probe leans inward 10 mm over a 40 mm drop.
- Sixteen application M3×10 screws are modeled: four for the Z enclosure side mount, four for its solid top mounting face, four upward into the radial enclosure mounting posts, and four upward into the horizontal output/probe-holder interface. Brackets are 6 mm at these interfaces: engagement is 4 mm into the flush radial mounting posts and 3.7 mm into the recessed output/side inserts. Do not substitute longer screws without checking the blind holes.

The upper motor axis remains at **X=0, Y=0** relative to the base rotation axis. The new rack and its smooth output tongue are substantially longer than R14. To preserve that motor location and the tapered probe extension, pivots move to **(±250, 0) and (0, ±250) mm**, with a **700 × 700 mm main platform**. This grows from the previous 510 × 510 mm concept. The PCB remains 100 × 100 mm. The PCB top is Z=194.8 mm above the main platform top, and the ground reference is Z=−90 mm.

The base and Z motors use 48 mm-deep NEMA17 envelopes; the radial motor uses a 34 mm-deep NEMA14. No pancake motors are used. The requested Ø15.25 printed shaft has nominal interference with the 15 mm bearing bore; actual printed fit or finishing is required. The intended fit is reported separately from rigid collision checks.

## Minimum Z height and deck attachment

`z_origin: null` selects the lowest mounting height that leaves **2 mm above both the deck and the central M6 clamp**. The origin is now **145.4 mm**, 1.6 mm lower than the previous main assembly. At full downward travel the rack ends at Z60.4; the centre bolt ends at Z58.4 and the deck top is Z54.2. The enclosure bottom is Z77.4. Using deck height alone would collide with the centre clamp, so it is included in the height limit.

The six deck bolt centers, in millimetres relative to the rotation axis, are **(−42, −54), (−8, −54), (24, −54), (42, −28), (42, 8), (42, 44)**. Flanges are 10 mm thick with 4.4 mm clearance bores. M4×16 screws give 5.7 mm engagement into the recessed deck inserts. A 9 mm-diameter, 150 mm-long straight driver corridor above each bolt was checked against the assembled geometry.

Print the cradle with its flange undersides on the bed. Orient the rotating deck with its flat upper face on the bed and the six insert bosses pointing upward.

Deck inserts are modeled as **M4, 6 mm OD × 6 mm long**, seated 0.3 mm below the deck surface in 5.6 mm printed pilots. Local bosses give 3.3 mm material beneath the pilot. Match these dimensions to the selected inserts and calibrate the pilot for your printer and material; insert pullout and cradle stiffness are not physically qualified. The named insert/host interference is intentional for heat setting.

## Mounting and clearance

Local actuator coordinates: +X is rack extension, +Z is the lid/output insert face, +Y is the side mounting face. The Z stage maps local +X to world +Z and local +Z to world +X. Rear projection on Z therefore points downward. The inverted radial stage maps local (X, Y, Z) to world (X, −Y, −Z), then translates to its mounting origin. Radial extension remains outward along +X. Keep the rear portal and the entire moving rack clear; the shorter case does not shorten the rack.

The Z enclosure uses both its side inserts and top mounting posts, supported by the same flanged cradle. The radial enclosure uses its reinforced top posts, now facing downward. Remove the radial stage from the carrier before opening its downward-facing lid. The exploded sequence demonstrates this order.

| Interface | Hole coordinates | Mounting direction |
| --- | --- | --- |
| Z enclosure side | Local X = −60.5, 49.5 mm; local Z = −42, −4 mm | Into local +Y face at Y=63.9 mm |
| Z enclosure top posts | Local X = −60.5, 49.5 mm; local Y = −19.4, 56.4 mm | Into local +Z face, world X=24.9 mm |
| Radial bottom posts | World X = −60.5, 122.5 mm; world Y = −52.4, 17.4 mm | Upward into Z=250.9 mm face at neutral Z position |

All four combinations are used per interface. `parameters-resolved.json` contains the exact housing bounds and mounting coordinates. The upstream insert defaults are M3, 4.6 mm OD × 5 mm long, with 4.2 mm printed pilots; calibrate these for your inserts and material. The 120 mm rack including its output pad is **314.5 mm long**, so it requires a sufficiently large print bed or diagonal placement. Do not scale the STL to fit.

The neutral radial rotation axis is Z=275.8 mm; its downward mounting face is Z=250.9 mm. The PCB and upper actuator assembly are 1.6 mm below the previous main assembly. The upper NEMA14 axis remains centered in plan at X=0, Y=0.

## Kinematics and viewer

The top navigation links to the Assembly and Base test pages. Left drag orbits, middle drag pans, and the scroll wheel zooms. Right drag does not pan. Right-click anywhere in the 3D view to toggle **Show hidden edges**. Occluded edges appear dashed; the preference is remembered across the Assembly and Base test pages. Right-click a visible part to download its STL. Printable parts use the saved print files (including the relaxed flexure chassis); hardware and clearance envelopes download as reference meshes. Downloads are independent of axis position and explosion offsets.

Reach is **195–315 mm** from each pivot, with 120 mm radial stroke and 40 mm vertical stroke. Stroke is calculated from the farthest PCB corner with 5 mm end margins and rounded upward to 10 mm. Required nominal yaw is approximately ±14.04°. Four-arm target-center controls run from −49 to +49 mm, keeping the complete 2 × 2 mm cluster on the 100 mm board.

Drag **Explode modules** to separate a single arm in 27 stages: remove the Z output nuts, withdraw the through-bolts and washers, lift the U-shaped carrier off the pad, move the horizontal assembly clear, withdraw its bottom-mount screws downward, lift its enclosure from the carrier, lower its lid, then release both Z mounting faces, move the enclosure clear, remove the six flange bolts, lift the cradle from the deck, and open the Z lid. The racks, bearings and pinions stay assembled in their trays. This view shows mounting and enclosure access. It is not the upstream complete internal disassembly animation. Switching to Four arms restores the assembled configuration. Axis animation is disabled during explosion.

The four-arm motion preview retracts all tips before moving the shared target, then lowers them together. It is a mechanism visualization rather than executable machine control.

## Validation

- `validation.json`: valid CAD solids, one solid per printed part, all rigid part pairs at nine Z/radial endpoint-and-center combinations, and the nominal rotary gear mesh. Designed pinion/rack preload and named heat-set insert/host interference are excluded from rigid collision failures.
- `z-mount-validation.json`: minimum height, measured rack/deck gap at full retraction, flange bores, insert backing, thread engagement, straight driver access, continuous corner material, a solid top face, straight Z output bores without inserts, and the eight-hole U carrier with its through-bolt hardware stack. Connected cross-sections above the shared flanges verify the corner away from bolt bores.
- `platform-validation.json`: simultaneous clusters at nine board locations with center coordinates −49, 0 and +49 mm, plus six raised configurations at 20 and 40 mm. Checks inter-arm, controller envelope, frame, PCB and support intersections, plus actual probe tip positions.
- `arm-explosion-validation.json`: every interval of the 27-stage, single-arm module explosion. Swept bounding boxes (including a checked union of enclosing boxes for the cradle) or conservative minimum-distance bounds certify each translation interval; undecided intervals are subdivided and unresolved intervals fail. No moving part is silently omitted. Parts moving together retain their checked assembled relationship. This check covers ideal CAD geometry, not print tolerances or workholding.
- Intended heat-set knurl/pilot interference represents plastic displaced during installation. These inserts remain with their hosts throughout explosion. Intended compliant tooth interference remains in the assembled drives. Fasteners must be unthreaded before withdrawal; threads themselves are not modeled.

The static travel and four-arm checks are sampled poses, not a proof of every coordinated motion through the full workspace. The module explosion has a separate continuous translation check. Physical stiffness, backlash, fatigue, holding torque, probe force, cable routing and motor thermal performance require bench testing. Angled probes can scrub laterally during compression.

## Controller mechanical reference

The [imrishabh18/rp2040-motor-controller](https://tscircuit.com/imrishabh18/rp2040-motor-controller) reference uses a 42.30 × 42.32 × 1.6 mm PCB and 31 × 31 mm hole pattern behind the base motor. The model retains 6 mm insulated spacers, 10 mm outward component allowance and a 30 mm lateral USB plug/cable allowance. These are packaging allowances, not component-accurate imported controller geometry. Motor rear mounting and actual connector clearance need verification against the selected hardware.

## Build from this repository

Python 3.12 is recommended. Install the CAD and verification dependencies, then regenerate both assemblies and their checks:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/rebuild.py
```

Generated STEP, STL and check reports go into `output/`. The same `rotary_base` package supplies both the main assembly and standalone fixture. The v3 reference under `base_test_kit_v4/reference_v3/` is used only to check retained geometry.

For the complete local website, offline base viewer, PDF guide and browser checks, install Node.js and Chromium (`/usr/bin/chromium` on Linux), then run:

```sh
npm ci --prefix .qa
.venv/bin/python scripts/rebuild.py --site
.venv/bin/python -m http.server 8000 --directory site/dist
```

Open http://localhost:8000. Generated downloads and CAD meshes are excluded from Git; the viewer source and pinned Three.js files are included. These commands build locally and do not publish or require ChatGPT Sites credentials. The live viewer above includes downloadable print files and STEP assemblies.

## Files and regeneration

- `model.py`, `parameters.json`: arm integration and PCB configuration.
- `rotary_base/`: shared rotary-base generator, gear geometry and configuration.
- `check_base_sync.py`: common-component identity, four single blocks, integral tilted axles and clamp-height checks.
- `check_flat_base.py`: connected planar underside, retained spindle floor, and matching flat STL exports on both pages.
- `check_deck_cutouts.py`: deck volume reduction, open windows, full cradle footprint, retained mounting lands and flat printing face.
- `check_base_cutouts.py`: volume reduction, five open windows, and retained mounting lands and structural connections.
- `check_platform.py`: four-arm cluster and frame checks.
- `check_z_mount.py`: low mounting and fastener-access checks.
- `check_base_drive.py`: minimum tooth count, shaft web, slot dimensions and ratio checks.
- `arm_explosion.py`, `check_arm_explosion.py`: shared staged motion and continuous translation checks.
- `single-arm.step`, `four-arm-platform.step`: named, colored assemblies in the corresponding ZIP downloads.
- `output/prototype-parts/`: prototype STL components, including both enclosure trays/lids and the relaxed chassis print geometries. These are development parts, not a qualified full-machine print kit.
- `upstream/rack-actuator-r24/`: unmodified pinned source, README, MIT license and `PIN.json`.

Use Python 3.12 and CadQuery 2.7.0:

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python model.py --check --preview-only
.venv/bin/python check_platform.py
.venv/bin/python check_z_mount.py
.venv/bin/python check_base_drive.py
.venv/bin/python check_base_sync.py
.venv/bin/python check_arm_explosion.py
.venv/bin/python model.py
```

The integration loader executes only the upstream construction section, with the selected NEMA17/NEMA14 motor, full motor depth, requested stroke and pass-through options. The radial flip is an assembly transform. The loader fills the original Z output insert pockets and cuts four straight 3.4 mm through-bores; the pinned upstream source remains unchanged. Cache keys include that source, stroke, motor depth, enclosure variant and output mounting style. No upstream parameter guard is patched. Changing the parameters requires regenerating geometry and rerunning checks.

The rotary open-tip pinion adapts [seveibar/compliant-spur-gear revision 3](https://github.com/seveibar/compliant-spur-gear/commit/37682731f360b1b327a91f8713c9e67c464a8b32): full-width hollow tooth walls with rounded reliefs and no small finger caps, against a solid-tooth internal ring. Gear module 2, 12/72 teeth and 25° pressure angle give 6:1 reduction. Nominal mesh results are reused only when the pinion and ring BREP hashes match. Actual elastic behavior remains unqualified.
