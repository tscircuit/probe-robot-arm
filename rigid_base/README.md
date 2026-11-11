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

The Z support retains its full-radius lower mount, now 6 mm thick instead of 10 mm. Nine M4 insert holes remain open through the rotating deck; the outer support bolts lie at a 138 mm radius. The ring stays 296 mm / 264T / 22:1. The earlier front/rear brace pairs, locating keys and rear deck extensions remain removed. One centered front strut connects the front frame to the support flange; a centered rear strut connects the back of the Z support directly to the rotating deck. The deck is circular again, 296 mm across. The original flat outer back face and the short integral corner gussets are retained.

## Removable front Z frame

One U-shaped printed `Front_Z_frame` wraps around the actuator housing and attaches to both sides of `Boxed_Z_support`. Four Ø4.4 mm through holes on each side use M4×25 screws, washers and nuts. The side mounting lands are integral with the rear support. The front frame's inner span is 216.4 mm, wider than the 206 mm actuator housing, so the open rear can pass over the Z housing before the radial module is attached. There is a 0.2 mm gap at each mounting interface before tightening.

Four large front windows, two large windows per side, and slots between the mounting lands remove approximately 63% of the solid U-shell volume. A diagonal front web and horizontal/vertical ribs remain. The front panel sits 22 mm ahead of the fixed Z housing and the side ports clear the radial housing throughout Z travel. This creates a deeper connected frame around the actuators without the former deck-to-tower struts. Physical stiffness, joint slip and print creep still need a loaded test.

## Centered front and rear struts

`Center_front_strut` sits at X=0, attaching to the front frame's center rib at Z=260 and 350 mm. Its foot shares the existing (0,126) mm support/deck mount. Use M4×20 for that shared base screw; the two former outer strut mounting screws at (±103,91) mm revert to M4×12.

`Center_rear_strut` also sits at X=0. It attaches to the Z support's back face at Z=236.7 and 360.7 mm, within the existing solid crossbars. Its foot bolts directly to the deck at (0,−126) mm through a new, fully open Ø5.6 mm insert bore in the solid rear spoke. Fit one additional M4 heat-set insert and an M4×16 foot screw. The rear screw tip ends at the deck underside.

Both struts use two M4×40 attachment screws, washers and nuts. The front frame and back support each have two new Ø4.4 mm through holes. The upper mounting pads give the screw heads flat seats outside the sloping chords. The front base screw extends 6 mm below the support flange; the rear foot screw passes through the full 6 mm insert. Both open triangular struts are 12 mm thick and print flat on their broad sides: front 311.8 × 81.8 mm; rear 317.8 × 49.8 mm. They stay inside the 148 mm ring radius and clear the actuator motion envelopes.

**Reprint the front frame, Z support and rotating deck, and print the two center struts.** Remove both previous side struts. Retain the larger ring, fixed base, stand and actuator prints. Install the rear strut's nuts/washers inside the Z support before the actuator limits access. Assemble the front frame before the radial module, then attach the front strut and replace the shared front base screw. Tighten the front and rear struts with the tower square. The support's flat back print face is retained; no rear bosses are added.

Printed parts have distinct colors in both the viewer and STEP assembly. The front strut is orange, rear strut purple, front frame green, Z support blue and rotating deck teal. Reference hardware retains conventional metal colors. Colors do not specify print material. Physical stiffness, joint slip and print creep still need a loaded test.

The 4× inverted Z and 1× upright radial actuator geometry, direct radial lid mount, 31 mm grids, full-depth motors and upper Z controller clearance remain unchanged. They sit 2 mm higher than the original main assembly because of the thicker experimental deck. This experiment does not yet define a new four-arm platform or certify inter-arm clearance for the larger base.

## Resolution and test expectations

For a 1.8° stepper:

- Full output step: 0.081818° instead of 0.3°.
- At 1/16 microstepping: 0.00511364° instead of 0.01875°.
- At 250 mm reach: nominal 0.02231 mm per microstep instead of 0.08181 mm.

These are **command increments, not accuracy or repeatability**. Microsteps do not guarantee equally spaced physical moves under load. The solid pinion replaces the original compliant tooth segments and has 0.04 mm nominal tangential pitch clearance; this clearance alone corresponds to approximately 0.076 mm of tangential tip lost motion at 250 mm reach if fully taken up on reversal. Printing error, bearing clearance, shaft fit, gear runout and structural flex can dominate this number. No measured vibration reduction, strength, fatigue life or probing accuracy is claimed.

More teeth improve reduction because the ring/pinion tooth-count ratio rises; shrinking both gears' teeth while preserving their tooth-count ratio would not improve resolution. The solid teeth and supported hub target mesh stiffness, while the thicker plates and deeper support target frame flex. There are no soft pads in the probe's structural load path: added compliance can allow positional deflection. Acceleration/current tuning remains necessary after the mechanical test.

Suggested comparison: use the same arm payload, current, microstepping and acceleration on both bases. Measure forward/reverse tip motion and settling with a dial indicator at a known reach. Check the ring through a full revolution by hand before powered testing; record tight spots and backlash before increasing speed. Start with the ring and pinion prints as a fit trial, then print the larger structure.

## Printing and hardware

Download **Print ZIP** for the 26 bed-oriented prototype STLs, manifest, parameters and validation reports. **STEP** contains the full assembly with reference hardware. Right-click any printed part for its actual print-oriented STL; hardware exports are reference envelopes.

Structural prints: `Rigid_fixed_base`, `Rigid_rotating_deck`, `Internal_264T_ring`, `Solid_12T_module1_pinion`, `Pinion_bearing_cap`, `Boxed_Z_support`, `Braced_test_stand`, `Front_Z_frame` and `Center_front_strut` and `Center_rear_strut`. Other actuator and central-cartridge parts are retained. The rear support prints on its flat outside face in approximately 296 × 324 mm; the front frame prints on its flat front face in approximately 224.4 × 314 mm, with a 122 mm height. Rotate the long footprint 90° on the H2S bed. The fixed base and stand are 312 mm square; the deck is 296 mm across. Review local supports and bridging in your slicer, especially the front frame's side-window bridges, the large lower flange and tilted axles. Supplied STLs are bed aligned; mesh checks do not replace slicing.

Additional/revised base hardware:

- One [688ZZ bearing, 8 × 16 × 5 mm](https://www.nsk-literature.com/en/bearing-replacement-guide/offline/download.pdf), on the nominal Ø8.05 mm printed journal.
- Four 625ZZ, 5 × 16 × 5 mm, on nominal Ø5.1 mm integral axles.
- Two 6002, 15 × 32 × 9 mm, on the retained slotted Ø15.25 mm spindle.
- Six M3×40 flat-seated button-head ring screws, six M3 washers and nuts.
- Four M3×20 motor-face screws; three M3×8 bearing-cap screws; one M3×4 pinion set screw.
- Four M5×30 stand screws and four captive M5 nuts.
- Nine M4 support/deck inserts plus one M4 rear-strut deck insert; six M4×12, one M4×20 and two M4×25 support screws (the longer pair pass through the corner gussets).
- Four M3×40 Z-base mounting screws into the actuator's existing receiving inserts.
- Front frame side mounts: eight M4×25 screws, eight M4 nuts and eight M4 washers.
- Center strut attachments: four M4×40 screws, four M4 nuts and four M4 washers; one M4×16 rear foot screw. The shared M4×20 front base screw is included above.
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
.venv/bin/python -m rigid_base.check_front_frame
.venv/bin/python -m rigid_base.check_rotation
.venv/bin/python -m rigid_base.check_explosion
.venv/bin/python -m rigid_base.package
.venv/bin/python -m rigid_base.check_package
```

The packaging command losslessly gzips viewer meshes and shares byte-identical radial print files between Z width pages to remain within hosting size limits. It does not simplify the CAD or print geometry.

The 296 mm ring, 312 mm square base/stand and 296 mm circular deck fit the H2S nominal 340 × 320 × 340 mm volume with 4 mm bed margin on every side. Rotate the deck and long tower/frame prints 90° on the bed where needed. Every actual STL is checked against this envelope; this does not replace slicing.

Compared with the previous 224 mm / 16:1 experiment, the ring is 32.1% larger in diameter, reduction rises 37.5%, and the commanded angular increment falls 27.3%. A larger ring also increases rotating inertia; physical vibration reduction is not assumed.

The model is script-parametric. `parameters.json` specifies the gear pair and selected interface dimensions for this particular design; changing the gear envelope, heights or mount layout requires updating the mating support geometry and rerunning every check. It is not an automatically constrained gearbox configurator. CAD caches are keyed to geometry-source and parameter hashes.

Checks include 65 engagement samples across one ring-tooth pitch, nine Z/radial travel poses against changed parts, full-revolution base samples every 15°, fit-envelope checks, single watertight positive-volume STL shells, flat print contact, through insert bores, and continuously bounded service-explosion translations. Existing actuator-to-actuator travel/thread checks are reused because those parts move together unchanged. Rotation and gear engagement checks are sampled, not a continuous arbitrary-motion proof. Expected press fits, released threads, receiving pilots and nonphysical controller-envelope intersections are recorded explicitly.

When upgrading from the older 224 mm ring experiment, also reprint the 264T ring, fixed base, stand and pinion bearing cap. The 12T pinion, actuator parts, motors and central bearing cartridge are retained. The motor moves from X=90 mm to X=126 mm; ring screws move to a 140 mm radius and stand legs to a 262 mm pitch. Physical stiffness and vibration reduction require a loaded test.

The exploded view lifts the arm/ring/deck/cartridge and attached front frame as one service module. Actuator internals stay assembled. It then separates the pinion/bearing/cap and motor. This is intentionally a module-level service view, not a full fastener-by-fastener assembly guide. Rotation is disabled and reset to zero during explosion.

References: [Oriental Motor — stepper fundamentals and microstepping](https://www.orientalmotor.com/stepper-motors/technology/stepper-motors-basics.html), [SDP/SI — metric gear geometry](https://www.sdp-si.com/resources/elements-of-metric-gear-technology/page3.php). Parent actuator source and provenance remain in the repository's main README.
