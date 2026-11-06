"""Verify the low cradle, flange bores, insert backing and driver access."""
import hashlib,json,pathlib
from model import build,layout,pose,cyl,box,overlap,V,union
root=pathlib.Path(__file__).resolve().parent
p=json.loads((root/'parameters.json').read_text());lay=layout(p);parts,_=build(p,lay)
dt=lay['deck_top_z'];dz=dt-60
byname={a['name']:a['shape'] for a in parts}
low={a['name']:a['shape'] for a in pose(parts,p,lay,z=-20)}
rack=low['Z_04_Beveled_compliant_rack'];deck=byname['Rotating_deck'];support=byname['Z_support']
zside=25.5-lay['z_actuator']['CASE_YMAX'];front=lay['z_actuator']['CASE_TOP'];top=p['z_origin']+lay['z_actuator']['CASE_RIGHT']
# Check the former gap itself, plus connected sections above the common feet.
bridge=box(5,1.3,top-(dt+10.2),(front+3,zside+.75,(top+dt+10)/2))
assert bridge.cut(support).Volume()<1e-7, 'Corner return is not continuous above the flanges'
sections=[]
for z in [dt+20,(dt+10+top)/2,top-3]:
 section=support.intersect(box(100,40,.5,(-7,-42,z)))
 assert len(section.Solids())==1, ('Disconnected corner section',z)
 sections.append(dict(height_mm=z,connected_solid_count=1))
assert len(support.Solids())==1
face_ymax=25.5-lay['z_actuator']['CASE_YMIN']
expected_face=box(6,face_ymax-(zside-6),top-dt,(front+3,(face_ymax+zside-6)/2,(top+dt)/2))
for x,y in lay['z_actuator']['CASE_CORNERS']:
 expected_face=expected_face.cut(cyl(1.7,8,(front-1,25.5-y,p['z_origin']+x),(1,0,0)))
assert expected_face.cut(support).Volume()<1e-6, 'Top mounting face has a gap or window'
gap=rack.distance(deck);lowest=rack.BoundingBox().zmin
assert abs(lowest-max(lay['deck_top_z'],lay['base_clamp_top_z'])-p['z_rack_deck_clearance'])<1e-6
assert min(rack.distance(byname[n]) for n in ['M6x60_axle_bolt','M6_axle_nut'])>=p['z_rack_deck_clearance']-1e-6
assert abs(lowest-lay['z_rack_lowest'])<1e-6
assert abs(p['z_origin']-lay['minimum_z_origin'])<1e-9
too_low=p.copy();too_low['z_origin']-=.01
try:layout(too_low)
except ValueError:lower_rejected=True
else:raise AssertionError('Height limit did not reject loss of clearance')
rows=[]
for i,(x,y) in enumerate(lay['z_deck_mounts']):
 assert not support.isInside(V(x,y,dt+5),1e-6)
 assert not deck.isInside(V(x,y,dt-4),1e-6)
 assert deck.isInside(V(x,y,dt-8),1e-6)
 tool=cyl(4.5,150,(x,y,dt+14));hits=[]
 for part in parts:
  if part['name']==f'Z_cradle_deck_screw_{i}' or part.get('keepout'):continue
  volume=overlap(tool,part['shape'])
  if volume>.001:hits.append({'part':part['name'],'overlap_mm3':volume})
 assert not hits,(i,hits)
 rows.append(dict(x=x,y=y,bolt='M4x16',flange_thickness_mm=10,insert_thread_engagement_mm=5.7,pilot_backing_mm=3.3,driver_diameter_mm=9,driver_access_length_mm=150))
report=dict(passed=True,z_origin_mm=p['z_origin'],previous_origin_mm=180,lowered_mm=180-p['z_origin'],case_bottom_above_deck_mm=lay['z_case_bottom']-lay['deck_top_z'],full_retraction_rack_to_deck_mm=gap,lower_height_rejected=lower_rejected,mount_faces=['enclosure top: 4 x M3x10','enclosure side: 4 x M3x10'],flange_mounts=rows,deck_insert_reference={'thread':'M4','outer_diameter_mm':6,'length_mm':6,'pilot_diameter_mm':5.6,'recess_mm':.3},limits=['Minimum height clears both the shared deck and the top of the M6 centre clamp by the configured nominal clearance.','Insert knurl/pilot interference is intentional. Physical press fit, pullout strength and cradle stiffness need testing.'])
report['source_sha256']={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ['model.py','parameters.json','rotary_base/core.py','rotary_base/gear_geometry.py','rotary_base/parameters.json']}
report['corner_connection']={'passed':True,'face_thickness_mm':6,'height_mm':top-dt,'former_gap_mm':1.5,'wall_overlap_mm':6,'sections_above_flange':sections,'print_solid_count':1,'top_mount_is_solid_face':True,'face_width_mm':face_ymax-(zside-6),'top_face_hole_count':4}
carrier=byname['Z_to_radial_carrier'];pad=byname['Z_04_Beveled_compliant_rack']
assert len(carrier.Solids())==1
assert not any(a.get('embedded_host')=='Z_04_Beveled_compliant_rack' for a in parts)
assert lay['z_actuator']['output_mount']=='through'
for i,(x,y) in enumerate(lay['z_actuator']['OUTPUT_MOUNTS']):
 y,z=25.5-y,p['z_origin']+x
 assert overlap(pad,cyl(1.69,18,(3,y,z),(1,0,0)))<1e-7
 assert overlap(carrier,cyl(1.69,30,(-3,y,z),(1,0,0)))<1e-7
 for cx in [0,24]:
  ring=cyl(3,6,(cx-3,y,z),(1,0,0)).cut(cyl(1.71,6,(cx-3,y,z),(1,0,0)))
  assert ring.cut(carrier).Volume()<1e-6
 for name in [f'Z_output_mount_screw_{i}',f'Z_output_nut_{i}',f'Z_output_front_washer_{i}',f'Z_output_rear_washer_{i}']:
  assert overlap(byname[name],carrier)<1e-7 and overlap(byname[name],pad)<1e-7
zp=lay['zpad'];zy=25.5-lay['z_actuator']['OUTPUT_PAD_Y']
assert box(18,18,3,(12,zy,zp+10.5)).cut(carrier).Volume()<1e-7
assert abs(low['Z_to_radial_carrier'].BoundingBox().zmin-top-1.5)<1e-6
report['z_output_carrier']={'passed':True,'shape':'one-piece U over pad top','output_insert_count':0,'bolt_count':4,'bolt':'M3x35','nuts':4,'washers':8,'carrier_contact_points':8,'carrier_leg_mm':6,'pad_thickness_mm':18,'through_bore_mm':3.4,'bolt_pattern_mm':[9,9],'thread_beyond_nut_mm':1.6,'minimum_carrier_height_above_cradle_mm':1.5}
(root/'output/z-mount-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
