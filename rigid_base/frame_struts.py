"""Flat-printing triangular front-frame struts sharing the outer support bolts."""
import cadquery as cq
from rotary_base.gear_geometry import box,cyl,annulus,union
from rotary_base import core

def layout(p,lay):
    return dict(xs=[-103,103],levels=[260,350],front_y=52.2,
                foot_bottom=p['deck_top_mm']+p['support_foot_thickness_mm'],
                foot_thickness=8,foot_y=91,top=lay['z_origin']+2.8)

def strut(p,lay,x):
    q=layout(p,lay);bottom=q['foot_bottom'];top=q['top'];fy=q['front_y']
    # A perforated triangular plate: vertical attachment rail, sloping outer
    # chord, and bottom tie. All material stays within one 12 mm extrusion.
    profile=[(fy,bottom),(100,bottom),(100,bottom+8),(88,bottom+8),(62.2,top),(fy,top)]
    s=cq.Workplane('YZ',origin=(x-6,0,0)).polyline(profile).close().extrude(12).val()
    window=cq.Workplane('YZ',origin=(x-7,0,0)).polyline([(62.2,bottom+20),(77,bottom+20),(62.2,top-112)]).close().extrude(14).val()
    s=s.cut(window)
    for z in q['levels']:
        s=s.fuse(box(12,16,20,(x,60.2,z)))
        s=s.cut(cyl(2.2,65,(x,47,z),(0,1,0)),cyl(4.1,45,(x,68.2,z),(0,1,0)))
    # Existing M4 deck insert reused. Clear the diagonal above the bolt seat.
    s=s.cut(cyl(2.2,10,(x,91,bottom-1)),cyl(4.1,340,(x,91,bottom+8)))
    return s.clean()

def frame_finish(s,p,lay):
    q=layout(p,lay)
    for x in q['xs']:
        for z in q['levels']:s=s.cut(cyl(2.2,8,(x,46,z),(0,1,0)))
    return s.clean()

def hardware(p,lay):
    q=layout(p,lay);out=[]
    for side,x in zip(['left','right'],q['xs']):
        for i,z in enumerate(q['levels']):
            bolt=cyl(1.95,25,(x,43.2,z),(0,1,0)).fuse(cyl(3.5,4,(x,68.2,z),(0,1,0)))
            washer=annulus(4.5,2.1,.8,0).rotate((0,0,0),(1,0,0),-90).translate((x,47.2,z))
            nut=core.hexagon(7,3.2,0,0,0).cut(cyl(2,3.2,(0,0,0))).rotate((0,0,0),(1,0,0),-90).translate((x,44,z))
            for n,s in [('M4x25_frame_strut',bolt),('M4_frame_strut_washer',washer),('M4_frame_strut_nut',nut)]:out.append((f'{n}_{side}_{i}',s))
    return out
