# Hollow backbone experiment

This independent variant replaces the rigid-base tower, two rear braces and extended deck with two closed-section trays and a socket deck. It keeps the 192T/12T module-1 internal drive, 4× inverted Z actuator, 1× radial actuator, 31 mm grid, motors and controller positions. The original assembly and printed-brace experiment remain available.

## Structure

The 3 mm skins are separated by 60 mm; 45° sidewalls taper from a 206 mm front face to an 86 mm rear face. Thin transverse diaphragms support the skins. Two continuous side keys and eight seam bolts transfer load across the split. The 12 mm raised deck socket has 0.3 mm nominal clearance to the shell, and four transverse bolts clamp the root. These are CAD clearances, not calibrated printed fits. Test a socket coupon before a full print if your shrinkage/elephant-foot compensation is unknown.

The three replacement prints have 43.2% less solid CAD volume than the previous support, rear braces and extended deck combined. This is not a slicer weight or stiffness prediction. All 24 printed parts in the resulting assembly fit the H2S dimensional envelope with 4 mm bed margin per side, using 90° bed rotation where needed.

No metal struts or soft isolators are used. Closing the section and widening the root load path is intended to reduce tower bending/twist without external outriggers. Physical stiffness, damping, creep and probe accuracy remain unmeasured. No finite-element stiffness claim is made.

## Parts and assembly

Print the three STLs in their supplied orientations. The trays print broad exterior face down; the deck prints flat underside down. Align the 324 mm tray length along the H2S 340 mm axis. Inspect small horizontal fastener holes in the slicer; clean holes after printing as needed. Keep the ring, fixed base, stand, bearings and actuators from the rigid-base kit. Do not use the old extended deck or tower braces.

Hardware replacing the old tower/brace hardware:

- Eight M4×25 socket-head seam bolts and eight M4 nuts. Place the nuts into the front tray's hexagonal seats before closing it.
- Four M4×20 socket bolts, four M4 washers and four M4 nuts.
- Four M3×10 actuator mounting bolts, replacing the long M3×40 bolts. Check engagement against the actual actuator insert depth.

Install the ring/deck fasteners, seat the front tray over the deck socket, and mount the Z actuator from the open inside face. Install the front socket bolts and nuts. Place the seam nuts in the front tray. Install the rear tray with its socket nuts/bolts loosely placed, engage the continuous side keys, and tighten the seam bolts from the rear angled faces. Tighten all four socket bolts while keeping the tower seated. Do not overtighten printed walls. The rear socket nuts are accessed through the open tray before closure; a small temporary adhesive dot can retain them during assembly. The current viewer explosion is by service module, not a bolt-by-bolt assembly guide.

The structure ZIP contains only the three replacement prints, guide, parameters/check records. The STEP is the replacement structure plus its new fasteners. Shared actuator/base prints remain in the linked rigid-base kit; the viewer reuses their exact meshes and downloads.

## H2S and larger-ring sizing

Bambu specifies 340 × 320 × 340 mm for H2S: https://blog.bambulab.com/h2s-the-ultimate-single-nozzle-3d-printer-now-bigger-than-ever/

This variant retains the 224 mm OD ring. Doubling it to 448 mm cannot print flat as one part. A future candidate is a 296 mm OD / 264T module-1 ring with a 12T pinion, giving 22:1, and a roughly 312 mm square fixed base/stand. This is a sizing proposal only: motor position, roller track, deck, mounting footprint, four-arm reach, backlash and clearances must be redesigned/checked before making it printable. A 312 mm square leaves 4 mm per side along the 320 mm bed axis before any brim. A larger ring alone does not cure tower bending.

## Reproduction

Run from repository root with CadQuery and trimesh installed:

```
python -m hollow_base.model
python -m hollow_base.check
python -m hollow_base.check_explosion
python -m hollow_base.package
node test_hollow_viewer.mjs
```

The mesh delta is tied to the current unchanged rigid-base mesh by hash. Tests check actual exported STLs, interfaces, new-part interference and full-travel envelope separation. The exact viewer explosion uses continuous translation checks. Existing actuator and gear validations apply to unchanged components. Four-arm placement and swept clearances are not yet validated for this experiment.
