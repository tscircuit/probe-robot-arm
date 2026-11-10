# Rigid internal-gear base variant

An independent prototype of the existing flying-probe arm. This variant keeps the direct NEMA17/internal-ring drive and adds finer gearing and a broader, deeper load path from the actuator to the stand. The original Assembly and Base test pages retain their existing parts.

[Interactive CAD](https://modular-flying-probe-arm.seveibar.chatgpt.site/rigid-base.html)

| Feature | Existing base | Rigid variant |
| --- | --- | --- |
| Internal ring / pinion | 72 / 12 teeth | 264 / 12 teeth |
| Reduction | 6:1 | 22:1 |
| Module / pressure angle | 2 / 25° | 1 / 25° |
| Ring outside diameter | 176 mm | 296 mm |
| Fixed plate | 190 × 190 × 11 mm | 312 × 312 × 15 mm |
| Rotating deck thickness | 6 mm | 8 mm |
| Z support depth at actuator | 20 mm | 42 mm |
| Main bearing cartridge | Two 6002 | Same two 6002 |
| Peripheral bearings | Four tilted 625ZZ | Four tilted 625ZZ, broader block roots |
| Pinion support | Motor shaft | Additional 688ZZ bearing near teeth |

The ring retains a continuous 45° outer running track and flat-seated M3 button heads. The blocks retain one integral axle each. The variant uses zero nominal roller/track interference instead of the original 0.4 mm preload: actual fit and smooth rotation must be established on the printed hardware.

The Z support now uses two detachable printed rear trusses. Each triangular plate has a middle crosspiece, three tower mounting points and two deck mounting points. The highest attachment is 304.5 mm above the deck. The rear deck extensions include shallow locating pockets for matching keys on the brace feet, and a crossmember joins the extensions. Two thin underside webs stiffen each extension, leaving the fasteners accessible between them. The revised brace foot bolts are at Y=−120/−138 mm, with a 10 mm locating key centred at Y=−129 mm. One of the tower’s large faces is removed; the remaining side webs and lower ribs are reduced. The existing 28 mm corner gussets remain. The braced tower is retained; the hollow-backbone experiment has been removed. The enlarged deck, shorter rear trusses and widened bearing/motor locations are checked together. Nine heat-set insert holes are open through the deck. The mirrored three-hole side braces spread to X=±90 mm, with the front centre mount at Y=88 mm. Small rounded deck windows preserve the support footprint. The fixed plate is solid to prioritize stiffness in this test.

The 4× inverted Z and 1× upright radial actuator geometry, direct threaded radial lid, 31 mm grids, full-depth motors and upper Z controller clearance come from the current main arm. They move up only 2 mm with the thicker deck. The rear deck reaches Y=−180 mm, 32 mm beyond the new circular deck. Its rear extensions are shortened to fit the H2S. This experiment does not yet define a new four-arm platform or certify inter-arm clearance for this larger swept envelope.

## Resolution and test expectations

For a 1.8° stepper:

- Full output step: 0.081818° instead of 0.3°.
- At 1/16 microstepping: 0.00511364° instead of 0.01875°.
- At 250 mm reach: nominal 0.02231 mm per microstep instead of 0.08181 mm.

These are **command increments, not accuracy or repeatability**. Microsteps do not guarantee equally spaced physical moves under load. The solid pinion replaces the original compliant tooth segments and has 0.04 mm nominal tangential pitch clearance; this clearance alone corresponds to approximately 0.076 mm of tangential tip lost motion at 250 mm reach if fully taken up on reversal. Printing error, bearing clearance, shaft fit, gear runout and structural flex can dominate this number. No measured vibration reduction, strength, fatigue life or probing accuracy is claimed.

More teeth improve reduction because the ring/pinion tooth-count ratio rises; shrinking both gears' teeth while preserving their tooth-count ratio would not improve resolution. The solid teeth and supported hub target mesh stiffness, while the thicker plates and deeper support target frame flex. There are no soft pads in the probe's structural load path: added compliance can allow positional deflection. Acceleration/current tuning remains necessary after the mechanical test.

Suggested comparison: use the same arm payload, current, microstepping and acceleration on both bases. Measure forward/reverse tip motion and settling with a dial indicator at a known reach. Check the ring through a full revolution by hand before powered testing; record tight spots and backlash before increasing speed. Start with the ring and pinion prints as a fit trial, then print the larger structure.

## Printing and hardware

Download **Print ZIP** for the 25 bed-oriented prototype STLs, manifest, parameters and validation reports. **STEP** contains the full assembly with reference hardware. Right-click any printed part for its actual print-oriented STL; hardware exports are reference envelopes.

New structural prints: `Rigid_fixed_base`, `Rigid_rotating_deck`, `Internal_264T_ring`, `Solid_12T_module1_pinion`, `Pinion_bearing_cap`, `Boxed_Z_support`, `Braced_test_stand`, `Printed_rear_brace_left` and `Printed_rear_brace_right`. The historical `Boxed_Z_support` filename is retained, but its current geometry has one large face removed and uses the rear trusses. Other actuator and central-cartridge parts are retained. The Z support prints on its flat outside face and needs approximately a 206 × 324 mm bed footprint. The fixed base and stand need 312 × 312 mm. The revised deck needs about 296 × 328 mm; each brace prints on its broad face in about 321 × 86 mm, with 12 mm thickness. The brace load paths lie in the print plane. The tower, braces and deck extensions are all printed; the fastening bolts, nuts and washers are ordinary metal hardware. Review local supports/bridging in your slicer, particularly integral tilted axles and internal frame recesses; mesh checks are not a slicer simulation.

Additional/revised base hardware:

- One [688ZZ bearing, 8 × 16 × 5 mm](https://www.nsk-literature.com/en/bearing-replacement-guide/offline/download.pdf), on the nominal Ø8.05 mm printed journal.
- Four 625ZZ, 5 × 16 × 5 mm, on nominal Ø5.1 mm integral axles.
- Two 6002, 15 × 32 × 9 mm, on the retained slotted Ø15.25 mm spindle.
- Six M3×40 flat-seated button-head ring screws, six M3 washers and nuts.
- Four M3×20 motor-face screws; three M3×8 bearing-cap screws; one M3×4 pinion set screw.
- Four M5×30 stand screws and four captive M5 nuts.
- Nine M4 heat-set deck inserts; seven M4×16 and two M4×25 support screws (the longer pair pass through the corner gussets).
- Four M3×40 Z-base mounting screws into the actuator's existing receiving inserts.
- Brace attachments: eight M4×35 and two M4×60 screws, ten M4 nuts and ten M4 washers. The two longer screws pass through the middle crosspieces.
- Retained central spindle/cartridge fasteners and full-depth NEMA17 with rear controller.

Press fits and receiving pilots are nominal starting points, not guaranteed printer fits. The pinion's bore matches the existing D shaft; check the flat and shaft engagement before fitting the 688 bearing. Assemble motor and pinion on the base, install its support bearing and cap, fit the central cartridge, then the ring/deck and support. Mount the stand after checking access to underside fasteners. Torque, material choice and final print settings require physical trials.

## Rebuild and validation

From the repository root, with Python 3.12:

```sh
python -m venv .venv
.venv/bin/python -m pip install -r rigid_base/requirements.txt
.venv/bin/python -m rigid_base.model
.venv/bin/python -m rigid_base.prepare_prints
.venv/bin/python -m rigid_base.check
.venv/bin/python -m rigid_base.check_braces
.venv/bin/python -m rigid_base.check_rotation
.venv/bin/python -m rigid_base.check_explosion
.venv/bin/python -m rigid_base.package
.venv/bin/python -m rigid_base.check_package
```

The packaging command losslessly gzips viewer meshes and shares byte-identical radial print files between Z width pages to remain within hosting size limits. It does not simplify the CAD or print geometry.

The 296 mm ring, 312 mm square base/stand and 296 × 328 mm deck fit the H2S nominal 340 × 320 × 340 mm volume with 4 mm bed margin on every side. Rotate the deck and long tower/brace prints 90° on the bed where needed. Every actual STL is checked against this envelope; this does not replace slicing.

Compared with the previous 224 mm / 16:1 experiment, the ring is 32.1% larger in diameter, reduction rises 37.5%, and the commanded angular increment falls 27.3%. A larger ring also increases rotating inertia; physical vibration reduction is not assumed.

The model is script-parametric. `parameters.json` specifies the gear pair and selected interface dimensions for this particular design; changing the gear envelope, heights or mount layout requires updating the mating support geometry and rerunning every check. It is not an automatically constrained gearbox configurator. CAD caches are keyed to geometry-source and parameter hashes.

Checks include 65 engagement samples across one ring-tooth pitch, nine Z/radial travel poses against changed parts, full-revolution base samples every 15°, fit-envelope checks, single watertight positive-volume STL shells, flat print contact, through insert bores, and continuously bounded service-explosion translations. Existing actuator-to-actuator travel/thread checks are reused because those parts move together unchanged. Rotation and gear engagement checks are sampled, not a continuous arbitrary-motion proof. Expected press fits, released threads, receiving pilots and nonphysical controller-envelope intersections are recorded explicitly.

For this revision, reprint the 264T ring, fixed base, rotating deck, stand, pinion bearing cap and both rear brace plates. Use the current support STL, whose ring-screw clearance cuts follow the new bolt circle. The 12T pinion, actuator parts, motors and central bearing cartridge are retained. The motor moves from X=90 mm to X=126 mm; ring screws move to a 140 mm radius and stand legs to a 262 mm pitch. Install the brace-to-tower nuts/washers before the actuator blocks access to the inside of the frame; the brace feet locate in the deck pockets before tightening their bolts. Keep the frame square while tightening. This is fixed triangulation, not a tensioned printed cable. Physical stiffness and vibration reduction still require a loaded test.

The exploded view lifts the arm/ring/deck/cartridge and attached trusses as one service module. Actuator internals stay assembled. It then separates the pinion/bearing/cap and motor. This is intentionally a module-level service view, not a full fastener-by-fastener assembly guide. Rotation is disabled and reset to zero during explosion.

References: [Oriental Motor — stepper fundamentals and microstepping](https://www.orientalmotor.com/stepper-motors/technology/stepper-motors-basics.html), [SDP/SI — metric gear geometry](https://www.sdp-si.com/resources/elements-of-metric-gear-technology/page3.php). Parent actuator source and provenance remain in the repository's main README.
