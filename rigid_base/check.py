"""Gear pitch sweep, physical interfaces and changed-part collision checks."""
import hashlib,itertools,json,math,pathlib
import cadquery as cq
from shapely.geometry import Polygon,Point
from shapely.affinity import rotate,translate
from .model import build,parameters,profiles,ROOT,cyl,annulus,box,overlap,V

def contacts(parts,info):
    allowed={frozenset(q['parts']):q['reason'] for q in info['linear_contacts']}
    def add(a,b,why):allowed[frozenset([a,b])]=why
    for z in [18,43]:add('Fixed_spindle',f'6002_bearing_{z}','Existing 15.25 mm printed spindle press fit; unchanged')
    for angle in [45,135,225,315]:add('Rigid_fixed_base',f'625ZZ_support_roller_{angle}','5.1 mm integral axle / 5 mm bearing press fit')
    add('Solid_12T_module1_pinion','688ZZ_pinion_bearing','8.05 mm printed journal / 8 mm bore press fit')
    add('Solid_12T_module1_pinion','M3x4_pinion_set_screw','M3 receiving pilot')
    add('Solid_12T_module1_pinion','Internal_264T_ring','Separately checked over one complete pitch in exact extruded polygon geometry')
    add('Controller_component_KEEPOUT','USB_cable_KEEPOUT','Overlapping nonphysical controller envelopes')
    for i in range(9):add('Rigid_rotating_deck',f'M4_deck_insert_{i}','Heat-set insert displaces its undersize printed pilot')
    add('Rigid_rotating_deck','M4_rear_strut_deck_insert','Heat-set insert displaces its undersize printed pilot')
    add('Rigid_rotating_deck','M4_cage_rear_deck_insert','Heat-set insert displaces its undersize printed pilot')
    for i in range(2):
        add('Boxed_Z_support',f'M4_front_frame_foot_insert_{i}','Heat-set insert displaces its undersize printed pilot')
        add('Boxed_Z_support',f'M4_center_strut_insert_rear_{i}','Heat-set insert displaces its undersize printed pilot')
    for i in range(3):add('Rigid_fixed_base',f'M3x8_pinion_cap_{i}','M3 tapped receiving pilot')
    return allowed

def main():
    p=parameters();out=ROOT/'output/rigid-base';out.mkdir(exist_ok=True);parts,info=build(p);by={a['name']:a for a in parts}
    pin,inner=profiles(p);pin=Polygon(pin);inside=Polygon(inner);assert pin.is_valid and inside.is_valid
    ring=Point(0,0).buffer(p['ring_outer_radius_mm']-6,quad_segs=512).difference(inside);gear=[]
    for i in range(65):
        angle=360/p['ring_teeth']*i/64
        q=translate(rotate(pin,angle*info['ratio'],origin=(0,0)),xoff=info['center_mm'])
        g=rotate(ring,angle,origin=(0,0));volume=q.intersection(g).area*p['gear_face_mm']
        assert volume<.001,(angle,volume)
        gear.append(dict(ring_angle_deg=angle,overlap_mm3=volume))
    print('65 gear engagement samples passed',flush=True)
    allowed=contacts(parts,info);failures=[];pair_cache={};checks=0
    # Original actuator-to-actuator geometry is translated as a unit. Its prior
    # travel/helix proofs remain applicable; every changed part is checked here.
    for z,r in itertools.product([-20,0,20],[-60,0,60]):
        shapes={}
        for a in parts:
            s=a['shape'];motion=a.get('motion')
            if motion=='z_drive':s=s.rotate((0,0,info['arm_parameters']['z_origin']+2),(0,0,info['arm_parameters']['z_origin']+3),z*360/8)
            if motion=='r_drive':
                lay=info['arm_layout'];s=s.rotate((lay['h_origin'],0,lay['r_drive_z']+2),(lay['h_origin']+1,0,lay['r_drive_z']+2),-r*360/8)
            if motion=='r_rack':s=s.translate((r,0,0))
            if motion in ['z_rack','r_rack','r_drive']:s=s.translate((0,0,z))
            shapes[a['name']]=s
        count=0;bounds={n:s.BoundingBox() for n,s in shapes.items()}
        for a,b in itertools.combinations(parts,2):
            na,nb=a['name'],b['name']
            if frozenset([na,nb]) in allowed:continue
            if a.get('motion') and b.get('motion'):continue
            ba,bb=bounds[na],bounds[nb]
            if any(getattr(ba,k+'max')<=getattr(bb,k+'min')+1e-6 or getattr(bb,k+'max')<=getattr(ba,k+'min')+1e-6 for k in 'xyz'):continue
            key=(na,nb,z if any(q.get('motion') in ['z_rack','r_rack','r_drive','z_drive'] for q in [a,b]) else 0,r if any(q.get('motion') in ['r_rack','r_drive'] for q in [a,b]) else 0)
            if key not in pair_cache:pair_cache[key]=overlap(shapes[na],shapes[nb]);checks+=1
            vol=pair_cache[key]
            if vol>.01:failures.append(dict(z=z,r=r,a=na,b=nb,overlap_mm3=vol));count+=1;print('Collision',na,nb,vol,flush=True)
        print('Travel',z,r,'collisions',count,flush=True)
        if failures:break
    report=dict(passed=not failures,gear_samples=gear,collision_pair_checks=checks,collisions=failures,full_step_deg=1.8/info['ratio'],sixteenth_step_deg=1.8/(16*info['ratio']),nominal_tip_increment_at_250_mm=250*math.radians(1.8/(16*info['ratio'])),physical_vibration_verified=False,physical_accuracy_verified=False,exceptions=[dict(parts=sorted(k),reason=v) for k,v in allowed.items()],source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['rigid_base/model.py','rigid_base/front_frame.py','rigid_base/frame_struts.py','rigid_base/check.py','rigid_base/parameters.json','model.py','rotary_base/core.py','rotary_base/parameters.json','direct_mount.py','leadscrew_actuator.py']})
    (out/'validation.json').write_text(json.dumps(report,indent=2));assert report['passed'],failures
    s=by['Boxed_Z_support' if 'Boxed_Z_support' in by else 'Cylindrical_Z_support']['shape'];assert abs(s.BoundingBox().ymin+(84 if 'Boxed_Z_support' in by else 148))<1e-5 and len(s.Solids())==1
    for x,y in p['support_mounts_mm']:
        assert [-x,y] in p['support_mounts_mm']
        assert overlap(cyl(2.79,14,(x,y,43.2)),by['Rigid_rotating_deck']['shape'])<1e-6
    assert by['Solid_12T_module1_pinion']['shape'].distance(by['Pinion_bearing_cap']['shape'])>.49
    print('Rigid variant checks passed',flush=True)

if __name__=='__main__':main()
