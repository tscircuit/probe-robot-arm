"""Measure the shaft, 45-degree lead-in, and fit coupon in exported STL files."""
import hashlib,json,pathlib,math
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
 tip_mask=np.abs(m.vertices[:,2]-top)<1e-4
 caps=m.submesh([np.flatnonzero(np.all(tip_mask[m.faces],axis=1))],append=True)
 assert len(caps.split(only_watertight=False))==4, 'Central spindle tip must have four segments'
 start=10 if file.startswith('STL/') else 2
 xy=m.vertices[:,:2];rho=np.linalg.norm(xy,axis=1);slots=[]
 for direction in [0,90,180,270]:
  a=math.radians(direction);radial=xy[:,0]*math.cos(a)+xy[:,1]*math.sin(a);across=-xy[:,0]*math.sin(a)+xy[:,1]*math.cos(a)
  edge=across[tip_mask&(radial>4)]
  width=float(min(edge[edge>0])-max(edge[edge<0]));assert abs(width-.5)<1e-4
  bottom=m.vertices[(radial>4)&(rho<7.8)&(np.abs(across)<.03)&(m.vertices[:,2]>start+.01),2]
  assert len(bottom)>0;end=float(min(bottom));assert abs(end-(start+.5))<.02,(file,direction,end)
  slots.append(dict(direction_deg=direction,width_mm=width,length_mm=top-end,connected_root_mm=end-start))
 rows.append(dict(relief_slots=slots,file=file,measured_mesh_diameter_mm=float(diameter),top_diameter_mm=float(tip_diameter),chamfer_axial_mm=.5,chamfer_radial_mm=(diameter-tip_diameter)/2,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
p=root/'STL/06_inner_race_spacer_15p8_bore_qty1.stl';m=trimesh.load_mesh(p)
bore=2*min(np.linalg.norm(m.vertices[:,:2],axis=1));assert abs(bore-15.8)<1e-4
assert m.is_watertight and m.is_winding_consistent and len(m.split())==1
rows.append(dict(file=str(p.relative_to(root)),measured_bore_mm=float(bore),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(root/'spindle_print_validation.json').write_text(json.dumps(dict(passed=True,requested_diameter_mm=15.25,top_chamfer_mm=.5,bearing_bore_mm=15,nominal_diametral_interference_mm=.25,files=rows),indent=2));print(rows)
