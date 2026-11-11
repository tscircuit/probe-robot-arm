import hashlib,json,pathlib,math
import cadquery as cq
from rigid_base import model as parent
from rigid_base.model import ROOT,parameters,profiles,box,cyl,annulus,union,holes,polar,overlap,V

def cage(p,lay):
    dt=p['deck_top_mm'];bottom=dt+6;top=lay['z_origin']+9;grid_bottom=lay['z_origin']-145
    s=annulus(148,143,top-bottom,bottom)
    def peaked_window(radial_start,depth,half_width,lo,hi,angle):
        w=half_width
        cut=cq.Workplane('YZ',origin=(radial_start,0,0)).polyline([(-w,lo),(w,lo),(w,hi-w),(0,hi),(-w,hi-w)]).close().extrude(depth).val()
        return cut.rotate((0,0,0),(0,0,1),angle)
    # Seven mm radial flange growth over seven mm rise: a 45-degree underside.
    for z in [224,top-6]:
        ramp=cyl(148,7,(0,0,z-7)).cut(cq.Solid.makeCone(143,136,7,V(0,0,z-7),V(0,0,1)))
        s=s.fuse(annulus(148,136,6,z),ramp)
    # Omit the four columns formerly clipped to slivers by the radial ports.
    for angle in [60,90,120,240,270,300]:
        for lo,hi in [(76,210),(230,364)]:s=s.cut(peaked_window(120,50,27,lo,hi,angle))
    for angle in [0,180]:s=s.cut(peaked_window(95,75,90,76,364,angle))
    foot=parent.linked_foot(p,dt,6).fuse(annulus(148,132,6,dt),box(206,20,6,(0,-45,dt+3)))
    plate=box(206,6,top-grid_bottom,(0,-45,(top+grid_bottom)/2))
    uprights=[box(12,6,grid_bottom-bottom,(x,-45,(bottom+grid_bottom)/2)) for x in [-96,96]]
    for sign in [-1,1]:
        uprights.append(cq.Workplane('XZ',origin=(0,-42,0)).polyline([(0,grid_bottom),(sign*102,grid_bottom-102),(sign*102,grid_bottom)]).close().extrude(6).val())
    # Broad full-height shear webs join the grid directly to the rear columns.
    # Windows leave 12 mm flanges and 45-degree roofs, without a floating shelf.
    for sign in [-1,1]:
        angle=-sign*math.degrees(math.atan2(24,92))
        def place(part):return part.rotate((0,0,0),(0,0,1),angle).translate((sign*62,-48,0))
        web=box(6,102,top-bottom,(0,-49,(top+bottom)/2))
        for lo,hi in [(82,204),(244,360)]:
            web=web.cut(cq.Workplane('YZ',origin=(-4,0,0)).polyline([(-82,lo),(-12,lo),(-12,hi-35),(-47,hi),(-82,hi-35)]).close().extrude(8).val())
        uprights.append(place(web).intersect(cyl(148,top-bottom,(0,0,bottom))))
        foot=foot.fuse(place(box(16,102,6,(0,-49,dt+3))).intersect(cyl(148,6,(0,0,dt))))
    # Transverse rear diaphragm transfers lateral shear between both rear webs
    # and the cylindrical wall. Peaked apertures keep the upright print open.
    rear=box(220,6,top-bottom,(0,-104,(top+bottom)/2))
    for x in [-46,46]:
        for lo,hi in [(82,204),(244,360)]:
            cut=cq.Workplane('XZ',origin=(x,-100,0)).polyline([(-31,lo),(31,lo),(31,hi-31),(0,hi),(-31,hi-31)]).close().extrude(8).val()
            rear=rear.cut(cut)
    uprights.append(rear.intersect(cyl(148,top-bottom,(0,0,bottom))))
    foot=foot.fuse(box(220,16,6,(0,-104,dt+3)).intersect(cyl(148,6,(0,0,dt))))
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
