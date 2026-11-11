"""Centered front and rear struts, printed flat on their broad sides."""
import cadquery as cq
from rotary_base.gear_geometry import box,cyl,annulus
from rotary_base import core

def layout(p,lay):
    return {
        'front':dict(sign=1,face=52.2,levels=[260,350],head=88.2,
                     bottom=p['deck_top_mm']+p['support_foot_thickness_mm'],
                     chord=126,top=lay['z_origin']+2.8,wall=4),
        'rear':dict(sign=-1,face=84.2,levels=[lay['z_origin']-134.5,lay['z_origin']-10.5],head=116.2,
                    bottom=p['deck_top_mm'],chord=130,top=lay['z_origin']+2.8,wall=6)}

def orient(s,q):return s if q['sign']==1 else s.mirror('XZ')

def strut(p,lay,side):
    q=layout(p,lay)[side];b=q['bottom'];t=q['top'];f=q['face'];c=q['chord']
    profile=[(f,b),(p['deck_radius_mm'],b),(p['deck_radius_mm'],b+8),(c,b+8),(f+10,t),(f,t)]
    s=cq.Workplane('YZ',origin=(-6,0,0)).polyline(profile).close().extrude(12).val()
    opening=[(f+8,b+20),(c-10,b+20),(f+8,t-90)]
    s=s.cut(cq.Workplane('YZ',origin=(-7,0,0)).polyline(opening).close().extrude(14).val())
    for z in q['levels']:
        s=s.fuse(box(12,q['head']-f,20,(0,(q['head']+f)/2,z)))
        s=s.cut(cyl(2.2,100,(0,f-5,z),(0,1,0)),cyl(4.1,60,(0,q['head'],z),(0,1,0)))
    s=s.cut(cyl(2.2,10,(0,p['strut_bolt_radius_mm'],b-1)),cyl(4.1,340,(0,p['strut_bolt_radius_mm'],b+8)))
    return orient(s.intersect(cyl(p['deck_radius_mm'],400,(0,0,0))).clean(),q)

def frame_finish(s,p,lay):
    for z in layout(p,lay)['front']['levels']:s=s.cut(cyl(2.2,8,(0,46,z),(0,1,0)))
    return s.clean()

def support_finish(s,p,lay):
    for z in layout(p,lay)['rear']['levels']:s=s.cut(cyl(2.2,8,(0,-85,z),(0,1,0)))
    return s.clean()

def deck_finish(s,p):
    # The rear center spoke is already solid; retain a fully open insert bore.
    return s.cut(cyl(2.8,10,(0,-p['strut_bolt_radius_mm'],p['deck_top_mm']-9))).clean()

def hardware(p,lay):
    out=[]
    for side,q in layout(p,lay).items():
        inside=q['face']-.2-q['wall']
        for i,z in enumerate(q['levels']):
            bolt=cyl(1.95,50,(0,q['head']-50,z),(0,1,0)).fuse(cyl(3.5,4,(0,q['head'],z),(0,1,0)))
            washer=annulus(4.5,2.1,.8,0).rotate((0,0,0),(1,0,0),-90).translate((0,inside-.8,z))
            nut=core.hexagon(7,3.2,0,0,0).cut(cyl(2,3.2,(0,0,0))).rotate((0,0,0),(1,0,0),-90).translate((0,inside-4,z))
            for n,s in [('M4x50_center_strut',bolt),('M4_center_strut_washer',washer),('M4_center_strut_nut',nut)]:out.append((f'{n}_{side}_{i}',orient(s,q)))
    dt=p['deck_top_mm']
    out.append(('M4_rear_strut_deck_insert',annulus(3,2,6,dt-6.3).translate((0,-p['strut_bolt_radius_mm'],0))))
    out.append(('M4x16_rear_strut_foot',cyl(1.95,16,(0,-p['strut_bolt_radius_mm'],dt-8)).fuse(cyl(3.5,4,(0,-p['strut_bolt_radius_mm'],dt+8)))))
    return out
