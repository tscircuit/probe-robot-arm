"""Front-lid fastening, full-radius support and continuous axis-envelope checks."""
import hashlib,json,math
from .model import ROOT,build,parameters,box,cyl,annulus,overlap
from .front_braces import layout

def main():
    parts,info=build();p=parameters();by={a['name']:a for a in parts};q=layout(p,dict(z_origin=info['arm_parameters']['z_origin']+info['arm_z_shift_mm']))
    support=by['Boxed_Z_support']['shape'];deck=by['Rigid_rotating_deck']['shape'];limit=cyl(p['ring_outer_radius_mm'],600,(0,0,0))
    assert len(support.Solids())==1 and support.cut(limit).Volume()<1e-5
    b=support.BoundingBox();assert abs(b.xmax-148)<1e-4 and abs(b.xmin+148)<1e-4 and abs(b.ymax-148)<1e-4 and abs(b.ymin+84)<1e-4
    seats=[]
    for i,(x,y) in enumerate(p['support_mounts_mm']):
        z=p['deck_top_mm']+(19 if i in [3,6] else 10);seat=annulus(3.5,2.2,.1,z-.1).translate((x,y,0))
        missing=seat.cut(support).Volume();assert missing<1e-6,(i,missing)
        seats.append(dict(index=i,unsupported_seating_volume_mm3=missing))
    holes=[]
    for side,x in zip(['left','right'],q['xs']):
        brace=by['Printed_front_brace_'+side]['shape'];assert len(brace.Solids())==1
        assert overlap(brace,support)<1e-6 and overlap(brace,deck)<1e-6
        assert brace.cut(limit).Volume()<1e-5
        for i,z in enumerate(q['levels']):
            screw=by[f'M3x20_front_brace_lid_{side}_{i}']['shape'];bb=screw.BoundingBox()
            assert abs(bb.ymin-23)<1e-5 and 26-bb.ymin<=4+1e-5
            matching=[a for a in parts if a['name'].startswith('Z_M3_lid_mounting_insert') and abs(a['shape'].Center().x-x)<1e-5 and abs(a['shape'].Center().z-z)<1e-5]
            assert len(matching)==1,(side,z)
            assert overlap(screw,matching[0]['shape'])<1e-6
            assert overlap(cyl(1.69,18,(x,25.5,z),(0,1,0)),brace)<1e-6
            holes.append(dict(side=side,z_mm=z,insert=matching[0]['name'],screw_entry_mm=26-bb.ymin))
        for y in q['foot_ys']:
            bore=cyl(2.19,40,(x,y,47.2))
            assert all(overlap(bore,s)<1e-6 for s in [brace,support,deck])
    # Exact solids are outside conservative swept bounding boxes. Linear axes
    # translate by their full travel; screw/clamp rotation uses corner-radius bounds.
    checks=[];new=[a for a in parts if a['name'].startswith(('Printed_front_brace_','M3x20_front_brace_','M4x40_front_brace_','M4_front_brace_')) or a['name']=='Boxed_Z_support']
    for a in parts:
        motion=a.get('motion')
        if motion not in ['z_rack','r_rack','z_drive','r_drive']:continue
        bb=a['shape'].BoundingBox();lo=[bb.xmin,bb.ymin,bb.zmin];hi=[bb.xmax,bb.ymax,bb.zmax]
        if motion=='z_drive':
            r=math.hypot(max(abs(lo[0]),abs(hi[0])),max(abs(lo[1]),abs(hi[1])));lo[:2]=[-r,-r];hi[:2]=[r,r]
        if motion=='r_drive':
            axis=info['arm_layout']['r_drive_z']+info['arm_z_shift_mm'];r=math.hypot(max(abs(lo[1]),abs(hi[1])),max(abs(lo[2]-axis),abs(hi[2]-axis)))
            lo[1:]=[-r,axis-r];hi[1:]=[r,axis+r]
        if motion in ['z_rack','r_rack','r_drive']:lo[2]-=20;hi[2]+=20
        if motion=='r_rack':lo[0]-=60;hi[0]+=60
        env=box(*(hi[k]-lo[k] for k in range(3)),tuple((hi[k]+lo[k])/2 for k in range(3)))
        for other in new:
            ob=other['shape'].BoundingBox()
            if any(hi[k]<=getattr(ob,axis+'min') or lo[k]>=getattr(ob,axis+'max') for k,axis in enumerate('xyz')):continue
            v=overlap(env,other['shape']);assert v<1e-6,(a['name'],other['name'],v)
            checks.append(dict(moving_part=a['name'],structure=other['name'],swept_box_overlap_mm3=v))
    report=dict(passed=True,support_outer_radius_mm=148,outer_support_mount_bolt_radius_mm=max(math.hypot(*xy) for xy in p['support_mounts_mm']),front_brace_count=2,rear_brace_count=2,front_lid_holes=holes,support_bolt_seats=seats,continuous_axis_envelope_checks=checks,physical_stiffness_verified=False,source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['rigid_base/model.py','rigid_base/parameters.json','rigid_base/front_braces.py','rigid_base/check_front_braces.py']})
    (ROOT/'output/rigid-base/front-brace-validation.json').write_text(json.dumps(report,indent=2));print('Full-radius support, six lid inserts, foot holes and continuous swept axis envelopes passed',flush=True)
if __name__=='__main__':main()
