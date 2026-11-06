# Rack actuator

FLEX revision 14: printable NEMA17 and NEMA14 linear actuators with compliant rack teeth and six 625ZZ bearings. Three printed parts per variant: an integral spring chassis, rack and pinion.

[Open the interactive viewer](https://flex17-compliant-linear-actuator.seveibar.chatgpt.site) or [open the NEMA14 prototype](https://flex17-compliant-linear-actuator.seveibar.chatgpt.site/?motor=nema14). The motor selector changes the actual CAD, resolution table, collision report and downloads. Both have actuation and staged assembly animations.

## Revision 14

- Spring preload remains **2.3 mm** nominal deflection. The relaxed chassis STL preloads when the rack is installed; assembled STEP shows the deflected shape.
- Bearing pockets have **0.8 mm radial and axial clearance** around rotating faces, with integral shoulders supporting only the inner races. Rack/chassis nominal clearance is **1 mm**.
- Rack backbone widened from **14.5 to 16 mm**, adding material behind the tooth roots.
- Socket-head relief is shallower, with **0.5 mm** clearance instead of 0.8 mm. It stops 7.75 mm before the output end of the guide, leaving the entire 14 mm mounting pad uncut by the head slot. Bolt heads remain modeled conservatively as Ø9.5 × 5 mm.
- The insertion end is square: the former 10 mm underside ramp/chamfer is removed. The curved lower bearing rims engage the square edge during insertion; support the spring seats by hand if needed. The floor remains attached to the actual walls, with an open underside and no rigid lower deck or travel stop.
- Service order removes the lower axles before the angled nuts to clear their removal paths at the higher preload.
- Both retain six 625ZZ bearings, four upper at 45° and two lower, 46 mm station spacing, staggered lower contacts, integral motor land, output mounting pad, oversized D bore and circular tooth-root reliefs.

| Default 40 mm-stroke variant | NEMA17 | NEMA14 development prototype |
| --- | --- | --- |
| Reference motor | 42 × 42 × 23 mm | 35.2 × 35.2 × 20 mm |
| Motor mounting pitch | 31 mm | 26 mm |
| Chassis footprint | 68 × 81 mm | 68 × 75 mm |
| Pinion, module 2 | 18 teeth / 20° | 14 teeth / 25° |
| Pinion outside diameter | 40 mm | 32 mm |
| Travel / motor revolution | 113.097336 mm | 87.964594 mm |
| Full step at 200 steps/rev | 0.565487 mm | 0.439823 mm |
| 1/16 command increment | 0.035343 mm | 0.027489 mm |

The NEMA14 gear produces 22.2% smaller commanded increments. This is theoretical resolution, not measured accuracy. Its matched 25° rack and pinion avoid the standard 20° undercut issue at 14 teeth. **Do not mix NEMA14 and NEMA17 racks/pinions.** Reference motor dimensions and shaft length must be checked against the actual motor drawing.

From revision 13, **reprint only the rack** for your selected variant. Reuse its chassis and matching pinion. From revision 12, the updated chassis is also needed. Print all three matching parts for a new NEMA14 build. Bearings and specified axle hardware remain the same.

## Files and regeneration

- [model.py](model.py): shared parametric CadQuery source.
- [NEMA17 downloads](dist/downloads): STEP, three STL files, source, validation and ZIP bundle.
- [NEMA14 downloads](dist/variants/nema14/downloads): equivalent variant-specific files.
- [README.txt](README.txt): printing, hardware, assembly and fit guidance.
- [dist](dist): standalone Three.js viewer, no API keys or backend.

Use Python 3.12 and CadQuery 2.7.0:

```sh
pip install -r requirements.txt
python model.py --motor nema17 --out dist --check
python model.py --motor nema14 --out dist/variants/nema14 --check
python package_designs.py
python -m http.server 8000 --directory dist
```

Packaging verifies that both passing reports match the current source before updating the downloadable source and ZIPs. Checks can take several minutes.

Parameters: `--stroke 40` (20–80 mm), `--preload 0.10` (tooth oversize), `--spring-preload 2.3` (0.1–2.5 mm), `--spring-thickness 1.4` (1.2–1.8 mm), `--bearing-clearance 0.8` and `--hardware-clearance 0.5` (0.5–1.2 mm). `--rack-backbone-width 16` accepts 14.5–18 mm. Shaft defaults: `--shaft-diameter 5 --shaft-flat-depth 0.5 --shaft-clearance 0.15`. Changed dimensions require fresh checks.

## Validation and physical testing

Generated reports check all assembled pairs, sampled travel and staged service, unloaded single-solid chassis, wall-local blends, rack-to-hardware clearances and nominal tooth mesh. Only the intended elastic tooth contact is allowed. Viewer and CAD use the same motion tracks. The viewer uses exact sampled chassis shapes at one twelfth of the spring preload while hardware follows the continuous tracks.

**2.3 mm is an aggressive spring prototype.** Prescribed CAD displacement does not establish elastic recovery, preload force, fatigue life or creep. Test a spring-floor coupon in the chosen print orientation/material before the full chassis. There is no lower mechanical stop. Sampled rigid intersections are not a continuous swept-volume proof or physical tolerance test. Use controller travel limits; the rack insertion end is open. Backlash, stiffness, load capacity and positioning accuracy remain unmeasured.

## License and inspiration

MIT; see [LICENSE](LICENSE). The rack adapts the spring-wall principle from [seveibar/compliant-spur-gear](https://github.com/seveibar/compliant-spur-gear); its license is included in both bundles.

