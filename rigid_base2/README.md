# Rigid Base 2

[Interactive assembly](https://modular-flying-probe-arm.seveibar.chatgpt.site/rigid-base2.html)

A separate prototype retaining the 296 mm ring, 22:1 drive, thin 6 mm actuator mounting face, direct radial mounting and lightened base/stand. It replaces the boxed Z support, front frame and both external struts with one **Cylindrical_Z_support** print.

The cage reaches the full **148 mm rotating-deck radius**. Its 5 mm cylindrical wall has large circumferential cutouts, vertical webs, and inward perimeter flanges at the base, middle and top. Wide opposed side ports clear the radial housing and motor throughout the Z stroke. The upper mounting face is solid except for the 31 mm mounting grid. A thin integral 45-degree arch beneath the face supports it while leaving a large opening below.

The cage uses all nine existing support/deck mounts plus the existing rear-center insert. All ten cage foot screws are **M4×12**. Retain the M4 deck inserts. Remove both external struts, the front frame and their hardware, including their old M4×20/M4×25 support screws. The four M3×10 actuator mount screws remain. No new holes are required in the rotating deck.

The kit contains 23 print-oriented STLs. The cage prints upright on its broad bottom flange, approximately 296 × 296 × 324 mm, within the H2S envelope with 4 mm bed margin. Review local support/bridging at the large wall windows and inward flanges; this is not a support-free print claim. The mounting face is accessible through the rear windows; install actuator screws before closing access with the remaining assembly.

Z actuator: blue-gray. Radial actuator: terracotta. The two complete modules keep separate colors, and custom parts keep their own colors.

```sh
.venv/bin/python -m rigid_base2.model
.venv/bin/python -m rigid_base2.check prints
.venv/bin/python -m rigid_base2.check cage
.venv/bin/python -m rigid_base2.check collision
.venv/bin/python -m rigid_base2.check rotation
.venv/bin/python -m rigid_base2.check explosion
.venv/bin/python -m rigid_base2.package
node test_rigid_viewer.mjs --cage
```

Validation checks the cage footprint and mounts, full linear swept boxes, sampled gear/base rotation, continuous service-explosion paths and actual STL integrity/print bounds. Intentional bearing/insert fits and released threads are exceptions. Physical stiffness, vibration, fatigue and probing accuracy remain unmeasured. This larger single-module experiment does not certify a four-arm platform.
