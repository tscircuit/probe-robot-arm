"""Flat-printable rear trusses; only ordinary fastening hardware is metallic."""
import cadquery as cq
from rotary_base.gear_geometry import box,cyl,union,annulus
from rotary_base import core

def layout(p,lay):
    return dict(xs=[-p['brace_half_spacing_mm'],p['brace_half_spacing_mm']],bottom=p['deck_top_mm'],back=-84,heel=p['brace_heel_y_mm'],top=lay['z_origin']-10.5+14,levels=[p['deck_top_mm']+24,lay['z_origin']-134.5,lay['z_origin']-10.5],foot_ys=p['brace_foot_ys_mm'],key_y=p['brace_key_y_mm'],key_length=p['brace_key_length_mm'],rear=p['brace_deck_rear_mm'],web_inner=p['brace_web_inner_y_mm'],thickness=p['brace_thickness_mm'])

def brace(p,lay,x):
    q=layout(p,lay);z=q['bottom'];t=q['thickness'];h=q['top']-z
    wp=cq.Workplane('YZ',origin=(x-t/2,0,0)).polyline([(q['heel'],z),(-84,z),(-84,q['top'])]).close()
    wire=wp.val();triangle=wp.extrude(t).val()
    s=triangle.fuse(box(t,24,h,(x,-96,z+h/2)))
    for w in wire.offset2D(-18,'arc'):
        cut=cq.Solid.extrudeLinear(w,[],cq.Vector(t+2,0,0)).translate((-1,0,0))
        cut=cut.intersect(box(400,400,500,(0,-308,250)))
        cut=cq.Workplane(obj=cut).edges('|X').fillet(3).val()
        s=s.cut(cut)
    s=s.fuse(triangle.intersect(box(t+2,220,16,(x,-160,q['levels'][1]))))
    s=s.fuse(cyl(5.5,24,(x,-132,q['levels'][1]),(0,1,0)))
    key=cq.Workplane('XY').box(t,q['key_length'],2).edges('|Z').fillet(.8).translate((x,q['key_y'],z-1)).val();s=s.fuse(key)
    for i,level in enumerate(q['levels']):
        seat=-132 if i==1 else -108
        s=s.cut(cyl(2.2,-83-seat+1,(x,seat-1,level),(0,1,0)),cyl(4,8,(x,seat-8,level),(0,1,0)))
    for y in q['foot_ys']:s=s.cut(cyl(2.2,22,(x,y,z-3)))
    return s.clean()

def deck_extension(deck,p,lay):
    q=layout(p,lay);z=q['bottom']
    for x in q['xs']:
        rail=cq.Workplane('XY').box(24,q['rear']-60,8).edges('|Z').fillet(3).translate((x,(-q['rear']-60)/2,z-4)).val()
        deck=deck.fuse(rail)
        # Two thin webs make the outrigger deeper without a solid thick beam.
        # Keep both webs outside the ring and beside the foot fasteners.
        for dx in [-8,8]:deck=deck.fuse(box(2.5,q['rear']+q['web_inner'],14,(x+dx,(-q['rear']+q['web_inner'])/2,z-15)))
    deck=deck.fuse(cq.Workplane('XY').box(2*p['brace_half_spacing_mm']+24,20,8).edges('|Z').fillet(3).translate((0,10-q['rear'],z-4)).val())
    for x in q['xs']:
        slot=cq.Workplane('XY').box(q['thickness']+.4,q['key_length']+.4,2.3).edges('|Z').fillet(1).translate((x,q['key_y'],z-1.05)).val()
        deck=deck.cut(slot)
        for y in q['foot_ys']:deck=deck.cut(cyl(2.2,10,(x,y,z-9)))
    # The new rear rails must retain all original open insert sockets.
    for x,y in p['support_mounts_mm']:deck=deck.cut(cyl(2.8,16,(x,y,43.2)))
    return deck.clean()

def hardware(p,lay):
    q=layout(p,lay);rows=[]
    for side,x in zip(['left','right'],q['xs']):
        for i,z in enumerate(q['levels']):
            seat=-132 if i==1 else -108;length=60 if i==1 else 35
            screw=cyl(1.95,length,(x,seat,z),(0,1,0)).fuse(cyl(3.5,4,(x,seat-4,z),(0,1,0)))
            washer=annulus(4.5,2.15,.8,0).rotate((0,0,0),(1,0,0),-90).translate((x,-78,z))
            nut=core.hexagon(7,3.2,0,0,0).cut(cyl(2.1,4,(0,0,-.1))).rotate((0,0,0),(1,0,0),-90).translate((x,-77.2,z))
            rows.extend([(f'M4x{length}_brace_tower_{side}_{i}',screw),(f'M4_brace_tower_washer_{side}_{i}',washer),(f'M4_brace_tower_nut_{side}_{i}',nut)])
        for i,y in enumerate(q['foot_ys']):
            z=q['bottom'];screw=cyl(1.95,35,(x,y,z-17)).fuse(cyl(3.5,4,(x,y,z+18)))
            washer=annulus(4.5,2.15,.8,z-8.8).translate((x,y,0));nut=core.hexagon(7,3.2,x,y,z-12).cut(cyl(2.1,4,(x,y,z-12.2)))
            rows.extend([(f'M4x35_brace_foot_{side}_{i}',screw),(f'M4_brace_foot_washer_{side}_{i}',washer),(f'M4_brace_foot_nut_{side}_{i}',nut)])
    return rows
