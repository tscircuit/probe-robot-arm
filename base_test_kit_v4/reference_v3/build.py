"""Standalone rotary base test kit, mm. Run with CadQuery 2.7.0.
No full arm or PCB platform is needed. Actual motor/controller are reference envelopes.
"""
from __future__ import annotations
import argparse, csv, hashlib, itertools, json, math, pathlib, shutil
import cadquery as cq
from gear_geometry import box,cyl,annulus,union,holes,overlap,polar,drive_gears,base_drive_center
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

def make_spindle(p,diameter=None):
    d=diameter or p['spindle_diameter'];ab=p['inner_race_abutment_diameter']/2
    s=union([cyl(19,4,(0,0,8)),cyl(ab,6,(0,0,12)),cyl(d/2,33.6,(0,0,18))])
    s=s.cut(cyl(3.3,46,(0,0,7)))
    s=holes(s,[(-12,0),(12,0)],1.7,7,7)
    for x in [-12,12]:s=s.cut(hexagon(5.8,2.5,x,0,9.6))
    return s.clean()

def build(p):
    assert 32<=p['bearing_seat_diameter']<=32.4
    assert 14.6<=p['spindle_diameter']<=15.5
    assert p['spindle_diameter']<p['inner_race_spacer_bore_diameter']<p['inner_race_abutment_diameter']
    assert p['stand_size']>=200 and p['stand_height']>=80
    assert p['base_motor_depth']<=60,'Longer motor needs a new clearance review'
    center=base_drive_center(p)
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
    platebase=plate(190,190,8,0).cut(box(45,45,10,(center,0,4)))
    platebase=holes(platebase,feet+list(itertools.product([-60,60],repeat=2)),2.7,-1,10)
    platebase=holes(platebase,[(-12,0),(12,0)],1.7,-1,10).cut(cyl(3.3,10,(0,0,-1)))
    motor_posts=[(center-20,-27),(center+20,-27),(center-20,27),(center+20,27)]
    platebase=holes(platebase,motor_posts,1.7,-1,10)
    add('Fixed_base_plate',platebase,print_id='01_fixed_base_plate_qty1')
    motor_holes=[(center+x,y) for x in [-15.5,15.5] for y in [-15.5,15.5]]
    mp=holes(box(45,45,5,(center,0,18.5)).cut(cyl(11.4,7,(center,0,15))),motor_holes,1.7,15,7)
    mp=union([mp]+[box(9,9,13,(x,y,14.5)) for x,y in motor_posts]+[box(47,7,5,(center,y,18.5)) for y in [-23,23]])
    mp=holes(mp,motor_posts,1.7,7,15)
    for x,y in motor_posts:mp=mp.cut(hexagon(5.8,2.5,x,y,18.6))
    add('NEMA17_mount',mp,print_id='04_NEMA17_mount_qty1',flip=True)
    add('Fixed_spindle',make_spindle(p),print_id='05_fixed_spindle_15p5_qty1',color='#b0b8c0')
    add('Inner_race_spacer',annulus(p['inner_race_abutment_diameter']/2,p['inner_race_spacer_bore_diameter']/2,16,27),print_id='06_inner_race_spacer_15p8_bore_qty1',color='#b0b8c0')
    add('Inner_race_top_washer',annulus(p['inner_race_abutment_diameter']/2,3.3,2,52),print_id='07_inner_race_top_washer_qty1',color='#b0b8c0')
    add('Bearing_housing',make_housing(p),'rotor',print_id='08_bearing_housing_32p2_qty1')
    lower=holes(annulus(24,p['outer_race_abutment_diameter']/2,4,13.8),rotor_bolts(),1.7,13,6)
    for x,y in rotor_bolts():lower=lower.cut(cyl(3.2,2,(x,y,13.8)))
    add('Lower_bearing_retainer',lower,'rotor',print_id='09_lower_bearing_retainer_qty1',flip=True)
    gear,ring,nominal,ring_bolts=drive_gears(p)
    # Open spokes expose the gear mesh; the centre also retains the upper bearing.
    spokes=[]
    for i in range(6):spokes.append(box(55,12,6,(51,0,55.2)).rotate((0,0,0),(0,0,1),30+60*i))
    deck=union([annulus(82,72,6,52.2),annulus(28,p['outer_race_abutment_diameter']/2,6,52.2)]+spokes+[cyl(6,6,(-55,y,52.2)) for y in [-28.5,38.5]])
    deck=holes(deck,rotor_bolts()+ring_bolts,1.7,51,9)
    deck=holes(deck,[(-55,y) for y in [-28.5,38.5]],2.2,51,9)
    for x,y in rotor_bolts():deck=deck.cut(hexagon(5.8,2.5,x,y,55.8))
    add('Rotating_test_deck',deck,'rotor',print_id='10_rotating_test_deck_qty1')
    ring=union([ring]+[annulus(4.5,1.7,8.2,44).translate((x,y,0)) for x,y in ring_bolts])
    add('Internal_72T_ring',ring,'rotor',color='#d5a345',print_id='11_ring_with_integral_spacers_qty1')
    add('Compliant_12T_pinion',gear,'pinion',color='#e6ad48',print_id='13_open_tip_12T_pinion_qty1',flip=True)
    for z in [18,43]:add(f'6002_bearing_{z}',annulus(16,7.5,9,z),color='#c1c9d0',reference=True)
    rear=16-p['base_motor_depth']
    motor=box(42.3,42.3,p['base_motor_depth'],(center,0,16-p['base_motor_depth']/2)).fuse(cyl(11,2,(center,0,16)))
    motor=holes(motor,motor_holes,1.5,10,8)
    add('NEMA17_motor_REFERENCE',motor,color='#303b42',reference=True)
    shaft=cyl(2.5,22,(center,0,18)).intersect(box(8,5,22,(center,.5,29)))
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
        screw(f'M5x20_upper_stand_{i}',x,y,8,20,2.5,4.25,5,False)
        nut(f'M5_stand_nut_{i}',x,y,-10.2,8,4,2.5)
    for i,(x,y) in enumerate(motor_posts):
        screw(f'M3x25_motor_mount_{i}',x,y,0,25)
        nut(f'M3_mount_nut_{i}',x,y,18.6)
    for i,(x,y) in enumerate(motor_holes):screw(f'M3x10_motor_face_{i}',x,y,21,10,up=False)
    for i,x in enumerate([-12,12]):
        screw(f'M3x16_spindle_flange_{i}',x,0,0,16)
        nut(f'M3_spindle_nut_{i}',x,0,9.6)
    for i,(x,y) in enumerate(rotor_bolts()):
        screw(f'M3x45_housing_{i}',x,y,15.8,45,group='rotor')
        nut(f'M3_housing_nut_{i}',x,y,55.8,group='rotor')
    for i,(x,y) in enumerate(ring_bolts):
        screw(f'M3x30_ring_{i}',x,y,32,30,group='rotor')
        add(f'M3_ring_washer_{i}',annulus(3.5,1.6,.5,58.2).translate((x,y,0)),'rotor',color='#acb8c2',reference=True)
        nut(f'M3_ring_nut_{i}',x,y,58.7,group='rotor')
    screw('M6x70_axle_bolt',0,0,-1.6,70,3,5,4)
    for z in [-1.6,54]:add(f'M6_washer_{z}',annulus(6,3.2,1.6,z),color='#acb8c2',reference=True)
    nut('M6_axle_nut',0,0,55.6,10,5.2,3)
    add('M3x4_pinion_set_screw',cyl(1.5,4,(center,-6,26),(0,1,0)),'pinion',color='#acb8c2',reference=True)
    return parts,nominal

def posed(part,angle,p):
    center=base_drive_center(p)
    s=part['shape']
    if part['group']=='rotor':return s.rotate((0,0,0),(0,0,1),angle)
    if part['group']=='pinion':return s.rotate((center,0,0),(center,0,1),angle*p['ring_teeth']/p['pinion_teeth'])
    return s

def spindle_fit_checks(parts,p):
    byname={a['name']:a['shape'] for a in parts}
    shaft=byname['Fixed_spindle'];radius=p['spindle_diameter']/2
    section=shaft.intersect(cyl(12,1,(0,0,30))).BoundingBox()
    assert abs(section.xlen-p['spindle_diameter'])<1e-6 and abs(section.ylen-p['spindle_diameter'])<1e-6
    rows=[]
    for z in [18,43]:
        bearing=byname[f'6002_bearing_{z}'];actual=shaft.intersect(bearing)
        height=min(z+9,51.6)-max(z,18)
        expected=math.pi*max(0,radius**2-7.5**2)*height
        assert abs(max(0,actual.Volume())-expected)<1e-5
        if radius>7.5:
            shell=annulus(radius,7.5,height,max(z,18))
            assert actual.cut(shell).Volume()<1e-6, 'Unexpected contact outside bearing-fit shell'
        rows.append(dict(part=f'6002_bearing_{z}',nominal_overlap_mm3=expected))
    spacer_gap=shaft.distance(byname['Inner_race_spacer'])
    assert abs(spacer_gap-(p['inner_race_spacer_bore_diameter']-p['spindle_diameter'])/2)<1e-6
    return dict(spacer_bore_mm=p['inner_race_spacer_bore_diameter'],spacer_radial_clearance_mm=spacer_gap,shaft_diameter_mm=p['spindle_diameter'],bearing_bore_mm=15,diametral_interference_mm=max(0,p['spindle_diameter']-15),radial_interference_mm=max(0,radius-7.5),measured_cad_diameter_mm=[section.xlen,section.ylen],bearing_contacts=rows,physical_fit_verified=False,note='15.5 mm is the user-selected print-fit target after the 15.1 mm print was loose. Bearing insertion/removal assumes actual print fit or finishing; nominal radial interference is 0.25 mm.')

def validate(parts,p):
    center=base_drive_center(p)
    failures=[];checks=0;cached=set();min_gap=1e9
    allowed=[{'Compliant_12T_pinion','Internal_72T_ring'}, {'Compliant_12T_pinion','M3x4_pinion_set_screw'},
             {'Controller_component_KEEPOUT','USB_cable_KEEPOUT'}]
    fit=spindle_fit_checks(parts,p)
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
            v=overlap(housing,annulus(16,7.5,9,z))
            insert.append(dict(end=end,bottom_z=z,overlap_mm3=v))
    assert max(q['overlap_mm3'] for q in insert)<.01
    # Verify the nuts and screw heads have full supporting lands, not just clear holes.
    mount=next(q['shape'] for q in parts if q['name']=='NEMA17_mount')
    cap=next(q['shape'] for q in parts if q['name']=='Lower_bearing_retainer')
    lands=[]
    for x,y in [(center-20,-27),(center+20,-27),(center-20,27),(center+20,27)]:
        sample=annulus(2.75,1.7,.05,18.55).translate((x,y,0))
        lands.append(overlap(sample,mount)/sample.Volume())
    for x,y in rotor_bolts():
        sample=annulus(2.75,1.7,.05,15.8).translate((x,y,0))
        lands.append(overlap(sample,cap)/sample.Volume())
    assert min(lands)>.999,lands
    return dict(passed=not failures,spindle_print_fit=fit,part_instances=len(parts),solid_validity=all(q['shape'].isValid() for q in parts),
                collision_pair_checks=checks,rotation_samples_deg=list(range(0,361,15)),collisions=failures,
                fastener_land_coverage_fractions=lands,bearing_insertion=insert,bearing_dimensions_mm=[15,32,9],bearing_center_spacing_mm=25,
                bearing_seat_diameter_mm=p['bearing_seat_diameter'],shaft_diameter_mm=p['spindle_diameter'],
                axial_retainer_clearance_per_end_mm=.2,controller_lowest_z_mm=16-p['base_motor_depth']-6-1.6-12,
                controller_to_stand_top_clearance_mm=(16-p['base_motor_depth']-6-1.6-12)+p['stand_height'],
                intentional_interferences=['Elastic open-tip pinion/ring mesh','M3 tapped pinion pilot','Oversized printed spindle / 6002 bore fit; physical fit or finishing required'],
                limits=['Sampled rigid geometry, not continuous swept-volume proof.', 'Bearing and thread fits require printing and measuring; no load/stiffness/fatigue certification.',
                        'Only base rotation is tested. No complete arm load or stability rating.', 'Motor/controller are packaging references; motor mounting screw engagement must match the selected motor.'])

def print_shape(part):
    s=part['shape']
    if part['flip']:s=s.rotate((0,0,0),(1,0,0),180)
    b=s.BoundingBox()
    return s.translate((-(b.xmin+b.xmax)/2,-(b.ymin+b.ymax)/2,-b.zmin))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default=str(ROOT.parent/'output/armature-base-test-v3'));ap.add_argument('--config',default=str(ROOT/'parameters.json'));ap.add_argument('--check-only',action='store_true');args=ap.parse_args()
    p=json.loads(pathlib.Path(args.config).read_text());out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    parts,nominal=build(p);report=validate(parts,p);report['parameters']=p
    (out/'validation.json').write_text(json.dumps(report,indent=2))
    assert report['passed'],report['collisions']
    if args.check_only:return
    stl=out/'STL';stl.mkdir(exist_ok=True);manifest=[]
    current={q['print_id']+'.stl' for q in parts if q['print_id']}
    for stale in stl.glob('*.stl'):
        if stale.name not in current:stale.unlink()
    for q in parts:
        if not q['print_id']:continue
        s=print_shape(q);b=s.BoundingBox();path=stl/(q['print_id']+'.stl')
        assert s.isValid() and len(s.Solids())==1 and abs(b.zmin)<1e-6
        assert max(b.xlen,b.ylen)<=p['stand_size']+.01
        cq.exporters.export(s,str(path),tolerance=.025,angularTolerance=.06)
        manifest.append(dict(file=str(path.relative_to(out)),quantity=q['qty'],size_mm=[round(b.xlen,2),round(b.ylen,2),round(b.zlen,2)],volume_mm3=round(s.Volume(),2),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    fits=out/'OPTIONAL_fit_tests';fits.mkdir(exist_ok=True)
    for d in [32,32.1,32.2,32.3]:
        coupon=annulus(20,14.6,11,0).cut(cyl(d/2,9.2,(0,0,1.8)))
        cq.exporters.export(coupon,str(fits/f'bearing_seat_coupon_{d:.1f}mm.stl'))
        if abs(d-p['bearing_seat_diameter'])>.001:
            cq.exporters.export(print_shape(dict(shape=make_housing(p,d),flip=False)),str(fits/f'ALTERNATE_housing_seat_{d:.1f}mm_USE_INSTEAD_OF_08.stl'))
    for d in [14.7,14.8,14.9,15.0,15.1,15.5]:
        coupon=box(22,22,2,(0,0,1)).fuse(cyl(d/2,10,(0,0,2)))
        cq.exporters.export(coupon,str(fits/f'spindle_coupon_{d:.1f}mm.stl'))
        if abs(d-p['spindle_diameter'])>.001:
            cq.exporters.export(print_shape(dict(shape=make_spindle(p,d),flip=False)),str(fits/f'ALTERNATE_spindle_{d:.1f}mm_USE_INSTEAD_OF_05.stl'))
    for path in fits.glob('*.stl'):assert path.stat().st_size>100
    (out/'print_manifest.json').write_text(json.dumps(manifest,indent=2))
    assembly=cq.Assembly(name='Armature_base_standalone_test')
    for q in parts:
        if not q['keepout']:assembly.add(q['shape'],name=q['name'],color=cq.Color(q['color']))
    assembly.save(str(out/'ASSEMBLY_reference_DO_NOT_PRINT.step'))
    from explosion import timeline
    stages=timeline(parts)
    (out/'explosion_path.json').write_text(json.dumps(stages,indent=2))
    data=[]
    for q in parts:
        vertices,triangles=q['shape'].tessellate(.15,.15)
        data.append(dict(name=q['name'],color=q['color'],group=q['group'],keepout=q['keepout'],vertices=[v.toTuple() for v in vertices],triangles=triangles))
    (out/'preview_mesh.json').write_text(json.dumps(data,separators=(',',':')))
    print('Exported',len(manifest),'STL designs;',sum(q['quantity'] for q in manifest),'printed pieces',flush=True)

if __name__=='__main__':main()
