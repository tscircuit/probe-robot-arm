"""FLEX revision 14: wider rack, bounded socket relief and square insertion end.
CadQuery 2.7, millimetres. python model.py --stroke 40 --preload .10 --check
"""
import cadquery as cq
import math,json,argparse,pathlib,itertools
P=argparse.ArgumentParser();P.add_argument('--motor',choices=['nema17','nema14'],default='nema17');P.add_argument('--bearing-clearance',type=float,default=.8);P.add_argument('--hardware-clearance',type=float,default=.5);P.add_argument('--rack-backbone-width',type=float,default=16.0);P.add_argument('--stroke',type=float,default=40);P.add_argument('--preload',type=float,default=.10);P.add_argument('--shaft-diameter',type=float,default=5.0);P.add_argument('--shaft-flat-depth',type=float,default=.5);P.add_argument('--shaft-clearance',type=float,default=.15);P.add_argument('--spring-preload',type=float,default=2.30);P.add_argument('--spring-thickness',type=float,default=1.4);P.add_argument('--out',default='dist');P.add_argument('--check',action='store_true');a=P.parse_args()
assert 20<=a.stroke<=80 and 0<=a.preload<=.2
assert 4<=a.shaft_diameter<=6 and .2<=a.shaft_flat_depth<=1 and .05<=a.shaft_clearance<=.3
assert .1<=a.spring_preload<=2.5 and 1.2<=a.spring_thickness<=1.8
SPRING_PRELOAD=a.spring_preload;SPRING_THICKNESS=a.spring_thickness;SPRING_CHECK_TRAVEL=max(2.6,SPRING_PRELOAD+.3);RAMP_LENGTH=0.;RAMP_RISE=0.
assert 14.5<=a.rack_backbone_width<=18
assert .5<=a.bearing_clearance<=1.2 and .5<=a.hardware_clearance<=1.2
IS14=a.motor=='nema14';LABEL='FLEX14' if IS14 else 'FLEX17';MOTOR_NAME='NEMA14' if IS14 else 'NEMA17'
MOTOR_SIZE=35.2 if IS14 else 42.;MOTOR_PITCH=26. if IS14 else 31.;MOTOR_DEPTH=20. if IS14 else 23.
N=14 if IS14 else 18;RP=float(N);MOTOR_Y=18-RP;PRESSURE_ANGLE=25 if IS14 else 20
BEARING_GAP=a.bearing_clearance;HARDWARE_GAP=a.hardware_clearance;POCKET_R=8+BEARING_GAP
BODY_FRONT=2.5+BEARING_GAP;CHASSIS_FRONT=-17 if IS14 else -23
GEAR_NAME=f'03 Involute pinion {N}T'
FLOOR_WIDTH=20.9 if IS14 else 22.1
PIVOT=(0,MOTOR_Y,0)
def rotate_drive(shape,degrees):return shape.rotate(PIVOT,(0,MOTOR_Y,1),degrees)

SHAFT_R=a.shaft_diameter/2; FLAT_Y=-SHAFT_R+a.shaft_flat_depth; BORE_R=SHAFT_R+a.shaft_clearance; BORE_FLAT_Y=FLAT_Y-a.shaft_clearance; SET_Z=6.5
def d_profile(r,flat_y,z,h):
 return cyl(r,h,0,0,z).intersect(box(2*r+2,r-flat_y,h,(0,(r+flat_y)/2,z+h/2)))
out=pathlib.Path(a.out);(out/'assets').mkdir(parents=True,exist_ok=True);(out/'downloads').mkdir(exist_ok=True)
parts=[]
def box(x,y,z,c):return cq.Workplane('XY').box(x,y,z).translate(c).val()
def cyl(r,h,x,y,z):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))
def ycyl(r,h,x,y,z):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z),cq.Vector(0,1,0))
def holes(s,pts,r,z,h):
 for x,y in pts:s=s.cut(cyl(r,h,x,y,z))
 return s
def add(name,s,color,group='fixed',printed=False):
 assert s.isValid(),name
 assert len(s.Solids())==1,(name,len(s.Solids()))
 parts.append(dict(name=name,shape=s,color=color,group=group,printed=printed));return s

# All bearing axes are perpendicular to X, the rolling/travel direction.
SQ=math.sqrt(.5);STATIONS=[-23.,23.];GUIDE_Y=32.;GUIDE_TOP=1.;RACK_EXTRA=72.
UPPER=[]
for side in ['front','rear']:
 sign=-1 if side=='front' else 1
 for x in STATIONS:
  contact=(x,GUIDE_Y+sign*5.5,GUIDE_TOP-2.5)
  normal=(0,sign*SQ,SQ);axis=(0,-sign*SQ,SQ)
  center=tuple(contact[i]+8*normal[i] for i in range(3))
  UPPER.append(dict(side=side,x=x,center=center,axis=axis,contact=contact,normal=normal))
def at(c,u,t):return tuple(c[i]+u[i]*t for i in range(3))
def acyl(r,h,c,u,t=0):return cq.Solid.makeCylinder(r,h,cq.Vector(*at(c,u,t)),cq.Vector(*u))
def ahex(d,h,c,u,t=0):
 return cq.Workplane('XY').polygon(6,d).extrude(h).val().located(cq.Plane(origin=at(c,u,t),xDir=(1,0,0),normal=u).location)
def ring(ro,ri,h,c,u,t=0):return acyl(ro,h,c,u,t).cut(acyl(ri,h,c,u,t))
# Plain-end withdrawal finishes at a full motor revolution.
WITHDRAW=2*math.pi*RP*math.ceil(((a.stroke+RACK_EXTRA)/2+31.5)/(2*math.pi*RP))
tracks={'fixed':[],
 'rack':[{'start':0,'end':.18,'delta':[WITHDRAW,0,0]}],
 'gear':[{'start':0,'end':.18,'degrees':-WITHDRAW/RP*180/math.pi},{'start':.22,'end':.26,'delta':[0,0,20]},{'start':.26,'end':.30,'delta':[0,-55,0]}],
 'shaft':[{'start':0,'end':.18,'degrees':-WITHDRAW/RP*180/math.pi},{'start':.63,'end':.72,'delta':[0,0,-38]}],
 'set_screw':[{'start':0,'end':.18,'degrees':-WITHDRAW/RP*180/math.pi},{'start':.18,'end':.22,'delta':[0,-28,0]}],
 'front_axles':[{'start':.30,'end':.36,'delta':[0,30*SQ,30*SQ]},{'start':.36,'end':.40,'delta':[0,-45,0]}],
 'rear_axles':[{'start':.40,'end':.46,'delta':[0,-30*SQ,30*SQ]},{'start':.46,'end':.50,'delta':[0,45,0]}],
 'upper_rollers':[{'start':.50,'end':.58,'delta':[0,0,40]}],
 'motor_screws':[{'start':.58,'end':.63,'delta':[0,0,16]}],
 'motor':[{'start':.63,'end':.72,'delta':[0,0,-38]}],
 'front_nuts':[{'start':.90,'end':.94,'delta':[0,-40*SQ,-40*SQ]}],
 'rear_nuts':[{'start':.90,'end':.94,'delta':[0,40*SQ,-40*SQ]}],
}
for side in ['left','right']:
 tracks['lower_'+side+'_nuts']=[{'start':.72,'end':.80,'delta':[0,45,0]}]
 tracks['lower_'+side+'_axles']=[{'start':.80,'end':.86,'delta':[0,-35,0]},{'start':.86,'end':.90,'delta':[45 if side=='right' else -45,0,0]}]
 tracks['lower_'+side+'_rollers']=[{'start':.94,'end':1,'delta':[0,0,25]}]
stages=[{'start':a,'end':b,'label':s} for a,b,s in [
 (0,.18,'Slide rack out; spring floors relax'),(.18,.22,'Withdraw pinion set screw'),(.22,.30,'Lift and clear pinion'),
 (.30,.40,'Withdraw front angled axle bolts'),(.40,.50,'Withdraw rear angled axle bolts'),(.50,.58,'Lift four angled rollers'),
 (.58,.63,'Remove motor screws'),(.63,.72,'Lower motor from integral mounting land'),
 (.72,.80,'Remove lower axle nuts'),(.80,.90,'Withdraw and park lower axle bolts'),(.90,.94,'Remove angled axle nuts'),(.94,1,'Lift lower rollers through chassis windows')]]

def lower_lift(x,e):
 # The roller can rise until its free spring height or the rack underside stops it.
 dx=WITHDRAW*max(0,min(1,e/.18));edge=-(a.stroke+RACK_EXTRA)/2+dx
 candidates=[-17+SPRING_PRELOAD]
 for x0,x1,z0,slope in [(edge,edge+a.stroke+RACK_EXTRA,-9,0)]:
  lo=max(x0,x-8);hi=min(x1,x+8)
  if lo>hi:continue
  tangent=max(lo,min(hi,x-8*slope/math.sqrt(1+slope*slope)))
  for q in [lo,hi,tangent]:candidates.append(z0+slope*(q-x0)-math.sqrt(max(0,64-(q-x)**2)))
 return max(0,min(SPRING_PRELOAD,min(candidates)+17))
def flex_lifts(e):return (lower_lift(-23,e),lower_lift(23,e))
def offset(group,e):
 v=[0.,0.,lower_lift(-23 if '_left_' in group else 23,e) if group.startswith('lower_') else 0.]
 for t in tracks[group]:
  f=max(0,min(1,(e-t['start'])/(t['end']-t['start'])))
  for k in range(3):v[k]+=f*t.get('delta',[0,0,0])[k]
 return tuple(v)
def angle(group,e):return sum(max(0,min(1,(e-t['start'])/(t['end']-t['start'])))*t.get('degrees',0) for t in tracks[group])
# Broad upper platform, deep rear web and lower crossmember, all one printed body.
base=box(68,58-CHASSIS_FRONT,7,(0,(58+CHASSIS_FRONT)/2,.5)).fuse(box(68,22.1,26,(0,32.45,-16)))
for p in UPPER:base=base.fuse(acyl(9.5,7,p['center'],p['axis'],-9.5))
# The motor leaves straight down; the 5 mm mounting land is integral.
base=base.cut(box(MOTOR_SIZE+.8,MOTOR_SIZE+.8,80,(0,MOTOR_Y,-43))).cut(cyl(11.4,9,0,MOTOR_Y,-4))
motor_holes=[(x,y+MOTOR_Y) for x in [-MOTOR_PITCH/2,MOTOR_PITCH/2] for y in [-MOTOR_PITCH/2,MOTOR_PITCH/2]]
base=holes(base,motor_holes,1.7,-4,12)
for x,y in motor_holes:
 base=base.cut(cq.Solid.makeCone(1.7,3.2,1.5,cq.Vector(x,y,-1.5),cq.Vector(0,0,1)))
 base=base.cut(cyl(3.5,15,x,y,0))
CHASSIS_MOUNTS=[(x,y) for x in [-30,30] for y in [-13,54]]
base=holes(base,CHASSIS_MOUNTS,2.2,-4,14)
for x,y in CHASSIS_MOUNTS:base=base.cut(box(10,10,14,(x,y,7)))
# A six-millimetre neck joins the original tooth spine to a stiff beveled guide.
RAIL_PROFILE=[(29,14),(35,14),(35,1),(40,-4),(36,-9),(28,-9),(24,-4),(29,1)]
def rail_shape(length,clearance=0):
 w=cq.Workplane('YZ').polyline(RAIL_PROFILE).close()
 if clearance:w=w.offset2D(clearance)
 return w.extrude(length).translate((-length/2,0,0)).val()
base=base.cut(rail_shape(70,1.0))
motor_land=box(MOTOR_SIZE,MOTOR_SIZE,5,(0,MOTOR_Y,-5.5)).cut(cyl(11.4,7,0,MOTOR_Y,-9))
motor_land=holes(motor_land,motor_holes,1.7,-9,7)
for p in UPPER:
 c,u=p['center'],p['axis']
 base=base.cut(acyl(POCKET_R,50,c,u,-2.5))
 base=base.cut(ring(POCKET_R,3.5,BEARING_GAP,c,u,-BODY_FRONT))
 base=base.cut(acyl(2.6,60,c,u,-35))
 base=base.cut(ahex(9.5,2.9,c,u,-12.3)).cut(acyl(5,22.7,c,u,-35))
 motor_land=motor_land.cut(acyl(2.7,60,c,u,-35)).cut(acyl(5,25.6,c,u,-35))
 if p['side']=='front':
  nutc=at(c,u,-10.85)
  motor_land=motor_land.cut(box(9.8,9.8,60,(c[0],nutc[1],-25)))
# Broad, integral spring floors support solid lower axle blocks. No separate springs.
BOTTOM=[]
for x in STATIONS:
 y=32.+(1 if x>0 else -1);c=(x,y,-17.)
 BOTTOM.append(dict(x=x,center=c,side='left' if x<0 else 'right'))
 # Retain the central spine and upper bearing roof; open the spring bay below.
 base=base.cut(box(31,22.1,19.5,((19.5 if x>0 else -19.5),32.45,-19.35)))
 # An open-top service window lets the bearing/washer lift out after axle removal.
 base=base.cut(box(2*POCKET_R,5+2*BEARING_GAP,60,(x,y,3.5)))
# The spring floors are open underneath: there is no rigid lower deck.
base=base.fuse(motor_land).clean()
frame=base

def floor_profile(deflection):
 # Plain full-width floor. Fillets are added only at actual wall intersections.
 x0=4.;x1=18.;h=SPRING_THICKNESS/2;z=-27+h
 def center(u):return z-deflection*(3*u*u-2*u*u*u)
 w=cq.Workplane('XZ').moveTo(3,z+h).lineTo(x0,z+h)
 w=w.spline([(x0+(x1-x0)*k/20,center(k/20)+h) for k in range(1,21)],includeCurrent=True)
 w=w.lineTo(28,z-deflection+h).lineTo(28,z-deflection-h).lineTo(x1,z-deflection-h)
 w=w.spline([(x0+(x1-x0)*k/20,center(k/20)-h) for k in range(19,-1,-1)],includeCurrent=True)
 return w.lineTo(3,z-h).close().extrude(FLOOR_WIDTH).val()
def spring_seat(spec,deflection):
 x=spec['x'];y=spec['center'][1];free_z=-17+SPRING_PRELOAD
 leaf=floor_profile(deflection).translate((0,43.5,0))
 if x<0:leaf=leaf.mirror('YZ')
 body=box(10,43.5-y-BODY_FRONT,16.5,(x,(43.5+y+BODY_FRONT)/2,-18.75-deflection))
 body=body.fuse(ycyl(3.5,BEARING_GAP,x,y+2.5,free_z-deflection))
 body=body.cut(ycyl(2.6,20,x,y+2.4,free_z-deflection))
 return leaf.fuse(body).clean()
def chassis(deflections):
 v=frame
 for p,d in zip(BOTTOM,deflections):v=v.fuse(spring_seat(p,d))
 v=v.clean();blends=[]
 for edge in v.Edges():
  if edge.geomType()!='LINE':continue
  c=edge.Center();bb=edge.BoundingBox()
  if abs(abs(c.x)-4)<1e-5 and abs(c.z-(-27+SPRING_THICKNESS))<1e-5 and bb.ylen>1:
   blends.append(edge);continue
  for p,d in zip(BOTTOM,deflections):
   z=-27+SPRING_THICKNESS-d
   inner=abs(c.x-(18 if p['x']>0 else -18))<1e-5 and bb.ylen>1 and c.y>p['center'][1]+BODY_FRONT
   front=abs(c.y-(p['center'][1]+BODY_FRONT))<1e-5 and abs(c.x-p['x'])<1 and bb.xlen>1
   if abs(c.z-z)<1e-5 and (inner or front):blends.append(edge);break
 assert len(blends)==6,('Expected wall-to-floor intersections',[(tuple(e.Center()),e.Length()) for e in blends])
 return cq.Workplane(obj=v).newObject(blends).fillet(1.2).val()
base=chassis((SPRING_PRELOAD,SPRING_PRELOAD))
base_print=chassis((0,0))
motor=box(MOTOR_SIZE,MOTOR_SIZE,MOTOR_DEPTH,(0,MOTOR_Y,-8-MOTOR_DEPTH/2)).fuse(cyl(11,2,0,MOTOR_Y,-8))
motor=holes(motor,motor_holes,1.65,-13,7)
add(MOTOR_NAME+' reference',motor,'#363d45','motor')
shaft=d_profile(SHAFT_R,FLAT_Y,-6,17).translate((0,MOTOR_Y,0));add(MOTOR_NAME+' D shaft',shaft,'#a4b4c2','shaft')
for x,y in motor_holes:
 screw=cyl(1.45,10.5,x,y,-12).fuse(cq.Solid.makeCone(1.45,2.9,1.5,cq.Vector(x,y,-1.5),cq.Vector(0,0,1)))
 add(f'M3 motor screw {x} {y}',screw,'#9da9b3','motor_screws')
# Sampled involute, module 2; tooth count and pressure angle follow motor variant.
m=2;n=N;rp=RP;rb=rp*math.cos(math.radians(PRESSURE_ANGLE));ra=rp+m;rr=rp-1.25*m
inv=lambda r:math.sqrt(max(0,(r/rb)**2-1))-math.acos(min(1,rb/r))
half_base=math.pi/(2*n)+inv(rp);points=[]
for i in range(n):
 center=2*math.pi*i/n;vals=[(rr,-half_base),(rb,-half_base)]
 for k in range(1,17):
  r=rb+(ra-rb)*k/16;vals.append((r,-half_base+inv(r)))
 for k in range(16,-1,-1):
  r=rb+(ra-rb)*k/16;vals.append((r,half_base-inv(r)))
 vals.append((rr,half_base))
 points.extend([(r*math.cos(center+t),r*math.sin(center+t)) for r,t in vals])
# Offset both the circular wall and the flat for a small slip-fit allowance.
bore=d_profile(BORE_R,BORE_FLAT_Y,-1,23)
gear=cq.Workplane('XY').polyline(points).close().extrude(8).translate((0,0,13)).val().fuse(cyl(6,13,0,0,0)).cut(bore).cut(ycyl(1.25,FLAT_Y+7.5,0,-7,SET_Z))
gear=gear.translate((0,MOTOR_Y,0))
add(GEAR_NAME,gear,'#f9b44d','gear',True)
# M3x4 flat-point screw: tip ends exactly on the shaft flat.
# Thread core is drawn; the 2.5mm pilot must be tapped M3 after printing.
set_screw=ycyl(1.2,4,0,FLAT_Y-4,SET_Z).cut(ycyl(.65,1.2,0,FLAT_Y-4,SET_Z))
set_screw=set_screw.translate((0,MOTOR_Y,0))
add('M3x4 flat-point pinion set screw',set_screw,'#9da9b3','set_screw')
# Uncapped, oversize tooth walls with central AND between-tooth root reliefs.
L=a.stroke+RACK_EXTRA;left=-L/2;right=L/2;pitch=math.pi*m;alpha=math.tan(math.radians(PRESSURE_ANGLE));wall=.6
centers=[i*pitch for i in range(-math.floor((L-8)/(2*pitch)),math.floor((L-8)/(2*pitch))+1)]
def make_rack(preload):
 half=lambda y:pitch/4+(y-18)*alpha+preload
 h0=half(16);h1=half(20.5)
 rack=box(L,a.rack_backbone_width,8,(0,20.5+a.rack_backbone_width/2,17)) # grow the continuous backbone away from the tooth roots
 for x in centers:
  tooth=cq.Workplane('XY').polyline([(x-h0,16),(x+h0,16),(x+h1,20.5),(x-h1,20.5)]).close().extrude(8).translate((0,0,13)).val()
  radius=h1-wall;cap_y=25-radius
  slot=(cq.Workplane('XY').moveTo(x-h0+wall,15.95).lineTo(x+h0-wall,15.95)
        .lineTo(x+radius,20.5).lineTo(x+radius,cap_y)
        .threePointArc((x,25),(x-radius,cap_y)).lineTo(x-radius,20.5)
        .close().extrude(8.2).translate((0,0,12.9)).val())
  rack=rack.fuse(tooth).cut(slot)
 # Semicircular caps tangent to both straight walls avoid sharp root corners.
 gaps=[(x0+h1,x1-h1) for x0,x1 in zip(centers[:-1],centers[1:])]
 gaps += [(left,centers[0]-h1),(centers[-1]+h1,right)]
 for lo,hi in gaps:
  radius=(hi-lo)/2;mid=(lo+hi)/2;cap_y=25-radius
  relief=(cq.Workplane('XY').moveTo(lo,20.5).lineTo(hi,20.5)
          .lineTo(hi,cap_y).threePointArc((mid,25),(lo,cap_y))
          .close().extrude(8.2).translate((0,0,12.9)).val())
  rack=rack.cut(relief)
 # Beveled faces carry downward/inward reactions; the bottom is a flat raceway.
 rack=rack.fuse(rail_shape(L))
 # Square insertion end: no ramp/chamfer cut. The roller rim cams the spring down.
 # The pad shares the Z=21 tooth face, so it starts on the print bed.
 pad=holes(box(14,16,18,(right+7,25.5,12)),[(right+7,20),(right+7,29)],1.7,2,20)
 rack=rack.fuse(pad)
 # Head relief is open at the insertion end and stops at the required travel envelope.
 # The output end and mounting pad remain solid; leave only the requested head margin.
 slot_end=max(STATIONS)+a.stroke/2+4.75+HARDWARE_GAP
 for p in UPPER:
  c,u=p['center'],p['axis'];v=(0,-u[2],u[1]);r=4.75+HARDWARE_GAP
  yz=[(c[1]+u[1]*t+v[1]*q,c[2]+u[2]*t+v[2]*q) for t,q in [(2.8-HARDWARE_GAP,-r),(7.8+HARDWARE_GAP,-r),(7.8+HARDWARE_GAP,r),(2.8-HARDWARE_GAP,r)]]
  channel=cq.Workplane('YZ').polyline(yz).close().extrude(slot_end-left+1).translate((left-1,0,0)).val()
  rack=rack.cut(channel)
 # Plain open left end permits insertion from the output/right side.
 return rack.clean()
central_relief_radius=pitch/4+2.5*alpha+a.preload-wall
intertooth_relief_radius=(pitch-2*(central_relief_radius+wall))/2
rack=make_rack(a.preload);add('04 Beveled compliant rack',rack,'#42d6ba','rack',True)

for p in UPPER:
 c,u,side=p['center'],p['axis'],p['side'];tag=f'{side} {p["x"]}'
 add('625ZZ angled '+tag,ring(8,2.5,5,c,u,-2.5),'#bac8d5','upper_rollers')
 parts[-1].update(spinAxis=list(u),spinCenter=list(c),spinSign=-1 if side=='front' else 1)
 add('M5 upper washer '+tag,ring(3.75,2.55,.3,c,u,2.5),'#c9d4dd','upper_rollers')
 bolt=acyl(2.45,16,c,u,-13.2).fuse(acyl(4.75,5,c,u,2.8)).cut(acyl(1.5,2.5,c,u,5.3))
 add('M5x16 angled axle '+tag,bolt,'#8393a1',side+'_axles')
 nut=ahex(9.24,2.7,c,u,-12.2).cut(acyl(2.55,2.7,c,u,-12.2))
 add('M5 angled nut '+tag,nut,'#b0bdc8',side+'_nuts')
for p in BOTTOM:
 c=p['center'];x=p['x'];u=(0,1,0);prefix='lower_'+p['side']+'_'
 add(f'625ZZ lower {x}',ring(8,2.5,5,c,u,-2.5),'#bac8d5',prefix+'rollers')
 parts[-1].update(spinAxis=list(u),spinCenter=list(c),spinSign=1)
 add(f'M5 lower washer {x}',ring(3.75,2.55,.3,c,u,-2.8),'#c9d4dd',prefix+'rollers')
 bolt=acyl(2.45,25,c,u,-2.8).fuse(acyl(4.75,5,c,u,-7.8)).cut(acyl(1.5,2.5,c,u,-7.8))
 add(f'M5x25 lower axle {x}',bolt,'#8393a1',prefix+'axles')
 nut=ahex(9.24,2.7,c,u,43.5-c[1]).cut(acyl(2.55,2.7,c,u,43.5-c[1]))
 add(f'M5 lower nut {x}',nut,'#b0bdc8',prefix+'nuts')
add('01 Integral spring chassis',base,'#526576',printed=True)
parts[-1]['flex_chassis']=True
# Clear obsolete generated meshes rather than leave old-bearing parts in the bundle.
expected={p['name'].replace(' ','_')+'.stl' for p in parts if p['printed']}
for f in (out/'downloads').glob('*.stl'):
 if f.name not in expected:f.unlink()
scene=[];assembly=cq.Assembly(name=LABEL+'_R14')
for p in parts:
 s=p['shape'];vs,ts=s.tessellate(.06,.12)
 scene.append({k:p[k] for k in ['name','color','group','printed']}|{k:p[k] for k in ['spinAxis','spinCenter','spinSign','flex_chassis'] if k in p}|{'vertices':[[round(v.x,5),round(v.y,5),round(v.z,5)] for v in vs],'triangles':ts})
 assembly.add(s,name=p['name'].replace(' ','_'),color=cq.Color(p['color']))
 if p['printed']:cq.exporters.export(base_print if p.get('flex_chassis') else s,str(out/'downloads'/(p['name'].replace(' ','_')+'.stl')),tolerance=.04,angularTolerance=.1)
assembly.save(str(out/'downloads'/(LABEL+'.step')))
bounds=[p['shape'].BoundingBox() for p in parts]
envelope=[max(getattr(b,k+'max') for b in bounds)-min(getattr(b,k+'min') for b in bounds) for k in ['x','y','z']]
data={'revision':14,'envelope':envelope,'motor':MOTOR_NAME,'motorSize':MOTOR_SIZE,'motorPitch':MOTOR_PITCH,'motorDepth':MOTOR_DEPTH,'rotationPivot':list(PIVOT),'pinionTeeth':N,'pressureAngle':PRESSURE_ANGLE,'withdrawal':WITHDRAW,'bearingClearance':BEARING_GAP,'hardwareClearance':HARDWARE_GAP,'chassisFootprint':[68,58-CHASSIS_FRONT],'stroke':a.stroke,'rackLength':L,'rackBackboneWidth':a.rack_backbone_width,'headReliefEndX':max(STATIONS)+a.stroke/2+4.75+HARDWARE_GAP,'solidRackEndLength':L/2-(max(STATIONS)+a.stroke/2+4.75+HARDWARE_GAP),'squareInsertionEnd':True,'pitchRadius':rp,'shaftDiameter':a.shaft_diameter,'shaftFlatDepth':a.shaft_flat_depth,'shaftClearance':a.shaft_clearance,'boreDiameter':2*BORE_R,'boreFlatY':BORE_FLAT_Y,'setScrewZ':SET_Z,'stationSpacing':46,'upperBearingAngle':45,'springPreload':SPRING_PRELOAD,'springThickness':SPRING_THICKNESS,'springTravelCheck':SPRING_CHECK_TRAVEL,'rampLength':RAMP_LENGTH,'rampRise':RAMP_RISE,'lowerContactY':[31,33],'chassisMounts':CHASSIS_MOUNTS,'bearingType':'625ZZ','bearingCount':6,'preloadPerFlank':a.preload,'wallThickness':wall,'rootRelief':'tangent semicircular end caps','centralReliefRadius':central_relief_radius,'intertoothReliefRadius':intertooth_relief_radius,'tracks':tracks,'stages':stages,'parts':scene}
# Exact sampled CAD states preserve wall fillets while the floors relax.
states=[]
for l,r in [(SPRING_PRELOAD*k/12,0) for k in range(1,13)]+[(SPRING_PRELOAD,SPRING_PRELOAD*k/12) for k in range(1,13)]:
 shape=chassis((SPRING_PRELOAD-l,SPRING_PRELOAD-r));vs,ts=shape.tessellate(.12,.22)
 states.append({'leftLift':l,'rightLift':r,'vertices':[[round(v.x,5),round(v.y,5),round(v.z,5)] for v in vs],'triangles':ts})
(out/'assets'/'spring-states.json').write_text(json.dumps(states,separators=(',',':')))
data['springStateStep']=SPRING_PRELOAD/12
(out/'assets'/'assembly.json').write_text(json.dumps(data,separators=(',',':')))
print('Exported',len(parts),'parts / six 625ZZ bearings',flush=True)
if a.check:
 def overlap(s,t):
  b,c=s.BoundingBox(),t.BoundingBox()
  if b.xmax<=c.xmin+1e-7 or c.xmax<=b.xmin+1e-7 or b.ymax<=c.ymin+1e-7 or c.ymax<=b.ymin+1e-7 or b.zmax<=c.zmin+1e-7 or c.zmax<=b.zmin+1e-7:return 0.
  return max(0,s.intersect(t).Volume())
 # Confirm the manufactured rack includes circular root arcs on both face edges.
 for wanted in [central_relief_radius,intertooth_relief_radius]:
  arcs=[e for e in rack.Edges() if e.geomType()=='CIRCLE' and abs(e.radius()-wanted)<1e-6]
  assert len(arcs)>=2*(len(centers)-1),(wanted,len(arcs))
 # Confirm restored end material and the square underside, not merely mesh appearance.
 square_end_check=rack.isInside(cq.Vector(left+.05,32,-8.95),1e-7)
 assert square_end_check,'Insertion end still has a ramp'
 rack_restoration_checks=[rack.isInside(cq.Vector(x,y,z),1e-7) for x,y,z in [(right-1,30,6),(right+4,30,6),(0,20.5+a.rack_backbone_width-.05,17)]]
 assert all(rack_restoration_checks),'Missing restored end or backbone material'
 end_solid_probe=box(L/2-(max(STATIONS)+a.stroke/2+4.75+HARDWARE_GAP),.1,.1,((L/2+max(STATIONS)+a.stroke/2+4.75+HARDWARE_GAP)/2,32,5))
 assert abs(end_solid_probe.intersect(rack).Volume()-end_solid_probe.Volume())<1e-7,'Head relief reaches solid end'
 # Explicit fit and axis checks, in addition to the general collision scan.
 assert shaft.distance(gear)>=a.shaft_clearance-1e-6
 assert abs(shaft.distance(set_screw))<1e-6
 assert gear.isInside(cq.Vector(0,MOTOR_Y+BORE_FLAT_Y-.02,10),1e-6)
 assert not gear.isInside(cq.Vector(0,MOTOR_Y+BORE_FLAT_Y+.02,10),1e-6)
 assert SET_Z-1.5>0 and SET_Z+1.5<11
 d_fit={'shaft_diameter_mm':a.shaft_diameter,'shaft_flat_depth_mm':a.shaft_flat_depth,'shaft_flat_y_mm':FLAT_Y,'bore_diameter_mm':2*BORE_R,'bore_flat_y_mm':BORE_FLAT_Y,'motor_center_y_mm':MOTOR_Y,'bore_flat_world_y_mm':MOTOR_Y+BORE_FLAT_Y,'wall_clearance_mm':a.shaft_clearance,'measured_shaft_gear_gap_mm':shaft.distance(gear),'set_screw':'M3x4 flat point','tap_pilot_diameter_mm':2.5,'set_screw_axis':'+Y, normal to flat','set_screw_axis_z_mm':SET_Z,'set_screw_tip_y_mm':MOTOR_Y+FLAT_Y,'set_screw_shaft_gap_mm':shaft.distance(set_screw),'shaft_engagement_z_mm':[0,11]}
 print('D shaft fit:',d_fit,flush=True)
 tolerance=.01;fail=[];allowed=[];mesh_pair={GEAR_NAME,'04 Beveled compliant rack'}
 # Validate the ideal unloaded tooth profile before allowing elastic preload.
 nominal=make_rack(0);period_vol=[];nominal_vol=[]
 for k in range(17):
  dx=pitch*k/16;g=rotate_drive(gear,-dx/rp*180/math.pi)
  period_vol.append(overlap(rack.translate((dx,0,0)),g))
  nominal_vol.append(overlap(nominal.translate((dx,0,0)),g))
 assert max(nominal_vol)<tolerance,('Nominal involute mesh collides',max(nominal_vol))
 elastic_limit=max(period_vol)*1.05+.02
 for i,j in itertools.combinations(range(len(parts)),2):
  p,q=parts[i],parts[j];v=overlap(p['shape'],q['shape'])
  if v>tolerance:
   rec={'phase':'assembled','a':p['name'],'b':q['name'],'volume_mm3':round(v,5)}
   (allowed if {p['name'],q['name']}==mesh_pair and v<=elastic_limit else fail).append(rec)
 print('Assembled rigid failures:',len(fail),fail[:8],'; nominal mesh max:',max(nominal_vol),flush=True)
 times={0.,1.};bounds=sorted({0.,1.}|{t[k] for ts in tracks.values() for t in ts for k in ['start','end']})
 for lo,hi in zip(bounds[:-1],bounds[1:]):
  moves=[math.dist(offset(g,lo),offset(g,hi)) for g in tracks]
  moves += [abs(angle(g,hi)-angle(g,lo))*math.pi/180*(20 if g=='gear' else 8) for g in tracks]
  steps=max(2,math.ceil(max(moves)/.5))
  times.update(lo+(hi-lo)*k/steps for k in range(steps+1))
 times=sorted(times);pose_cache={};pair_cache={}
 def placed(i,e):
  p=parts[i];t=offset(p['group'],e);deg=angle(p['group'],e);key=(i,round(deg%360,8))+tuple(round(x,8) for x in t)+(tuple(round(v,8) for v in flex_lifts(e)) if p.get('flex_chassis') else ())
  if key not in pose_cache:
   v=chassis(tuple(SPRING_PRELOAD-v for v in flex_lifts(e))) if p.get('flex_chassis') else p['shape']
   if abs(deg%360)>1e-7:v=rotate_drive(v,deg)
   if any(abs(x)>1e-8 for x in t):v=v.translate(t)
   pose_cache[key]=v
  return pose_cache[key]
 last_phase=-1
 for k,e in enumerate(times):
  if k%50==0:print('Explosion pose',k+1,'of',len(times),flush=True)
  trans=[offset(p['group'],e) for p in parts];rot=[angle(p['group'],e) for p in parts]
  for i,j in itertools.combinations(range(len(parts)),2):
   if trans[i]==trans[j] and abs((rot[j]-rot[i])%360)<1e-7 and not (any(parts[q].get('flex_chassis') for q in [i,j]) and max(flex_lifts(e))>1e-8):continue
   # Volume is invariant under a common rigid transform; cache relative poses.
   radians=-rot[i]*math.pi/180;d=[trans[j][q]-trans[i][q] for q in range(3)]
   rel=(d[0]*math.cos(radians)-d[1]*math.sin(radians),d[0]*math.sin(radians)+d[1]*math.cos(radians),d[2])
   key=(i,j,round((rot[j]-rot[i])%360,7))+tuple(round(v,7) for v in rel)+(tuple(round(v,7) for v in flex_lifts(e)) if any(parts[q].get('flex_chassis') for q in [i,j]) else ())
   if key not in pair_cache:pair_cache[key]=overlap(placed(i,e),placed(j,e))
   v=pair_cache[key]
   if v<=tolerance:continue
   p,q=parts[i],parts[j]
   elastic={p['name'],q['name']}==mesh_pair and offset('rack',e)[0]<L/2+ra and v<=elastic_limit
   if not elastic:fail.append({'phase':'explosion','at':round(e,6),'a':p['name'],'b':q['name'],'volume_mm3':round(v,5)})
  phase=max(j for j,t in enumerate(stages) if e>=t['start']-1e-9)
  if phase!=last_phase:print('Stage',phase+1,stages[phase]['label'],'failures:',len(fail),flush=True);last_phase=phase
 print('Explosion:',len(times),'samples;',len(fail),'rigid failures',fail[:10],flush=True)
 motion_fail=[];mesh_volumes=[]
 for k in range(41):
  dx=-a.stroke/2+a.stroke*k/40;r=rack.translate((dx,0,0));deg=-dx/rp*180/math.pi
  g=rotate_drive(gear,deg);shaft_shape=rotate_drive(shaft,deg);set_shape=rotate_drive(next(p['shape'] for p in parts if p['group']=='set_screw'),deg)
  mesh_volumes.append(overlap(r,g))
  for p in parts:
   if p['group'] in ['rack','gear','set_screw','shaft']:continue
   for label,moving in [('rack',r),('pinion',g),('set screw',set_shape),('D shaft',shaft_shape)]:
    v=overlap(moving,p['shape'])
    if v>tolerance:motion_fail.append({'at_mm':dx,'a':label,'b':p['name'],'volume_mm3':round(v,5)})
  # The shaft/gear/screw share a rigid transform; their initial fit also holds during motion.
 print('Motion failures:',len(motion_fail),motion_fail[:10],flush=True)
 contact_checks=[]
 for p in UPPER:
  point=p['contact'];normal=p['normal'];inside=tuple(point[k]-.05*normal[k] for k in range(3));outside=tuple(point[k]+.05*normal[k] for k in range(3))
  contact_checks.extend([rack.isInside(cq.Vector(*inside),1e-7),not rack.isInside(cq.Vector(*outside),1e-7),abs(sum(p['axis'][k]*normal[k] for k in range(3)))<1e-9])
 for p in BOTTOM:
  x=p['x'];contact_checks.extend([rack.isInside(cq.Vector(x,p['center'][1],-8.95),1e-7),not rack.isInside(cq.Vector(x,p['center'][1],-9.05),1e-7)])
 assert all(contact_checks),'Guide contact geometry is incorrect'
 gap=[]
 for dx in [-a.stroke/2,0,a.stroke/2]:
  for dy in [0]:
   for dz in [0]:gap.append({'x':dx,'y':dy,'z':dz,'part':'01 Integral spring chassis','gap_mm':round(rack.translate((dx,dy,dz)).distance(base),4)})
 print('Minimum rack/chassis clearance:',min(p['gap_mm'] for p in gap),flush=True)
 # Check wall-local blends and clearance without a rigid lower stop deck.
 assert base_print.isValid() and len(base_print.Solids())==1
 wall_blend_checks=[]
 for p in BOTTOM:
  sign=1 if p['x']>0 else -1;front=p['center'][1]+BODY_FRONT
  # No raised fillet/ridge is allowed in the unsupported floor in front of the axle wall.
  for x in [15.,17.8,18.2,23.]:
   wall_blend_checks.append(not base_print.isInside(cq.Vector(sign*x,front-3,-27+SPRING_THICKNESS+.2),1e-7))
 assert all(wall_blend_checks),'A blend extends beyond its supporting wall'
 compressed=chassis((SPRING_CHECK_TRAVEL,SPRING_CHECK_TRAVEL))
 assert compressed.isValid() and len(compressed.Solids())==1
 spring_check={'integral_with_chassis':True,'free_stl_valid':True,'free_stl_solid_count':1,'preload_deflection_mm':SPRING_PRELOAD,'leaf_thickness_mm':SPRING_THICKNESS,'leaf_width_mm':FLOOR_WIDTH,'root_radius_mm':1.2,'wall_local_blend_checks_passed':len(wall_blend_checks),'rigid_lower_deck':False,'mechanical_downward_stop':False,'checked_deflection_mm':SPRING_CHECK_TRAVEL,'method':'Prescribed nominal displacement, not finite element analysis. Chassis STL is relaxed; STEP/viewer start deflected. No mechanical travel stop.'}
 hardware_gaps=[]
 for dx in [-a.stroke/2,0,a.stroke/2]:
  r=rack.translate((dx,0,0))
  for p in parts:
   if 'axle' in p['name'] or 'washer' in p['name'] or 'nut' in p['name']:
    hardware_gaps.append({'travel_mm':dx,'part':p['name'],'gap_mm':r.distance(p['shape'])})
 assert min(q['gap_mm'] for q in hardware_gaps)>=HARDWARE_GAP-1e-5,('Hardware clearance',sorted(hardware_gaps,key=lambda q:q['gap_mm'])[:5])
 references={str(e):{g:{'translation':list(offset(g,e)),'rotation_z_deg':angle(g,e)} for g in tracks} for e in [0,.05,.18,.35,.4,.45,.5,.55,.6,.625,.65,.7,.75,.8,.82,.87,.9,.95,1]}
 report={'revision':14,'rack_backbone_width_mm':a.rack_backbone_width,'head_relief_end_x_mm':max(STATIONS)+a.stroke/2+4.75+HARDWARE_GAP,'solid_rack_end_length_mm':L/2-(max(STATIONS)+a.stroke/2+4.75+HARDWARE_GAP),'square_insertion_end':True,'rack_restoration_checks_passed':len(rack_restoration_checks)+int(square_end_check),'motor':MOTOR_NAME,'pinion_teeth':N,'pressure_angle_deg':PRESSURE_ANGLE,'bearing_clearance_mm':BEARING_GAP,'hardware_clearance_mm':HARDWARE_GAP,'socket_head_envelope_mm':[9.5,5.0],'chassis_footprint_mm':[68,58-CHASSIS_FRONT],'spring_carrier':spring_check,'root_relief':{'shape':'semicircular caps tangent to straight slot walls','central_radius_mm':central_relief_radius,'intertooth_radius_mm':intertooth_relief_radius,'maximum_y_mm':25,'arc_geometry_checked':True},'shaft_fit':d_fit,'bearing_count':6,'bearing_type':'625ZZ','bearing_dimensions_mm':[5,16,5],'station_spacing_mm':46,'upper_bearing_angle_deg':45,'spring_preload_mm':SPRING_PRELOAD,'spring_thickness_mm':SPRING_THICKNESS,'checked_spring_deflection_mm':SPRING_CHECK_TRAVEL,'spring_free_stl':True,'chassis_mounts_mm':CHASSIS_MOUNTS,'motor_face_z_mm':-8,'integral_motor_land_mm':5,'chassis_solid_count':len(base.Solids()),'rack_solid_count':len(rack.Solids()),'insertion_side':'right/output side, plain left end first','rack_withdrawal_mm':WITHDRAW,'contact_checks_passed':len(contact_checks),'upper_force_normals':[[0,SQ,-SQ],[0,-SQ,-SQ]],'lower_force_normal':[0,0,1],'preload_per_flank_mm':a.preload,'nominal_mesh_max_overlap_mm3':max(nominal_vol),'elastic_mesh_limit_mm3':elastic_limit,'elastic_mesh_volume_mm3_range':[min(mesh_volumes),max(mesh_volumes)],'hardware_clearance_samples':hardware_gaps,'minimum_rack_hardware_gap_mm':min(q['gap_mm'] for q in hardware_gaps),'source_sha256':__import__('hashlib').sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'method':'All assembled pairs and moving relative rigid poses, with translation/rotation tip motion sampled <=0.5 mm. Same tracks drive viewer. Nominal tooth profile checked separately.','intersection_tolerance_mm3':tolerance,'explosion_samples':len(times),'motion_samples':41,'explosion_failures':fail,'motion_failures':motion_fail,'intentional_contacts':allowed,'minimum_rack_frame_gap_mm':min(p['gap_mm'] for p in gap),'plastic_clearance_samples':gap,'viewer_reference_poses':references,'limits':['2.3 mm default spring deflection is an aggressive physical prototype. Force, elastic recovery and fatigue require testing in the chosen print material.','Sampled rigid geometry, not continuous swept-volume proof or a physical fit test.','Oversized teeth require elastic deflection. No load, backlash or fatigue rating.','The plain insertion end has no axial hard stop; enforce software travel limits.','Viewer chassis uses exact CAD shape samples at one twelfth of the spring preload; bearing translations follow the CAD tracks continuously.',
 'Pinion is free to turn during rack insertion. Remove front and rear angled axles in sequence. Spring carrier supplies passive preload; force, creep and fatigue have not been measured. STL is unloaded; STEP is assembled and deflected.']}
 (out/'downloads'/'validation.json').write_text(json.dumps(report,indent=2))
 assert not fail and not motion_fail,'See validation report'
 assert min(p['gap_mm'] for p in gap)>.25,'Rack rubs frame'

