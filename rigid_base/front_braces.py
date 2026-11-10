"""Mirrored front trusses, using the fixed Z lid's existing 31 mm insert grid."""
import cadquery as cq
from rotary_base.gear_geometry import box,cyl,annulus
from rotary_base import core

def layout(p,lay):
    return dict(xs=[-46.5,46.5],thickness=12,face_y=26,seat_y=43,bottom=p['deck_top_mm']+10,levels=[lay['z_origin']-x for x in [10.5,41.5,72.5]],foot_ys=[98,130],key_y=114,key_length=18)

def brace(p,lay,x):
    q=layout(p,lay);z=q['bottom'];t=q['thickness'];top=q['levels'][0]+14;low=q['levels'][-1]-10
    # The lower edge rises out of the radial stage's entire travel envelope.
    # Both deck bolts sit on ears outside the diagonal members, leaving tool access.
    wp=cq.Workplane('YZ',origin=(x-t/2,0,0)).polyline([(26,low),(26,top),(43,top),(122,z+18),(106,z+18)]).close()
    wire=wp.val();s=wp.extrude(t).val()
    for opening in wire.offset2D(-10,'arc'):
        cut=cq.Solid.extrudeLinear(opening,[],cq.Vector(t+2,0,0)).translate((-1,0,0))
        cut=cq.Workplane(obj=cut).edges('|X').fillet(2).val();s=s.cut(cut)
    s=s.fuse(box(t,17,top-low,(x,34.5,(top+low)/2)),box(t,48,18,(x,114,z+9)))
    key=cq.Workplane('XY').box(t,18,2).edges('|Z').fillet(.8).translate((x,114,z-1)).val();s=s.fuse(key)
    for level in q['levels']:s=s.cut(cyl(1.7,19,(x,25,level),(0,1,0)),cyl(3.4,30,(x,43,level),(0,1,0)))
    for y in q['foot_ys']:s=s.cut(cyl(2.2,22,(x,y,z-3)))
    return s.clean()

def support_finish(s,p,lay):
    q=layout(p,lay);z=q['bottom']
    for x in q['xs']:
        slot=cq.Workplane('XY').box(12.4,18.4,2.3).edges('|Z').fillet(1).translate((x,114,z-1.05)).val()
        s=s.cut(slot)
        for y in q['foot_ys']:s=s.cut(cyl(2.2,14,(x,y,z-11)))
    return s.clean()

def deck_finish(s,p,lay):
    for x in layout(p,lay)['xs']:
        for y in layout(p,lay)['foot_ys']:s=s.cut(cyl(2.2,12,(x,y,p['deck_top_mm']-9)))
    return s.clean()

def hardware(p,lay):
    q=layout(p,lay);rows=[];z=q['bottom']
    for side,x in zip(['left','right'],q['xs']):
        for i,level in enumerate(q['levels']):
            # 17 mm printed clamping thickness + 3 mm entry into the 4 mm insert.
            screw=cyl(1.45,20,(x,23,level),(0,1,0)).fuse(cyl(2.75,3,(x,43,level),(0,1,0)))
            rows.append((f'M3x20_front_brace_lid_{side}_{i}',screw))
        for i,y in enumerate(q['foot_ys']):
            screw=cyl(1.95,40,(x,y,z-22)).fuse(cyl(3.5,4,(x,y,z+18)))
            washer=annulus(4.5,2.15,.8,z-18.8).translate((x,y,0))
            nut=core.hexagon(7,3.2,x,y,z-22).cut(cyl(2.1,4,(x,y,z-22.2)))
            rows.extend([(f'M4x40_front_brace_foot_{side}_{i}',screw),(f'M4_front_brace_foot_washer_{side}_{i}',washer),(f'M4_front_brace_foot_nut_{side}_{i}',nut)])
    return rows
