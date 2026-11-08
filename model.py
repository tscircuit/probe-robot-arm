"""Modular theta/Z/r flying probe CAD. Units mm. Prototype, not load rated.

The two stages adapt pinned printed-leadscrew Site v61 geometry.
Run: .venv/bin/python model.py --config parameters.json --out output
"""
from __future__ import annotations
import argparse, contextlib, hashlib, io, itertools, json, math, pathlib, sys
import cadquery as cq
import rotary_base
import leadscrew_actuator as linear
import direct_mount
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
    w,d=p['pcb_width'],p['pcb_depth'];edge=p['edge_to_pivot']
    assert p['z_stroke']==40 and min(w,d)>0
    far=max(math.hypot(w+edge,d/2),math.hypot(d+edge,w/2));rmin=edge-p['radial_margin']
    needed=far+p['radial_margin']-rmin;stroke=p['radial_stroke'] or math.ceil(needed/10)*10
    assert stroke>=needed and stroke>=40
    width=p.get('z_width',4);assert width in [1,2,4]
    zm=linear.metadata(40,width,p['z_motor'],p['z_motor_depth']);rm=linear.metadata(stroke,1,p['radial_motor'],p['radial_motor_depth'],p['radial_body_extension_mm'])
    dt=58.2-p['rotor_drop_mm'];clamp=58.4
    # At the lowest Z pose, the radial body clears the 28 mm support gussets by 6 mm.
    hz=dt+38+20+6;zp=hz+direct_mount.LID_TOP
    minimum=zp+zm['end']+20
    if p['z_origin'] is None:p['z_origin']=minimum
    if p['z_origin']<minimum:raise ValueError('Inverted Z must keep the radial stage above the support gussets')
    zo=p['z_origin'];zp=zo-zm['end']-20;hz=zp-direct_mount.LID_TOP;face=zp
    hx=p['radial_motor_depth']/2-p['radial_setback_mm']
    pad=hx+rm['end']+stroke/2;tip=rmin+stroke/2
    assert tip-pad>=35,'Increase edge_to_pivot to leave a tapered probe extension'
    zm['CASE_TOP']=26 # Shared unchanged deck flange footprint.
    return dict(base_motor_x=base_drive_center(p),base_gear_ratio=p['ring_teeth']/p['pinion_teeth'],mounts=[(w/2+edge,0,180),(0,d/2+edge,-90),(-w/2-edge,0,0),(0,-d/2-edge,90)],
      rmin=rmin,rmax=rmin+stroke,radial_stroke=stroke,required_stroke=needed,h_origin=hx,horizontal_pad=pad-hx,zpad=zp,board_top=hz+21-p['probe_drop']-20,tip_radius=tip,probe_extension=tip-pad,
      horizontal_origin_y=0,horizontal_z=hz,probe_mount_z=hz+21,radial_mount_face_z=face,z_drive_y=0,r_drive_y=0,z_drive_x=0,r_drive_z=hz+42,lead_mm=8,
      actuator_enclosure='printed-leadscrew',rack_source_revision=16,minimum_z_origin=minimum,z_case_bottom=zo-zm['end'],z_rack_lowest=zp-20,deck_top_z=dt,base_clamp_top_z=clamp,z_deck_mounts=p['z_deck_mounts'],
      radial_motor_center_x_mm=-p['radial_setback_mm'],z_inverted=True,z_drive_rotation_sign=-1,z_controller_lowest_z_mm=zo+p['z_motor_depth'],base_revision='shared-rounded-blocks',z_actuator=zm,r_actuator=rm,yaw_required=math.degrees(math.atan2(max(w,d)/2,edge)))

def actuator_mount_patterns(axis,lay):
    widths=[1,2,4] if axis=='Z' else [1]
    strokes=[40] if axis=='Z' else sorted(set([40,lay['radial_stroke']]))
    extensions=[0,lay['r_actuator'].get('extension_mm',0)] if axis=='R' else [0]
    return [linear.patterns(w,stroke,variant,e)|dict(stroke=stroke) for e in sorted(set(extensions)) for stroke in strokes for w in widths for variant in ['printed','t8']]

def linear_contacts(parts,lay):
    result={}
    for axis in ['Z','R']:
        for q in lay['z_actuator' if axis=='Z' else 'r_actuator']['thread_joints']:
            result[frozenset([axis+'_'+q['host'].replace(' ','_'),axis+'_'+q['bolt'].replace(' ','_')])]='Upstream three-ridge self-forming pilot / fastener engagement'
    for a in parts:
        if a.get('thread_host'):result[frozenset([a['name'],a['thread_host']])]='External screw engages modeled receiving thread / pilot'
    result[frozenset(['Z_Controller_component_KEEPOUT','Z_USB_cable_KEEPOUT'])]='Overlapping nonphysical controller keepout volumes'
    return result

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
        seat=19 if i in [3,6] else 10
        screw=cyl(1.95,seat+6,(x,y,dt-6)).fuse(cyl(3.5,4,(x,y,dt+seat)))
        add(f'Z_cradle_deck_screw_{i}',screw,'theta','#a5b5c1',reference=True)
    # One mounting plane against the actuator's underside/base; no lid or side arms.
    zo=p['z_origin'];zm=lay['z_actuator'];rm=lay['r_actuator'];top=zo+9;wide=103
    side_foot=box(114,23.6,10,(0,-50.2,dt+5));feet=[box(26,104,10,(x,2,dt+5)) for x in [-39,39]]
    flanges=side_foot.fuse(*feet).intersect(cyl(80,10,(0,0,dt)))
    # All outer lands share Y=-62: lay this face on the bed. Reinforcement
    # projects inward only, retaining the actuator mounting datum at Y=-42.
    height=top-dt-10;mid=(top+dt+10)/2
    back=box(206,10,height,(0,-57,mid))
    ribs=[box(14,10,height,(x,-47,mid)) for x in [-96,96]]
    ribs += [box(206,10,12,(0,-47,zo+z)) for z in [3,-115,-149]]
    ribs += [box(206,10,14,(0,-47,dt+17))]
    ribs += [box(26,10,zo-143-dt-10,(x,-47,(zo-143+dt+10)/2)) for x in [-39,39]] # Solid backing for the entire corner root.
    # 28 mm x 28 mm internal 45-degree chamfer reinforces the loaded corner.
    corner=cq.Workplane('YZ',origin=(26,0,0)).polyline([(-42,dt+10),(-14,dt+10),(-42,dt+38)]).close().extrude(26).val()
    corners=[corner,corner.mirror('YZ')];support=union([flanges,back,*corners,*ribs])
    # Rounded through-windows leave broad edge rails and every mounting row.
    # The lower right opening stays clear of the solid corner reinforcement.
    windows=[(-89,89,zo-103,zo-9),(-89,-64,dt+24,zo-161),
             (-14,14,dt+24,zo-161),(64,89,dt+24,zo-161),(-89,89,zo-137,zo-127)]
    for x0,x1,z0,z1 in windows:
        cutter=cq.Workplane('XY').box(x1-x0,24,z1-z0).edges('|Y').fillet(4).translate(((x0+x1)/2,-52,(z0+z1)/2)).val()
        support=support.cut(cutter)
    support=holes(support,upright_mounts,2.2,dt-1,40)
    # Keep flange screw heads and their initial withdrawal corridors open.
    for i,(x,y) in enumerate(upright_mounts):support=support.cut(cyl(4.1,60,(x,y,dt+(19 if i in [3,6] else 10))))
    # Rear bolts exit through the flat back wall after 40 mm withdrawal.
    for x,y in upright_mounts[:3]:
        access=cq.Workplane('XY').box(8.2,12,26).edges('|Y').fillet(2).translate((x,-58,dt+45)).val()
        support=support.cut(access)
    patterns=actuator_mount_patterns('Z',lay)
    for x,y in set(tuple(q) for pat in patterns for q in pat['base']):
        support=support.cut(cyl(2.75,24,(-y,-65,zo-x),(0,1,0)),cyl(5.4,13,(-y,-65,zo-x),(0,1,0)))
    add('Z_support',support.clean(),'theta','#6d849c',True)
    parts[-1]['sweep_boxes']=[[[b.xmin,b.ymin,b.zmin],[b.xmax,b.ymax,b.zmax]] for b in [q.BoundingBox() for q in [side_foot,*feet,back,*corners,*ribs]]]
    def add_actuator(axis):
        meta=zm if axis=='Z' else rm
        data=direct_mount.parts(axis,meta,lay['h_origin'])
        for a in data:
            s=linear.home_shape(a,meta)
            if axis=='Z':s=s.rotate((0,0,0),(1,0,1),180).translate((-42,0,0)).rotate((0,0,0),(0,0,1),90).rotate((0,0,0),(0,1,0),180).translate((0,0,zo))
            else:s=s.translate((lay['h_origin'],0,lay['horizontal_z']))
            group=('z_rack' if axis=='Z' else 'r_rack') if a['group']=='carriage' else ('z_drive' if axis=='Z' else 'r_drive') if a['group']=='rotor' else ('theta' if axis=='Z' else 'z_rack')
            add(axis+'_'+a['name'].replace(' ','_'),s,group,a['color'],a['printed'],not a['printed'])
            parts[-1].update(actuator=axis,actuator_group=a['group'],explodeKind=a.get('explodeKind'))
    add_actuator('Z')
    # Rear Z controller matches the base controller's reference packaging dimensions.
    rear=zo-p['z_motor_depth'];pcb_top=rear-p['controller_spacer'];pcb_bottom=pcb_top-1.6
    def controller_part(name,shape,color,keepout=False):
        shape=shape.rotate((0,0,zo),(0,1,zo),180)
        add('Z_'+name,shape,'theta',color,reference=True,keepout=keepout);parts[-1]['actuator']='Z'
    controller_part('Rear_controller_PCB_REFERENCE',holes(box(42.3,42.32,1.6,(0,0,pcb_bottom+.8)),list(itertools.product([-15.5,15.5],repeat=2)),1.65,pcb_bottom-1,3.6),'#267c60')
    for i,(x,y) in enumerate(itertools.product([-15.5,15.5],repeat=2)):
        controller_part(f'Controller_spacer_{i}',annulus(3,1.65,p['controller_spacer'],pcb_top).translate((x,y,0)),'#ddd1aa')
    controller_part('Controller_component_KEEPOUT',box(42.3,42.32,p['controller_component_height'],(0,0,pcb_bottom-p['controller_component_height']/2)),'#70b598',True)
    controller_part('USB_cable_KEEPOUT',box(42.3,30,14,(0,36.16,pcb_bottom-5)),'#70b598',True)
    for i,(x,y) in enumerate(zm['base']):
        screw=cyl(2.45,30,(-y,-62,zo-x),(0,1,0)).fuse(cyl(4.25,5,(-y,-32,zo-x),(0,1,0)))
        add(f'Z_base_mount_screw_{i}',screw,'theta','#a5b5c1',reference=True)
        washer=cyl(5,2,(-y,-54,zo-x),(0,1,0)).cut(cyl(2.65,2,(-y,-54,zo-x),(0,1,0)))
        add(f'Z_base_mount_washer_{i}',washer,'theta','#a5b5c1',reference=True)
        nut=rotary_base.core.hexagon(8,4,0,0,0).cut(cyl(2.5,4)).rotate((0,0,0),(1,0,0),-90).translate((-y,-58,zo-x))
        add(f'Z_base_mount_nut_{i}',nut,'theta','#a5b5c1',reference=True)
    hx=lay['h_origin'];hz=lay['horizontal_z'];zp=lay['zpad'];end=rm['end']
    for i,(y,z) in enumerate(zm['output_holes']):
        x=-y;y=z-42
        screw=cyl(1.45,12,(x,y,zp-7.2)).fuse(cyl(2.75,3,(x,y,zp+4.8)))
        add(f'Z_output_mount_screw_{i}',screw,'z_rack','#a5b5c1',reference=True)
        parts[-1]['thread_host']='R_Structural_mounting_lid'
    add_actuator('R')
    padx=hx+end+lay['radial_stroke']/2;mountz=lay['probe_mount_z'];tipx=lay['tip_radius'];anchorx=tipx-p['probe_inward_lean']
    outline=[(padx,-21),(padx+6,-21),(anchorx+3,-3),(anchorx+3,3),(padx+6,21),(padx,21)]
    holder=cq.Workplane('XY').polyline(outline).close().extrude(6).translate((0,0,mountz-6)).val()
    holder=holder.fuse(box(6,42,42,(padx+3,0,hz+42))).clean()
    for y,z in rm['output_holes']:holder=holder.cut(cyl(1.7,8,(padx-1,y,hz+z),(1,0,0)))
    tip=V(tipx,0,mountz-p['probe_drop']);axis=V(-p['probe_inward_lean'],0,p['probe_drop']).normalized()
    holder=holder.cut(cq.Solid.makeCylinder(1.05,55,tip,axis)).cut(cyl(.8,4,(anchorx,-4,mountz-3),(0,1,0))).clean()
    add('Triangular_probe_outrigger',holder,'r_rack','#8a789e',True)
    for i,(y,z) in enumerate(rm['output_holes']):
        screw=cyl(1.45,12,(padx-6,y,hz+z),(1,0,0)).fuse(cyl(2.75,3,(padx+6,y,hz+z),(1,0,0)))
        add(f'Probe_output_mount_screw_{i}',screw,'r_rack','#a5b5c1',reference=True);parts[-1]['thread_host']='R_Hollow_triangular_carriage'
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
                s=s.rotate((0,0,p["z_origin"]),(0,0,p["z_origin"]+1),z*360/lay["lead_mm"])
            if g=="r_drive":
                s=s.rotate((lay['h_origin'],0,lay['r_drive_z']),(lay['h_origin']+1,0,lay['r_drive_z']),-r*360/lay['lead_mm'])
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
                      "Printed leadscrew: selectable Z width, upright 1x radial with custom 120 mm stroke and NEMA14 mount. Inferred T8 width patterns require checking against future variants.",
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
    allowed=base_contacts(parts,p)|linear_contacts(parts,lay)
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
            if a['name']=='Z_support':
                shape=shape.rotate((0,0,0),(1,0,0),90)
                b=shape.BoundingBox();shape=shape.translate((0,-(b.ymin+b.ymax)/2,-b.zmin))
            cq.exporters.export(shape,str(custom/(a['name']+'.stl')),tolerance=.025 if a.get('base_name') else .05,angularTolerance=.06 if a.get('base_name') else .12)
    for label,meta in [('Z',lay['z_actuator']),('R',lay['r_actuator'])]:
        for part in direct_mount.parts(label,meta,lay['h_origin']):
            if part['printed']:
                shape=linear.home_shape(part,meta,printing=True)
                shape=shape.translate((0,0,-shape.BoundingBox().zmin))
                cq.exporters.export(shape,str(custom/(label+'_'+part['name'].replace(' ','_')+'.stl')),tolerance=.025,angularTolerance=.12)
    print("Exported STEP assemblies and meshes to",out,flush=True)

if __name__=="__main__": main()
