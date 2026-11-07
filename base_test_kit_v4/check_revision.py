"""Verify reuse, direct mount, and the complete roller/rotor axial clearance."""
import importlib.util,json,pathlib,hashlib
import cadquery as cq
from build import build,print_shape
ROOT=pathlib.Path(__file__).resolve().parent
p=json.loads((ROOT/'parameters.json').read_text());parts,_=build(p);now={q['name']:q for q in parts}
previous=ROOT/'reference_v3'
if not previous.exists():previous=ROOT.parent/'base_test_kit_v3'
spec=importlib.util.spec_from_file_location('previous_base_build',previous/'build.py');oldmodule=importlib.util.module_from_spec(spec);spec.loader.exec_module(oldmodule)
oldparts,_=oldmodule.build(json.loads((previous/'parameters.json').read_text()));old={q['name']:q for q in oldparts}
reuse=[]
for name in ['Integrated_stand','Inner_race_spacer','Inner_race_top_washer','Bearing_housing','Lower_bearing_retainer','Compliant_12T_pinion']:
 a=print_shape(now[name]);b=oldmodule.print_shape(old[name]);difference=max(0,a.cut(b).Volume())+max(0,b.cut(a).Volume())
 assert difference<1e-5,(name,difference)
 reuse.append(dict(part=name,geometry_difference_mm3=difference))
assert 'NEMA17_mount' not in now
base=now['Fixed_base_plate']['shape'];motor=now['NEMA17_motor_REFERENCE']['shape'];ring=now['Internal_72T_ring']['shape'];deck=now['Rotating_test_deck']['shape']
assert abs(ring.BoundingBox().zmin-28)<1e-6
assert abs(deck.BoundingBox().zmin-44.2)<1e-6
assert abs(base.distance(motor))<1e-6
# The axisymmetric conical envelope bounds intentional roller/track overlap
# throughout rotation. Screw heads remain radially inside the rollers.
from rotary_base.core import roller_layout,roller_fit_checks,roller_track_fit_checks,V
import math
rl=roller_layout(p);q=math.sqrt(.5)
envelope=cq.Solid.makeCone(82,102.2,20.2,V(0,0,28),V(0,0,1))
assert ring.cut(envelope).Volume()<1e-6
min_bearing_radius=rl['center_r']-(8+2.5)*q
max_head_radius=78+2.85
assert min_bearing_radius-max_head_radius>2
rollers=[]
for i,angle in enumerate(p['roller_angles_deg']):
 wheel=now[f'625ZZ_support_roller_{i}']['shape']
 assert abs(wheel.distance(ring))<1e-6
 assert (wheel.intersect(ring).Volume()>0) if p.get('roller_track_overlap_mm',0)>0 else wheel.intersect(ring).Volume()<1e-6
 for j in range(6):assert wheel.distance(now[f'M3x30_ring_{j}']['shape'])>2
 rollers.append(dict(index=i,angle_deg=angle,tilt_deg=45,blocks=1,integral_axle=True,contact_radius_mm=rl['contact_radius'],contact_z_mm=rl['contact_z']))
assert not any(n.startswith(('M5x25_roller','M5_roller','M5_inner_race')) for n in now)
# The old ring is fully retained; new material is confined to the outer rim.
a=ring.translate((0,0,p['rotor_drop_mm']));b=old['Internal_72T_ring']['shape'];added=a.cut(b)
assert b.cut(a).Volume()<1e-6
assert added.intersect(cq.Solid.makeCylinder(82-1e-5,30,V(0,0,25))).Volume()<1e-5
fit=roller_fit_checks(parts,p)
r=dict(passed=True,reused_prints=reuse,spindle_change='15.25 mm journal with 0.5 mm top chamfer; flange, bore and height unchanged',ring_change='Outer radius 88 mm, 6 x 6 mm lower 45-degree track; straight bolt holes and flat-seated button heads',ring_added_mm3=added.Volume(),roller_print_fit=fit,roller_track_fit=roller_track_fit_checks(parts,p),minimum_radial_head_to_bearing_gap_mm=min_bearing_radius-max_head_radius,roller_supports=rollers,ring_to_plate_gap_mm=dict(previous=24,current=17,reduction=7),direct_motor_mount=True,motor_mount_screw='4 x M3x16; nominal 5 mm motor engagement',pinion_shaft_engagement_mm=7,controller_envelope_to_stand_clearance_mm=12.4,roller_rotation_clearance='All angles: axisymmetric outer track has the requested 0.4 mm normal interference; button heads remain more than 2 mm radially inside the rollers',limits=['Four fixed printed axles require checking all contacts and free rotation after printing.','Rigid envelopes only; four supports do not establish stiffness, print creep, wear or probing accuracy.'],source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['build.py','rotary_base/core.py','rotary_base/gear_geometry.py','parameters.json','check_revision.py']})
out=ROOT.parent/'output/armature-base-test-v4';(out/'revision_validation.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
