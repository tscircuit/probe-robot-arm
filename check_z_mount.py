"""Check single-face mounting, shared hole patterns and the direct ribbed carrier."""
import argparse,hashlib,json,pathlib
from model import build,layout,pose,cyl,box,overlap,V,actuator_mount_patterns
root=pathlib.Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--config',default=str(root/'parameters.json'));ap.add_argument('--out',default=str(root/'output'));args=ap.parse_args();out=pathlib.Path(args.out)
p=json.loads(pathlib.Path(args.config).read_text());lay=layout(p);parts,_=build(p,lay);by={a['name']:a for a in parts};support=by['Z_support']['shape'];carrier=by['Z_to_radial_carrier']['shape'];zo=p['z_origin'];dt=lay['deck_top_z'];zp=lay['zpad'];hx=lay['h_origin']
assert len(support.Solids())==len(carrier.Solids())==1
# A single bed plane contains all outer lands, with no rear-facing ribs.
assert abs(support.BoundingBox().ymin+62)<1e-6
bed=[f for f in support.Faces() if f.geomType()=='PLANE' and abs(f.Center().y+62)<1e-6 and f.normalAt().y<-.999]
assert sum(f.Area() for f in bed)>15000
for x,z in [(0,zo+56),(-40,dt+40),(76,dt+40),(0,zo+132)]:
 assert overlap(cyl(3,24,(x,-64,z),(0,1,0)),support)<1e-6,'Relief window obstructed'
assert not any(a['name'].startswith(('Z_top_mount_','Z_enclosure_mount_')) for a in parts)
assert overlap(support,box(500,200,500,(0,58.001,dt+288.001)))<1e-6,'Support extends past the base mounting plane above the corner gusset'
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
motor=by['Z_NEMA17_full-depth_reference']['shape'];gap=motor.distance(by['M6x60_axle_bolt']['shape'])
# Flat seating land and a longer M4x25 bolt pass through the 45-degree reinforcement.
assert support.isInside(V(30,-35,dt+24),1e-6)
seat=cyl(4,1,(42,-28,dt+18)).cut(cyl(2.21,1,(42,-28,dt+18)))
assert seat.cut(support).Volume()<1e-6
bolt=by['Z_cradle_deck_screw_3']['shape'];assert abs(bolt.BoundingBox().zmax-(dt+23))<1e-6
assert overlap(bolt,support)<1e-6
controller=[a for a in parts if a['name'].startswith(('Z_Rear_controller','Z_Controller_','Z_USB_'))]
assert len(controller)==7
assert abs(min(a['shape'].BoundingBox().zmin for a in controller)-lay['z_controller_lowest_z_mm'])<1e-6
assert lay['z_controller_lowest_z_mm']-lay['base_clamp_top_z']>=10-1e-6
for a in controller:
 # The full downward 10 mm clearance prism must remain free of the support and rotary assembly.
 swept=a['shape'].BoundingBox();free=box(swept.xlen,swept.ylen,10,((swept.xmin+swept.xmax)/2,(swept.ymin+swept.ymax)/2,swept.zmin-5))
 if a['keepout']:
  for b in parts:
   if b.get('base_name') or b['name']=='Z_support':assert overlap(free,b['shape'])<1e-6,(a['name'],b['name'],'controller clearance')

r=dict(passed=True,z_width=p['z_width'],patterns=records,z_mount_faces=['base only'],z_base_fasteners='4 x M5x30 with washers and nuts',radial_orientation='upright, base underneath',radial_base_fasteners='4 x M5x20 into side-loaded captive nuts',carrier=dict(direction=[1,0,0],z_flange_long_axis=[1,0,0],direct_seat_mm=[168,42,2],plate_thickness_mm=10,edge_ribs_mm=[8,16],output_screw_heads_recessed_mm=.2,physical_stiffness_verified=False),motor_to_clamp_mm=gap,z_controller_bottom_margin_mm=lay['z_controller_lowest_z_mm']-lay['base_clamp_top_z'],corner_gusset_mm=[26,28,28],corner_bolt='M4x25 through 45 degree gusset, flat recessed head seat',source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ['model.py','leadscrew_actuator.py','check_z_mount.py','rotary_base/core.py','rotary_base/parameters.json',str(pathlib.Path(args.config).resolve().relative_to(root))]})
r['support_printability']=dict(outer_bed_plane_y_mm=-62,outer_planar_area_mm2=sum(f.Area() for f in bed),volume_mm3=support.Volume(),rounded_through_windows=4,window_corner_radius_mm=4,reinforcement='inward only',stl_orientation='outer face down, minimum Z=0')
(out/'z-mount-validation.json').write_text(json.dumps(r,indent=2));(out/'mounting-patterns.json').write_text(json.dumps(records,indent=2));print('Single-face mounting and aligned carrier passed',p['z_width'],flush=True)
