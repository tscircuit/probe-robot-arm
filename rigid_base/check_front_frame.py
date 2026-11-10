"""Side-mounted front frame: seats, bores, continuous actuator envelopes and cutouts."""
import hashlib,json,math
from .model import ROOT,build,parameters,box,cyl,annulus,overlap
from .front_frame import layout,blank

def main():
    parts,info=build();p=parameters();by={a['name']:a for a in parts};lay=dict(z_origin=info['arm_parameters']['z_origin']+info['arm_z_shift_mm']);q=layout(p,lay)
    support=by['Boxed_Z_support']['shape'];deck=by['Rigid_rotating_deck']['shape'];frame=by['Front_Z_frame']['shape'];limit=cyl(p['ring_outer_radius_mm'],600,(0,0,0))
    assert not any(a['name'].startswith(('Printed_front_brace','Printed_rear_brace')) for a in parts)
    assert len(support.Solids())==len(frame.Solids())==1 and support.cut(limit).Volume()<1e-5
    b=support.BoundingBox();assert abs(b.xmax-148)<1e-4 and abs(b.xmin+148)<1e-4 and abs(b.ymax-148)<1e-4 and abs(b.ymin+84)<1e-4
    assert deck.cut(limit).Volume()<1e-5
    assert overlap(support,frame)<1e-6 and overlap(deck,frame)<1e-6
    removed=1-frame.Volume()/blank(p,lay).Volume();assert removed>.5
    seats=[]
    for i,(x,y) in enumerate(p['support_mounts_mm']):
        z=p['deck_top_mm']+(19 if i in [3,6] else p['support_foot_thickness_mm']);seat=annulus(3.5,2.2,.1,z-.1).translate((x,y,0))
        missing=seat.cut(support).Volume();assert missing<1e-6,(i,missing)
        seats.append(dict(index=i,unsupported_seating_volume_mm3=missing))
    holes=[]
    for side,sign in [('left',-1),('right',1)]:
        for i,z in enumerate(q['levels']):
            bore=cyl(2.19,18,(sign*95,-60,z),(sign,0,0))
            assert overlap(bore,support)<1e-6 and overlap(bore,frame)<1e-6
            # The full screw-head annulus is supported on the front frame's side.
            seat=annulus(3.5,2.2,.1,0).rotate((0,0,0),(0,1,0),90).translate((112.1,-60,z))
            if sign<0:seat=seat.mirror('YZ')
            assert seat.cut(frame).Volume()<1e-6
            holes.append(dict(side=side,z_mm=z,diameter_mm=4.4,bolt='M4x25'))
    # Exact solids are outside conservative swept bounding boxes. Linear axes
    # translate by their full travel; screw/clamp rotation uses corner-radius bounds.
    checks=[];new=[a for a in parts if 'front_frame' in a['name'] or a['name'] in ['Boxed_Z_support','Front_Z_frame']]
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
    report=dict(passed=True,support_outer_radius_mm=148,base_flange_thickness_mm=p['support_foot_thickness_mm'],front_frame_count=1,brace_count=0,cutout_volume_reduction_fraction=removed,side_holes=holes,support_bolt_seats=seats,continuous_axis_envelope_checks=checks,physical_stiffness_verified=False,source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['rigid_base/model.py','rigid_base/parameters.json','rigid_base/front_frame.py','rigid_base/check_front_frame.py']})
    (ROOT/'output/rigid-base/frame-validation.json').write_text(json.dumps(report,indent=2));print('Front frame, eight side mounts, bolt seats and continuous axis envelopes passed; cutout fraction',removed,flush=True)
if __name__=='__main__':main()
