"""Measure the shaft, 45-degree lead-in, and fit coupon in exported STL files."""
import hashlib,json,pathlib
import numpy as np
import trimesh
root=pathlib.Path(__file__).resolve().parent.parent/'output/armature-base-test-v4'
rows=[]
for file,zmin in [('STL/05_fixed_spindle_15p25_chamfer0p5_qty1.stl',10.1),('OPTIONAL_fit_tests/spindle_coupon_15.25mm.stl',2.1)]:
 p=root/file;m=trimesh.load_mesh(p,process=True);top=float(m.bounds[1,2]);v=m.vertices[m.vertices[:,2]>zmin]
 diameter=2*max(np.linalg.norm(v[:,:2],axis=1))
 tip=m.vertices[np.abs(m.vertices[:,2]-top)<1e-4]
 tip_diameter=2*max(np.linalg.norm(tip[:,:2],axis=1))
 shoulder=m.vertices[np.abs(m.vertices[:,2]-(top-.5))<1e-4]
 assert len(shoulder)>0 and abs(2*max(np.linalg.norm(shoulder[:,:2],axis=1))-15.25)<1e-4
 assert abs(diameter-15.25)<1e-4 and abs(tip_diameter-14.25)<1e-4,(file,diameter,tip_diameter)
 assert m.is_watertight and m.is_winding_consistent and len(m.split())==1
 assert abs(m.bounds[0,2])<1e-5 and abs(top-(43.6 if file.startswith('STL/') else 12))<1e-4
 rows.append(dict(file=file,measured_mesh_diameter_mm=float(diameter),top_diameter_mm=float(tip_diameter),chamfer_axial_mm=.5,chamfer_radial_mm=(diameter-tip_diameter)/2,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
p=root/'STL/06_inner_race_spacer_15p8_bore_qty1.stl';m=trimesh.load_mesh(p)
bore=2*min(np.linalg.norm(m.vertices[:,:2],axis=1));assert abs(bore-15.8)<1e-4
assert m.is_watertight and m.is_winding_consistent and len(m.split())==1
rows.append(dict(file=str(p.relative_to(root)),measured_bore_mm=float(bore),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(root/'spindle_print_validation.json').write_text(json.dumps(dict(passed=True,requested_diameter_mm=15.25,top_chamfer_mm=.5,bearing_bore_mm=15,nominal_diametral_interference_mm=.25,files=rows),indent=2));print(rows)
