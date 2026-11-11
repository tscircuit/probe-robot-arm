"""Perforated front shell, attached to the stationary Z support's two sides."""
import math
import cadquery as cq
from rotary_base.gear_geometry import box,cyl,annulus,union
from rotary_base import core

def layout(p,lay):
    return dict(bottom=p['deck_top_mm']+10,top=lay['z_origin']+9,
                levels=[80,174,270,364],mount_y=-60,inner_x=108.2,outer_x=112.2,
                back_y=-70,front_y=52)

def blank(p,lay):
    q=layout(p,lay);h=q['top']-q['bottom'];mid=(q['top']+q['bottom'])/2
    return union([box(224.4,4,h,(0,50,mid))]+[box(4,122,h,(x,-9,mid)) for x in [-110.2,110.2]])

def frame(p,lay):
    q=layout(p,lay);s=blank(p,lay)
    # One diagonal ties the perforated front panel into a shear web.
    dx,dz=196,278;angle=-math.degrees(math.atan2(dz,dx))
    web=box(math.hypot(dx,dz),8,12,(0,50,223)).rotate((0,50,223),(0,51,223),angle)
    for x0,x1 in [(-98,-8),(8,98)]:
        for z0,z1 in [(84,206),(222,362)]:
            cut=cq.Workplane('XY').box(x1-x0,8,z1-z0).edges('|Y').fillet(5).translate(((x0+x1)/2,50,(z0+z1)/2)).val()
            s=s.cut(cut.cut(web))
    for x in [-110.2,110.2]:
        for y0,y1,z0,z1 in [(-46,44,90,226),(-42,42,242,360)]:
            cut=cq.Workplane('XY').box(8,y1-y0,z1-z0).edges('|X').fillet(5).translate((x,(y0+y1)/2,(z0+z1)/2)).val()
            s=s.cut(cut)
        for low,high in zip(q['levels'],q['levels'][1:]):
            cut=cq.Workplane('XY').box(8,10,high-low-28).edges('|X').fillet(4).translate((x,-60,(low+high)/2)).val()
            s=s.cut(cut)
    for z in q['levels']:s=s.cut(cyl(2.2,240,(-120,q['mount_y'],z),(1,0,0)))
    return s.clean()

def support_finish(s,p,lay):
    q=layout(p,lay)
    for x in [-102,102]:
        for z in q['levels']:s=s.fuse(box(12,22,20,(x,-59,z)))
    for z in q['levels']:s=s.cut(cyl(2.2,240,(-120,q['mount_y'],z),(1,0,0)))
    return s.clean()

def hardware(p,lay):
    q=layout(p,lay);out=[]
    for side in ['left','right']:
        for i,z in enumerate(q['levels']):
            bolt=cyl(1.95,25,(87.2,-60,z),(1,0,0)).fuse(cyl(3.5,4,(112.2,-60,z),(1,0,0)))
            washer=annulus(4.5,2.1,.8,0).rotate((0,0,0),(0,1,0),90).translate((95.2,-60,z))
            nut=core.hexagon(7,3.2,0,0,0).cut(cyl(2,3.2,(0,0,0))).rotate((0,0,0),(0,1,0),90).translate((92,-60,z))
            for name,s in [('M4x25_front_frame',bolt),('M4_front_frame_washer',washer),('M4_front_frame_nut',nut)]:
                if side=='left':s=s.mirror('YZ')
                out.append((f'{name}_{side}_{i}',s))
    return out
