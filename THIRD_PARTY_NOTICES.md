# Third-party sources

- `upstream/rack-actuator-r24/` pins tscircuit/rack-actuator revision 24 at `a0ccaf201d6f6f5f988ca64dc1a9f5e7aba931b5`. Its MIT license and upstream README are included. `model.py` loads its construction section and adapts the Z output pad locally.
- `upstream/compliant-spur-gear/` contains the original gear sources and MIT license. The shared Python rotary gear geometry adapts the open-tip tooth profile from revision 3, `37682731f360b1b327a91f8713c9e67c464a8b32`, in seveibar/compliant-spur-gear.
- Three.js and OrbitControls in `site/dist/vendor/` and `base_test_kit_v4/vendor/` are version 0.180.0, under the included MIT license. The offline viewer bundle contains these libraries.
- CadQuery and development dependencies retain their respective licenses and are installed separately.
