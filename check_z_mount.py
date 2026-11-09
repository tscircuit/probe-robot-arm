"""Check inverted Z, direct threaded radial lid, access and symmetric support."""
import argparse,hashlib,json,pathlib
import direct_mount
import leadscrew_actuator as linear
import cadquery as cq
from model import build,layout,pose,cyl,box,overlap,V,actuator_mount_patterns
root=pathlib.Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--config',default=str(root/'parameters.json'));ap.add_argument('--out',default=str(root/'output'));args=ap.parse_args();out=pathlib.Path(args.out)
p=json.loads(pathlib.Path(args.config).read_text());lay=layout(p);parts,_=build(p,lay);by={a['name']:a for a in parts};support=by['Z_support']['shape'];lid=by['R_Structural_mounting_lid']['shape'];flange=by['Z_Hollow_triangular_carriage']['shape'];zo=p['z_origin'];dt=lay['deck_top_z'];zp=lay['zpad'];hx=lay['h_origin']
assert len(support.Solids())==len(lid.Solids())==len(flange.Solids())==1
assert not any(a['name'].startswith(('Z_to_radial_carrier','R_enclosure_mount_','R_base_captive_nut_','Z_top_mount_')) for a in parts)
assert abs(support.BoundingBox().ymin+62)<1e-6
bed=[f for f in support.Faces() if f.geomType()=='PLANE' and abs(f.Center().y+62)<1e-6 and f.normalAt().y<-.999]
assert sum(f.Area() for f in bed)>15000
for x,z in [(0,zo-56),(0,dt+40),(-76,dt+40),(76,dt+40),(0,zo-119)]:
 assert overlap(cyl(3,24,(x,-64,z),(0,1,0)),support)<1e-6,'Relief window obstructed'
records=[];hole_checks=set()
for pat in actuator_mount_patterns('Z',lay):
 checks=[]
 for x,y in pat['base']:
  c=(-y,-52,zo-x);u=(0,1,0)
  if (x,y) not in hole_checks:
   assert overlap(cyl(1.69,10,c,u),support)<1e-6,(pat,x,y)
   land=cyl(4,10,c,u).cut(cyl(1.71,10,c,u));assert land.cut(support).Volume()<1e-6
   hole_checks.add((x,y))
  checks.append(dict(local_xy_mm=[x,y],bore_mm=3.4))
 records.append(dict(axis='Z',**pat,checked_holes=checks))
# The pinned 31 mm host grid and mating output grids must coincide.
for axis,key in [('Z','z_actuator'),('R','r_actuator')]:
 m=lay[key];xs=m['grid_x'];ys=m['grid_y']
 assert xs==[10.5+31*j for j in range(5)]
 assert all(abs(b-a-31)<1e-9 for a,b in zip(ys,ys[1:]))
 assert len(m['base'])==len(m['lid'])==5*len(ys)
 assert len(m['output_holes'])==2*len(ys)
 assert all(abs(z-42)==15.5 for y,z in m['output_holes'])
for y,z in lay['z_actuator']['output_holes']:assert (-y,z-42) in direct_mount.THREAD_POINTS
assert not any(a['name'].startswith(('Z_base_mount_nut_','Z_base_mount_washer_','R_M3_lid_mounting_insert')) for a in parts)
# Head-access modifications must preserve every bearing's running skin
# throughout the full native stroke, including the 4x middle grid columns.
native=linear.build(40,p['z_width'],p['z_motor'],p['z_motor_depth'])[0]
original=next(a['shape'] for a in native if a['name']=='Hollow triangular carriage')
modified=next(a['shape'] for a in direct_mount.parts('Z',lay['z_actuator'],hx) if a['name']=='Hollow triangular carriage')
bearing_skins=[]
for a in native:
 if not a.get('bearing'):continue
 n=V(*a['explodeNormal']);c=V(*a['center'])-n*8-V(20,0,0)
 skin=cq.Workplane(cq.Plane(origin=c,xDir=(1,0,0),normal=n)).box(40.2,5,.2).val()
 # Intersect the small local skin first: subtracting the two entire, nearly
 # coincident threaded carriages can produce inverted OCC shells.
 before=skin.intersect(original);after=skin.intersect(modified)
 assert before.isValid() and after.isValid() and before.Volume()>0
 lost=before.cut(after).Volume()
 assert abs(lost)<1e-5 and abs(before.Volume()-after.Volume())<1e-5,(a['name'],'running face removed',lost)
 bearing_skins.append(dict(name=a['name'],original_running_skin_mm3=before.Volume(),retained_running_skin_mm3=after.Volume(),lost_running_skin_mm3=max(0,lost)))
# Independent thread-depth / minor-bore checks at all 12 mounting sites.
for x,y in direct_mount.THREAD_POINTS:
 assert overlap(cyl(1.29,7.6,(x,y,zp-7.5)),lid)<1e-6,(x,y,'minor bore')
 ring=cyl(2,7,(x,y,zp-7.4)).cut(cyl(1.61,7,(x,y,zp-7.4)))
 assert ring.cut(lid).Volume()<1e-6,(x,y,'thread wall')
 assert lid.isInside(V(x,y,zp-7.9),1e-6),'blind thread floor'
records.append(dict(axis='R',face='lid',grid_pitch_mm=31,pattern='NEMA17 31 mm square and Z widths 1/2/4',thread='M3 x 0.5 modeled helix, chase after printing',points_relative_to_Z_axis_mm=direct_mount.THREAD_POINTS,thread_depth_mm=7.7,center_recess_mm=[22.2,2]))
assert abs(lid.BoundingBox().zmax-zp)<1e-6
assert abs(flange.BoundingBox().zmin-zp)<1e-6
assert flange.distance(lid)<1e-6 and overlap(flange,lid)<1e-6
for a in parts:
 if a['name'].startswith('Z_base_mount_'):
  assert overlap(a['shape'],support)<1e-6,a['name']
  assert overlap(a['shape'],by['Z_Adjustable_six-bearing_base']['shape'])<1e-6,a['name']
 if a['name'].startswith('Z_output_mount_screw_'):
  assert abs(a['shape'].BoundingBox().zmax-(zp+7.8))<1e-6
  assert overlap(a['shape'],flange)<1e-6
  # 18 mm axial removal into the side-open service wells, continuous cylinder envelope.
  bb=a['shape'].BoundingBox();x=(bb.xmin+bb.xmax)/2;y=(bb.ymin+bb.ymax)/2
  assert overlap(cyl(2.75,21,(x,y,zp+4.8)),flange)<1e-6
assert len([a for a in parts if a['name'].startswith('Z_base_mount_screw_')])==4
assert not p['radial_inverted'] and lay['z_inverted']
assert abs(lay['r_drive_z']-lay['horizontal_z']-42)<1e-6
assert abs(lay['horizontal_z']-20-(dt+38)-6)<1e-6
for i,sign in [(3,1),(6,-1)]:
 bolt=by[f'Z_cradle_deck_screw_{i}']['shape'];assert abs(bolt.BoundingBox().zmax-(dt+23))<1e-6
 assert overlap(bolt,support)<1e-6
 assert support.isInside(V(sign*30,-35,dt+24),1e-6)
 for x,y in [(sign*42,-28),(sign*58,8),(sign*42,44)]:
  assert [x,y] in lay['z_deck_mounts']
  assert overlap(cyl(2.19,40,(x,y,dt)),support)<1e-6
assert len([a for a in parts if a['name'].startswith('Z_cradle_deck_screw_')])==9
for x,y in lay['z_deck_mounts']:
 assert [-x,y] in lay['z_deck_mounts']
 assert overlap(cyl(2.19,40,(x,y,dt)),support)<1e-6
assert [0,64] in lay['z_deck_mounts']
right=support.intersect(box(220,180,45,(0,0,dt+22.5)));left=right.mirror('YZ')
assert right.cut(left).Volume()+left.cut(right).Volume()<1e-6
controller=[a for a in parts if a['name'].startswith(('Z_Rear_controller','Z_Controller_','Z_USB_'))]
assert len(controller)==7
assert abs(min(a['shape'].BoundingBox().zmin for a in controller)-lay['z_controller_lowest_z_mm'])<1e-6
for a in controller:
 if a['keepout']:
  b=a['shape'].BoundingBox();free=box(b.xlen,b.ylen,10,((b.xmin+b.xmax)/2,(b.ymin+b.ymax)/2,b.zmax+5))
  for q in parts:
   if q.get('base_name') or q['name']=='Z_support':assert overlap(free,q['shape'])<1e-6
bounds=support.BoundingBox()
r=dict(passed=True,bearing_running_skin_checks=bearing_skins,output_grid_holes=len(lay['z_actuator']['output_holes']),used_output_hole_indices=direct_mount.output_indices(lay['z_actuator']),z_width=p['z_width'],patterns=records,z_mount_faces=['base only'],z_base_fasteners='4 x M3x20 into 4 mm M3 inserts',radial_orientation='upright; lid attached directly to downward Z flange',direct_mount_fasteners=f"{len(direct_mount.output_indices(lay['z_actuator']))} x M3x12",pcb_top_mm=lay['board_top'],carrier_removed=True,controller_clearance_mm=10,corner_gusset_mm=[26,28,28],physical_stiffness_verified=False,symmetric_braces=dict(count=2,holes_per_brace=3),support_printability=dict(outer_bed_plane_y_mm=-62,outer_planar_area_mm2=sum(f.Area() for f in bed),volume_mm3=support.Volume(),footprint_mm=[bounds.xlen,bounds.zlen],height_mm=bounds.ylen,rounded_through_windows=7,stl_orientation='outer face down, minimum Z=0'),source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ['model.py','direct_mount.py','leadscrew_actuator.py','check_z_mount.py','rotary_base/core.py','rotary_base/parameters.json',str(pathlib.Path(args.config).resolve().relative_to(root))]})
(out/'z-mount-validation.json').write_text(json.dumps(r,indent=2));(out/'mounting-patterns.json').write_text(json.dumps(records,indent=2));print('Inverted Z and direct threaded lid passed',p['z_width'],flush=True)
