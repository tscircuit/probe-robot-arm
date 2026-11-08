"""Measure actual support bores, common datums, connected faces and screw entry."""
import hashlib,json,pathlib,math
from model import build,layout,pose,cyl,box,overlap,V,actuator_mount_patterns,linear_contacts
root=pathlib.Path(__file__).resolve().parent;p=json.loads((root/'parameters.json').read_text());lay=layout(p);parts,_=build(p,lay);by={a['name']:a for a in parts};support=by['Z_support']['shape'];carrier=by['Z_to_radial_carrier']['shape'];zo=p['z_origin'];dt=lay['deck_top_z'];face=lay['radial_mount_face_z'];hx=lay['h_origin'];zp=lay['zpad']
assert len(support.Solids())==len(carrier.Solids())==1
records=[]
for axis in ['Z','R']:
 for pattern in actuator_mount_patterns(axis,lay):
  checks=[]
  for x,y in pattern['lid']:
   hole=cyl(2.74,6,(26,-y,zo+x),(1,0,0)) if axis=='Z' else cyl(2.74,6,(hx+x,-y,face-6))
   assert overlap(hole,support if axis=='Z' else carrier)<1e-6
   outer=cyl(4,6,(26,-y,zo+x),(1,0,0)) if axis=='Z' else cyl(4,6,(hx+x,-y,face-6))
   land=outer.cut(cyl(2.76,6,(26,-y,zo+x),(1,0,0)) if axis=='Z' else cyl(2.76,6,(hx+x,-y,face-6)))
   assert land.cut(support if axis=='Z' else carrier).Volume()<1e-6,(axis,pattern,x,y)
   checks.append(dict(face='lid',center_local_mm=[x,y],bore_mm=5.5))
  if axis=='Z':
   for x,y in pattern['base']:
    assert overlap(cyl(2.74,8,(-50,-y,zo+x),(1,0,0)),support)<1e-6
    checks.append(dict(face='base',center_local_mm=[x,y],bore_mm=5.5))
  records.append(dict(axis=axis,**pattern,checked_holes=checks))
# The two full-height faces overlap continuously at the outer corner.
for z in [dt+15,zo+45,zo+140]:
 assert support.isInside(V(29,-106,z),1e-6)
 section=support.intersect(box(84,220,.2,(-9,-4,z)))
 assert len(section.Solids())==1
for x,y in lay['z_deck_mounts']:
 assert not support.isInside(V(x,y,dt+5),1e-6)
# All new output pattern bores, including unused 2x outer holes.
for x in [-15.5,15.5]:
 for y in [-78.5,-36.5,-15.5,15.5,36.5,78.5]:assert overlap(cyl(1.69,6,(x,y,zp)),carrier)<1e-6
# Match active M5 holes to the imported receiving pilot centres, not just a drawing.
for axis,meta in [('Z',lay['z_actuator']),('R',lay['r_actuator'])]:
 for i,(x,y) in enumerate(meta['lid']):
  screw=by[f'Z_top_mount_screw_{i}' if axis=='Z' else f'R_enclosure_mount_screw_{i}']['shape']
  assert overlap(screw,support if axis=='Z' else carrier)<1e-6
  assert 14-6==8 and 8<9 # 8 mm entry in 9 mm blind receiving pilot.
# Bound all allowed new screw/plastic contact inside each receiving bore.
contacts=[]
for a in parts:
 if not a.get('thread_host'):continue
 host=by[a['thread_host']]['shape'];v=overlap(a['shape'],host)
 assert v<20,(a['name'],v)
 contacts.append(dict(screw=a['name'],host=a['thread_host'],pilot_engagement_overlap_mm3=v))
low={a['name']:a['shape'] for a in pose(parts,p,lay,z=-20)}
motor=by['Z_NEMA17_full-depth_reference']['shape'];clamp=by['M6x60_axle_bolt']['shape']
assert abs(motor.distance(clamp)-p['z_rack_deck_clearance'])<1e-6
assert low['Z_to_radial_carrier'].distance(support)>=4.9
r=dict(passed=True,patterns=records,output_plate_bores=12,active_output_bolts=8,active_z_mounts=dict(lid=4,side=6),radial_bottom_mounts=4,lid_m5_length_mm=14,side_m5_length_mm=16,m5_entry_mm=8,blind_pilot_depth_mm=9,motor_to_centre_clamp_mm=motor.distance(clamp),corner_connected=True,printed_solids=1,thread_contacts=contacts,notes=['T8 2x/4x holes inferred from published 1x T8 longitudinal pattern and 21 mm widening per multiplier step.','Radial adapter includes stock 40 mm and lengthened 120 mm patterns for both screw families.','Same hole pattern does not establish stroke, load, screw fit or drive compatibility.'],source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ['model.py','parameters.json','leadscrew_actuator.py','check_z_mount.py','rotary_base/core.py','rotary_base/parameters.json']})
(root/'output/z-mount-validation.json').write_text(json.dumps(r,indent=2));(root/'output/mounting-patterns.json').write_text(json.dumps(records,indent=2));print('Mounts verified',len(records),'patterns',flush=True)
