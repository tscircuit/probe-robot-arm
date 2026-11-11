"""Side-mounted front frame: seats, bores, continuous actuator envelopes and cutouts."""
import hashlib,json,math
from .model import ROOT,build,parameters,box,cyl,annulus,overlap,fixed_base_cutouts
from .front_frame import layout,blank
from . import frame_struts

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
    assert abs((30-p['ring_bolt_phase_deg'])*p['ring_teeth']/360-round((30-p['ring_bolt_phase_deg'])*p['ring_teeth']/360))<1e-9
    strut_checks=[];sq=frame_struts.layout(p,lay)
    assert not any(a['name'].startswith('Front_frame_strut_') for a in parts)
    prints=[a for a in parts if a['printed']];custom=[a for a in prints if not (a.get('source_name') or '').startswith(('Z_','R_'))];actuators=[a for a in parts if (a.get('source_name') or '').startswith(('Z_','R_')) and not a['keepout']]
    assert len({a['color'] for a in custom})==len(custom)
    actuator_colors={axis:{a['color'] for a in actuators if a['source_name'].startswith(axis+'_')} for axis in ['Z','R']}
    assert all(len(c)==1 for c in actuator_colors.values()) and actuator_colors['Z']!=actuator_colors['R']
    assert not set.union(*actuator_colors.values())&{a['color'] for a in custom}
    # Grid center is a single solid sheet: no rear wall, tubes or ladder windows.
    grid_bottom=lay['z_origin']-145;top=lay['z_origin']+9
    grid=support.intersect(box(180,100,top-grid_bottom,(0,-70,(top+grid_bottom)/2)))
    gb=grid.BoundingBox();assert abs(gb.ymin+48)<1e-5 and abs(gb.ymax+42)<1e-5
    expected=box(180,6,top-grid_bottom,(0,-45,(top+grid_bottom)/2))
    for z in [lay['z_origin']-x for x in [10.5,41.5,72.5,103.5,134.5]]:
        for x in [-77.5,-46.5,-15.5,15.5,46.5,77.5]:expected=expected.cut(cyl(1.7,8,(x,-49,z),(0,1,0)))
    for z in [lay['z_origin']-134.5,lay['z_origin']-10.5]:expected=expected.cut(cyl(2.8,8,(0,-49,z),(0,1,0)))
    assert expected.cut(grid).Volume()<1e-5 and grid.cut(expected).Volume()<1e-5
    for x in [-118.2,118.2]:
        assert annulus(5,2.8,.1,p['deck_top_mm']+5.9).translate((x,40,0)).cut(support).Volume()<1e-6
        assert annulus(3.5,2.2,.1,p['deck_top_mm']+11.9).translate((x,40,0)).cut(frame).Volume()<1e-6
    for side,q in sq.items():
        st=by['Center_'+side+'_strut']['shape'];assert st.isValid() and len(st.Solids())==1
        assert st.cut(limit).Volume()<1e-5 and overlap(st,support)<1e-6 and overlap(st,frame)<1e-6 and overlap(st,deck)<1e-6
        bb=st.BoundingBox();assert abs((bb.ymax if side=='front' else -bb.ymin)-p['deck_radius_mm'])<1e-4
        base=q['bottom'];y=q['sign']*p['strut_bolt_radius_mm'];head=base+8;mount=support if side=='front' else deck
        assert annulus(5,2.8,.1,base-.1).translate((0,y,0)).cut(mount).Volume()<1e-6
        assert annulus(3.5,2.2,.1,head-.1).translate((0,y,0)).cut(st).Volume()<1e-6
        bore=cyl(2.19,24,(0,y,p['deck_top_mm']-9))
        assert all(overlap(bore,obj)<1e-6 for obj in [mount,st])
        wall=frame if side=='front' else support
        for z in q['levels']:
            bore=frame_struts.orient(cyl(2.19,40,(0,q['face']-8,z),(0,1,0)),q)
            assert overlap(bore,wall)<1e-6 and overlap(bore,st)<1e-6
            seat=annulus(3.5,2.2,.1,0).rotate((0,0,0),(1,0,0),-90).translate((0,q['head']-.1,z))
            assert frame_struts.orient(seat,q).cut(st).Volume()<1e-6
        strut_checks.append(dict(side=side,base_mount_mm=[0,y],base_bolt='M4x20' if side=='front' else 'M4x16',wall_bolts='2 x M4x50',valid_solid=True))
    assert overlap(cyl(2.79,10,(0,-p['strut_bolt_radius_mm'],p['deck_top_mm']-9)),deck)<1e-6
    base=by['Rigid_fixed_base']['shape'];cutouts=fixed_base_cutouts(p,info['center_mm'])
    assert len(cutouts)==5 and all(overlap(c,base)<1e-6 for c in cutouts)
    # Material survives beneath all stand, motor and spindle fastener seats.
    for x,y,r,z in [(x,y,5,14.9) for x in [-131,131] for y in [-131,131]]+[(126+x,y,4,14.9) for x in [-15.5,15.5] for y in [-15.5,15.5]]+[(x,0,4,3.9) for x in [-12,12]]:
        seat=annulus(r,2.7 if r==5 else 1.7,.1,z).translate((x,y,0))
        assert seat.cut(base).Volume()<1e-6,(x,y,'base mount undermined')
    # Four short screws bear on 6 mm rails, without the former 42 mm tubes.
    mount_checks=[]
    for a in parts:
        if not a['name'].startswith('M3x10_Z_base_mount_'):continue
        bb=a['shape'].BoundingBox();x=(bb.xmin+bb.xmax)/2;z=(bb.zmin+bb.zmax)/2
        seat=annulus(2.75,1.7,.1,0).rotate((0,0,0),(1,0,0),-90).translate((x,-48,z))
        assert seat.cut(support).Volume()<1e-6
        assert overlap(cyl(3.2,37,(x,-85,z),(0,1,0)),support)<1e-6
        mount_checks.append(a['name'])
    assert len(mount_checks)==4
    stand=by['Braced_test_stand']['shape']
    for x,y in [(0,90),(0,-90),(90,0),(-90,0)]:assert overlap(cyl(10,10,(x,y,-89)),stand)<1e-6
    for x in [-131,131]:
        for y in [-131,131]:
            assert cyl(14,.1,(x,y,-80.1)).cut(stand).Volume()<1e-6
            for w,d,cx,cy in [(35,12,x+(-17.5 if x>0 else 17.5),y),(12,35,x,y+(-17.5 if y>0 else 17.5))]:
                assert box(w,d,.1,(cx,cy,-80.05)).cut(stand).Volume()<1e-6
    # Exact solids are outside conservative swept bounding boxes. Linear axes
    # translate by their full travel; screw/clamp rotation uses corner-radius bounds.
    checks=[];new=[a for a in parts if 'front_frame' in a['name'] or 'center_strut' in a['name'] or a['name'] in ['Boxed_Z_support','Front_Z_frame','Center_front_strut','Center_rear_strut']]
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
    report=dict(passed=True,support_outer_radius_mm=148,base_flange_thickness_mm=p['support_foot_thickness_mm'],grid_plate_depth_mm=6,grid_plate_solid_except_mounting_holes=True,front_bottom_flange_count=2,front_frame_count=1,strut_count=2,strut_edge_radius_mm=p['deck_radius_mm'],ring_index_change_deg=p['ring_bolt_phase_deg']-30,distinct_custom_print_colors=len(custom),actuator_colors={a:next(iter(c)) for a,c in actuator_colors.items()},strut_mounts=strut_checks,cutout_volume_reduction_fraction=removed,side_holes=holes,support_bolt_seats=seats,continuous_axis_envelope_checks=checks,physical_stiffness_verified=False,source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['rigid_base/model.py','rigid_base/parameters.json','rigid_base/front_frame.py','rigid_base/frame_struts.py','rigid_base/check_front_frame.py']})
    report.update(support_wall_mm=p['support_wall_mm'],support_mount_land_mm=p['support_mount_land_mm'],internal_cylinders_removed=True,short_actuator_mount_screws=mount_checks,fixed_base_cutout_count=len(cutouts),stand_cutout_count=4,stand_leg_and_gusset_seats_supported=True,stand_volume_mm3=stand.Volume(),fixed_base_cutout_corner_radius_mm=p['base_cutout_radius_mm'],fixed_base_volume_mm3=base.Volume(),z_support_volume_mm3=support.Volume())
    (ROOT/'output/rigid-base/frame-validation.json').write_text(json.dumps(report,indent=2));print('Front frame, centered front/rear struts, thin support, five base cutouts, bolt seats and continuous axis envelopes passed; cutout fraction',removed,flush=True)
if __name__=='__main__':main()
