"""Independent rigid, fine-pitch internal-gear variant. Dimensions in millimetres.

The production arm and original standalone fixture are deliberately not modified.
Run from the repository root: python -m rigid_base.model
"""
import argparse, colorsys, hashlib, itertools, json, math, pathlib
import cadquery as cq
import model as arm
import rotary_base
from . import front_frame,frame_struts
from rotary_base import core
from rotary_base.gear_geometry import box,cyl,annulus,union,holes,polar,inv,overlap
V=cq.Vector
ROOT=pathlib.Path(__file__).resolve().parent.parent

def parameters():return json.loads((ROOT/'rigid_base/parameters.json').read_text())
def linked_foot(p,z,height,margin=0):
    shapes=[box(180+2*margin,20+2*margin,height,(0,-74,z+height/2))]
    for sign,ids in [(1,[3,4,5]),(-1,[6,7,8])]:
        pts=[(sign*72,-70)]+[p['support_mounts_mm'][i] for i in ids]+[p['support_mounts_mm'][1]]
        for a,b in zip(pts,pts[1:]):
            center=((a[0]+b[0])/2,(a[1]+b[1])/2,z+height/2)
            bar=box(math.dist(a,b),20+2*margin,height,center)
            shapes.append(bar.rotate((center[0],center[1],0),(center[0],center[1],1),math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))))
        shapes += [cyl(10+margin,height,(x,y,z)) for x,y in pts]
    shapes += [box(160+2*margin,28+2*margin,height,(0,-50,z+height/2))]
    # Continuous perimeter ties the widened pads together at the ring's full radius.
    shapes += [annulus(p['deck_radius_mm']+margin,p['deck_radius_mm']-16-margin,height,z)]
    return union(shapes).intersect(cyl(p['deck_radius_mm']+margin,height,(0,0,z))).intersect(box(400,400,height,(0,116+margin,z+height/2)))

def profiles(p):
    m=p['module_mm'];n=p['pinion_teeth'];nr=p['ring_teeth'];pa=math.radians(p['pressure_angle_deg'])
    assert n>=math.ceil(2/math.sin(pa)**2),'Unshifted full-depth pinion undercut limit'
    rp=m*n/2;rb=rp*math.cos(pa);rr=rp-1.25*m;ra=rp+m
    # External tooth is thick at its root and thin at its tip.
    def eh(r):return math.pi/(2*n)-p['pitch_backlash_mm']/(2*rp)+inv(rp,rb)-inv(max(r,rb),rb)
    pin=[]
    for i in range(n):
        t=2*math.pi*i/n;rs=[rr]+[rb+(ra-rb)*k/16 for k in range(17)]
        pin += [polar(r,t-eh(r)) for r in rs]+[polar(r,t+eh(r)) for r in reversed(rs)]
    R=m*nr/2;RB=R*math.cos(pa);tip=R-m;root=R+1.25*m;ring=[]
    def ih(r):return math.pi/(2*nr)+inv(r,RB)-inv(R,RB)
    for i in range(nr):
        t=2*math.pi*(i+.5)/nr;rs=[root+(tip-root)*k/12 for k in range(13)]
        ring += [polar(r,t-ih(r)) for r in rs]+[polar(r,t+ih(r)) for r in reversed(rs)]
    return pin,ring

def gears(p):
    pin,inside=profiles(p);center=p['module_mm']*(p['ring_teeth']-p['pinion_teeth'])/2;z=p['gear_bottom_mm'];h=p['gear_face_mm']
    tooth=cq.Workplane('XY').polyline(pin).close().extrude(h).val().translate((center,0,z))
    # Solid teeth; a journal close to the tooth load is supported by a 688 bearing.
    hub=cyl(6,4.5,(center,0,12)).fuse(cyl(4.025,7.5,(center,0,16.5)))
    bore=cyl(2.65,26,(center,0,11)).intersect(box(8,5.3,26,(center,.5,24)))
    pinion=tooth.fuse(hub).cut(bore,cyl(1.25,8,(center,-7,15),(0,1,0))).clean()
    cavity=cq.Workplane('XY').polyline(inside).close().extrude(h+2).val().translate((0,0,z-1))
    ring=cyl(p['ring_outer_radius_mm']-6,h,(0,0,z)).cut(cavity)
    ro=p['ring_outer_radius_mm'];body=ro-6
    rim=cq.Solid.makeCone(body,ro,6,V(0,0,28),V(0,0,1)).fuse(cyl(ro,6,(0,0,34))).cut(cyl(body-.5,14,(0,0,27)))
    bolts=[polar(p['ring_bolt_radius_mm'],math.radians(p['ring_bolt_phase_deg']+60*i)) for i in range(6)]
    ring=union([ring,rim]+[annulus(4.5,1.7,12.2,36).translate((x,y,0)) for x,y in bolts])
    ring=holes(ring,bolts,1.7,23,27)
    return pinion,ring,bolts

def support(p,lay):
    dt=p['deck_top_mm'];foot=p['support_foot_thickness_mm'];zo=lay['z_origin'];top=zo+9;height=top-dt-foot;mid=(top+dt+foot)/2
    solids=[linked_foot(p,dt,foot),box(206,6,height,(0,-81,mid))]
    solids += [box(6,42,height,(x,-63,mid)) for x in [-99,99]]
    solids += [box(206,10,12,(0,-47,zo-x)) for x in lay['z_actuator']['grid_x']]
    solids += [box(206,42,8,(0,-63,z)) for z in [dt+foot+4,top-4]]
    solids += [box(12,42,zo-129-dt-foot,(x,-63,(zo-129+dt+foot)/2)) for x in [-76,76]]
    for x in lay['z_actuator']['grid_x']:
        for y in lay['z_actuator']['grid_y']:solids.append(cyl(5,42,(-y,-84,zo-x),(0,1,0)))
    for x in [-80,80]:
        solids.append(cq.Workplane('YZ',origin=(x-10,0,0)).polyline([(-42,dt+foot),(-14,dt+foot),(-42,dt+foot+28)]).close().extrude(20).val())
    s=union(solids)
    rows=sorted(zo-x for x in lay['z_actuator']['grid_x'])
    windows=[(-64,-46,dt+32,zo-161),(-30,30,dt+32,zo-161),(46,64,dt+32,zo-161)]
    windows += [(-89,89,lo+6,hi-6) for lo,hi in zip(rows,rows[1:])]
    for x0,x1,z0,z1 in windows:
        s=s.cut(cq.Workplane('XY').box(x1-x0,46,z1-z0).edges('|Y').fillet(4).translate(((x0+x1)/2,-63,(z0+z1)/2)).val())
    for x in lay['z_actuator']['grid_x']:
        for y in lay['z_actuator']['grid_y']:
            s=s.cut(cyl(1.7,44,(-y,-85,zo-x),(0,1,0)),cyl(3.3,7,(-y,-85,zo-x),(0,1,0)))
    for i,(x,y) in enumerate(p['support_mounts_mm']):
        s=s.cut(cyl(2.2,42,(x,y,dt-1)),cyl(4.1,60,(x,y,dt+(19 if i in [3,6] else foot))))
    # Tool and nut clearance around the ring bolts, outside the support pads.
    for i in range(6):
        x,y=polar(p['ring_bolt_radius_mm'],math.radians(p['ring_bolt_phase_deg']+60*i))
        s=s.cut(cyl(5.5,50,(x,y,dt-1)))
    return frame_struts.support_finish(front_frame.support_finish(s,p,lay),p,lay)

def build(p=None):
    p=p or parameters()
    key=hashlib.sha256(json.dumps(p,sort_keys=True).encode()+b''.join((ROOT/n).read_bytes() for n in ['rigid_base/model.py','rigid_base/front_frame.py','rigid_base/frame_struts.py','model.py','direct_mount.py','leadscrew_actuator.py','rotary_base/core.py','rotary_base/gear_geometry.py','rotary_base/parameters.json','parameters.json','upstream/leadscrew-grid31/experiments/t8-leadscrew/model.py'])).hexdigest()[:20]
    cache=ROOT/'cache'/('rigid-'+key)
    if (cache/'complete').exists():
        parts=json.loads((cache/'parts.json').read_text());info=json.loads((cache/'info.json').read_text())
        for i,a in enumerate(parts):a['shape']=cq.Shape.importBrep(str(cache/f'{i}.brep'))
        return parts,info
    ap=json.loads((ROOT/'parameters.json').read_text());oldlay=arm.layout(ap);old,_=arm.build(ap,oldlay)
    ro=p['ring_outer_radius_mm'];body=ro-6;tip=p['module_mm']*(p['ring_teeth']/2-1)
    center=p['module_mm']*(p['ring_teeth']-p['pinion_teeth'])/2;dt=p['deck_top_mm'];dz=dt-oldlay['deck_top_z'];lay=dict(oldlay,z_origin=ap['z_origin']+dz)
    parts=[]
    def add(name,s,group='fixed',printed=False,color='#71879a',reference=False,keepout=False,flip=False,context=False,source_name=None,free=None):
        assert s.isValid() and (not printed or len(s.Solids())==1),(name,'invalid or disconnected')
        parts.append(dict(name=name,shape=s,group=group,printed=printed,color=color,reference=reference,keepout=keepout,flip=flip,context=context,source_name=source_name,**({'freeShape':free} if free is not None else {})))
    skip={'Fixed_base_plate','Rotating_test_deck','Internal_72T_ring','Compliant_12T_pinion','M3x4_pinion_set_screw'}
    for a in old:
        if a.get('base_name'):
            name=a['base_name']
            if name in skip or name.startswith(('625ZZ_support','M3x16_motor_face','M3x30_ring','M3_ring_')):continue
            s=a['shape'];g=a['base_group']
            if name.startswith(('NEMA17_motor','Motor_D_shaft','Rear_controller','Controller_','USB_')):s=s.translate((center-60,0,0))
            if name.startswith('M3_housing_nut_'):s=s.translate((0,0,dz))
            add(name,s,g,a['printed'],a['color'],a['reference'],a['keepout'],a.get('print_flip',False),source_name=a['name'])
        elif not a['name'].startswith(('M5_platform','M4_deck_insert','Z_cradle_deck','Z_base_mount_')) and a['name']!='Z_support':
            add(a['name'],a['shape'].translate((0,0,dz)),'rotor',a['printed'],a['color'],a['reference'],a['keepout'],context=True,source_name=a['name'])
            parts[-1]['motion']=a['group']
    # Stiffer 15 mm fixed plate, widened bearing circle and corner-braced test stand.
    feet=list(itertools.product([-p['stand_leg_pitch_mm']/2,p['stand_leg_pitch_mm']/2],repeat=2));motor_holes=[(center+x,y) for x in [-15.5,15.5] for y in [-15.5,15.5]]
    plate=core.plate(p['base_size_mm'],p['base_size_mm'],15,0).cut(cyl(11.4,17,(center,0,-1)),cyl(25,13,(0,0,4)),cyl(3.3,17,(0,0,-1)))
    plate=holes(plate,feet,2.7,-1,17);plate=holes(plate,motor_holes+[(-12,0),(12,0)],1.7,-1,17)
    rp=rotary_base.parameters()|dict(ring_outer_radius_mm=ro,base_plate_thickness_mm=15,roller_track_overlap_mm=0)
    for angle in rp['roller_angles_deg']:
        b=core.roller_block(rp,angle)
        # Broaden the root behind the existing single integral axle.
        root=cq.Workplane('YZ').polyline([(-12,-20),(12,-20),(8,0)]).threePointArc((0,8),(-8,0)).close().extrude(12).translate((-15.5,0,0)).val()
        root=core.roller_transform(root,rp,angle).intersect(box(400,400,100,(0,0,65)))
        plate=plate.fuse(b,root)
        wheel=annulus(8,2.5,5,-2.5).rotate((0,0,0),(0,1,0),90)
        add(f'625ZZ_support_roller_{angle}',core.roller_transform(wheel,rp,angle),reference=True,color='#c1c9d0')
    # A local bearing tower supports the pinion hub just below its loaded teeth.
    tower=cyl(14,7,(center,0,15)).cut(cyl(6.5,9,(center,0,14)),cyl(8.1,5.2,(center,0,17)))
    capholes=[(center+11*math.cos(math.radians(a)),11*math.sin(math.radians(a))) for a in [135,180,225]]
    tower=holes(tower,capholes,1.3,14,10)
    # Continuous rotational clearance under the ring body, including enlarged block roots.
    swept=cyl(body+.3,4.3,(0,0,23.7)).fuse(cq.Solid.makeCone(body+.3,ro+.3,6,V(0,0,28),V(0,0,1)),cyl(ro+.3,6.3,(0,0,34))).cut(cyl(tip-.3,18,(0,0,23)))
    head_sweep=annulus(p['ring_bolt_radius_mm']+3.2,p['ring_bolt_radius_mm']-3.2,2.3,22.05)
    # Radial tool bore permits tightening/removing the pinion set screw.
    access=cyl(1.8,11,(center,-16,15),(0,1,0))
    plate=plate.fuse(tower).cut(swept,head_sweep,access).clean();add('Rigid_fixed_base',plate,printed=True)
    cap=holes(annulus(14,6.5,1.5,22).translate((center,0,0)),capholes,1.7,21,4)
    # Trim the outer lip clear of every ring-screw head around the full orbit.
    cap=cap.intersect(cyl(p['ring_bolt_radius_mm']-3.2,4,(0,0,21))).clean()
    add('Pinion_bearing_cap',cap,printed=True)
    add('688ZZ_pinion_bearing',annulus(8,4,5,17).translate((center,0,0)),reference=True,color='#c1c9d0')
    for i,(x,y) in enumerate(capholes):add(f'M3x8_pinion_cap_{i}',cyl(1.45,8,(x,y,15.5)).fuse(cyl(2.75,3,(x,y,23.5))),reference=True)
    for i,(x,y) in enumerate(motor_holes):add(f'M3x20_motor_face_{i}',cyl(1.45,20,(x,y,-5)).fuse(cyl(2.75,3,(x,y,15))),reference=True)
    stand=core.plate(p['base_size_mm'],p['base_size_mm'],8,-88)
    for x,y in feet:
        leg=cyl(14,80,(x,y,-80)).cut(cyl(2.7,21,(x,y,-20)),core.hexagon(8.4,4.4,x,y,-10.4).fuse(box(16,8.4,4.4,(x+8,y,-8.2))))
        stand=stand.fuse(leg)
        sx=1 if x>0 else -1;sy=1 if y>0 else -1
        for a,b in [((x,y),(x-sx*35,y)),((x,y),(x,y-sy*35))]:
            dx,dy=b[0]-a[0],b[1]-a[1];angle=math.degrees(math.atan2(dy,dx))
            brace=cq.Workplane('XZ').polyline([(0,-80),(35,-80),(0,-35)]).close().extrude(6,both=True).val().rotate((0,0,0),(0,0,1),angle).translate((a[0],a[1],0))
            stand=stand.fuse(brace)
    add('Braced_test_stand',stand.clean(),printed=True,color='#455b6b')
    for i,(x,y) in enumerate(feet):
        add(f'M5x30_stand_{i}',cyl(2.45,30,(x,y,-15)).fuse(cyl(4.25,5,(x,y,15))),reference=True)
        add(f'M5_stand_nut_{i}',core.hexagon(8,4,x,y,-10.2).cut(cyl(2.5,5,(x,y,-10.5))),reference=True)
    pinion,ring,bolts=gears(p);add('Solid_12T_module1_pinion',pinion,'pinion',True,'#e6ad48',flip=True)
    add(f"Internal_{p['ring_teeth']}T_ring",ring,'rotor',True,'#d5a345')
    add('M3x4_pinion_set_screw',cyl(1.5,4,(center,-6,15),(0,1,0)),'pinion',reference=True)
    deck=annulus(p['deck_radius_mm'],14.6,8,48.2)
    for x,y in p['support_mounts_mm']:deck=deck.fuse(cyl(7,12,(x,y,44.2))).cut(cyl(2.8,14,(x,y,43.2)))
    deck=holes(deck,core.rotor_bolts()+bolts,1.7,43,15)
    for x,y in core.rotor_bolts():deck=deck.cut(core.hexagon(5.8,2.5,x,y,53.8))
    # Small relief windows retain the complete support footprint and wide spokes.
    cutters=annulus(p['deck_radius_mm']-14,30,10,47.2).cut(linked_foot(p,47.2,10,2))
    for angle in [p['ring_bolt_phase_deg']+a for a in [0,60,120]]+[90]:cutters=cutters.cut(box(2*p['deck_radius_mm']+20,20,12,(0,0,52.2)).rotate((0,0,0),(0,0,1),angle))
    for s in cutters.Solids():
        if s.Volume()/10<=100:continue
        face=min((f for f in s.Faces() if f.geomType()=='PLANE' and abs(f.normalAt().z)>.99),key=lambda f:f.Center().z)
        for wire in face.outerWire().offset2D(-2,'arc'):
            for rounded in wire.offset2D(2,'arc'):deck=deck.cut(cq.Solid.extrudeLinear(rounded,[],V(0,0,10)))
    deck=frame_struts.deck_finish(deck,p)
    add('Rigid_rotating_deck',deck,'rotor',True,flip=True)
    for i,(x,y) in enumerate(bolts):
        head=cq.Workplane('XY').circle(2.85).extrude(1.65).edges('<Z').fillet(.65).translate((x,y,22.35)).val()
        add(f'M3x40_ring_{i}',head.fuse(cyl(1.45,40,(x,y,24))),'rotor',reference=True)
        add(f'M3_ring_washer_{i}',annulus(3.5,1.6,.5,dt).translate((x,y,0)),'rotor',reference=True)
        add(f'M3_ring_nut_{i}',core.hexagon(5.5,2.4,x,y,dt+.5).cut(cyl(1.5,4,(x,y,dt))),'rotor',reference=True)
    add('Boxed_Z_support',support(p,lay),'rotor',True,'#6d849c',context=True)
    add('Front_Z_frame',frame_struts.frame_finish(front_frame.frame(p,lay),p,lay),'rotor',True,'#829982',context=True)
    for side in ['front','rear']:add('Center_'+side+'_strut',frame_struts.strut(p,lay,side),'rotor',True,context=True)
    for name,shape in frame_struts.hardware(p,lay):add(name,shape,'rotor',reference=True,context=True)
    for name,shape in front_frame.hardware(p,lay):add(name,shape,'rotor',reference=True,context=True)
    for i,(x,y) in enumerate(p['support_mounts_mm']):
        add(f'M4_deck_insert_{i}',annulus(3,2,6,dt-6.3).translate((x,y,0)),'rotor',reference=True)
        seat=19 if i in [3,6] else p['support_foot_thickness_mm']+(8 if i==1 else 0)
        add(f'Z_support_deck_screw_{i}',cyl(1.95,seat+6,(x,y,dt-6)).fuse(cyl(3.5,4,(x,y,dt+seat))),'rotor',reference=True,context=True)
    for i,(x,y) in enumerate(lay['z_actuator']['base_fasteners']):
        s=cyl(1.45,40,(-y,-78,lay['z_origin']-x),(0,1,0)).fuse(cyl(2.75,3,(-y,-81,lay['z_origin']-x),(0,1,0)))
        add(f'M3x40_Z_base_mount_{i}',s,'rotor',reference=True,context=True)
    # Treat the upstream actuator assemblies as single-color modules.
    palette={'Center_front_strut':'#e99039','Center_rear_strut':'#9365c5',
             'Front_Z_frame':'#73aa87','Boxed_Z_support':'#577eae',
             'Rigid_rotating_deck':'#4eaaa5','Rigid_fixed_base':'#748393',
             'Internal_264T_ring':'#e0b448','Braced_test_stand':'#465b71'}
    actuator_color='#819dab'
    used=set(palette.values())|{actuator_color}
    for a in parts:
        if (a.get('source_name') or '').startswith(('Z_','R_')) and not a['keepout']:
            a['color']=actuator_color;continue
        if not a['printed']:continue
        if a['name'] in palette:a['color']=palette[a['name']];continue
        hue=int(hashlib.sha256(a['name'].encode()).hexdigest()[:8],16)/2**32
        color='#'+''.join(f'{round(v*255):02x}' for v in colorsys.hls_to_rgb(hue,.61,.47))
        while color in used:
            hue=(hue+.07)%1;color='#'+''.join(f'{round(v*255):02x}' for v in colorsys.hls_to_rgb(hue,.61,.47))
        a['color']=color;used.add(color)
    info=dict(center_mm=center,ratio=p['ring_teeth']/p['pinion_teeth'],arm_z_shift_mm=dz,arm_parameters=ap,arm_layout=oldlay,roller_parameters=rp,linear_contacts=[dict(parts=sorted(k),reason=v) for k,v in arm.linear_contacts(old,oldlay).items()])
    cache.mkdir(parents=True,exist_ok=True)
    for i,a in enumerate(parts):a['shape'].exportBrep(str(cache/f'{i}.brep'))
    (cache/'parts.json').write_text(json.dumps([{k:v for k,v in a.items() if k not in ['shape','freeShape']} for a in parts]))
    (cache/'info.json').write_text(json.dumps(info));(cache/'complete').write_text('1')
    return parts,info

def export(parts,info,out):
    out.mkdir(parents=True,exist_ok=True);stl=out/'STL';stl.mkdir(exist_ok=True);mesh=[];manifest=[]
    native={}
    for axis,key in [('Z','z_actuator'),('R','r_actuator')]:
        meta=info['arm_layout'][key]
        for a in arm.direct_mount.parts(axis,meta,info['arm_layout']['h_origin']):
            if a['printed']:native[axis+'_'+a['name'].replace(' ','_')]=arm.linear.home_shape(a,meta,printing=True)
    assy=cq.Assembly(name=f"Rigid_{info['ratio']:g}_to_1_arm_variant")
    for a in parts:
        s=a['shape'];assy.add(s,name=a['name'],color=cq.Color(a['color']))
        vertices,triangles=s.tessellate(.18,.2)
        mesh.append({k:v for k,v in a.items() if k not in ['shape','freeShape']}|dict(vertices=[[round(x,4) for x in v.toTuple()] for v in vertices],triangles=triangles))
        if a['printed']:
            ps=native.get(a['source_name'],a.get('freeShape',s))
            if a['name']=='Boxed_Z_support':ps=ps.rotate((0,0,0),(1,0,0),90)
            elif a['name'] in ['Center_front_strut','Center_rear_strut']:ps=ps.rotate((0,0,0),(0,1,0),90)
            elif a['name']=='Front_Z_frame':ps=ps.rotate((0,0,0),(1,0,0),-90)
            elif a['flip']:ps=ps.rotate((0,0,0),(1,0,0),180)
            b=ps.BoundingBox();ps=ps.translate((0,0,-b.zmin));file=stl/(a['name']+'.stl')
            cq.exporters.export(ps,str(file),tolerance=.025,angularTolerance=.09)
            b=ps.BoundingBox();manifest.append(dict(name=a['name'],file='STL/'+file.name,size_mm=[b.xlen,b.ylen,b.zlen],volume_mm3=ps.Volume(),sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
    assy.save(str(out/'rigid-arm.step'))
    (out/'mesh.json').write_text(json.dumps(mesh,separators=(',',':')))
    (out/'print-manifest.json').write_text(json.dumps(manifest,indent=2))
    (out/'config.json').write_text(json.dumps(parameters()|{k:v for k,v in info.items() if k not in ['arm_parameters','arm_layout','roller_parameters','linear_contacts']},indent=2))
    print('Exported',len(parts),'parts and',len(manifest),'prints',flush=True)

if __name__=='__main__':
    args=argparse.ArgumentParser();args.add_argument('--out',default='output/rigid-base');a=args.parse_args()
    parts,info=build();export(parts,info,pathlib.Path(a.out))
