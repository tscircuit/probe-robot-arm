"""Check the printable base's broad bed contact and recessed spindle floor."""
import hashlib, json, pathlib
import numpy as np
import trimesh
import rotary_base
from rotary_base.core import cyl

root = pathlib.Path(__file__).resolve().parent
p = rotary_base.parameters()
parts, _ = rotary_base.build(p)
base = next(q for q in parts if q['name'] == 'Fixed_base_plate')
s = base['shape']
assert s.isValid() and len(s.Solids()) == 1
assert abs(s.BoundingBox().zmin) < 1e-7
bottom = [f for f in s.Faces() if f.geomType() == 'PLANE'
          and abs(f.Center().z) < 1e-7 and f.normalAt().z < -.999]
area = sum(f.Area() for f in bottom)
assert len(bottom) == 1 and area > .5 * 190 * 190
relief=json.loads((root/'output/base-cutouts-validation.json').read_text());assert relief['passed']
expected_area=35364.87570440102-relief['removed_volume_mm3']/p['base_plate_thickness_mm']
assert abs(area-expected_area)<1e-5
# Test away from the three through-holes: 4 mm material, open recess above it.
floor = cyl(2, 4, (0, 12, 0))
above = cyl(2, 7, (0, 12, 4))
assert floor.cut(s).Volume() < 1e-6 and above.intersect(s).Volume() < 1e-6
files = [root/'output/prototype-parts/Module_base.stl',
         root/'output/armature-base-test-v4/STL'/(base['print_id']+'.stl')]
rows = []
for path in files:
    mesh = trimesh.load_mesh(path)
    assert mesh.is_watertight and mesh.is_winding_consistent
    assert len(mesh.split()) == 1 and abs(mesh.bounds[0, 2]) < 1e-6
    bed = np.all(np.abs(mesh.triangles[:, :, 2]) < 1e-6, axis=1)
    mesh_area = float(mesh.area_faces[bed].sum())
    assert abs(mesh_area - area) < 1 and mesh_area > .5 * 190 * 190
    rows.append(dict(file=str(path.relative_to(root)), bed_contact_area_mm2=mesh_area,
                     sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
assert rows[0]['sha256'] == rows[1]['sha256']
report = dict(passed=True, plate_thickness_mm=p['base_plate_thickness_mm'],
              underside_z_mm=0, spindle_floor_mm=4, bottom_face_count=len(bottom),
              cad_bed_contact_area_mm2=area, footprint_contact_fraction=area/(190*190),
              files=rows, source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest()
              for n in ['check_flat_base.py','rotary_base/core.py','rotary_base/parameters.json']})
(root/'output/flat-base-validation.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
