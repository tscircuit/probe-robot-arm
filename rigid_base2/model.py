import hashlib,json,pathlib,math
import cadquery as cq
from rigid_base import model as parent
from rigid_base.model import ROOT,parameters,profiles,box,cyl,annulus,union,holes,polar,overlap,V

def cage(p,lay):
    dt=p['deck_top_mm'];bottom=dt+6;top=lay['z_origin']+9;grid_bottom=lay['z_origin']-145
    s=annulus(148,143,top-bottom,bottom)
    for angle in range(0,360,30):
        pts=[polar(r,math.radians(a)) for r,a in [(130,angle-11),(165,angle-11),(165,angle+11),(130,angle+11)]]
        for lo,hi in [(76,210),(230,364)]:
            cut=cq.Workplane('XY').polyline(pts).close().extrude(hi-lo).edges('|Z').fillet(3).val().translate((0,0,lo))
            s=s.cut(cut)
    s=s.fuse(annulus(148,136,6,224),annulus(148,136,6,top-6))
    # Wide side ports clear the radial housing and motor through all Z travel.
    for x in [-150,150]:s=s.cut(box(110,96,144,(x,0,158)))
    foot=parent.linked_foot(p,dt,6).fuse(annulus(148,132,6,dt),box(206,20,6,(0,-45,dt+3)))
    plate=box(296,6,top-grid_bottom,(0,-45,(top+grid_bottom)/2)).intersect(cyl(148,top-grid_bottom,(0,0,grid_bottom)))
    uprights=[box(12,6,grid_bottom-bottom,(x,-45,(bottom+grid_bottom)/2)) for x in [-96,96]]
    # A 45-degree arch supports the thin grid's first layers while leaving a
    # large opening below it; this is integral to the mounting face.
    for sign in [-1,1]:
        uprights.append(cq.Workplane('XZ',origin=(0,-42,0)).polyline([(0,grid_bottom),(sign*102,grid_bottom-102),(sign*102,grid_bottom)]).close().extrude(6).val())
    s=union([s,foot,plate]+uprights)
    for a in lay['z_actuator']['grid_x']:
        for b in lay['z_actuator']['grid_y']:s=s.cut(cyl(1.7,8,(-b,-49,lay['z_origin']-a),(0,1,0)))
    for x,y in p['support_mounts_mm']+[[0,-138]]:
        s=s.cut(cyl(2.2,8,(x,y,dt-1)),cyl(4.1,30,(x,y,dt+6)))
    for i in range(6):
        x,y=polar(140,math.radians(p['ring_bolt_phase_deg']+60*i));s=s.cut(cyl(5.5,30,(x,y,dt-1)))
    return s.clean()

def build(p=None):
    p=p or parameters();base,info=parent.build(p)
    key=hashlib.sha256(b''.join((ROOT/n).read_bytes() for n in ['rigid_base2/model.py','rigid_base/model.py','rigid_base/front_frame.py','rigid_base/frame_struts.py','rigid_base/parameters.json'])).hexdigest()[:20]
    cache=ROOT/'cache'/('rigid2-'+key)
    if (cache/'complete').exists():
        parts=json.loads((cache/'parts.json').read_text())
        for i,a in enumerate(parts):a['shape']=cq.Shape.importBrep(str(cache/f'{i}.brep'))
        return parts,info
    parts=[]
    for a in base:
        n=a['name']
        if n in ['Boxed_Z_support','Front_Z_frame','Center_front_strut','Center_rear_strut'] or 'front_frame' in n or 'center_strut' in n or n=='M4x16_rear_strut_foot':continue
        a=dict(a)
        if n=='M4_rear_strut_deck_insert':a['name']='M4_cage_rear_deck_insert'
        if n.startswith('Z_support_deck_screw_'):
            i=int(n.rsplit('_',1)[1]);x,y=p['support_mounts_mm'][i];dt=p['deck_top_mm']
            a['shape']=cyl(1.95,12,(x,y,dt-6)).fuse(cyl(3.5,4,(x,y,dt+6)))
        parts.append(a)
    lay=info['arm_layout']|dict(z_origin=info['arm_parameters']['z_origin']+info['arm_z_shift_mm'])
    def add(name,s,printed=False,color='#71879a'):
        assert s.isValid() and len(s.Solids())==1,name
        parts.append(dict(name=name,shape=s,group='rotor',printed=printed,reference=not printed,keepout=False,context=True,source_name=None,color=color,flip=False))
    add('Cylindrical_Z_support',cage(p,lay),True,'#577eae')
    dt=p['deck_top_mm'];add('M4x12_cage_rear_foot',cyl(1.95,12,(0,-138,dt-6)).fuse(cyl(3.5,4,(0,-138,dt+6))))
    cache.mkdir(parents=True,exist_ok=True)
    for i,a in enumerate(parts):a['shape'].exportBrep(str(cache/f'{i}.brep'))
    (cache/'parts.json').write_text(json.dumps([{k:v for k,v in a.items() if k not in ['shape','freeShape']} for a in parts]));(cache/'complete').write_text('1')
    return parts,info

if __name__=='__main__':
    parts,info=build();parent.export(parts,info,ROOT/'output/rigid-base2')
