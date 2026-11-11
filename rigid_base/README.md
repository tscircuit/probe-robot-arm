# Rigid base

[Interactive assembly and print kit](https://modular-flying-probe-arm.seveibar.chatgpt.site/rigid-base.html)

The braced version retains the 296 mm / 264T internal ring, 12T pinion, 22:1 ratio, 312 mm fixed base and two centered struts. Rigid Base 2 is a separate cylindrical-support experiment.

## Thin grid mounting plate

The upper grid is now one solid **6 mm plate**, from Z=226.2 to 380.2 mm, with only its 31 mm grid holes and two rear-strut insert holes. The former 42 mm deep ladder, rear skin and upper box walls are removed. Small side attachment lands remain outside the grid. The actuator mounting face stays at Y=−42 mm, so actuator and probe positions do not move.

The lower support frame retains its lightened walls, full-radius 6 mm foot and local screw seats. Four M3×10 screws pass through the plate into the actuator's existing inserts. The rear strut steps around the lower support and attaches directly to the new plate using two M4×50 screws and **two 5 mm-long M4 heat-set inserts**. The rear nuts and washers are removed. Its deck foot still uses M4×16 and an open deck insert.

The front frame retains its eight side bolts and gains two small, integral 6 mm bottom flanges at (±118.2,40) mm. Two M4×12 screws attach these flanges to **two 5 mm-long M4 inserts** in the Z-support foot. The screw ends stop at the rotating deck surface. The front center strut and its shared M4×20 foot screw remain.

The entire Z actuator is blue-gray; the radial actuator is terracotta. Each actuator uses one color, including its hardware. Custom structural parts remain individually colored.

## Relieved base and stand

Five rounded through openings lighten the fixed base while preserving its 16 mm rim, 28 mm diagonal webs, spindle land, motor pad and four integral tilted roller blocks. The braced test stand now also has four large rounded openings in its bottom plate. Continuous perimeter and diagonal members remain, together with solid material under all four legs and their eight gussets.

## Printing and assembly changes

From the preceding lightweight revision, reprint **Boxed_Z_support, Front_Z_frame, Center_rear_strut and Braced_test_stand**. The fixed base, deck, front strut, ring and actuators are retained. The kit includes all 26 print-oriented STLs and a complete STEP assembly.

The thin upper plate is offset from the lower support's original flat back. When printing the support on that back, enable slicer supports beneath the upper plate; it is no longer a fully coplanar back-face print. The front-frame side windows and bottom flanges also require slicer review/local support. The rear strut prints flat on its broad side. All actual meshes are checked for watertightness and H2S fit with 4 mm bed margin. Mesh checks do not establish support-free printability.

Fit the rear-strut inserts before mounting the actuator. Use M4 inserts no longer than 5 mm in the 6 mm plate and foot. Assemble the front frame before the radial module passes through its side ports. Tighten the frame and struts with the tower square.

Hardware retained: two 6002 bearings; four 625ZZ rollers; one 688ZZ pinion bearing; six M3×40 button-head ring screws; four M3×20 motor screws; three M3×8 pinion-cap screws; four M5×30 stand screws. Nine support/deck inserts plus the rear-strut deck insert remain. Front strut attachments use two M4×50 screws, nuts and washers; front-frame sides use eight M4×25 screws, nuts and washers. The new bottom flanges add two M4×12 screws and two M4 inserts; the rear strut now uses two M4 inserts instead of nuts and washers.

## Validation

```sh
.venv/bin/python -m rigid_base.model
.venv/bin/python -m rigid_base.prepare_prints
.venv/bin/python -m rigid_base.check_front_frame
.venv/bin/python -m rigid_base.check
.venv/bin/python -m rigid_base.check_rotation
.venv/bin/python -m rigid_base.check_explosion
.venv/bin/python -m rigid_base.package
.venv/bin/python -m rigid_base.check_package
node test_rigid_viewer.mjs
```

Checks cover grid solid/depth, mounting seats, actuator sweeps, sampled gear engagement and base rotation, continuously bounded service-module explosion, actual STL integrity and print bounds, and browser/download behavior. Intentional insert fits, bearing press fits and released threads are recorded exceptions. Physical stiffness, creep, vibration and probing accuracy require loaded testing. The larger experimental base does not certify four-arm platform clearance.
