"""Verify exported print meshes rather than only the source CAD solids."""
import argparse,json,pathlib
import numpy as np
import trimesh
ap=argparse.ArgumentParser();ap.add_argument('directory');args=ap.parse_args();root=pathlib.Path(args.directory)
rows=[]
for p in sorted(list((root/'STL').glob('*.stl'))+list((root/'OPTIONAL_fit_tests').glob('*.stl'))):
    mesh=trimesh.load_mesh(p,process=True)
    r=dict(file=str(p.relative_to(root)),watertight=bool(mesh.is_watertight),consistent_winding=bool(mesh.is_winding_consistent),positive_volume=bool(mesh.volume>0),connected_shells=len(mesh.split(only_watertight=False)),size_mm=mesh.extents.tolist(),bed_z_mm=float(mesh.bounds[0,2]),triangles=len(mesh.faces))
    assert r['watertight'] and r['consistent_winding'] and r['positive_volume'] and r['connected_shells']==1,r
    assert abs(r['bed_z_mm'])<1e-5 and max(r['size_mm'][:2])<=200.01,r
    rows.append(r)
assert len(rows)>=20,'Missing expected main and fit-test meshes'
(root/'mesh_validation.json').write_text(json.dumps(dict(passed=True,files=rows),indent=2))
print('Verified',len(rows),'watertight, consistently wound, single-shell STLs, on Z=0 and within 200 mm XY.')
