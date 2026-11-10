"""Closed, split printed backbone experiment. Millimetres; independent of rigid_base."""
import hashlib,json,pathlib
import cadquery as cq
from rigid_base import model as baseline
from rigid_base.explosion import timeline
from rotary_base import core
from rotary_base.gear_geometry import box,cyl,annulus,holes,union,polar
ROOT=baseline.ROOT
OUT=ROOT/'output/hollow-base'
# Wide front mounting face, 45-degree sides and narrow rear face.
OUTLINE=[(-103,-42),(103,-42),(43,-102),(-43,-102)]
WALL=3.;SEAM=-72.;BOTTOM=56.2;TOP=380.2
LEVELS=[88.,173.,258.,363.]

def prism(inset,z,h):
    wire=cq.Workplane('XY').polyline(OUTLINE).close().val()
    if inset:wire=wire.offset2D(-inset,'intersection')[0]
    return cq.Solid.extrudeLinear(wire,[],cq.Vector(0,0,h)).translate((0,0,z))
def band(outer,inner,z,h):return prism(outer,z,h).cut(prism(inner,z-1,h+2))
def half(s,front):return s.intersect(box(400,300,500,(0,SEAM+(150 if front else -150),250)))
def yhole(r,length,x,y,z):return cyl(r,length,(x,y,z),(0,1,0))
def washer(x,y,z):return annulus(4.5,2.15,.8,0).rotate((0,0,0),(1,0,0),-90).translate((x,y,z))
def nut(x,y,z):return core.hexagon(7,3.2,0,0,0).cut(cyl(2.1,4,(0,0,-.1))).rotate((0,0,0),(1,0,0),-90).translate((x,y,z))

def structure(info):
    zo=info['arm_parameters']['z_origin']+info['arm_z_shift_mm'];meta=info['arm_layout']['z_actuator']
    shell=band(0,WALL,BOTTOM,TOP-BOTTOM)
    # A shallow floor above the socket and a top cap; sparse transverse diaphragms.
    for z in [70.2,TOP-3]+[q-1.5 for q in LEVELS]:shell=shell.fuse(prism(0,z,3))
    front=half(shell,True);back=half(shell,False)
    # Continuous side keys, separated from the back tray by 0.2 mm clearance.
    tongue=band(.8,2.2,70.2,TOP-73.2).intersect(box(400,2,500,(0,-73,250)))
    pocket=band(.6,2.4,70,TOP-72.8).intersect(box(400,2.2,500,(0,-73.1,250)))
    front=front.fuse(tongue);back=back.cut(pocket)
    hardware=[]
    for i,z in enumerate(LEVELS):
        for sign in [-1,1]:
            x=sign*60
            front=front.fuse(yhole(6,9,x,-72,z))
            back=back.fuse(yhole(6,15.8,x,-88,z))
            bore=yhole(2.2,40,x,-95,z)
            pocket=core.hexagon(7.3,3.5,0,0,0).rotate((0,0,0),(1,0,0),-90).translate((x,-66.4,z))
            front=front.cut(bore,pocket,yhole(5,12,x,-63,z));back=back.cut(bore,yhole(4,20,x,-108,z))
            hardware.extend([(f'M4x25_shell_seam_{i}_{sign}',yhole(1.95,25,x,-88,z).fuse(yhole(3.5,4,x,-92,z))),(f'M4_shell_seam_nut_{i}_{sign}',nut(x,-66.2,z))])
    # All 31 mm grid positions are retained, with short bolts into the existing base.
    for gx in meta['grid_x']:
        for gy in meta['grid_y']:
            x,z=-gy,zo-gx
            front=front.fuse(yhole(5,6,x,-48,z)).cut(yhole(1.7,8,x,-49,z))
    for i,(gx,gy) in enumerate(meta['base_fasteners']):
        front=front.cut(yhole(3.3,10,-gy,-58,zo-gx))
        hardware.append((f'M3x10_backbone_actuator_{i}',yhole(1.45,10,-gy,-48,zo-gx).fuse(yhole(2.75,3,-gy,-51,zo-gx))))
    deck=annulus(112,14.6,8,48.2).fuse(band(3.3,8.3,BOTTOM,12))
    ringbolts=[polar(104,__import__('math').radians(30+60*i)) for i in range(6)]
    deck=holes(deck,core.rotor_bolts()+ringbolts,1.7,47.2,25)
    for x,y in core.rotor_bolts():deck=deck.cut(core.hexagon(5.8,2.5,x,y,53.8))
    # Small windows only in the unused front half; no undercut underside bosses.
    for x,y in [(-60,20),(60,20),(-60,50),(60,50),(-30,65),(30,65),(0,85)]:deck=deck.cut(cyl(9,10,(x,y,47.2)))
    # Tool wells preserve access to the existing six ring screws.
    for x,y in ringbolts:
        well=cyl(5.5,22,(x,y,BOTTOM))
        deck=deck.cut(well);front=front.cut(well);back=back.cut(well)
    # Four ordinary transverse bolts clamp the shell over the male deck socket.
    for side,xs in [('front',[-60,60]),('rear',[-25,25])]:
        for x in xs:
            z=62.2;bore=yhole(2.2,80,x,-110,z)
            deck=deck.cut(bore);front=front.cut(bore);back=back.cut(bore)
            if side=='front':
                screw=yhole(1.95,20,x,-62,z).fuse(yhole(3.5,4,x,-42,z));w=washer(x,-51.1,z);n=nut(x,-54.3,z)
            else:
                screw=yhole(1.95,20,x,-102,z).fuse(yhole(3.5,4,x,-106,z));w=washer(x,-93.7,z);n=nut(x,-92.9,z)
            hardware.extend([(f'M4x20_socket_{side}_{x}',screw),(f'M4_socket_washer_{side}_{x}',w),(f'M4_socket_nut_{side}_{x}',n)])
    return [('Backbone_front_tray',front.clean()),('Backbone_rear_tray',back.clean()),('Socket_rotating_deck',deck.clean())],hardware

def build():
    original,info=baseline.build()
    skip=['Boxed_Z_support','Rigid_rotating_deck']
    prefixes=('Printed_rear_brace_','M4_deck_insert_','Z_support_deck_screw_','M3x40_Z_base_mount_','M4x35_brace_','M4x60_brace_','M4_brace_')
    parts=[a.copy() for a in original if a['name'] not in skip and not a['name'].startswith(prefixes)]
    key=hashlib.sha256(pathlib.Path(__file__).read_bytes()+json.dumps(info,sort_keys=True).encode()).hexdigest()[:20]
    cache=ROOT/'cache'/('hollow-'+key)
    if (cache/'complete').exists():
        added=json.loads((cache/'parts.json').read_text())
        for i,a in enumerate(added):a['shape']=cq.Shape.importBrep(str(cache/f'{i}.brep'))
    else:
        printed,hardware=structure(info);added=[]
        for name,s in printed+hardware:
            isp=name in [n for n,_ in printed]
            assert s.isValid() and len(s.Solids())==1,(name,s.isValid(),len(s.Solids()))
            added.append(dict(name=name,shape=s,group='rotor',printed=isp,color=('#73988f' if name=='Backbone_rear_tray' else '#6d849c') if isp else '#c1c9d0',reference=not isp,keepout=False,context=name!='Socket_rotating_deck',flip=False,source_name=None))
        cache.mkdir(exist_ok=True)
        for i,a in enumerate(added):a['shape'].exportBrep(str(cache/f'{i}.brep'))
        (cache/'parts.json').write_text(json.dumps([{k:v for k,v in a.items() if k!='shape'} for a in added]));(cache/'complete').write_text('1')
    return parts+added,info

def print_shape(a):
    s=a['shape']
    if a['name']=='Backbone_front_tray':s=s.rotate((0,0,0),(1,0,0),-90)
    elif a['name']=='Backbone_rear_tray':s=s.rotate((0,0,0),(1,0,0),90)
    b=s.BoundingBox();return s.translate((-b.xmin,-b.ymin,-b.zmin))

def export():
    parts,info=build();original,_=baseline.build();old={a['name']:a for a in original};OUT.mkdir(exist_ok=True);(OUT/'STL').mkdir(exist_ok=True)
    added=[a for a in parts if a['name'] not in old];manifest=[];meshes=[]
    for a in added:
        s=a['shape'];vs,ts=s.tessellate(.18,.2)
        meshes.append({k:v for k,v in a.items() if k!='shape'}|dict(vertices=[[round(x,4) for x in v.toTuple()] for v in vs],triangles=ts))
        if a['printed']:
            ps=print_shape(a);file=OUT/'STL'/(a['name']+'.stl');cq.exporters.export(ps,str(file),tolerance=.025,angularTolerance=.09)
            import trimesh
            m=trimesh.load_mesh(file);m.apply_translation([0,0,-m.bounds[0,2]]);m.export(file)
            manifest.append(dict(name=a['name'],file='STL/'+file.name,volume_mm3=s.Volume(),size_mm=m.extents.tolist(),sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
    delta=dict(remove=[n for n in old if n not in {a['name'] for a in parts}],add=meshes)
    (OUT/'delta.json').write_text(json.dumps(delta,separators=(',',':')))
    (OUT/'print-manifest.json').write_text(json.dumps(manifest,indent=2))
    (OUT/'explosion.json').write_text(json.dumps(timeline(parts)))
    (OUT/'config.json').write_text(json.dumps(baseline.parameters()|dict(center_mm=info['center_mm'],ratio=info['ratio'])))
    # STEP contains the replacement structure, preserving shared actuator exports.
    assy=cq.Assembly(name='Hollow_backbone_replacement_structure')
    for a in added:assy.add(a['shape'],name=a['name'],color=cq.Color(a['color']))
    assy.save(str(OUT/'backbone-structure.step'))
    print('Exported',len(parts),'assembly parts;',len(manifest),'replacement prints',flush=True)
if __name__=='__main__':export()
