"""Measure all four tilted integral axles in the actual printable base STL."""
import hashlib,json,math,pathlib
import numpy as np
import trimesh
from rotary_base.core import roller_layout
root=pathlib.Path(__file__).resolve().parent
p=json.loads((root/'parameters.json').read_text());lay=roller_layout(p);out=root.parent/'output/armature-base-test-v4'
file=out/'STL/01_cutout_base_four_45deg_axles_qty1.stl';mesh=trimesh.load_mesh(file);v=mesh.vertices;q=math.sqrt(.5);rows=[]
assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1
for angle in p['roller_angles_deg']:
 a=math.radians(angle);x=v[:,0]*math.cos(a)+v[:,1]*math.sin(a)-lay['center_r'];y=-v[:,0]*math.sin(a)+v[:,1]*math.cos(a);z=v[:,2]-lay['center_z']
 t=q*(x+z);normal=q*(-x+z);rho=np.sqrt(y*y+normal*normal)
 journal=rho[(t>-2.501)&(t<2.701)&(rho<3)]
 tip=rho[(np.abs(t-3)<1e-4)&(rho<3)]
 assert len(journal)>20 and len(tip)>20
 diameter=2*max(journal);tip_diameter=2*max(tip)
 assert abs(diameter-5.1)<1e-4 and abs(tip_diameter-4.5)<1e-4,(angle,diameter,tip_diameter)
 slots=[]
 if p.get('roller_axle_slot_width_mm',0):
  tip_mask=(np.abs(t-3)<1e-4)&(rho<3)
  face_ids=np.flatnonzero(np.all(tip_mask[mesh.faces],axis=1))
  caps=mesh.submesh([face_ids],append=True)
  assert len(caps.split(only_watertight=False))==4,'Axle tip must have four separate segments'
  for direction in [0,90,180,270]:
   c=math.cos(math.radians(direction));s=math.sin(math.radians(direction))
   radial=y*c+normal*s;across=-y*s+normal*c
   edge=across[tip_mask&(radial>.75)]
   width=float(min(edge[edge>0])-max(edge[edge<0]))
   assert abs(width-p['roller_axle_slot_width_mm'])<1e-4,(angle,direction,width)
   bottom=t[(radial>.75)&(rho<2.6)&(np.abs(across)<.03)&(t>-2.49)]
   assert len(bottom)>0
   end=float(min(bottom));expected=-2.5+p['roller_axle_slot_root_mm']
   assert abs(end-expected)<.02,(angle,direction,end)
   slots.append(dict(direction_deg=direction,width_mm=width,length_mm=3-end,root_mm=end+2.5))
 rows.append(dict(angle_deg=angle,tilt_deg=45,axle_diameter_mm=float(diameter),tip_diameter_mm=float(tip_diameter),chamfer_mm=.3,relief_slots=slots))
report=dict(passed=True,track_normal_advance_mm=p.get('roller_track_overlap_mm',0),bearing_center_radius_mm=lay['center_r'],bearing_center_z_mm=lay['center_z'],blocks_per_bearing=1,roller_count=4,roller_fasteners=0,file=str(file.relative_to(out)),sha256=hashlib.sha256(file.read_bytes()).hexdigest(),axles=rows)
(out/'roller_print_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
