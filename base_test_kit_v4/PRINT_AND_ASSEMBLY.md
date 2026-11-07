# Armature base — four angled press-fit rollers, v4.7

The main arm and this independent test fixture use the same rotary-base CAD. Four **625ZZ bearings** run on a continuous **45° outer track** on the 72T ring. Each bearing has **one integral block and printed axle**, tilted 45°. There are no roller bolts, nuts or separate spacers.

![Assembly and exploded view](ASSEMBLY_PREVIEW.png)

## Roller track fit update (v4.7)

Reprint **part 01 only** when updating from v4.6. All four bearings and their integral axle blocks move **0.4 mm perpendicular to the 45° track** (0.282843 mm inward and upward), creating the requested nominal overlap. The ring, deck and hardware are unchanged. This is a print-fit adjustment, not a measured preload force. Verify seating and free rotation on the printed assembly before powering the motor.

The viewer now offers **Isolate**, **Hide part** and **Show All** on right-click. Show All works on empty space and restores hardware and clearance envelopes too.

## Lightweight deck update (v4.6)

Reprint **part 10 only** when updating from v4.5. Five R3-cornered windows reduce the rotating deck's solid CAD volume by **25.2%**. The 6 mm plate retains its 10 mm outer rim, 28 mm-radius hub, six 14 mm radial ribs, all fastener seats and complete Z-cradle flange footprints. Print with the original top face against the bed, as oriented in the supplied STL. The main assembly and test fixture share this exact deck. Other parts and hardware are unchanged. Physical stiffness remains unmeasured.

## Lightweight plate update (v4.5)

The v4.5 update changed **part 01** from v4.4. Five large through-cutouts with R6 corners remove approximately **37% of the base's solid CAD volume**. The remaining plate has a 10 mm perimeter and 28.3 mm diagonal webs, with the complete motor pad, spindle hub, mounting lands and bearing-block footprints retained. Plate thickness stays 11 mm, and all remaining lower faces lie on Z0 for printing. Slicer material saving depends on wall and infill settings; stiffness has not been physically measured.

## Changes to print

When updating from the flat-base kit (v4.2), reprint **01 base plate, 05 spindle, 10 rotating deck and 11 ring**. The integrated stand, central bearing housing, spacer, top washer, lower retainer and 12T pinion retain their printable geometry. The plate underside remains flat; the plate, motor and deck mounting heights are unchanged.

The spindle journal is **Ø15.25 mm**, with a **0.5 mm × 45° top chamfer** and Ø14.25 mm lead-in. The flange, centre bolt bore and total height are unchanged. Keep the Ø15.8 spacer. The nominal 6002 bore is 15 mm, so the selected print-fit allowance is 0.25 mm diametrically. Check a coupon or finish the printed fit as needed.

The ring outer radius grows from 82 to **88 mm (176 mm OD)**. Its lower outer edge has a **6 × 6 mm, 45° bevel**, from radius 82 at Z28 to radius 88 at Z34. The contact line is centered at radius 85, Z31. The involute teeth, six bolt locations and integral deck spacers remain unchanged.

Use **M3×30 button-head screws with flat bearing faces**, maximum head diameter 5.7 mm and height 1.65 mm, through the six straight ring holes. Do not countersink them. Their heads sit under the ring at radius 78 and never form part of the rolling track. The modeled bearing bodies stay more than 2 mm radially outside every head throughout rotation.

## Four roller supports

Use **4 × 625ZZ, 5 mm bore × 16 mm OD × 5 mm wide**. Axles are placed at 45°, 135°, 225° and 315° around the base, pointing outward and upward at 45°. Each bearing presses onto its printed axle from the outside. The single block has an 8 mm thickness, tapered shoulders and an R6 rounded crown.

The axle is **Ø5.1 mm**, with a **0.3 mm × 45° lead-in** at its free end. A 1 mm-long, 8 mm OD shoulder supports only the inner race. The cylindrical bearing engagement is 5 mm; the axle tip projects 0.5 mm past the bearing. No bolt, nut, clip or second block is used. The outer race and shields must turn freely after installation.

The axles are fixed rather than slotted. Seat the 6002 cartridge first, then check how the nominal 0.4 mm track interference fits the actual print. Do not power a binding assembly. Check free rotation through a full turn. Four printed contacts require accurate printing; the model does not establish preload, stiffness, axle strength, creep or wear. Use the optional 4.9, 5.0 and 5.1 mm axle coupons printed at the same 45° orientation to check your bearing fit before printing the plate.

## Print list and orientation

All STL files use millimetres. Import at 100% scale. The largest part is the 200 × 200 mm stand; allow room for a brim.

| Prefix | Part | Quantity |
|---|---|---:|
| 01 | Flat module plate with five large cutouts, four single blocks and integral 45° axles | 1 |
| 02 | Integrated 200 × 200 mm stand | 1 |
| 05 | Ø15.25 spindle with 0.5 mm top chamfer | 1 |
| 06 | 16 mm inner-race spacer, Ø15.8 bore | 1 |
| 07 | Inner-race top washer | 1 |
| 08 | Housing with two Ø32.2 bearing seats | 1 |
| 09 | Lower outer-race retainer | 1 |
| 10 | Shared deck with five rounded windows and six Z-cradle insert seats | 1 |
| 11 | 72T ring, integral spacers and continuous outer bevel | 1 |
| 13 | Open-tip compliant 12T pinion | 1 |

Print the **plate flat underside down**, with the blocks and axles upward. Its plate is 11 mm thick and the recessed spindle seat keeps a 4 mm floor. No support is needed beneath the broad underside. Inspect the 45° axles and layer adhesion in the slicer; keep their bearing surfaces clean. Five walls and 40–50% infill are starting settings for a fit prototype, not a load qualification.

Print the ring with its broad lower face on the bed and spacer posts up; the outer track grows upward at 45°. The stand prints platform-down and the pinion with its broad gear face down. The lower retainer and deck are supplied flipped. The deck's flat upper face goes on the bed, with its insert bosses upward. The spindle and race spacer should be solid.

Optional fit files include housing seat coupons and replacements for 32.0–32.3 mm seats, spindle coupons/replacements for 14.7, 14.8, 14.9, 15.0, 15.1, 15.25 and 15.5 mm journals, and three tilted 625 axle coupons. Fit alternatives replace their corresponding main part. Do not scale the whole assembly to adjust a fit.

## Hardware for one base

| Item | Quantity | Use |
|---|---:|---|
| 6002 bearings, 15 × 32 × 9 mm | 2 | Central cartridge |
| 625ZZ bearings, 5 × 16 × 5 mm | 4 | Tilted outer-track rollers on printed axles |
| Full-depth NEMA17, reference 42.3 mm square × 48 mm body, 5 mm D shaft | 1 | Direct underside mount |
| M5×25 socket-cap screws | 4 | Plate to integrated stand |
| M5 hex nuts, 8 mm AF × 4 mm thick | 4 | Captive in stand |
| M3×16 socket-cap screws | 4 | Motor face: 11 mm plate plus nominal 5 mm engagement |
| M3×12 socket-cap screws | 2 | Spindle flange through recessed plate floor |
| M3×45 socket-cap screws | 4 | Lower retainer, housing and deck |
| M3×30 button-head screws, head ≤5.7 mm OD × 1.65 mm high | 6 | Flat seats underneath ring; no countersinks |
| M3 hex nuts, 5.5 mm AF × 2.4 mm | 12 | 2 spindle + 4 housing + 6 ring |
| M3 flat washers, approximately 0.5 mm thick | 6 | Above deck under ring nuts |
| M3×4 flat-point grub screw | 1 | Pinion clamp; tap its 2.5 mm pilot M3 |
| M6×60 bolt | 1 | Centre inner-race stack |
| M6 hex nut | 1 | Centre clamp |
| M6 washers, approximately 12 mm OD × 1.6 mm | 2 | Below flat plate and above printed washer |

The main platform uses four **M5×30 bolts per module**, with washers and nuts below its 10 mm plate, instead of the bench stand screws. Main-arm Z-cradle M4 inserts and actuator hardware are shown in the main assembly.

Verify actual motor thread depth and shaft projection. The motor face is Z0, pilot Z0–2 and reference D shaft Z2–24. The pinion hub is Z17–28, giving 7 mm nominal shaft engagement; its grub screw is at Z22. The rear controller reference includes 6 mm insulating spacers, a 1.6 mm PCB and provisional component/USB envelopes. The lowest envelope is Z−67.6, 12.4 mm above the stand top.

## Assembly

1. Check the spindle and tilted axle coupons against your actual bearings. Remove burrs without changing the intended bearing shoulders.
2. Fasten the NEMA17 below the flat plate using four M3×16 screws. Check the nominal 5 mm motor thread engagement against your selected motor.
3. Press each 625ZZ onto its printed axle **along the 45° axis**, supporting its inner race. Seat it against the shoulder and check that its outer race turns freely.
4. Assemble the central cartridge: two 6002 bearings in the housing, Ø15.8 spacer between inner races, lower retainer and deck secured with four M3×45 screws and captive nuts. Bearing centres remain 25 mm apart, with 0.2 mm nominal outer-retainer end clearance.
5. Fit the Ø15.25 spindle through the cartridge. Its flange rests at Z4 in the plate recess. Secure it from below with two M3×12 screws and the flange's captive nuts.
6. Pass the M6×60 bolt and lower washer upward through the plate and spindle. Fit the printed top washer, steel washer and M6 nut. Retain the inner races without binding the cartridge.
7. Fit the pinion onto the motor shaft, hub down, with its set screw. Secure the ring to the deck using the six **flat-seated M3×30 button-head screws** from below, plus the top washers and nuts. Teeth run at Z28–40; the bevel must rest on the four rollers. Do not force the compliant teeth into mesh.
8. Check all four outer races roll on the bevel through a complete turn. They must not touch screw heads. Attach the stand with four M5×25 screws and captive nuts, then install the rear controller after checking real connector clearance. Start with hand rotation, then slow unloaded powered rotation. The 12/72 pair gives 6:1 reduction.

## Viewer and checks

Left drag orbits, middle-button drag pans, and the scroll wheel zooms. Right-click opens the part download and **Show hidden edges** menu; it does not pan. Both the main and Base test pages use identical shared parts. The offline `VIEWER.html` also supports these controls.

The base explosion has **34 translation stages**. The central cartridge lifts clear of the tilted rollers before disassembly. The four rollers finally slide off the printed axles along their 45° axes. Rotation is reset and disabled during explosion. Threads are assumed unthreaded before withdrawal. Intended spindle/bearing and printed-axle/bearing press fits are explicitly measured and reported separately from rigid collision checks. Exact tangent-plane bounds verify that the ring clears the tilted bearings throughout its initial lift.

Collision checks cover ideal CAD and stated reference envelopes; printed fits, stiffness, wear, cable routing and probing accuracy still require physical testing.
