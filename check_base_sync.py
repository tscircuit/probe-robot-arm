"""Prevent the main arm and standalone fixture from diverging."""
import hashlib,json,pathlib,math
from model import build,layout,BASE_NAME_MAP
import rotary_base
from rotary_base.core import V,roller_layout
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
def top_z(shape):
 b=Bnd_Box();BRepBndLib.AddOptimal_s(shape.wrapped,b,False,False);return b.Get()[5]
root=pathlib.Path(__file__).resolve().parent
p=json.loads((root/'parameters.json').read_text());lay=layout(p);main,_=build(p,lay)
bench,_=rotary_base.build(rotary_base.parameters());main_by={a['base_name']:a for a in main if a.get('base_name')}
expected={a['name']:a for a in bench if a['name']!='Integrated_stand' and not a['name'].startswith(('M5x25_upper_stand_','M5_stand_nut_'))}
assert main_by.keys()==expected.keys()
def fingerprint(shape):
 vertices,triangles=shape.tessellate(.15,.2)
 pts=[tuple(round(x,6) for x in v.toTuple()) for v in vertices]
 faces=sorted(tuple(sorted(pts[i] for i in t)) for t in triangles)
 return hashlib.sha256(repr(faces).encode()).hexdigest()
rows=[]
for name,ref in expected.items():
 actual=main_by[name]
 assert fingerprint(actual['shape'])==fingerprint(ref['shape']),name
 assert actual['group']=={'fixed':'fixed','rotor':'theta','pinion':'base_drive'}[ref['group']]
 rows.append(dict(part=name,main_name=actual['name'],printed=actual['printed'],matched=True))
assert not {'Base_motor_mount','Stationary_spindle_15mm','Rotating_bearing_housing'} & {a['name'] for a in main}
base=main_by['Fixed_base_plate']['shape']
rl=roller_layout(p);q=math.sqrt(.5)
for angle in p['roller_angles_deg']:
 def point(t,y,v):
  a=math.radians(angle);r=rl['center_r']+q*(t-v);z=rl['center_z']+q*(t+v)
  return V(r*math.cos(a)-y*math.sin(a),r*math.sin(a)+y*math.cos(a),z)
 assert base.isInside(point(-7.5,0,5.5),1e-6)
 assert not base.isInside(point(-7.5,5,5.5),1e-6),'Rectangular cap remains'
 assert base.isInside(point(-7.5,6,-8),1e-6),'Missing widened foot'
 assert base.isInside(point(0,1,1),1e-6),'Missing integral axle finger'
 assert base.isInside(point(-2.25,0,0),1e-6),'Missing connected axle root'
 if p.get('roller_axle_slot_width_mm',0):assert not base.isInside(point(0,0,0),1e-6),'Missing axle relief slots'
 assert not base.isInside(point(7.5,0,0),1e-6),'Second bearing block remains'
assert abs(top_z(main_by['M6x60_axle_bolt']['shape'])-lay['base_clamp_top_z'])<1e-6
assert abs(top_z(main_by['Rotating_test_deck']['shape'])-lay['deck_top_z'])<1e-6
assert lay['z_rack_lowest']>=lay['base_clamp_top_z']+p['z_rack_deck_clearance']-1e-6
r=dict(passed=True,shared_components=rows,shared_source='rotary_base/core.py',shared_parameters='rotary_base/parameters.json',roller_block=dict(count=4,blocks_per_bearing=1,tilt_deg=45,crown_radius_mm=6,base_width_mm=16,integral_axle_diameter_mm=p['roller_axle_diameter_mm'],fasteners=0),motor_face_z_mm=0,ring_bottom_z_mm=28,deck_top_z_mm=lay['deck_top_z'],z_origin_mm=p['z_origin'],z_lowest_mm=lay['z_rack_lowest'],clamp_top_mm=lay['base_clamp_top_z'],fixture_differences=['Bench stand versus main platform and its bolts','Main Z-cradle inserts and actuators attach to the shared deck'],source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ['model.py','parameters.json','rotary_base/core.py','rotary_base/gear_geometry.py','rotary_base/parameters.json','check_base_sync.py']})
(root/'output/base-sync-validation.json').write_text(json.dumps(r,indent=2));print('Shared base matches:',len(rows),'components; single blocks and integral 45-degree axles verified.')
