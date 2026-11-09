"""Standalone rotary base test kit, mm. Run with CadQuery 2.7.0.
No full arm or PCB platform is needed. Actual motor/controller are reference envelopes.
"""
from __future__ import annotations
import argparse, csv, hashlib, itertools, json, math, pathlib, shutil
import cadquery as cq
from .gear_geometry import box,cyl,annulus,union,holes,overlap,polar,drive_gears,base_drive_center
V=cq.Vector
ROOT=pathlib.Path(__file__).resolve().parent

def hexagon(af,h,x,y,z):
    pts=[polar(af/math.sqrt(3),math.radians(60*i)) for i in range(6)]
    return cq.Workplane('XY').polyline(pts).close().extrude(h).translate((x,y,z)).val()

def plate(w,d,h,z):
    return cq.Workplane('XY').box(w,d,h).edges('|Z').fillet(8).translate((0,0,z+h/2)).val()

def make_housing(p,diameter=None):
    d=diameter or p['bearing_seat_diameter']
    s=annulus(p['housing_outer_diameter']/2,p['outer_race_abutment_diameter']/2,34.4,17.8)
    s=s.cut(cyl(d/2,9.3,(0,0,17.7)),cyl(d/2,9.3,(0,0,43)))
    return holes(s,rotor_bolts(),1.7,17,36)

def rotor_bolts():return [polar(20.5,math.radians(45+90*i)) for i in range(4)]

def chamfered_shaft(radius,height,z,chamfer):
    assert 0<=chamfer<min(radius,height)
    if not chamfer:return cyl(radius,height,(0,0,z))
    return cyl(radius,height-chamfer,(0,0,z)).fuse(cq.Solid.makeCone(radius,radius-chamfer,chamfer,V(0,0,z+height-chamfer),V(0,0,1))).clean()

def spindle_relief_cutters(p,diameter=None,height=33.6,z=18):
    """Four longitudinal radial slots from the central bore to the journal OD."""
    width=p.get('spindle_slot_width_mm',0)
    if not width:return []
    root=p['spindle_slot_root_mm'];radius=(diameter or p['spindle_diameter'])/2
    assert 0<width<=1 and .25<=root<height-width/2
    bottom=z+root;top=z+height+1
    slot=(cq.Workplane('YZ').moveTo(-width/2,top).lineTo(-width/2,bottom+width/2)
          .threePointArc((0,bottom),(width/2,bottom+width/2)).lineTo(width/2,top)
          .close().extrude(radius+1).val())
    return [slot.rotate((0,0,0),(0,0,1),a) for a in [0,90,180,270]]

def make_spindle(p,diameter=None):
    d=diameter or p['spindle_diameter'];ab=p['inner_race_abutment_diameter']/2
    s=union([cyl(19,4,(0,0,8)),cyl(ab,6,(0,0,12)),chamfered_shaft(d/2,33.6,18,p['spindle_top_chamfer_mm'])])
    s=s.cut(cyl(3.3,46,(0,0,7)))
    s=holes(s,[(-12,0),(12,0)],1.7,7,7)
    for x in [-12,12]:s=s.cut(hexagon(5.8,2.5,x,0,9.6))
    cuts=spindle_relief_cutters(p,d)
    if cuts:s=s.cut(*cuts)
    return s.clean()

def roller_layout(p):
    q=math.sqrt(.5)
    contact_r=p['ring_outer_radius_mm']-p['ring_track_chamfer_mm']/2
    contact_z=32-p['rotor_drop_mm']+p['ring_track_chamfer_mm']/2
    advance=p.get('roller_track_overlap_mm',0)
    assert 0<=advance<=.5
    return dict(contact_radius=contact_r,contact_z=contact_z,center_r=contact_r+(8-advance)*q,center_z=contact_z-(8-advance)*q,axis=(q,0,q),track_overlap_mm=advance)

def roller_transform(shape,p,angle=0):
    lay=roller_layout(p)
    return shape.rotate((0,0,0),(0,1,0),-45).translate((lay['center_r'],0,lay['center_z'])).rotate((0,0,0),(0,0,1),angle)

def roller_block(p,angle=0):
    # One tilted block. Local X is the axle, local Z points toward the track.
    profile=[(-8,-20),(8,-20),(6,0)]
    block=cq.Workplane('YZ').polyline(profile).threePointArc((0,6),(-6,0)).close().extrude(8).translate((-11.5,0,0)).val()
    shoulder=cyl(4,1.1,(-3.6,0,0),(1,0,0))
    axle=chamfered_shaft(p['roller_axle_diameter_mm']/2,5.5,-2.5,p['roller_axle_chamfer_mm']).rotate((0,0,0),(0,1,0),90)
    block=roller_transform(block.fuse(shoulder,axle).clean(),p,angle)
    # The block's broad foot joins the flat plate without protruding beneath it.
    return block.intersect(box(400,400,100,(0,0,p['base_plate_thickness_mm']+50))).clean()

def roller_fit_checks(parts,p):
    by={a['name']:a['shape'] for a in parts};base=by['Fixed_base_plate'];r=p['roller_axle_diameter_mm']/2;rows=[]
    for i,angle in enumerate(p['roller_angles_deg']):
        bearing=by[f'625ZZ_support_roller_{i}'];actual=base.intersect(bearing)
        expected=math.pi*max(0,r*r-2.5**2)*5
        assert abs(max(0,actual.Volume())-expected)<1e-5,(i,actual.Volume(),expected)
        if r>2.5:
            shell=annulus(r,2.5,5,-2.5).rotate((0,0,0),(0,1,0),90)
            assert actual.cut(roller_transform(shell,p,angle)).Volume()<1e-6,'Unexpected block/bearing contact outside printed axle fit'
        rows.append(dict(bearing=f'625ZZ_support_roller_{i}',nominal_overlap_mm3=expected))
    return dict(axle_diameter_mm=2*r,bearing_bore_mm=5,diametral_interference_mm=max(0,2*r-5),top_chamfer_mm=p['roller_axle_chamfer_mm'],contacts=rows,physical_fit_verified=False)

def roller_track_fit_checks(parts,p):
    """Bound the requested interference by the actual ring's tangent planes."""
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    by={a['name']:a['shape'] for a in parts};lay=roller_layout(p);rows=[]
    depth=lay['track_overlap_mm']
    for i,angle in enumerate(p['roller_angles_deg']):
        def bounds(shape):
            local=shape.rotate((0,0,0),(0,0,1),-angle).translate((-lay['center_r'],0,-lay['center_z'])).rotate((0,0,0),(0,1,0),45)
            b=Bnd_Box();BRepBndLib.AddOptimal_s(local.wrapped,b,False,False);return b.Get()
        ring=bounds(by['Internal_72T_ring']);wheel=bounds(by[f'625ZZ_support_roller_{i}'])
        assert abs(ring[2]-(8-depth))<1e-6 and abs(wheel[5]-8)<1e-6
        if depth:
            # A point halfway through the allowed contact cap is inside both solids.
            q=math.sqrt(.5);r=lay['center_r']-(8-depth/2)*q;z=lay['center_z']+(8-depth/2)*q
            x,y=polar(r,math.radians(angle));point=V(x,y,z)
            assert by['Internal_72T_ring'].isInside(point,1e-7) and by[f'625ZZ_support_roller_{i}'].isInside(point,1e-7)
        rows.append(dict(bearing=f'625ZZ_support_roller_{i}',normal_overlap_bound_mm=wheel[5]-ring[2]))
    return dict(requested_normal_advance_mm=depth,radial_inward_mm=depth*math.sqrt(.5),vertical_upward_mm=depth*math.sqrt(.5),contacts=rows,physical_fit_verified=False,note='Intentional nominal overlap at the outer 45-degree track; actual preload, free rotation and print deflection require testing.')

def base_relief_cutters(p):
    # Three large trapezoids and two smaller windows beside the motor.
    # Their boundaries leave a 10 mm rim and 20*sqrt(2) mm diagonal webs.
    top=[(-65,85),(65,85),(15,35),(-15,35)]
    outlines=[]
    for angle in [0,90,180]:
        c=math.cos(math.radians(angle));s=math.sin(math.radians(angle))
        outlines.append([(c*x-s*y,s*x+c*y) for x,y in top])
    for sign in [-1,1]:outlines.append([(49,sign*29),(85,sign*29),(85,sign*65)])
    return [cq.Workplane('XY').polyline(pts).close().extrude(p['base_plate_thickness_mm']+2).edges('|Z').fillet(p['base_cutout_corner_radius_mm']).translate((0,0,-1)).val() for pts in outlines]

def support_footprint(p,z,height,margin=0):
    """Shared flange envelope: two staggered braces and a central front tie."""
    def link(a,b):
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        bar=box(length,18+2*margin,height,((a[0]+b[0])/2,(a[1]+b[1])/2,z+height/2))
        return bar.rotate(((a[0]+b[0])/2,(a[1]+b[1])/2,0),((a[0]+b[0])/2,(a[1]+b[1])/2,1),math.degrees(math.atan2(dy,dx)))
    shapes=[box(114+2*margin,23.6+2*margin,height,(0,-50.2,z+height/2))]
    for sign,ids in [(1,[3,4,5]),(-1,[6,7,8])]:
        shapes.append(box(26+2*margin,28+2*margin,height,(sign*39,-28,z+height/2)))
        points=[(sign*39,-42)]+[p['z_deck_mounts'][i] for i in ids]+[p['z_deck_mounts'][1]]
        shapes += [link(a,b) for a,b in zip(points,points[1:])]
        shapes += [cyl(9+margin,height,(x,y,z)) for x,y in points]
    return union(shapes).intersect(cyl(80+margin,height,(0,0,z)))

def deck_relief_cutters(p):
    # Primary spokes connect the hub to all six ring fasteners. Narrower
    # intermediate ribs split the free areas into smaller rounded windows.
    windows=annulus(82-p['deck_cutout_rim_mm'],p['deck_cutout_hub_radius_mm'],12,47.2)
    for angle in [30,90,150]:
        windows=windows.cut(box(180,p['deck_cutout_spoke_width_mm'],14,(0,0,53.2)).rotate((0,0,0),(0,0,1),angle))
    for angle in ([0,60,120] if p['deck_cutout_secondary_spoke_width_mm'] else []):
        windows=windows.cut(box(180,p['deck_cutout_secondary_spoke_width_mm'],14,(0,0,53.2)).rotate((0,0,0),(0,0,1),angle))
    windows=windows.cut(support_footprint(p,46.2,14,margin=2)).clean()
    rounded=[]
    for s in windows.Solids():
        if s.Volume()/12<80:continue
        bottom=min((f for f in s.Faces() if f.geomType()=='PLANE' and abs(f.normalAt().z)>.99),key=lambda f:f.Center().z)
        radius=p['deck_cutout_corner_radius_mm']
        for inset in bottom.outerWire().offset2D(-radius,'arc'):
            for wire in inset.offset2D(radius,'arc'):
                cutter=cq.Solid.extrudeLinear(wire,[],V(0,0,12))
                assert cutter.isValid() and cutter.cut(s).Volume()<1e-5
                rounded.append(cutter)
    return rounded

def build(p):
    assert 32<=p['bearing_seat_diameter']<=32.4
    assert 14.6<=p['spindle_diameter']<=15.5
    assert p['spindle_diameter']<p['inner_race_spacer_bore_diameter']<p['inner_race_abutment_diameter']
    assert p['stand_size']>=200 and p['stand_height']>=80
    assert p['base_motor_depth']<=60,'Longer motor needs a new clearance review'
    center=base_drive_center(p)
    drop=p['rotor_drop_mm'];plate_t=p['base_plate_thickness_mm']
    assert drop==4 and plate_t==11
    assert p['roller_count']==4 and len(p['roller_angles_deg'])==4 and p['roller_tilt_deg']==45
    assert p['ring_outer_radius_mm']==88 and p['ring_track_chamfer_mm']==6
    assert 4.8<=p['roller_axle_diameter_mm']<=5.3
    parts=[]
    def add(name,shape,group='fixed',color='#71879a',print_id=None,flip=False,qty=1,reference=False,keepout=False):
        assert shape.isValid(),name
        if print_id:assert len(shape.Solids())==1,(name,len(shape.Solids()))
        parts.append(dict(name=name,shape=shape.clean(),group=group,color=color,print_id=print_id,flip=flip,qty=qty,reference=reference,keepout=keepout))
    a=p['stand_leg_pitch']/2; feet=list(itertools.product([-a,a],repeat=2));h=p['stand_height'];t=p['stand_thickness']
    # One printable stand: platform and four upright legs, with only upper nuts.
    platform=plate(p['stand_size'],p['stand_size'],t,-h-t)
    for x,y in itertools.product([-90,90],repeat=2):
        slot=cq.Workplane('XY').center(x,y).slot2D(12,6).extrude(t+2).translate((0,0,-h-t-1)).val()
        platform=platform.cut(slot)
    leg=cyl(12,h,(0,0,-h)).cut(cyl(2.7,20,(0,0,-20)))
    pocket=hexagon(8.4,4.4,0,0,-10.4).fuse(box(13,8.4,4.4,(6.5,0,-8.2)))
    leg=leg.cut(pocket)
    stand=union([platform]+[leg.translate((x,y,0)) for x,y in feet])
    add('Integrated_stand',stand,print_id='02_integrated_stand_qty1',color='#455b6b')
    motor_holes=[(center+x,y) for x in [-15.5,15.5] for y in [-15.5,15.5]]
    # Direct motor mounting: flat 11 mm plate, round pilot opening, four face screws.
    platebase=plate(190,190,plate_t,0).cut(cyl(11.4,plate_t+2,(center,0,-1)))
    platebase=holes(platebase,feet+list(itertools.product([-60,60],repeat=2)),2.7,-1,plate_t+2)
    platebase=holes(platebase,motor_holes,1.7,-1,plate_t+2)
    # Lower the unchanged bearing cartridge into a recessed central well.
    # A 4 mm floor supports the spindle flange; the entire underside lies on Z0.
    platebase=platebase.cut(cyl(25,plate_t,(0,0,8-drop)))
    platebase=holes(platebase,[(-12,0),(12,0)],1.7,-1,plate_t+2).cut(cyl(3.3,plate_t+2,(0,0,-1)))
    if p.get('base_cutouts',False):platebase=platebase.cut(*base_relief_cutters(p)).clean()
    # Four single blocks, each with an integral 45-degree press-fit axle.
    for angle in p['roller_angles_deg']:platebase=platebase.fuse(roller_block(p,angle))
    add('Fixed_base_plate',platebase,print_id='01_cutout_base_four_45deg_axles_qty1')
    add('Fixed_spindle',make_spindle(p),print_id='05_fixed_spindle_15p25_chamfer0p5_qty1',color='#b0b8c0')
    add('Inner_race_spacer',annulus(p['inner_race_abutment_diameter']/2,p['inner_race_spacer_bore_diameter']/2,16,27),print_id='06_inner_race_spacer_15p8_bore_qty1',color='#b0b8c0')
    add('Inner_race_top_washer',annulus(p['inner_race_abutment_diameter']/2,3.3,2,52),print_id='07_inner_race_top_washer_qty1',color='#b0b8c0')
    add('Bearing_housing',make_housing(p),'rotor',print_id='08_bearing_housing_32p2_qty1')
    lower=holes(annulus(24,p['outer_race_abutment_diameter']/2,4,13.8),rotor_bolts(),1.7,13,6)
    for x,y in rotor_bolts():lower=lower.cut(cyl(3.2,2,(x,y,13.8)))
    add('Lower_bearing_retainer',lower,'rotor',print_id='09_lower_bearing_retainer_qty1',flip=True)
    gear,ring,nominal,ring_bolts=drive_gears(p)
    # Shared structural deck: central bearing retainer plus the nine Z-cradle insert seats.
    deck=annulus(82,p['outer_race_abutment_diameter']/2,6,52.2)
    for x,y in p['z_deck_mounts']:
        deck=deck.fuse(cyl(7,10,(x,y,48.2)))
        deck=deck.cut(cyl(2.8,12,(x,y,47.2))).cut(cyl(3.1,.5,(x,y,57.9)))
    deck=holes(deck,rotor_bolts()+ring_bolts,1.7,47,13)
    for x,y in rotor_bolts():deck=deck.cut(hexagon(5.8,2.5,x,y,55.8))
    if p.get('deck_cutouts',False):deck=deck.cut(*deck_relief_cutters(p)).clean()
    add('Rotating_test_deck',deck,'rotor',print_id='10_shared_rotating_deck_qty1',flip=True)
    # Add a continuous outer raceway; preserve the teeth and six bolt positions.
    outer=p['ring_outer_radius_mm'];ch=p['ring_track_chamfer_mm']
    rim=cq.Solid.makeCone(outer-ch,outer,ch,V(0,0,32),V(0,0,1)).fuse(cyl(outer,12-ch,(0,0,32+ch)))
    rim=rim.cut(cyl(81.5,14,(0,0,31)))
    ring=union([ring,rim]+[annulus(4.5,1.7,8.2,44).translate((x,y,0)) for x,y in ring_bolts])
    add('Internal_72T_ring',ring,'rotor',color='#d5a345',print_id='11_ring_176mm_45deg_track_qty1')
    add('Compliant_12T_pinion',gear,'pinion',color='#e6ad48',print_id='13_open_tip_12T_pinion_qty1',flip=True)
    for z in [18,43]:add(f'6002_bearing_{z}',annulus(16,7.5,9,z),color='#c1c9d0',reference=True)
    rear=0-p['base_motor_depth']
    motor=box(42.3,42.3,p['base_motor_depth'],(center,0,-p['base_motor_depth']/2)).fuse(cyl(11,2,(center,0,0)))
    motor=holes(motor,motor_holes,1.5,-6,8)
    add('NEMA17_motor_REFERENCE',motor,color='#303b42',reference=True)
    shaft=cyl(2.5,22,(center,0,2)).intersect(box(8,5,22,(center,.5,13)))
    add('Motor_D_shaft_REFERENCE',shaft,'pinion',color='#bac5cf',reference=True)
    pcb_top=rear-6; pcb_bottom=pcb_top-1.6
    pcb=holes(box(42.3,42.32,1.6,(center,0,pcb_bottom+.8)),motor_holes,1.65,pcb_bottom-1,3.6)
    add('Rear_controller_PCB_REFERENCE',pcb,color='#267c60',reference=True)
    for i,(x,y) in enumerate(motor_holes):add(f'Controller_spacer_{i}',annulus(3,1.65,6,pcb_top).translate((x,y,0)),color='#ddd1aa',reference=True)
    add('Controller_component_KEEPOUT',box(42.3,42.32,10,(center,0,pcb_bottom-5)),color='#70b598',reference=True,keepout=True)
    add('USB_cable_KEEPOUT',box(42.3,30,14,(center,36.16,pcb_bottom-5)),color='#70b598',reference=True,keepout=True)
    # Hardware envelopes include fasteners so length/access mistakes are visible.
    def screw(name,x,y,face,length,r=1.5,hr=2.75,hh=3,up=True,group='fixed'):
        shaft=cyl(r,length,(x,y,face if up else face-length))
        head=cyl(hr,hh,(x,y,face-hh if up else face))
        add(name,shaft.fuse(head),group,color='#acb8c2',reference=True)
    def nut(name,x,y,z,af=5.5,thick=2.4,r=1.5,group='fixed'):
        add(name,hexagon(af,thick,x,y,z).cut(cyl(r,thick+2,(x,y,z-1))),group,color='#acb8c2',reference=True)
    for i,(x,y) in enumerate(feet):
        screw(f'M5x25_upper_stand_{i}',x,y,plate_t,25,2.5,4.25,5,False)
        nut(f'M5_stand_nut_{i}',x,y,-10.2,8,4,2.5)
    for i,(x,y) in enumerate(motor_holes):screw(f'M3x16_motor_face_{i}',x,y,plate_t,16,up=False)
    for i,x in enumerate([-12,12]):
        screw(f'M3x12_spindle_flange_{i}',x,0,0,12)
        nut(f'M3_spindle_nut_{i}',x,0,9.6-drop)
    for i,(x,y) in enumerate(rotor_bolts()):
        screw(f'M3x45_housing_{i}',x,y,15.8,45,group='rotor')
        nut(f'M3_housing_nut_{i}',x,y,55.8,group='rotor')
    for i,(x,y) in enumerate(ring_bolts):
        # Button head: flat bearing face against the ring, rounded exposed edge.
        head=cq.Workplane('XY').circle(2.85).extrude(1.65).edges('<Z').fillet(.65).translate((x,y,30.35)).val()
        add(f'M3x30_ring_{i}',head.fuse(cyl(1.5,30,(x,y,32))),'rotor',reference=True)
        add(f'M3_ring_washer_{i}',annulus(3.5,1.6,.5,58.2).translate((x,y,0)),'rotor',color='#acb8c2',reference=True)
        nut(f'M3_ring_nut_{i}',x,y,58.7,group='rotor')
    screw('M6x60_axle_bolt',0,0,-1.6,60,3,5,4)
    for z in [-1.6,54-drop]:add(f'M6_washer_{z}',annulus(6,3.2,1.6,z),color='#acb8c2',reference=True)
    nut('M6_axle_nut',0,0,55.6-drop,10,5.2,3)
    add('M3x4_pinion_set_screw',cyl(1.5,4,(center,-6,26),(0,1,0)),'pinion',color='#acb8c2',reference=True)
    # Only the bearing is separate: its inner race presses onto the printed axle.
    for i,angle in enumerate(p['roller_angles_deg']):
        bearing=annulus(8,2.5,5,-2.5).rotate((0,0,0),(0,1,0),90)
        add(f'625ZZ_support_roller_{i}',roller_transform(bearing,p,angle),color='#c1c9d0',reference=True)
    lower_names={'Fixed_spindle','Inner_race_spacer','Inner_race_top_washer','Bearing_housing',
                 'Lower_bearing_retainer','Rotating_test_deck','Internal_72T_ring','Compliant_12T_pinion',
                 '6002_bearing_18','6002_bearing_43','M3x4_pinion_set_screw'}
    for q in parts:
        if q['name'] in lower_names or q['group']=='rotor':q['shape']=q['shape'].translate((0,0,-drop))
    return parts,nominal.translate((0,0,-drop))

def posed(part,angle,p):
    center=base_drive_center(p)
    s=part['shape']
    if part['group']=='rotor':return s.rotate((0,0,0),(0,0,1),angle)
    if part['group']=='pinion':return s.rotate((center,0,0),(center,0,1),angle*p['ring_teeth']/p['pinion_teeth'])
    return s

def spindle_fit_checks(parts,p):
    byname={a['name']:a['shape'] for a in parts}
    shaft=byname['Fixed_spindle'];radius=p['spindle_diameter']/2;drop=p['rotor_drop_mm']
    # Measure along uncut diagonals; cardinal-axis slots remove the OD extrema.
    section=shaft.intersect(cyl(12,1,(0,0,30))).rotate((0,0,0),(0,0,1),45).BoundingBox()
    assert abs(section.xlen-p['spindle_diameter'])<1e-6 and abs(section.ylen-p['spindle_diameter'])<1e-6
    fit_shell=None
    if radius>7.5:
        fit_shell=chamfered_shaft(radius,33.6,18,p['spindle_top_chamfer_mm']).cut(cyl(7.5,35,(0,0,17.5)))
        cuts=spindle_relief_cutters(p)
        if cuts:fit_shell=fit_shell.cut(*cuts).clean()
    rows=[]
    for z in [18,43]:
        bearing=byname[f'6002_bearing_{z}'];actual=shaft.intersect(bearing)
        shell=fit_shell.intersect(cyl(radius+1,9,(0,0,z))) if fit_shell else None
        expected=shell.Volume() if shell else 0
        assert abs(max(0,actual.Volume())-expected)<1e-5
        if shell:assert actual.cut(shell.translate((0,0,-drop))).Volume()<1e-6, 'Unexpected contact outside slotted bearing-fit shell'
        rows.append(dict(part=f'6002_bearing_{z}',nominal_overlap_mm3=expected))
    spacer_gap=shaft.distance(byname['Inner_race_spacer'])
    assert abs(spacer_gap-(p['inner_race_spacer_bore_diameter']-p['spindle_diameter'])/2)<1e-6
    return dict(spacer_bore_mm=p['inner_race_spacer_bore_diameter'],spacer_radial_clearance_mm=spacer_gap,shaft_diameter_mm=p['spindle_diameter'],bearing_bore_mm=15,diametral_interference_mm=max(0,p['spindle_diameter']-15),radial_interference_mm=max(0,radius-7.5),measured_cad_diameter_mm=[section.xlen,section.ylen],bearing_contacts=rows,top_chamfer_mm=p['spindle_top_chamfer_mm'],slot_count=4 if p.get('spindle_slot_width_mm',0) else 0,slot_width_mm=p.get('spindle_slot_width_mm',0),physical_fit_verified=False,note='15.25 mm print-fit target with a 0.5 mm top chamfer, reduced from the too-tight 15.5 mm print. Bearing insertion/removal assumes actual print fit or finishing; nominal radial interference is 0.125 mm.')

def validate(parts,p):
    center=base_drive_center(p)
    failures=[];checks=0;cached=set();min_gap=1e9
    allowed=[{'Compliant_12T_pinion','Internal_72T_ring'}, {'Compliant_12T_pinion','M3x4_pinion_set_screw'},
             {'Controller_component_KEEPOUT','USB_cable_KEEPOUT'}]
    fit=spindle_fit_checks(parts,p);roller_fit=roller_fit_checks(parts,p);track_fit=roller_track_fit_checks(parts,p)
    if p.get('roller_track_overlap_mm',0)>0:allowed.extend([{'Internal_72T_ring',f'625ZZ_support_roller_{i}'} for i in range(p['roller_count'])])
    if p['roller_axle_diameter_mm']>5:allowed.extend([{'Fixed_base_plate',f'625ZZ_support_roller_{i}'} for i in range(p['roller_count'])])
    if p['spindle_diameter']>15:allowed.extend([{'Fixed_spindle',f'6002_bearing_{z}'} for z in [18,43]])
    for angle in range(0,361,15):
        shapes={q['name']:posed(q,angle,p) for q in parts}
        for a,b in itertools.combinations(parts,2):
            if {a['name'],b['name']} in allowed:continue
            key=(a['name'],b['name'],0 if a['group']==b['group'] else angle)
            if key in cached:continue
            cached.add(key);checks+=1
            vol=overlap(shapes[a['name']],shapes[b['name']])
            if vol>.01:failures.append(dict(angle=angle,a=a['name'],b=b['name'],overlap_mm3=round(vol,5)))
        print('Rotation',angle,'collisions',len(failures),flush=True)
        if failures:break
    # Insertion path: a single bearing fits into either housing end before the retainers are installed.
    housing=next(q['shape'] for q in parts if q['name']=='Bearing_housing')
    insert=[]
    for end,zs in [('lower',[7,10,14,18]),('upper',[64,56,48,43])]:
        for z in zs:
            v=overlap(housing,annulus(16,7.5,9,z-p['rotor_drop_mm']))
            insert.append(dict(end=end,bottom_z=z,overlap_mm3=v))
    assert max(q['overlap_mm3'] for q in insert)<.01
    # Verify the nuts and screw heads have full supporting lands, not just clear holes.
    mount=next(q['shape'] for q in parts if q['name']=='Fixed_base_plate')
    cap=next(q['shape'] for q in parts if q['name']=='Lower_bearing_retainer')
    lands=[]
    for x in [center-15.5,center+15.5]:
        for y in [-15.5,15.5]:
            sample=annulus(2.75,1.7,.05,p['base_plate_thickness_mm']-.05).translate((x,y,0))
            lands.append(overlap(sample,mount)/sample.Volume())
    for x,y in rotor_bolts():
        sample=annulus(2.75,1.7,.05,15.8-p['rotor_drop_mm']).translate((x,y,0))
        lands.append(overlap(sample,cap)/sample.Volume())
    assert min(lands)>.999,lands
    return dict(passed=not failures,spindle_print_fit=fit,roller_print_fit=roller_fit,roller_track_fit=track_fit,part_instances=len(parts),solid_validity=all(q['shape'].isValid() for q in parts),
                collision_pair_checks=checks,rotation_samples_deg=list(range(0,361,15)),collisions=failures,
                fastener_land_coverage_fractions=lands,bearing_insertion=insert,bearing_dimensions_mm=[15,32,9],bearing_center_spacing_mm=25,
                bearing_seat_diameter_mm=p['bearing_seat_diameter'],shaft_diameter_mm=p['spindle_diameter'],
                axial_retainer_clearance_per_end_mm=.2,controller_lowest_z_mm=-p['base_motor_depth']-6-1.6-12,
                controller_to_stand_top_clearance_mm=(-p['base_motor_depth']-6-1.6-12)+p['stand_height'],
                intentional_interferences=['Elastic open-tip pinion/ring mesh','M3 tapped pinion pilot','Oversized printed spindle / 6002 bore fit; physical fit or finishing required',f"Requested {p.get('roller_track_overlap_mm',0):g} mm normal roller/track interference"],
                limits=['Sampled rigid geometry, not continuous swept-volume proof.', 'Bearing and thread fits require printing and measuring; no load/stiffness/fatigue certification.',
                        'Only base rotation is tested. No complete arm load or stability rating.', 'Motor/controller are packaging references; motor mounting screw engagement must match the selected motor.'])

def print_shape(part):
    s=part['shape']
    if part['flip']:s=s.rotate((0,0,0),(1,0,0),180)
    b=s.BoundingBox()
    return s.translate((-(b.xmin+b.xmax)/2,-(b.ymin+b.ymax)/2,-b.zmin))

def contact_exceptions(parts,p):
    pairs={frozenset(['Compliant_12T_pinion','Internal_72T_ring']):'Designed elastic tooth preload during axial disengagement',
           frozenset(['Compliant_12T_pinion','M3x4_pinion_set_screw']):'Tapped pilot / thread contact; screw is released before pinion lifts',
           frozenset(['Controller_component_KEEPOUT','USB_cable_KEEPOUT']):'Overlapping nonphysical keepout volumes'}
    for a,b,n in [('M5x25_upper_stand_','M5_stand_nut_',4),('M3x12_spindle_flange_','M3_spindle_nut_',2),('M3x45_housing_','M3_housing_nut_',4),('M3x30_ring_','M3_ring_nut_',6)]:
        for i in range(n):pairs[frozenset([a+str(i),b+str(i)])]='Thread interface; fastener assumed unthreaded before withdrawal'
    pairs[frozenset(['M6x60_axle_bolt','M6_axle_nut'])]='Thread interface; fastener assumed unthreaded before withdrawal'
    roller_fit_checks(parts,p)
    roller_track_fit_checks(parts,p)
    if p.get('roller_track_overlap_mm',0)>0:
        for i in range(p['roller_count']):pairs[frozenset(['Internal_72T_ring',f'625ZZ_support_roller_{i}'])]=f"User-requested {p['roller_track_overlap_mm']:g} mm normal interference at the 45-degree track, bounded by verified tangent planes. Physical preload and free rotation untested."
    if p['roller_axle_diameter_mm']>5:
        for i in range(p['roller_count']):pairs[frozenset(['Fixed_base_plate',f'625ZZ_support_roller_{i}'])]='Only verified 5.1 mm printed axle / 5 mm bearing-bore shell; insertion/removal assumes physical press fit or finishing.'
    for i in range(4):pairs[frozenset([f'M3x16_motor_face_{i}','NEMA17_motor_REFERENCE'])]='Tapped motor-face thread; screw unthreaded before axial withdrawal'
    fit=spindle_fit_checks(parts,p)
    if fit['diametral_interference_mm']>0:
        for z in [18,43]:
            pairs[frozenset(['Fixed_spindle',f'6002_bearing_{z}'])]='User-selected 15.25 mm printed shaft in nominal 15 mm bore: 0.125 mm radial interference, with 0.5 mm top chamfer. Motion assumes actual print fit or finishing; rigid bore clearance is not certified.'
    return pairs
