"""Check single-face mounting, shared hole patterns and the direct ribbed carrier."""
import argparse,hashlib,json,pathlib
from model import build,layout,pose,cyl,box,overlap,V,actuator_mount_patterns
root=pathlib.Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--config',default=str(root/'parameters.json'));ap.add_argument('--out',default=str(root/'output'));args=ap.parse_args();out=pathlib.Path(args.out)
p=json.loads(pathlib.Path(args.config).read_text());lay=layout(p);parts,_=build(p,lay);by={a['name']:a for a in parts};support=by['Z_support']['shape'];carrier=by['Z_to_radial_carrier']['shape'];zo=p['z_origin'];dt=lay['deck_top_z'];zp=lay['zpad'];hx=lay['h_origin']
assert len(support.Solids())==len(carrier.Solids())==1
assert not any(a['name'].startswith(('Z_top_mount_','Z_enclosure_mount_')) for a in parts)
assert overlap(support,box(500,200,500,(0,58.001,dt+260.001)))<1e-6,'Support extends past the base mounting plane'
records=[]
for axis in ['Z','R']:
 for pat in actuator_mount_patterns(axis,lay):
  checks=[]
  for x,y in pat['base']:
   c=(y,-52,zo+x) if axis=='Z' else (hx+x,y,zp+2);u=(0,1,0) if axis=='Z' else (0,0,1)
   hole=cyl(2.74,10,c,u);host=support if axis=='Z' else carrier
   assert overlap(hole,host)<1e-6,(axis,pat,x,y)
   if axis=='Z':
    land=cyl(4,10,c,u).cut(cyl(2.76,10,c,u));assert land.cut(host).Volume()<1e-6
   checks.append(dict(face='base',local_xy_mm=[x,y],bore_mm=5.5))
  records.append(dict(axis=axis,**pat,checked_holes=checks))
# The full 4x flange bears directly on a continuous seat, with no narrow stem.
seat=box(168,42,2,(0,0,zp+1))
for x in [-78.5,-36.5,-15.5,15.5,36.5,78.5]:
 for y in [-15.5,15.5]:seat=seat.cut(cyl(1.71,4,(x,y,zp-1)))
assert seat.cut(carrier).Volume()<1e-6
assert carrier.isInside(V(0,0,zp+7),1e-6)
for y in [-46,46]:assert box(200,7,15,(100,y,zp+20)).cut(carrier).Volume()<1e-6
for a in parts:
 if a['name'].startswith('Z_base_mount_'):
  assert overlap(a['shape'],support)<1e-6,(a['name'],'support')
  assert overlap(a['shape'],by['Z_Adjustable_six-bearing_base']['shape'])<1e-6,(a['name'],'actuator')
 if a['name'].startswith(('R_enclosure_mount_','R_base_captive_nut_')):
  assert overlap(a['shape'],carrier)<1e-6,a['name']
  assert overlap(a['shape'],by['R_Adjustable_six-bearing_base']['shape'])<1e-6,a['name']
assert len([a for a in parts if a['name'].startswith('Z_base_mount_screw_')])==4
assert len([a for a in parts if a['name'].startswith('R_base_captive_nut_')])==4
for a in parts:
 if a['name'].startswith('Z_output_mount_screw_'):assert a['shape'].BoundingBox().zmax<lay['radial_mount_face_z']-.19
# Body floor sits on the carrier, and the screw axis is above that floor.
assert not p['radial_inverted'];assert lay['r_drive_z']-lay['radial_mount_face_z']==42
motor=by['Z_NEMA17_full-depth_reference']['shape'];gap=motor.distance(by['M6x60_axle_bolt']['shape']);assert abs(gap-p['z_rack_deck_clearance'])<1e-6
r=dict(passed=True,z_width=p['z_width'],patterns=records,z_mount_faces=['base only'],z_base_fasteners='4 x M5x30 with washers and nuts',radial_orientation='upright, base underneath',radial_base_fasteners='4 x M5x20 into side-loaded captive nuts',carrier=dict(direction=[1,0,0],z_flange_long_axis=[1,0,0],direct_seat_mm=[168,42,2],plate_thickness_mm=10,edge_ribs_mm=[8,16],output_screw_heads_recessed_mm=.2,physical_stiffness_verified=False),motor_to_clamp_mm=gap,source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ['model.py','leadscrew_actuator.py','check_z_mount.py','rotary_base/core.py','rotary_base/parameters.json',str(pathlib.Path(args.config).resolve().relative_to(root))]})
(out/'z-mount-validation.json').write_text(json.dumps(r,indent=2));(out/'mounting-patterns.json').write_text(json.dumps(records,indent=2));print('Single-face mounting and aligned carrier passed',p['z_width'],flush=True)
