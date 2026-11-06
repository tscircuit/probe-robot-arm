"""Modular theta/Z/r flying probe CAD. Units mm. Prototype, not load rated.

The two FLEX stages use the pinned upstream R24 pass-through construction.
Run: .venv/bin/python model.py --config parameters.json --out output
"""
from __future__ import annotations
import argparse, contextlib, hashlib, io, itertools, json, math, pathlib, sys
import cadquery as cq
import rotary_base
from rotary_base import gear_geometry as base_gears

ROOT = pathlib.Path(__file__).resolve().parent
V = cq.Vector

def box(x, y, z, c):
    return cq.Workplane("XY").box(x, y, z).translate(c).val()

def cyl(r, h, c=(0, 0, 0), axis=(0, 0, 1)):
    return cq.Solid.makeCylinder(r, h, V(*c), V(*axis))

def annulus(ro, ri, h, z):
    return cyl(ro, h, (0, 0, z)).cut(cyl(ri, h, (0, 0, z)))

def union(shapes):
    first, *rest = shapes
    return first.fuse(*rest).clean() if rest else first

def holes(shape, points, r, z, height):
    return shape.cut(*[cyl(r, height, (x, y, z)) for x, y in points]).clean()

def overlap(a, b):
    x, y = a.BoundingBox(), b.BoundingBox()
    if any(getattr(x, k+"max") <= getattr(y, k+"min")+1e-6 or
           getattr(y, k+"max") <= getattr(x, k+"min")+1e-6 for k in "xyz"):
        return 0.0
    return max(0.0, a.intersect(b).Volume())

def layout(p):
    p.update(rotary_base.parameters())
    w, d = p["pcb_width"], p["pcb_depth"]
    if min(w, d) <= 0 or p["z_stroke"] != 40:
        raise ValueError("Positive PCB dimensions and the specified 40 mm Z stroke are required")
    edge = p["edge_to_pivot"]
    if edge < 95:
        raise ValueError("Base/PCB clearance requires edge_to_pivot >= 95 mm")
    mounts = [(w/2+edge, 0, 180), (0, d/2+edge, -90),
              (-w/2-edge, 0, 0), (0, -d/2-edge, 90)]
    far = max(math.hypot(w+edge, d/2), math.hypot(d+edge, w/2))
    rmin = edge-p["radial_margin"]
    needed = far+p["radial_margin"]-rmin
    stroke = p["radial_stroke"] or math.ceil(needed/10)*10
    if stroke < needed or not 20 <= stroke <= 150:
        raise ValueError(f"Radial stroke must cover {needed:.3f} mm and be within prototype range 20..150")
    zm={k:v for k,v in flex_metadata(40,p['z_motor_depth'],p['z_motor'],output_mount='through').items() if k not in ['tracks','stages']}
    rm={k:v for k,v in flex_metadata(stroke,p['radial_motor_depth'],p['radial_motor']).items() if k not in ['tracks','stages']}
    deck_top=58.2-p['rotor_drop_mm']
    clearance=p['z_rack_deck_clearance']
    if clearance<1:raise ValueError('Allow at least 1 mm nominal rack/deck clearance')
    clamp_top=58.4  # Shared M6x60 bolt: -1.6 mm under-head seat + 60 mm.
    minimum_z=max(deck_top,clamp_top)+clearance-zm['left']+p['z_stroke']/2
    if p['z_origin'] is None:p['z_origin']=minimum_z
    if p['z_origin']<minimum_z:raise ValueError(f'Z origin must be at least {minimum_z} mm for full downward travel')
    pad = rm["right"]+rm["OUTPUT_PAD_SIZE"]/2
    h_origin = p['horizontal_motor_x']
    tip_radius=rmin+stroke/2
    outrigger=tip_radius-h_origin-pad
    if outrigger < 35: raise ValueError('The tapered probe outrigger needs at least 35 mm reach')
    if p['base_motor_depth']<40 or p['z_motor_depth']<40 or p['radial_motor_depth']<30: raise ValueError('Pancake motor envelopes are not permitted')
    if (p['z_motor'],p['radial_motor'],p['radial_inverted'])!=('nema17','nema14',True): raise ValueError('This integration requires NEMA17 Z and inverted NEMA14 radial stages')
    zpad = p["z_origin"]+zm["right"]+zm["OUTPUT_PAD_SIZE"]/2
    board_top = zpad+p['horizontal_height_offset']-rm['OUTPUT_PAD_TOP']-p['probe_drop']-20
    return dict(base_motor_x=base_drive_center(p),base_gear_ratio=p['ring_teeth']/p['pinion_teeth'],mounts=mounts, rmin=rmin, rmax=rmin+stroke, radial_stroke=stroke,
                required_stroke=needed, h_origin=h_origin, horizontal_pad=pad,
                zpad=zpad, board_top=board_top, tip_radius=tip_radius, probe_extension=outrigger,
                horizontal_origin_y=p['horizontal_origin_y'], horizontal_z=zpad+p['horizontal_height_offset'],
                probe_mount_z=zpad+p['horizontal_height_offset']-rm['OUTPUT_PAD_TOP'],
                radial_mount_face_z=zpad+p['horizontal_height_offset']-rm['CASE_TOP'],
                z_drive_y=25.5-zm['MOTOR_Y'],z_pitch_radius=zm['RP'],
                r_drive_y=p['horizontal_origin_y']-rm['MOTOR_Y'],r_pitch_radius=rm['RP'],
                actuator_enclosure='pass-through',rack_source_revision=24,
                minimum_z_origin=minimum_z,z_case_bottom=p['z_origin']+zm['CASE_LEFT'],
                z_rack_lowest=p['z_origin']+zm['left']-p['z_stroke']/2,
                deck_top_z=deck_top,base_clamp_top_z=clamp_top,z_deck_mounts=p['z_deck_mounts'],base_revision='shared-rounded-blocks',
                z_actuator=zm,r_actuator=rm,
                yaw_required=max(math.degrees(math.atan2(w/2, edge)),math.degrees(math.atan2(d/2,edge))))

def flex(stroke,relaxed=False,depth=34,motor='nema14',output_mount='inserts'):
    """Execute only upstream construction; keep upstream source unchanged.

    The upstream motor, depth, stroke and pass-through options are used directly.
    Export and service animation code are excluded. The Z output pad is locally
    adapted to through-bores; the pinned upstream file remains unchanged.
    """
    source = (ROOT/"upstream/rack-actuator-r24/model.py").read_text()
    source = source.split("# Clear obsolete generated meshes")[0]
    key = hashlib.sha256((source+str(stroke)+str(depth)+motor+'pass-through'+output_mount).encode()).hexdigest()[:16]
    cache = ROOT/"cache"/key
    if (cache/"parts.json").exists():
        data = json.loads((cache/"parts.json").read_text())
        for i, part in enumerate(data):
            part["shape"] = cq.Shape.importBrep(str(cache/f"{i}.brep"))
            if relaxed and part.get("flex_chassis"):
                part["shape"] = cq.Shape.importBrep(str(cache/"relaxed-chassis.brep"))
        return data
    print(f"Building upstream R24 pass-through {motor}, stroke {stroke} mm", flush=True)
    cache.mkdir(parents=True, exist_ok=True)
    argv = sys.argv
    sys.argv = ['model.py','--motor',motor,'--stroke',str(stroke),'--motor-depth',str(depth),'--enclosure','pass-through','--out',str(cache)]
    ns = {"__name__": "flex_geometry", "__file__": str(ROOT/"upstream/rack-actuator-r24/model.py")}
    try:
        exec(compile(source, ns["__file__"], "exec"), ns)
    finally:
        sys.argv = argv
    data = ns["parts"]
    assert output_mount in ['inserts','through']
    if output_mount=='through':
        data=[a for a in data if a.get('embedded_host')!='04 Beveled compliant rack']
        rack=next(a for a in data if a['name']=='04 Beveled compliant rack')
        pad=box(18,18,18,(ns['right']+9,ns['OUTPUT_PAD_Y'],12))
        rack['shape']=holes(rack['shape'].fuse(pad),ns['OUTPUT_MOUNTS'],1.7,2,20)
    keys=['CASE_LEFT','CASE_RIGHT','CASE_LENGTH','CASE_YMIN','CASE_YMAX','CASE_BOTTOM','CASE_TOP','CASE_MOUNTS','CASE_CORNERS','OUTPUT_MOUNTS','OUTPUT_PAD_Y','OUTPUT_PAD_TOP','OUTPUT_PAD_SIZE','left','right','REAR_OPENING_YZ','tracks','stages','MOTOR_Y','RP','MOTOR_SIZE','MOTOR_PITCH','MOTOR_DEPTH','N']
    (cache/'metadata.json').write_text(json.dumps({**{k:ns[k] for k in keys},'output_mount':output_mount}))
    # Keep a separate relaxed chassis, as the assembled chassis is preloaded.
    ns["base_print"].exportBrep(str(cache/"relaxed-chassis.brep"))
    for i, part in enumerate(data):
        part["shape"].exportBrep(str(cache/f"{i}.brep"))
    (cache/"parts.json").write_text(json.dumps([{k:v for k,v in a.items() if k!="shape"} for a in data]))
    return flex(stroke,True,depth,motor,output_mount) if relaxed else data

def flex_metadata(stroke,depth=34,motor='nema14',output_mount='inserts'):
    source=(ROOT/'upstream/rack-actuator-r24/model.py').read_text().split('# Clear obsolete generated meshes')[0]
    key=hashlib.sha256((source+str(stroke)+str(depth)+motor+'pass-through'+output_mount).encode()).hexdigest()[:16]
    path=ROOT/'cache'/key/'metadata.json'
    if not path.exists():flex(stroke,depth=depth,motor=motor,output_mount=output_mount)
    return json.loads(path.read_text())

def full_depth_flex(stroke,depth,motor='nema14',output_mount='inserts'):
    return flex(stroke,depth=depth,motor=motor,output_mount=output_mount)

def cluster_targets(p,cx=0,cy=0):
    h=p['probe_cluster_pitch']/2
    return [(cx+h,cy+h),(cx-h,cy+h),(cx-h,cy-h),(cx+h,cy-h)]

def target_pose(lay,index,target,z=-20):
    x,y,deg=lay['mounts'][index];dx=target[0]-x;dy=target[1]-y
    yaw=(math.degrees(math.atan2(dy,dx))-deg+180)%360-180
    radius=math.hypot(dx,dy)
    if not lay['rmin']-1e-8<=radius<=lay['rmax']+1e-8 or abs(yaw)>30: raise ValueError('Target outside arm workspace')
    return dict(yaw=yaw,z=z,r=radius-lay['tip_radius'])

def inv(r, rb):
    return math.sqrt(max(0, (r/rb)**2-1))-math.acos(min(1, rb/r))

def polar(r, t):
    return (r*math.cos(t), r*math.sin(t))

def pinion_profile(m, n, pa, preload=0):
    rp=m*n/2; rb=rp*math.cos(math.radians(pa)); rr=rp-1.25*m; ra=rp+m
    def half(r):
        return math.pi/(2*n)+preload/rp+inv(rp,rb)-inv(max(r,rb),rb)
    pts=[]
    for i in range(n):
        t=2*math.pi*i/n
        rs=[rr]+[rb+(ra-rb)*k/24 for k in range(25)]
        pts += [polar(r,t-half(r)) for r in rs]
        pts += [polar(r,t+half(r)) for r in reversed(rs)]
    return cq.Workplane("XY").polyline(pts).close().extrude(12).val(), half

def base_drive_center(p):
    p.update(rotary_base.parameters())
    return base_gears.base_drive_center(p)

def base_drive_cache(p):
    p.update(rotary_base.parameters())
    return base_gears.base_drive_cache(p)

def drive_gears(p):
    p.update(rotary_base.parameters())
    return base_gears.drive_gears(p)

BASE_NAME_MAP={'Fixed_base_plate':'Module_base','Rotating_test_deck':'Rotating_deck',
 'NEMA17_motor_REFERENCE':'Base_NEMA17_48mm_reference','Motor_D_shaft_REFERENCE':'Base_motor_D_shaft',
 'Rear_controller_PCB_REFERENCE':'Controller_RP2040_PCB_envelope',
 'Controller_component_KEEPOUT':'Controller_component_clearance','USB_cable_KEEPOUT':'Controller_USB_cable_clearance'}

def base_contacts(parts,p):
    canonical=[dict(q,name=q['base_name']) for q in parts if q.get('base_name')]
    allowed=rotary_base.core.contact_exceptions(canonical,p)
    return {frozenset(BASE_NAME_MAP.get(n,n) for n in pair):reason for pair,reason in allowed.items()}

def build(p, lay):
    parts=[]
    center=base_drive_center(p)
    def add(name,shape,group,color="#8392a5",printed=False,reference=False,keepout=False):
        if not shape.isValid(): raise ValueError(f"Invalid solid: {name}")
        parts.append(dict(name=name,shape=shape,group=group,color=color,printed=printed,reference=reference,keepout=keepout))
    base_parts,nominal=rotary_base.build(p)
    for q in base_parts:
        if q['name']=='Integrated_stand' or q['name'].startswith(('M5x25_upper_stand_','M5_stand_nut_')):continue
        name=BASE_NAME_MAP.get(q['name'],q['name'])
        add(name,q['shape'],{'fixed':'fixed','rotor':'theta','pinion':'base_drive'}[q['group']],q['color'],bool(q['print_id']),q['reference'],q['keepout'])
        parts[-1].update(base_name=q['name'],base_group=q['group'],print_flip=q['flip'])
    # Main platform hardware replaces the bench stand hardware only.
    a=p['stand_leg_pitch']/2
    for i,(x,y) in enumerate(itertools.product([-a,a],repeat=2)):
        screw=cyl(2.5,30,(x,y,-19)).fuse(cyl(4.25,5,(x,y,11)))
        add(f'M5_platform_bolt_{i}',screw,'fixed','#acb8c2',reference=True)
        add(f'M5_platform_washer_{i}',annulus(5,2.6,1,-11).translate((x,y,0)),'fixed','#acb8c2',reference=True)
        nut=rotary_base.core.hexagon(8,4,x,y,-15).cut(cyl(2.5,6,(x,y,-16)))
        add(f'M5_platform_nut_{i}',nut,'fixed','#acb8c2',reference=True)
    upright_mounts=lay['z_deck_mounts'];dt=lay['deck_top_z'];dz=dt-60
    for i,(x,y) in enumerate(upright_mounts):
        insert=cyl(3,6,(x,y,dt-6.3)).cut(cyl(2,6,(x,y,dt-6.3)))
        add(f'M4_deck_insert_{i}',insert,'theta','#d4a54a',reference=True)
        parts[-1]['embedded_host']='Rotating_deck'
        screw=cyl(1.95,16,(x,y,dt-6)).fuse(cyl(3.5,4,(x,y,dt+10)))
        add(f'Z_cradle_deck_screw_{i}',screw,'theta','#a5b5c1',reference=True)
    # Dual-face cradle: solid top/side mounting faces share broad deck flanges.
    zo=p['z_origin'];zm=lay['z_actuator'];rm=lay['r_actuator']
    zside=25.5-zm['CASE_YMAX'];top=zo+zm['CASE_RIGHT'];front=zm['CASE_TOP']
    side=box(front+6+52,6,top-dt,((front+6-52)/2,zside-3,(top+dt)/2))
    side_foot=box(88,23.6,10,(-13,-50.2,dt+5))
    front_foot=box(52-front,104,10,((52+front)/2,2,dt+5))
    flanges=side_foot.fuse(front_foot).intersect(cyl(80,10,(0,0,dt)))
    # Full solid face, with a 6 x 6 mm overlapping corner along the full height.
    # Only the mounting bolt bores are removed; no separated rails or windows.
    face_ymax=25.5-zm['CASE_YMIN']
    top_face=box(6,face_ymax-(zside-6),top-dt,(front+3,(face_ymax+zside-6)/2,(top+dt)/2))
    support=union([side,flanges,top_face])
    support=holes(support,upright_mounts,2.2,dt-1,12)
    for localx,localz in zm['CASE_MOUNTS']:
        support=support.cut(cyl(1.7,8,(localz,zside-7,zo+localx),(0,1,0)))
    for localx,localy in zm['CASE_CORNERS']:
        support=support.cut(cyl(1.7,8,(front-1,25.5-localy,zo+localx),(1,0,0)))
    add('Z_support',support.clean(),'theta','#6d849c',True)
    # Conservative uncut primitives certify separation from both mounting faces.
    # They contain the final cradle, including its holes and trimmed flange corners.
    parts[-1]['sweep_boxes']=[[[b.xmin,b.ymin,b.zmin],[b.xmax,b.ymax,b.zmax]] for b in [s.BoundingBox() for s in [side,side_foot,front_foot,top_face]]]
    for a in full_depth_flex(40,p['z_motor_depth'],p['z_motor'],output_mount='through'):
        s=a['shape'].rotate((0,0,0),(1,0,1),180).translate((0,25.5,zo))
        g='z_rack' if a['group']=='rack' else 'z_drive' if a['group'] in ['gear','shaft','set_screw'] else 'theta'
        add('Z_'+a['name'].replace(' ','_'),s,g,a['color'],a['printed'])
        parts[-1]['actuator_group']=a['group'];parts[-1]['actuator']='Z'
        if a.get('embedded_host'):parts[-1]['embedded_host']='Z_'+a['embedded_host'].replace(' ','_')
    for i,(localx,localz) in enumerate(zm['CASE_MOUNTS']):
        # M3x10 through 6 mm bracket: 3.7 mm into the recessed insert.
        s=cyl(1.45,10,(localz,zside-6,zo+localx),(0,1,0)).fuse(cyl(2.75,3,(localz,zside-9,zo+localx),(0,1,0)))
        add(f'Z_enclosure_mount_screw_{i}',s,'theta','#a5b5c1',reference=True)
    for i,(localx,localy) in enumerate(zm['CASE_CORNERS']):
        # Flush top-post inserts: 4 mm engagement through the 6 mm solid face.
        screw=cyl(1.45,10,(front-4,25.5-localy,zo+localx),(1,0,0)).fuse(cyl(2.75,3,(front+6,25.5-localy,zo+localx),(1,0,0)))
        add(f'Z_top_mount_screw_{i}',screw,'theta','#a5b5c1',reference=True)
    hx=lay['h_origin'];hy=lay['horizontal_origin_y'];zp=lay['zpad'];hz=lay['horizontal_z']
    # One-piece inverted U wraps both output-pad faces and its top.
    zy=25.5-zm['OUTPUT_PAD_Y']
    face=lay['radial_mount_face_z']
    assert face-zp>=15, 'Bottom-mounted radial shelf must clear the Z output fasteners'
    vertical=box(6,24,face-(zp-9),(24,zy,(face+zp-9)/2))
    rear=box(6,24,face-(zp-9),(0,zy,(face+zp-9)/2))
    bridge=box(30,24,face-(zp+9),(12,zy,(face+zp+9)/2))
    xmin=hx+rm['CASE_LEFT'];xmax=hx+rm['CASE_RIGHT']
    ymin=hy-rm['CASE_YMAX'];ymax=hy-rm['CASE_YMIN']
    shelf=box(xmax-xmin,ymax-ymin,6,((xmin+xmax)/2,(ymin+ymax)/2,face-3))
    carrier=union([vertical,rear,bridge,shelf])
    for localx,localy in zm['OUTPUT_MOUNTS']:
        carrier=carrier.cut(cyl(1.7,32,(-4,25.5-localy,zo+localx),(1,0,0)))
    for localx,localy in rm['CASE_CORNERS']:
        carrier=carrier.cut(cyl(1.7,8,(hx+localx,hy-localy,face-7)))
    add('Z_to_radial_carrier',carrier.clean(),'z_rack','#8a789e',True)
    for i,(localx,localy) in enumerate(zm['OUTPUT_MOUNTS']):
        y,z=25.5-localy,zo+localx
        s=cyl(1.45,35,(-7.5,y,z),(1,0,0)).fuse(cyl(2.75,3,(27.5,y,z),(1,0,0)))
        add(f'Z_output_mount_screw_{i}',s,'z_rack','#a5b5c1',reference=True)
        for label,x in [('front',27),('rear',-3.5)]:
            washer=cyl(3,.5,(x,y,z),(1,0,0)).cut(cyl(1.7,.5,(x,y,z),(1,0,0)))
            add(f'Z_output_{label}_washer_{i}',washer,'z_rack','#a5b5c1',reference=True)
        nut=cq.Workplane('YZ').polygon(6,5.5/math.cos(math.pi/6)).extrude(2.4).translate((-5.9,y,z)).val()
        nut=nut.cut(cyl(1.6,2.6,(-6,y,z),(1,0,0)))
        add(f'Z_output_nut_{i}',nut,'z_rack','#a5b5c1',reference=True)
    for a in full_depth_flex(lay['radial_stroke'],p['radial_motor_depth'],p['radial_motor']):
        s=a['shape'].rotate((0,0,0),(1,0,0),180).translate((hx,hy,hz))
        g='r_rack' if a['group']=='rack' else 'r_drive' if a['group'] in ['gear','shaft','set_screw'] else 'z_rack'
        add('R_'+a['name'].replace(' ','_'),s,g,a['color'],a['printed'])
        parts[-1]['actuator_group']=a['group'];parts[-1]['actuator']='R'
        if a.get('embedded_host'):parts[-1]['embedded_host']='R_'+a['embedded_host'].replace(' ','_')
    for i,(localx,localy) in enumerate(rm['CASE_CORNERS']):
        # M3x10 enters upward through the 6 mm shelf into flush top-post inserts.
        s=cyl(1.45,10,(hx+localx,hy-localy,face-6)).fuse(cyl(2.75,3,(hx+localx,hy-localy,face-9)))
        add(f'R_enclosure_mount_screw_{i}',s,'z_rack','#a5b5c1',reference=True)
    padx=hx+lay['horizontal_pad'];pady=hy-rm['OUTPUT_PAD_Y'];mountz=lay['probe_mount_z']
    tipx=lay['tip_radius'];anchorx=tipx-p['probe_inward_lean']
    outline=[(padx-9,pady-10),(padx+9,pady-10),(anchorx+3,-3),(anchorx+3,3),(padx+9,pady+10),(padx-9,pady+10)]
    holder=cq.Workplane('XY').polyline(outline).close().extrude(6).translate((0,0,mountz-6)).val().fuse(cyl(3,6,(anchorx,0,mountz-6))).clean()
    holder=holes(holder,[(hx+x,hy-y) for x,y in rm['OUTPUT_MOUNTS']],1.7,mountz-7,8)
    tip=V(tipx,0,mountz-p['probe_drop']);axis=V(-p['probe_inward_lean'],0,p['probe_drop']).normalized()
    holder=holder.cut(cq.Solid.makeCylinder(1.05,55,tip,axis)).cut(cyl(.8,4,(anchorx,-4,mountz-3),(0,1,0))).clean()
    add('Triangular_probe_outrigger',holder,'r_rack','#8a789e',True)
    for i,(x,y) in enumerate(rm['OUTPUT_MOUNTS']):
        s=cyl(1.45,10,(hx+x,hy-y,mountz-6)).fuse(cyl(2.75,3,(hx+x,hy-y,mountz-9)))
        add(f'Probe_output_mount_screw_{i}',s,'r_rack','#a5b5c1',reference=True)
    probe=cq.Solid.makeCone(0,.2,1.5,tip,axis).fuse(cq.Solid.makeCylinder(.2,6.5,tip+axis*1.5,axis),cq.Solid.makeCylinder(1,40,tip+axis*8,axis)).clean()
    add('Spring_probe_reference',probe,'r_rack','#ead286',reference=True)
    return parts,nominal

def pose(parts,p,lay,yaw=0,z=0,r=0):
    if abs(z)>20 or abs(r)>lay["radial_stroke"]/2: raise ValueError("Pose outside stroke")
    result=[]
    for part in parts:
        a=part.copy(); s=a["shape"]; g=a["group"]
        if g=="base_drive":
            s=s.rotate((base_drive_center(p),0,0),(base_drive_center(p),0,1),yaw*p["ring_teeth"]/p["pinion_teeth"])
        else:
            if g=="z_drive":
                s=s.rotate((0,lay["z_drive_y"],p["z_origin"]),(1,lay["z_drive_y"],p["z_origin"]),-z/lay["z_pitch_radius"]*180/math.pi)
            if g=="r_drive":
                s=s.rotate((lay['h_origin'],lay['r_drive_y'],lay['horizontal_z']),(lay['h_origin'],lay['r_drive_y'],lay['horizontal_z']+1),r/lay['r_pitch_radius']*180/math.pi)
            if g=="r_rack": s=s.translate((r,0,0))
            if g in ["z_rack","r_rack","r_drive"]: s=s.translate((0,0,z))
            if g!="fixed": s=s.rotate((0,0,0),(0,0,1),yaw)
        a["shape"]=s; result.append(a)
    return result

def assembly(parts,name):
    a=cq.Assembly(name=name)
    for part in parts:
        a.add(part["shape"],name=part["name"],color=cq.Color(part["color"]))
    return a

def mesh_export(parts,path):
    data=[]
    for part in parts:
        vs,ts=part["shape"].tessellate(.15,.2)
        data.append({k:v for k,v in part.items() if k!="shape"}|{
            "vertices":[[round(v.x,4),round(v.y,4),round(v.z,4)] for v in vs],"triangles":ts})
    path.write_text(json.dumps(data,separators=(",",":")))

def platform_parts(p,lay):
    w,d=p['pcb_width'],p['pcb_depth'];top=lay['board_top']; result=[]
    def add(name,s,color): result.append(dict(name=name,shape=s,color=color))
    plate=box(w+2*p['edge_to_pivot']+200,d+2*p['edge_to_pivot']+200,10,(0,0,-5))
    mounting=[]
    for x,y,ang in lay['mounts']:
        ca,sa=math.cos(math.radians(ang)),math.sin(math.radians(ang))
        for u,v in itertools.product([-p['stand_leg_pitch']/2,p['stand_leg_pitch']/2],repeat=2):mounting.append((x+ca*u-sa*v,y+sa*u+ca*v))
        pocket=box(50,50,12,(base_drive_center(p),0,-5)).rotate((0,0,0),(0,0,1),ang).translate((x,y,0))
        plate=plate.cut(pocket,cyl(29,12,(x,y,-11)))
    add('Main_platform',holes(plate,mounting,2.7,-11,12),'#485563')
    add('PCB_reference',box(w,d,1.6,(0,0,top-.8)),'#277c60')
    for i,(x,y) in enumerate(itertools.product([-w/2+6,w/2-6],[-d/2+6,d/2-6])):
        add(f'PCB_support_{i}',cyl(4,top-1.6,(x,y,0)),'#9aabb7')
    for i,(x,y) in enumerate(itertools.product([-(w/2+p['edge_to_pivot']+80),w/2+p['edge_to_pivot']+80],[-(d/2+p['edge_to_pivot']+80),d/2+p['edge_to_pivot']+80])):
        h=-10-p['platform_ground_z']
        add(f'Platform_leg_{i}',box(20,20,h,(x,y,p['platform_ground_z']+h/2)).cut(box(16,16,h+2,(x,y,p['platform_ground_z']+h/2))),'#485563')
    return result

def validate(parts,p,lay,nominal):
    report={"status":"prototype", "solid_validity":all(a["shape"].isValid() for a in parts),
            "part_count":len(parts),"layout":lay,"collisions":[],"nominal_base_mesh":[],"travel_samples":[],
            "limits":["Geometry prototype. No physical accuracy, stiffness, fatigue, holding torque or contact force certification.",
                      "R24 pass-through rack and housing, 120 mm custom stroke within upstream limits; stiffness remains untested.",
                      "Shared rotary base includes retainers, direct motor mounting and four single blocks with integral tilted axles. Hardware envelopes are references; homing remains unfinished.",
                      "Simultaneous four-tip cluster checks are in platform-validation.json; they are sampled geometric checks, not physical accuracy tests.",
                      "Sampled collision checks are not a continuous swept-volume proof."]}
    report["printed_solid_counts"]={a["name"]:len(a["shape"].Solids()) for a in parts if a["printed"]}
    # Base mesh over one complete tooth engagement, without elastic preload.
    ring=next(a["shape"] for a in parts if a["name"]=="Internal_72T_ring")
    drive_cache=base_drive_cache(p)
    digest=hashlib.sha256((drive_cache/'nominal.brep').read_bytes()+(drive_cache/'ring.brep').read_bytes()).hexdigest()
    cache_file=drive_cache/'mesh-validation.json'
    cached=json.loads(cache_file.read_text()) if cache_file.exists() else {}
    if cached.get('sha256')==digest:
        report['nominal_base_mesh']=cached['samples']; report['unchanged_gear_mesh_reused']=True
    else:
        for k in range(13):
            t=360/p["ring_teeth"]*k/12
            v=overlap(nominal.rotate((base_drive_center(p),0,0),(base_drive_center(p),0,1),t*p["ring_teeth"]/p["pinion_teeth"]),ring.rotate((0,0,0),(0,0,1),t))
            report["nominal_base_mesh"].append({"ring_angle_deg":t,"overlap_mm3":v})
        cache_file.write_text(json.dumps({'sha256':digest,'samples':report['nominal_base_mesh']}))
    # All rigid pairs, excluding the intended preloaded tooth contacts.
    def stage(name):
        return "Z" if name.startswith("Z_") and name!="Z_support" and name!="Z_to_radial_carrier" else "R" if name.startswith("R_") else None
    allowed=base_contacts(parts,p)
    pair_cache={}
    for z,r in itertools.product([-20,0,20],[-lay["radial_stroke"]/2,0,lay["radial_stroke"]/2]):
        posed=pose(parts,p,lay,z=z,r=r)
        bounds={a['name']:a['shape'].BoundingBox() for a in posed}
        failures=[]
        for a,b in itertools.combinations(posed,2):
            if frozenset([a["name"],b["name"]]) in allowed:continue
            if a.get("embedded_host")==b["name"] or b.get("embedded_host")==a["name"]: continue
            if stage(a["name"]) and stage(a["name"])==stage(b["name"]):
                if any("pinion" in q["name"] for q in [a,b]) and any("compliant_rack" in q["name"] for q in [a,b]): continue
            if {a["name"],b["name"]}=={f"Compliant_{p['pinion_teeth']}T_pinion","Internal_72T_ring"}: continue
            ga,gb=a["group"],b["group"]
            if ga==gb: rk=zk=0
            else:
                rk=r if any(g in ["r_rack","r_drive"] for g in [ga,gb]) else 0
                moving_z={"z_rack","r_rack","r_drive"}
                zk=z if "z_drive" in [ga,gb] or ((ga in moving_z)!=(gb in moving_z)) else 0
            key=(a["name"],b["name"],rk,zk)
            if key not in pair_cache:
                aa,bb=bounds[a['name']],bounds[b['name']]
                disjoint=any(getattr(aa,k+'max')<=getattr(bb,k+'min')+1e-6 or getattr(bb,k+'max')<=getattr(aa,k+'min')+1e-6 for k in 'xyz')
                pair_cache[key]=0 if disjoint else overlap(a['shape'],b['shape'])
            v=pair_cache[key]
            if v>.03: failures.append({"a":a["name"],"b":b["name"],"overlap_mm3":round(v,4)})
        report["travel_samples"].append({"z_mm":z,"r_mm":r,"collisions":failures})
        print("Pose",z,r,"rigid collisions",len(failures),flush=True)
    report["collisions"]=report["travel_samples"][4]["collisions"]
    report["geometry_checks_passed"]=(report["solid_validity"] and all(v==1 for v in report["printed_solid_counts"].values()) and not any(s["collisions"] for s in report["travel_samples"]) and max(s["overlap_mm3"] for s in report["nominal_base_mesh"])<.01)
    return report

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--config",default="parameters.json");ap.add_argument("--out",default="output");ap.add_argument("--check",action="store_true");ap.add_argument('--preview-only',action='store_true')
    args=ap.parse_args(); p=json.loads(pathlib.Path(args.config).read_text());lay=layout(p)
    out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    print("Layout:",json.dumps(lay),flush=True)
    parts,nominal=build(p,lay)
    print("Built",len(parts),"parts",flush=True)
    if args.check:
        report=validate(parts,p,lay,nominal)
        (out/"validation.json").write_text(json.dumps(report,indent=2))
        if not report["geometry_checks_passed"]: raise RuntimeError("Geometry check failed; inspect output/validation.json")
    (out/'parameters-resolved.json').write_text(json.dumps(p|lay,indent=2))
    mesh_export(parts,out/'arm-mesh.json')
    mesh_export(platform_parts(p,lay),out/'platform-mesh.json')
    if args.preview_only:return
    current=pose(parts,p,lay,p["yaw_degrees"],p["z_position"],p["radial_position"])
    assembly(current,"Modular_probe_arm").save(str(out/"single-arm.step"))
    platform=cq.Assembly(name="Four_probe_platform")
    contact_cache={}
    for i,(x,y,angle) in enumerate(lay["mounts"]):
        q=target_pose(lay,i,cluster_targets(p)[i]);key=tuple(round(q[k],8) for k in ['yaw','z','r'])
        if key not in contact_cache:contact_cache[key]=pose(parts,p,lay,**q)
        module=assembly(contact_cache[key],f"Arm_{i+1}")
        platform.add(module,loc=cq.Location(V(x,y,0),V(0,0,1),angle))
    for part in platform_parts(p,lay):platform.add(part['shape'],name=part['name'],color=cq.Color(part['color']))
    platform.save(str(out/"four-arm-platform.step"))
    custom=out/"prototype-parts";custom.mkdir(exist_ok=True)
    for a in parts:
        if a["printed"] and not a["name"].startswith(("Z_0","R_0")):
            shape=rotary_base.print_shape(dict(shape=a['shape'],flip=a.get('print_flip',False))) if a.get('base_name') else a['shape']
            cq.exporters.export(shape,str(custom/(a['name']+'.stl')),tolerance=.025 if a.get('base_name') else .05,angularTolerance=.06 if a.get('base_name') else .12)
    for label,stroke,depth,motor in [('Z',40,p['z_motor_depth'],p['z_motor']),('R',lay['radial_stroke'],p['radial_motor_depth'],p['radial_motor'])]:
        for part in flex(stroke,relaxed=True,depth=depth,motor=motor,output_mount='through' if label=='Z' else 'inserts'):
            if part["printed"]:
                cq.exporters.export(part["shape"],str(custom/(label+"_"+part["name"].replace(" ","_")+".stl")),tolerance=.05,angularTolerance=.12)
    print("Exported STEP assemblies and meshes to",out,flush=True)

if __name__=="__main__": main()
