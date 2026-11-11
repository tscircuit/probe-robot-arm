# Rigid Base 2

[Interactive assembly](https://modular-flying-probe-arm.seveibar.chatgpt.site/rigid-base2.html)

A separate prototype retaining the 296 mm ring, 22:1 drive, thin 6 mm actuator mounting face, direct radial mounting and lightened base/stand. It replaces the boxed Z support, front frame and both external struts with one **Cylindrical_Z_support** print.

The cage reaches the full **148 mm rotating-deck radius**. Its 5 mm cylindrical wall has large peaked cutouts, broad columns, and inward perimeter flanges with 45° undersides at the base, middle and top. Four columns previously clipped into thin remnants are removed. Wide opposed side ports clear the radial housing and motor throughout the Z stroke. The upper mounting face is solid except for the 31 mm mounting grid. A thin integral 45-degree arch beneath the face supports it while leaving a large opening below. Two 6 mm perforated shear webs directly connect the grid to the rear columns. They angle from X=±62 mm at the grid to roughly X=±38 mm at the rear, placing their feet near existing bolts. Their windows have 45° roofs and broad perimeter margins.

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

## Support and structural study

[Detailed results, assumptions and figures](https://modular-flying-probe-arm.seveibar.chatgpt.site/downloads/rigid-base2/analysis/report.html).

The actual-STL upright audit at 0.2 mm layers found no floating islands or large unsupported growth in the revised cage. Steep downward-facing area is reduced about 97%. Short horizontal-hole bridges remain: inspect the actual H2S slicer preview and bridge performance. The audit is geometric, not generated support material or G-code.

Comparative linear-tetrahedral FEA uses an assumed effective E=1 GPa, ν=0.35, rigidly clamped bottom bolt-pad regions, and four distributed actuator mounting patches. It tests radial/rear-directed 10 N loads, a 20 N load with 150 mm offset, and 1 N·m yaw. Three mesh sizes (6, 4 and 3 mm) consistently indicate better rear-directed bending and offset-payload stiffness. Radial stiffness is effectively unchanged; yaw improvement is not resolved reliably. **Absolute displacement and stress are not mesh-converged. No probing-accuracy or strength certification/safety factor is claimed.** Infill, print anisotropy, insert/bolt compliance, actual deck movement, creep and fatigue are not modeled.

Reproduce after building and bed-aligning the print kit:

```sh
.venv/bin/python -m pip install -r rigid_base2/analysis-requirements.txt
.venv/bin/python -m rigid_base2.prepare_analysis
.venv/bin/python -m rigid_base2.support_analysis before
.venv/bin/python -m rigid_base2.support_analysis after
for mesh in 6 4 3; do
  .venv/bin/python -m rigid_base2.structural_analysis before --size "$mesh"
  .venv/bin/python -m rigid_base2.structural_analysis after --size "$mesh"
done
.venv/bin/python -m rigid_base2.analysis_report
```

The baseline STEP/STL are supplied compressed in `reference/`, from commit ae030ba. Raw mesh and displacement arrays remain local; the website/print ZIP carry the report, figures and input hashes. Reprint only `Cylindrical_Z_support` for this revision. All other kit parts and hardware remain compatible.
