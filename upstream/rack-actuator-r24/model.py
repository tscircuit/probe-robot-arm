"""FLEX revision 24: enclosed and shorter rear pass-through housings.
CadQuery 2.7, millimetres. python model.py --stroke 40 --preload .10 --check
"""
import cadquery as cq
import math,json,argparse,pathlib,itertools
P=argparse.ArgumentParser();P.add_argument('--enclosure',choices=['enclosed','pass-through'],default='enclosed');P.add_argument('--skip-export',action='store_true',help='Build/check solids without rewriting existing mesh and STEP exports');P.add_argument('--insert-od',type=float,default=4.6);P.add_argument('--insert-length',type=float,default=5.0);P.add_argument('--insert-pilot',type=float,default=4.2);P.add_argument('--tooth-module',type=float,default=2.0);P.add_argument('--actuator-length',type=float,default=None,help='Fixed housing length along travel, excluding output extension');P.add_argument('--motor-depth',type=float,default=None);P.add_argument('--motor',choices=['nema17','nema14'],default='nema17');P.add_argument('--bearing-clearance',type=float,default=.8);P.add_argument('--hardware-clearance',type=float,default=.5);P.add_argument('--rack-backbone-width',type=float,default=16.0);P.add_argument('--stroke',type=float,default=40);P.add_argument('--preload',type=float,default=.10);P.add_argument('--shaft-diameter',type=float,default=5.0);P.add_argument('--shaft-flat-depth',type=float,default=.5);P.add_argument('--shaft-clearance',type=float,default=.15);P.add_argument('--spring-preload',type=float,default=2.30);P.add_argument('--spring-thickness',type=float,default=None,help='Default 1.8 mm, restored single-floor flexure');P.add_argument('--out',default='dist');P.add_argument('--check',action='store_true');P.add_argument('--config',type=pathlib.Path)
config_args,_=P.parse_known_args()
if config_args.config:
 values=json.loads(config_args.config.read_text())
 allowed_keys={'enclosure','insert_od','insert_length','insert_pilot','motor','tooth_module','stroke','actuator_length','motor_depth','bearing_clearance','hardware_clearance','rack_backbone_width','preload','shaft_diameter','shaft_flat_depth','shaft_clearance','spring_preload','spring_thickness'}
 assert isinstance(values,dict) and not set(values)-allowed_keys,'Unknown configuration key'
 P.set_defaults(**values)
a=P.parse_args()
assert a.motor in ['nema17','nema14'] and a.enclosure in ['enclosed','pass-through']
PASS_THROUGH=a.enclosure=='pass-through'

assert 20<=a.stroke<=150 and 0<=a.preload<=.2
assert 4<=a.shaft_diameter<=6 and .2<=a.shaft_flat_depth<=1 and .05<=a.shaft_clearance<=.3
assert .1<=a.spring_preload<=2.5
SPRING_PRELOAD=a.spring_preload
SPRING_THICKNESS=1.8 if a.spring_thickness is None else a.spring_thickness
assert 1.6<=SPRING_THICKNESS<=2.2
SPRING_CHECK_TRAVEL=max(2.6,SPRING_PRELOAD+.3);RAMP_LENGTH=0.;RAMP_RISE=0.
LEAF_LENGTH=14.;FRONT_MOUNT_Y=-13.;CHASSIS_REAR=60.;REAR_MOUNT_Y=54.

assert 14.5<=a.rack_backbone_width<=18
assert .5<=a.bearing_clearance<=1.2 and .5<=a.hardware_clearance<=1.2
IS14=a.motor=='nema14';LABEL='FLEX14' if IS14 else 'FLEX17';MOTOR_NAME='NEMA14' if IS14 else 'NEMA17'
MOTOR_SIZE=35.2 if IS14 else 42.;MOTOR_PITCH=26. if IS14 else 31.;MOTOR_DEPTH=a.motor_depth if a.motor_depth is not None else (34. if IS14 else 40.)
assert 32<=MOTOR_DEPTH<=60 and 1.5<=a.tooth_module<=2.5
N=14 if IS14 else 18;MODULE=a.tooth_module;RP=MODULE*N/2;MOTOR_Y=4. if IS14 else 0.;PRESSURE_ANGLE=25 if IS14 else 20
PITCH_Y=MOTOR_Y+RP;TIP_Y=PITCH_Y-MODULE;ROOT_Y=PITCH_Y+1.25*MODULE;RELIEF_Y=ROOT_Y+2.25*MODULE
BACK_Y=max(ROOT_Y+a.rack_backbone_width,36.5)
TOOTH_PITCH=math.pi*MODULE;TOOTH_HALF_COUNT=math.floor((a.stroke/2+TOOTH_PITCH)/TOOTH_PITCH)
TOOTH_XMAX=TOOTH_HALF_COUNT*TOOTH_PITCH+TOOTH_PITCH/4+1.25*MODULE*math.tan(math.radians(PRESSURE_ANGLE))+a.preload
CASE_WALL=2.4;CASE_TOP=24.9;CASE_SPLIT=7.;CASE_BOTTOM=-8-MOTOR_DEPTH+4
CASE_RIGHT=math.ceil(max(52,TOOTH_XMAX+a.stroke/2+CASE_WALL+1.))
# Preserve the pictured housing and rack. Only the exit station moves.
REAR_STATION=-32.
CASE_RIGHT=max(CASE_RIGHT,57.)
# Bearing-seat radius, exit wall and print clearance determine the forward limit.
EXIT_BEARING_OFFSET=math.ceil(9.5+CASE_WALL+.8)
FRONT_STATION=CASE_RIGHT-EXIT_BEARING_OFFSET
STATIONS=[REAR_STATION,FRONT_STATION]
RACK_EXTRA=90.
CHASSIS_LEFT=REAR_STATION-11.;CHASSIS_RIGHT=CASE_RIGHT-CASE_WALL-1.
CHASSIS_WIDTH=CHASSIS_RIGHT-CHASSIS_LEFT;CHASSIS_CENTER_X=(CHASSIS_LEFT+CHASSIS_RIGHT)/2
MOUNT_XS=sorted([REAR_STATION-7,max(39.,FRONT_STATION-7)]+([30.] if FRONT_STATION>65 else []))
REAR_MOUNT_XS=sorted([REAR_STATION-7,FRONT_STATION-17]+([30.] if FRONT_STATION>65 else []))
ENCLOSED_MIN_CASE_LENGTH=math.ceil(CASE_RIGHT-REAR_STATION+a.stroke+13+CASE_WALL+1.)
# Reserve room for corner posts and the 10 mm chassis service slide.
MIN_CASE_LENGTH=math.ceil(CASE_RIGHT-CHASSIS_LEFT+25.) if PASS_THROUGH else ENCLOSED_MIN_CASE_LENGTH
CASE_LENGTH=a.actuator_length if a.actuator_length is not None else float(MIN_CASE_LENGTH)
assert MIN_CASE_LENGTH<=CASE_LENGTH<=2000,('Housing too short for selected stroke/teeth',MIN_CASE_LENGTH)
CASE_LEFT=CASE_RIGHT-CASE_LENGTH
OUTPUT_EXTENSION=max(0,CASE_RIGHT+1.5+a.stroke/2-(a.stroke+RACK_EXTRA)/2)
CASE_YMIN=min(-17 if IS14 else -23,MOTOR_Y-RP-MODULE)-CASE_WALL-1.5;CASE_YMAX=CHASSIS_REAR+CASE_WALL+1.5
CASE_CENTER=((CASE_LEFT+CASE_RIGHT)/2,(CASE_YMIN+CASE_YMAX)/2)
CASE_CORNERS=[(x,y) for x in [CASE_LEFT+7.5,CASE_RIGHT-7.5] for y in [CASE_YMIN+7.5,CASE_YMAX-7.5]]
# The exit/rear lid fastener moves inboard so the rollers can reach the opening.
COVER_SEATS=[(FRONT_STATION-42 if x==CASE_RIGHT-7.5 and y>0 else x,y+(10 if y<0 else -10)) for x,y in CASE_CORNERS]
# Additional lid retention along long housings, outside the tested bearing core.
for i in range(1,math.ceil(CASE_LENGTH/120)):
 x=CASE_LEFT+CASE_LENGTH*i/math.ceil(CASE_LENGTH/120)
 if abs(x)<44:continue
 for station in STATIONS:
  if abs(x-station)<32:x=station+math.copysign(32,x-station)
 if not CASE_LEFT+20<=x<=CASE_RIGHT-20 or abs(x)<44 or any(abs(x-q[0])<20 for q in COVER_SEATS):continue
 COVER_SEATS.extend((x,y) for y in [CASE_YMIN+7.5,CASE_YMAX-7.5])
INSERT_OD=a.insert_od;INSERT_LENGTH=a.insert_length;INSERT_PILOT=a.insert_pilot
assert 4.3<=INSERT_OD<=5 and 4<=INSERT_LENGTH<=5.5 and 3.8<=INSERT_PILOT<INSERT_OD
INSERTS=[]
SIDE_INSERT_RECESS=.3
SIDE_BOSS_DEPTH=INSERT_LENGTH+SIDE_INSERT_RECESS+.4+2.
CASE_MOUNTS=[(x,z) for x in [CASE_LEFT+7.5,CASE_RIGHT-7.5] for z in [CASE_BOTTOM+10,-4.]]
FRONT_MOUNTS=[(y,z) for y in [CASE_YMIN+9,CASE_YMAX-9] for z in [CASE_BOTTOM+10,-4.]]
FRONT_INSERT_RECESS=.3
FRONT_BOSS_DEPTH=INSERT_LENGTH+FRONT_INSERT_RECESS+.4+2.
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
SQ=math.sqrt(.5);GUIDE_Y=32.;GUIDE_TOP=1.
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
WITHDRAW=2*math.pi*RP*math.ceil(((a.stroke+RACK_EXTRA)/2+FRONT_STATION+8.5)/(2*math.pi*RP))
tracks={'fixed':[],
 'cover_screws':[{'start':0,'end':.03,'delta':[0,0,35]},{'start':.03,'end':.05,'delta':[0,-180,0]}],
 'cover':[{'start':.05,'end':.10,'delta':[0,0,70]}],
 'rack':[{'start':.10,'end':.28,'delta':[WITHDRAW,0,0]}],
 'gear':[{'start':.10,'end':.28,'degrees':-WITHDRAW/RP*180/math.pi},{'start':.31,'end':.34,'delta':[0,0,20]},{'start':.34,'end':.38,'delta':[0,-55,0]}],
 'shaft':[{'start':.10,'end':.28,'degrees':-WITHDRAW/RP*180/math.pi},{'start':.64,'end':.70,'delta':[0,0,-80]}],
 'set_screw':[{'start':.10,'end':.28,'degrees':-WITHDRAW/RP*180/math.pi},{'start':.28,'end':.31,'delta':[0,-28,0]}],
 'motor_screws':[{'start':.60,'end':.62,'delta':[0,0,21]},{'start':.62,'end':.64,'delta':[0,-80,0]}],
 'motor':[{'start':.64,'end':.70,'delta':[0,0,-80]}],
 'chassis_screws':[{'start':.70,'end':.73,'delta':[0,0,24]},{'start':.73,'end':.76,'delta':[0,-90,0]}],
 'tray':[{'start':.78,'end':.82,'delta':[0,0,-80]}],
 'front_axles':[{'start':.38,'end':.42,'delta':[0,30*SQ,30*SQ]},{'start':.42,'end':.44,'delta':[0,0,20]},{'start':.44,'end':.46,'delta':[0,-45,0]}],
 'rear_axles':[{'start':.46,'end':.50,'delta':[0,-30*SQ,30*SQ]},{'start':.50,'end':.52,'delta':[0,0,20]},{'start':.52,'end':.54,'delta':[0,45,0]}],
 'upper_rollers':[{'start':.54,'end':.60,'delta':[0,0,40]}],
 'front_nuts':[{'start':.93,'end':.97,'delta':[0,-40*SQ,-40*SQ]}],
 'rear_nuts':[{'start':.93,'end':.97,'delta':[0,40*SQ,-40*SQ]}],
}
for side in ['left','right']:
 tracks['lower_'+side+'_nuts']=[{'start':.82,'end':.86,'delta':[0,45,0]}]
 tracks['lower_'+side+'_axles']=[{'start':.86,'end':.90,'delta':[0,-35,0]},{'start':.90,'end':.93,'delta':[45 if side=='right' else -45,0,0]}]
 tracks['lower_'+side+'_rollers']=[{'start':.97,'end':1,'delta':[0,0,25]}]
# Slide the retained bearing/chassis subassembly clear before lowering the tray.
for group in ['fixed','front_nuts','rear_nuts']+[g for g in tracks if g.startswith('lower_')]:
 tracks[group].extend([{'start':.765,'end':.7725,'delta':[0,0,6]},{'start':.7725,'end':.78,'delta':[-10,0,0]}])
for side in ['left','right']:
 tracks['lower_'+side+'_axles'].insert(0,{'start':.76,'end':.765,'delta':[0,-10,0]})
stages=[{'start':a,'end':b,'label':s} for a,b,s in [
 (0,.05,'Remove and park lid screws'),(.05,.10,'Lift cover'),(.10,.28,'Withdraw rack; spring floors relax'),
 (.28,.31,'Withdraw pinion set screw'),(.31,.38,'Lift and clear pinion'),(.38,.46,'Withdraw front angled axles'),
 (.46,.54,'Withdraw rear angled axles'),(.54,.60,'Lift upper rollers to access motor screws'),(.60,.64,'Remove and park motor screws'),
 (.64,.70,'Lower motor with its rear-mounted driver'),(.70,.76,'Remove and park chassis screws'),(.76,.765,'Back lower axles out 10 mm'),(.765,.7725,'Lift chassis 6 mm above rear standoffs'),(.7725,.78,'Slide bearing subassembly clear of end posts'),(.78,.82,'Lower tray with installed inserts'),
 (.82,.86,'Remove and park lower axle nuts'),(.86,.93,'Withdraw and park lower axles'),(.93,.97,'Remove angled axle nuts'),(.97,1,'Lift lower rollers')]]

def lower_lift(x,e):
 # The roller can rise until its free spring height or the rack underside stops it.
 dx=WITHDRAW*max(0,min(1,(e-.10)/.18));edge=-(a.stroke+RACK_EXTRA)/2+dx
 candidates=[-17+SPRING_PRELOAD]
 for x0,x1,z0,slope in [(edge,edge+a.stroke+RACK_EXTRA+OUTPUT_EXTENSION,-9,0)]:
  lo=max(x0,x-8);hi=min(x1,x+8)
  if lo>hi:continue
  tangent=max(lo,min(hi,x-8*slope/math.sqrt(1+slope*slope)))
  for q in [lo,hi,tangent]:candidates.append(z0+slope*(q-x0)-math.sqrt(max(0,64-(q-x)**2)))
 return max(0,min(SPRING_PRELOAD,min(candidates)+17))
def flex_lifts(e):return (lower_lift(STATIONS[0],e),lower_lift(STATIONS[1],e))
def offset(group,e):
 v=[0.,0.,lower_lift(STATIONS[0] if '_left_' in group else STATIONS[1],e) if group.startswith('lower_') else 0.]
 for t in tracks[group]:
  f=max(0,min(1,(e-t['start'])/(t['end']-t['start'])))
  for k in range(3):v[k]+=f*t.get('delta',[0,0,0])[k]
 return tuple(v)
def angle(group,e):return sum(max(0,min(1,(e-t['start'])/(t['end']-t['start'])))*t.get('degrees',0) for t in tracks[group])
# Broad upper platform, deep rear web and lower crossmember, all one printed body.
base=box(CHASSIS_WIDTH,CHASSIS_REAR-CHASSIS_FRONT,7,(CHASSIS_CENTER_X,(CHASSIS_REAR+CHASSIS_FRONT)/2,.5)).fuse(box(CHASSIS_WIDTH,22.1,26,(CHASSIS_CENTER_X,32.45,-16)))
for p in UPPER:base=base.fuse(acyl(9.5,7,p['center'],p['axis'],-9.5))
# The motor leaves straight down; the 5 mm mounting land is integral.
base=base.cut(box(MOTOR_SIZE+.8,MOTOR_SIZE+.8,80,(0,MOTOR_Y,-43))).cut(cyl(11.4,9,0,MOTOR_Y,-4))
motor_holes=[(x,y+MOTOR_Y) for x in [-MOTOR_PITCH/2,MOTOR_PITCH/2] for y in [-MOTOR_PITCH/2,MOTOR_PITCH/2]]
base=holes(base,motor_holes,1.7,-4,12)
for x,y in motor_holes:
 base=base.cut(cq.Solid.makeCone(1.7,3.2,1.5,cq.Vector(x,y,-1.5),cq.Vector(0,0,1)))
 base=base.cut(cyl(3.5,15,x,y,0))
CHASSIS_MOUNTS=[(x,FRONT_MOUNT_Y) for x in MOUNT_XS]+[(x,REAR_MOUNT_Y) for x in REAR_MOUNT_XS]
base=holes(base,[(x,FRONT_MOUNT_Y) for x in MOUNT_XS],1.7,-4,14)
base=holes(base,[(x,REAR_MOUNT_Y) for x in REAR_MOUNT_XS],2.2,-4,14)
for x,y in CHASSIS_MOUNTS:base=base.cut(box(10,10,14,(x,y,7)))
# A six-millimetre neck joins the original tooth spine to a stiff beveled guide.
RAIL_PROFILE=[(29,14),(35,14),(35,1),(40,-4),(36,-9),(28,-9),(24,-4),(29,1)]
def rail_shape(length,clearance=0):
 w=cq.Workplane('YZ').polyline(RAIL_PROFILE).close()
 if clearance:w=w.offset2D(clearance)
 return w.extrude(length).translate((-length/2,0,0)).val()
base=base.cut(rail_shape(CHASSIS_WIDTH+2,1.0).translate((CHASSIS_CENTER_X,0,0)))
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
# Clearance notches let intermediate lid posts/webs pass through the long
# chassis. These seats stay clear of the motor and local spring bays.
for x,y in COVER_SEATS:
 if x in [CASE_LEFT+7.5,CASE_RIGHT-7.5]:base=base.cut(cyl(5.3,80,x,y,-50))
 else:base=base.cut(cq.Workplane('XY').slot2D(20.6,10.6).extrude(80).translate((x+5,y,-50)).val())
 if x in [CASE_LEFT+7.5,CASE_RIGHT-7.5]:
  x0,x1=(CASE_LEFT-1,x) if x<CASE_CENTER[0] else (x,CASE_RIGHT+1)
  base=base.cut(box(x1-x0,10.6,80,((x0+x1)/2,y,-10)))
 else:
  y0,y1=(CASE_YMIN-1,y) if y<0 else (y,CASE_YMAX+1)
  base=base.cut(box(20.6,y1-y0,80,(x+5,(y0+y1)/2,-10)))
# Top mounting posts also pass through the extended chassis end.
for x,y in CASE_CORNERS:
 base=base.cut(cyl(5.8,80,x,y,-50))
 x0,x1=(CASE_LEFT-1,x) if x<CASE_CENTER[0] else (x,CASE_RIGHT+1)
 base=base.cut(box(x1-x0,11.6,80,((x0+x1)/2,y,-10)))
# Clear the existing internal mounting columns without changing the case outline.
for x in [CASE_LEFT+7.5,CASE_RIGHT-7.5]:
 y0=CASE_YMAX-SIDE_BOSS_DEPTH-.8
 base=base.cut(box(11.6,CASE_YMAX+1-y0,80,(x,(y0+CASE_YMAX+1)/2,-10)))
for y in [CASE_YMIN+9,CASE_YMAX-9]:
 x0=CASE_RIGHT-FRONT_BOSS_DEPTH-.8
 base=base.cut(box(CASE_RIGHT+1-x0,11.6,80,((x0+CASE_RIGHT+1)/2,y,-10)))
# Broad, integral spring floors support solid lower axle blocks. No separate springs.
BOTTOM=[]
for x in STATIONS:
 y=32.+(1 if x>0 else -1);c=(x,y,-17.)
 BOTTOM.append(dict(x=x,center=c,side='left' if x<0 else 'right'))
 # Retain the central spine and upper bearing roof; open the spring bay below.
 base=base.cut(box(31,22.1,19.5,(x-math.copysign(3.5,x),32.45,-19.35)))
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
 leaf=leaf.translate((x-math.copysign(23,x),0,0))
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
  if any(abs(c.x-(p['x']-math.copysign(19,p['x'])))<1e-5 for p in BOTTOM) and abs(c.z-(-27+SPRING_THICKNESS))<1e-5 and bb.ylen>1:
   blends.append(edge);continue
  for p,d in zip(BOTTOM,deflections):
   z=-27+SPRING_THICKNESS-d
   inner=abs(c.x-(p['x']-math.copysign(5,p['x'])))<1e-5 and bb.ylen>1 and c.y>p['center'][1]+BODY_FRONT
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
m=MODULE;n=N;rp=RP;rb=rp*math.cos(math.radians(PRESSURE_ANGLE));ra=rp+m;rr=rp-1.25*m
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
L=a.stroke+RACK_EXTRA;left=-L/2;right=L/2+OUTPUT_EXTENSION;pitch=math.pi*m;alpha=math.tan(math.radians(PRESSURE_ANGLE));wall=.6
OUTPUT_PAD_SIZE=18.;OUTPUT_PAD_Y=(ROOT_Y+BACK_Y)/2;OUTPUT_PAD_BOTTOM=3.;OUTPUT_PAD_TOP=21.
OUTPUT_MOUNT_PITCH=9.;OUTPUT_INSERT_RECESS=.3
OUTPUT_MOUNTS=[(right+OUTPUT_PAD_SIZE/2+dx,OUTPUT_PAD_Y+dy) for dx in [-OUTPUT_MOUNT_PITCH/2,OUTPUT_MOUNT_PITCH/2] for dy in [-OUTPUT_MOUNT_PITCH/2,OUTPUT_MOUNT_PITCH/2]]
OUTPUT_INSERTS=[]
centers=[i*pitch for i in range(-TOOTH_HALF_COUNT,TOOTH_HALF_COUNT+1)]
def make_rack(preload):
 half=lambda y:pitch/4+(y-PITCH_Y)*alpha+preload
 h0=half(TIP_Y);h1=half(ROOT_Y)
 rack=box(right-left,BACK_Y-ROOT_Y,8,((left+right)/2,(ROOT_Y+BACK_Y)/2,17))
 for x in centers:
  tooth=cq.Workplane('XY').polyline([(x-h0,TIP_Y),(x+h0,TIP_Y),(x+h1,ROOT_Y),(x-h1,ROOT_Y)]).close().extrude(8).translate((0,0,13)).val()
  radius=h1-wall;cap_y=RELIEF_Y-radius
  slot=(cq.Workplane('XY').moveTo(x-h0+wall,TIP_Y-.05).lineTo(x+h0-wall,TIP_Y-.05)
        .lineTo(x+radius,ROOT_Y).lineTo(x+radius,cap_y)
        .threePointArc((x,RELIEF_Y),(x-radius,cap_y)).lineTo(x-radius,ROOT_Y)
        .close().extrude(8.2).translate((0,0,12.9)).val())
  rack=rack.fuse(tooth).cut(slot)
 # Semicircular caps tangent to both straight walls avoid sharp root corners.
 gaps=[(x0+h1,x1-h1) for x0,x1 in zip(centers[:-1],centers[1:])]
 end_gap=pitch-2*h1
 gaps += [(centers[0]-h1-end_gap,centers[0]-h1),(centers[-1]+h1,centers[-1]+h1+end_gap)]
 for lo,hi in gaps:
  radius=(hi-lo)/2;mid=(lo+hi)/2;cap_y=RELIEF_Y-radius
  relief=(cq.Workplane('XY').moveTo(lo,ROOT_Y).lineTo(hi,ROOT_Y)
          .lineTo(hi,cap_y).threePointArc((mid,RELIEF_Y),(lo,cap_y))
          .close().extrude(8.2).translate((0,0,12.9)).val())
  rack=rack.cut(relief)
 # Beveled faces carry downward/inward reactions; the bottom is a flat raceway.
 rack=rack.fuse(rail_shape(right-left).translate(((left+right)/2,0,0)))
 # Square insertion end: no ramp/chamfer cut. The roller rim cams the spring down.
 # The pad shares the Z=21 tooth face, so it starts on the print bed.
 pad=box(OUTPUT_PAD_SIZE,OUTPUT_PAD_SIZE,OUTPUT_PAD_TOP-OUTPUT_PAD_BOTTOM,(right+OUTPUT_PAD_SIZE/2,OUTPUT_PAD_Y,(OUTPUT_PAD_TOP+OUTPUT_PAD_BOTTOM)/2))
 for x,y in OUTPUT_MOUNTS:
  face=OUTPUT_PAD_TOP-OUTPUT_INSERT_RECESS
  pad=pad.cut(cyl(INSERT_PILOT/2,INSERT_LENGTH+.4+OUTPUT_INSERT_RECESS+.1,x,y,face-INSERT_LENGTH-.4))
  pad=pad.cut(cyl(INSERT_OD/2+.1,OUTPUT_INSERT_RECESS+.1,x,y,face))
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
central_relief_radius=pitch/4+1.25*m*alpha+a.preload-wall
intertooth_relief_radius=(pitch-2*(central_relief_radius+wall))/2
rack=make_rack(a.preload);add('04 Beveled compliant rack',rack,'#42d6ba','rack',True)
for x,y in OUTPUT_MOUNTS:
 face=OUTPUT_PAD_TOP-OUTPUT_INSERT_RECESS
 insert=cyl(INSERT_OD/2,INSERT_LENGTH,x,y,face-INSERT_LENGTH).cut(cyl(1.6,INSERT_LENGTH,x,y,face-INSERT_LENGTH))
 name=f'M3 heat-set insert output {x:g} {y:g}'
 add(name,insert,'#d4a54a','rack');parts[-1]['embedded_host']='04 Beveled compliant rack'
 OUTPUT_INSERTS.append(dict(name=name,position=[x,y,face],axis=[0,0,1],purpose='output mount'))

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
# Two printable enclosure halves. The rear controller is deliberately not represented
# by a guessed solid: its mounting plane stays 4 mm outside the motor aperture.
def shell_box(z0,z1):
 return box(CASE_LENGTH,CASE_YMAX-CASE_YMIN,z1-z0,(*CASE_CENTER,(z0+z1)/2))
def rect_cut(x0,x1,y0,y1,z0,z1):return box(x1-x0,y1-y0,z1-z0,((x0+x1)/2,(y0+y1)/2,(z0+z1)/2))
tray=shell_box(CASE_BOTTOM,CASE_SPLIT).cut(rect_cut(CASE_LEFT+CASE_WALL,CASE_RIGHT-CASE_WALL,CASE_YMIN+CASE_WALL,CASE_YMAX-CASE_WALL,CASE_BOTTOM+CASE_WALL,CASE_SPLIT+1))
cover=shell_box(CASE_SPLIT+.4,CASE_TOP).cut(rect_cut(CASE_LEFT+CASE_WALL,CASE_RIGHT-CASE_WALL,CASE_YMIN+CASE_WALL,CASE_YMAX-CASE_WALL,CASE_SPLIT,CASE_TOP-CASE_WALL))
tray_webs=[];cover_webs=[]
def heat_insert(shape,x,y,top,purpose):
 # Printed pilot is intentionally smaller than the knurled insert. This modeled
 # overlap is displaced by heat during installation, not a moving-part collision.
 shape=shape.cut(cyl(INSERT_PILOT/2,INSERT_LENGTH+.4,x,y,top-INSERT_LENGTH-.4))
 insert=cyl(INSERT_OD/2,INSERT_LENGTH,x,y,top-INSERT_LENGTH).cut(cyl(1.6,INSERT_LENGTH,x,y,top-INSERT_LENGTH))
 name=f'M3 heat-set insert {purpose} {x:g} {y:g}'
 add(name,insert,'#d4a54a','tray')
 parts[-1]['embedded_host']='05 Mounting enclosure tray'
 INSERTS.append(dict(name=name,position=[x,y,top],axis=[0,0,1],purpose=purpose))
 return shape
# M3 chassis fasteners replace enclosure nuts. Bearing through-bolts remain M5.
for x in MOUNT_XS:
 tray=tray.fuse(cyl(6,-3-CASE_BOTTOM,x,FRONT_MOUNT_Y,CASE_BOTTOM))
 tray=tray.fuse(rect_cut(x-2,x+2,CASE_YMIN,FRONT_MOUNT_Y,CASE_BOTTOM,-3))
 tray=tray.cut(cyl(1.7,-3-CASE_BOTTOM+1,x,FRONT_MOUNT_Y,CASE_BOTTOM-1))
 tray=heat_insert(tray,x,FRONT_MOUNT_Y,-3,'chassis')
 bolt=cyl(1.45,10,x,FRONT_MOUNT_Y,-10).fuse(cyl(2.75,3,x,FRONT_MOUNT_Y,0)).cut(cyl(1.25,2,x,FRONT_MOUNT_Y,1))
 add(f'M3x10 chassis screw {x}',bolt,'#a5b5c1','chassis_screws')
for x in REAR_MOUNT_XS:tray=tray.fuse(rect_cut(x-6,x+6,CHASSIS_REAR-1.5,CASE_YMAX,CASE_BOTTOM,-3))
# Rear chassis holes now bolt directly into floor-supported, wall-tied posts.
# Keep the existing chassis holes; rear M3x16 screws reach recessed inserts.
for x in REAR_MOUNT_XS:
 post=cyl(4,-3-CASE_BOTTOM,x,REAR_MOUNT_Y,CASE_BOTTOM)
 for bearing in UPPER:
  if bearing['side']=='rear':post=post.cut(acyl(4.62+BEARING_GAP,4.3,bearing['center'],bearing['axis'],-13.))
 tray=tray.fuse(post)
 tray=tray.fuse(rect_cut(x-2,x+2,REAR_MOUNT_Y,CASE_YMAX,CASE_BOTTOM,-3))
 tray=tray.cut(cyl(1.7,-3-CASE_BOTTOM+1,x,REAR_MOUNT_Y,CASE_BOTTOM-1))
 # Recess the insert below the neighboring M5 nut clearance; install before chassis.
 tray=tray.cut(cyl(INSERT_OD/2+.1,6.1,x,REAR_MOUNT_Y,-9))
 tray=heat_insert(tray,x,REAR_MOUNT_Y,-9,'rear chassis')
 bolt=cyl(1.45,16,x,REAR_MOUNT_Y,-16).fuse(cyl(2.75,3,x,REAR_MOUNT_Y,0)).cut(cyl(1.25,2,x,REAR_MOUNT_Y,1))
 add(f'M3x16 rear chassis screw {x}',bolt,'#a5b5c1','chassis_screws')
# Four full-height, wall-connected posts transfer top mounting loads directly
# to the tray. The lid lifts over them through clearance openings.
for x,y in CASE_CORNERS:
 tray=tray.fuse(cyl(5,CASE_TOP-CASE_BOTTOM,x,y,CASE_BOTTOM))
 web=(CASE_LEFT,x,y-5,y+5,CASE_BOTTOM,CASE_TOP) if x<CASE_CENTER[0] else (x,CASE_RIGHT,y-5,y+5,CASE_BOTTOM,CASE_TOP)
 tray=tray.fuse(rect_cut(*web));tray_webs.append(web)
 cover=cover.cut(cyl(5.4,CASE_TOP-CASE_SPLIT+2,x,y,CASE_SPLIT-1))
 tray=heat_insert(tray,x,y,CASE_TOP,'top mount')
# Separate recessed lid screws keep the top mounting face flat.
for x,y in COVER_SEATS:
 tray=tray.fuse(cyl(4.5,CASE_SPLIT-CASE_BOTTOM,x,y,CASE_BOTTOM))
 cover=cover.fuse(cyl(4.5,CASE_TOP-CASE_SPLIT,x,y,CASE_SPLIT))
 if x in [CASE_LEFT+7.5,CASE_RIGHT-7.5]:
  xy=(CASE_LEFT,x,y-4.5,y+4.5) if x<CASE_CENTER[0] else (x,CASE_RIGHT,y-4.5,y+4.5)
 else:xy=(x-4.5,x+4.5,CASE_YMIN,y) if y<0 else (x-4.5,x+4.5,y,CASE_YMAX)
 web=(*xy,CASE_BOTTOM,CASE_SPLIT);tray=tray.fuse(rect_cut(*web));tray_webs.append(web)
 web=(*xy,CASE_SPLIT,CASE_TOP);cover=cover.fuse(rect_cut(*web));cover_webs.append(web)
 tray=tray.cut(cyl(1.7,CASE_SPLIT-CASE_BOTTOM+1,x,y,CASE_BOTTOM-1))
 tray=heat_insert(tray,x,y,CASE_SPLIT,'lid')
 cover=cover.cut(cyl(1.7,CASE_TOP-CASE_SPLIT+2,x,y,CASE_SPLIT-1))
 head_z=CASE_TOP-3.3
 cover=cover.cut(cyl(3.1,4.3,x,y,head_z))
 bolt=cyl(1.45,20,x,y,head_z-20).fuse(cyl(2.75,3,x,y,head_z)).cut(cyl(1.25,2,x,y,head_z+1))
 add(f'M3x20 recessed lid screw {x:g} {y:g}',bolt,'#a5b5c1','cover_screws')
# Re-cut the top-post openings after adding adjoining lid screw bosses.
for x,y in CASE_CORNERS:
 cover=cover.cut(cyl(5.4,CASE_TOP-CASE_SPLIT+2,x,y,CASE_SPLIT-1))
 notch=(CASE_LEFT-1,x,y-5.4,y+5.4,CASE_SPLIT-1,CASE_TOP+1) if x<CASE_CENTER[0] else (x,CASE_RIGHT+1,y-5.4,y+5.4,CASE_SPLIT-1,CASE_TOP+1)
 cover=cover.cut(rect_cut(*notch))
# Rectangular motor rear opening is larger than the body; driver stays outside.
tray=tray.cut(rect_cut(-MOTOR_SIZE/2-1,MOTOR_SIZE/2+1,MOTOR_Y-MOTOR_SIZE/2-1,MOTOR_Y+MOTOR_SIZE/2+1,CASE_BOTTOM-1,CASE_BOTTOM+CASE_WALL+1))
# Only the smooth output tongue passes through this portal during normal motion.
portal=rect_cut(CASE_RIGHT-CASE_WALL-1,CASE_RIGHT+1,min(ROOT_Y,24)-1,max(BACK_Y,40)+1,-10,22)
tray=tray.cut(portal);cover=cover.cut(portal)
REAR_OPENING_YZ=[min(TIP_Y,24)-1,max(BACK_Y,40)+1,-10,22]
if PASS_THROUGH:
 rear_portal=rect_cut(CASE_LEFT-1,CASE_LEFT+CASE_WALL+1,*REAR_OPENING_YZ)
 tray=tray.cut(rear_portal);cover=cover.cut(rear_portal)
# Set-screw service notch is accessible once the lid is removed.
tray=tray.cut(rect_cut(-3,3,CASE_YMIN-1,CASE_YMIN+CASE_WALL+1,3.5,CASE_SPLIT+1))
# Ventilate the front motor wall while leaving the rear driver exposed.
for z in [CASE_BOTTOM+10,CASE_BOTTOM+17,CASE_BOTTOM+24]:
 if z<-9:tray=tray.cut(rect_cut(-10,10,CASE_YMIN-1,CASE_YMIN+CASE_WALL+1,z-1,z+1))
# Reinforcement stays inside the flat side wall. Floor-connected columns print
# upward without a projecting ledge and join the existing corner-post structure.
for x in [CASE_LEFT+7.5,CASE_RIGHT-7.5]:
 tray=tray.fuse(rect_cut(x-5,x+5,CASE_YMAX-SIDE_BOSS_DEPTH,CASE_YMAX,CASE_BOTTOM,1.))
for y in [CASE_YMIN+9,CASE_YMAX-9]:
 tray=tray.fuse(rect_cut(CASE_RIGHT-FRONT_BOSS_DEPTH,CASE_RIGHT,y-5,y+5,CASE_BOTTOM,1.))
for x,z in CASE_MOUNTS:
 face=CASE_YMAX-SIDE_INSERT_RECESS
 tray=tray.cut(ycyl(INSERT_PILOT/2,INSERT_LENGTH+.4+SIDE_INSERT_RECESS+.1,x,face-INSERT_LENGTH-.4,z))
 tray=tray.cut(ycyl(INSERT_OD/2+.1,SIDE_INSERT_RECESS+.1,x,face,z))
 insert=ycyl(INSERT_OD/2,INSERT_LENGTH,x,face-INSERT_LENGTH,z).cut(ycyl(1.6,INSERT_LENGTH,x,face-INSERT_LENGTH,z))
 name=f'M3 heat-set insert side mount {x:g} {z:g}'
 add(name,insert,'#d4a54a','tray');parts[-1]['embedded_host']='05 Mounting enclosure tray'
 INSERTS.append(dict(name=name,position=[x,face,z],axis=[0,1,0],purpose='side mount'))
# Flush exit-face mounts are carried by inward columns, outside the rack portal.
for y,z in FRONT_MOUNTS:
 face=CASE_RIGHT-FRONT_INSERT_RECESS;c=(face,y,z);u=(1,0,0)
 tray=tray.cut(acyl(INSERT_PILOT/2,INSERT_LENGTH+.4+FRONT_INSERT_RECESS+.1,c,u,-INSERT_LENGTH-.4))
 tray=tray.cut(acyl(INSERT_OD/2+.1,FRONT_INSERT_RECESS+.1,c,u))
 insert=ring(INSERT_OD/2,1.6,INSERT_LENGTH,c,u,-INSERT_LENGTH)
 name=f'M3 heat-set insert front mount {y:g} {z:g}'
 add(name,insert,'#d4a54a','tray');parts[-1]['embedded_host']='05 Mounting enclosure tray'
 INSERTS.append(dict(name=name,position=list(c),axis=list(u),purpose='front mount'))
# Local clearances keep the existing bearing bolts/nuts clear of the end posts.
# The lower axle rises with the relaxed spring before the tray is removed.
p=next(p for p in BOTTOM if p['x']==FRONT_STATION);x,y,z=p['center'];rad=2.45+BEARING_GAP
clear=ycyl(rad,26.6,x,y-3.6,z).fuse(ycyl(rad,26.6,x,y-3.6,z+SPRING_PRELOAD)).fuse(box(2*rad,26.6,SPRING_PRELOAD,(x,y+9.7,z+SPRING_PRELOAD/2)))
tray=tray.cut(clear)
p=next(p for p in UPPER if p['x']==FRONT_STATION and p['side']=='rear');c,u=p['center'],p['axis']
clear=acyl(4.62+BEARING_GAP,4.3,c,u,-13.).fuse(acyl(2.45+BEARING_GAP,23.4,c,u,-14.)).fuse(acyl(8+BEARING_GAP,6.6,c,u,-3.3))
# Allow the retained upper nut to rise with the chassis before its X slide.
clear=clear.fuse(acyl(4.62+BEARING_GAP,4.3,c,u,-13.).translate((0,0,6)))
for dz in [1,2,3,4,5]:clear=clear.fuse(acyl(4.62+BEARING_GAP,4.3,c,u,-13.).translate((0,0,dz)))
tray=tray.cut(clear);cover=cover.cut(clear)
tray=tray.clean();cover=cover.clean()
add('05 Mounting enclosure tray',tray,'#314959','tray',True)
add('06 Removable enclosure cover',cover,'#d4dee5','cover',True)
# Conservative boxes for hollow enclosure broad-phase checks. Each comes from
# an uncut construction primitive; holes only remove material. Exact coverage
# is checked below before any pair is excluded by these boxes.
def bounds_box(x0,x1,y0,y1,z0,z1):return (x0,x1,y0,y1,z0,z1)
cover_boxes=[
 bounds_box(CASE_LEFT,CASE_RIGHT,CASE_YMIN,CASE_YMAX,CASE_TOP-CASE_WALL,CASE_TOP),
 bounds_box(CASE_LEFT,CASE_RIGHT,CASE_YMIN,CASE_YMIN+CASE_WALL,CASE_SPLIT+.4,CASE_TOP),
 bounds_box(CASE_LEFT,CASE_RIGHT,CASE_YMAX-CASE_WALL,CASE_YMAX,CASE_SPLIT+.4,CASE_TOP),
 ]
for y0,y1 in [(CASE_YMIN,CASE_YMIN+7.5-5.4),(CASE_YMIN+7.5+5.4,CASE_YMAX-7.5-5.4),(CASE_YMAX-7.5+5.4,CASE_YMAX)]:
 cover_boxes.extend([bounds_box(CASE_LEFT,CASE_LEFT+CASE_WALL,y0,y1,CASE_SPLIT+.4,CASE_TOP),bounds_box(CASE_RIGHT-CASE_WALL,CASE_RIGHT,y0,y1,CASE_SPLIT+.4,CASE_TOP)])
cover_boxes += [bounds_box(x-4.5,x+4.5,y-4.5,y+4.5,CASE_SPLIT,CASE_TOP) for x,y in COVER_SEATS]
cover_boxes += cover_webs
mx0=-MOTOR_SIZE/2-1;mx1=MOTOR_SIZE/2+1;my0=MOTOR_Y-MOTOR_SIZE/2-1;my1=MOTOR_Y+MOTOR_SIZE/2+1
tray_boxes=[
 bounds_box(CASE_LEFT,mx0,CASE_YMIN,CASE_YMAX,CASE_BOTTOM,CASE_BOTTOM+CASE_WALL),
 bounds_box(mx1,CASE_RIGHT,CASE_YMIN,CASE_YMAX,CASE_BOTTOM,CASE_BOTTOM+CASE_WALL),
 bounds_box(mx0,mx1,CASE_YMIN,my0,CASE_BOTTOM,CASE_BOTTOM+CASE_WALL),
 bounds_box(mx0,mx1,my1,CASE_YMAX,CASE_BOTTOM,CASE_BOTTOM+CASE_WALL),
 bounds_box(CASE_LEFT,CASE_RIGHT,CASE_YMIN,CASE_YMIN+CASE_WALL,CASE_BOTTOM,CASE_SPLIT),
 bounds_box(CASE_LEFT,CASE_RIGHT,CASE_YMAX-CASE_WALL,CASE_YMAX,CASE_BOTTOM,CASE_SPLIT),
 bounds_box(CASE_LEFT,CASE_LEFT+CASE_WALL,CASE_YMIN,CASE_YMAX,CASE_BOTTOM,CASE_SPLIT),
 bounds_box(CASE_RIGHT-CASE_WALL,CASE_RIGHT,CASE_YMIN,CASE_YMAX,CASE_BOTTOM,CASE_SPLIT),
 bounds_box(CHASSIS_LEFT-2,CHASSIS_RIGHT+2,CHASSIS_REAR-1.5,CASE_YMAX,CASE_BOTTOM,-3)]
tray_boxes += [bounds_box(CASE_RIGHT-FRONT_BOSS_DEPTH,CASE_RIGHT,y-5,y+5,CASE_BOTTOM,1.) for y in [CASE_YMIN+9,CASE_YMAX-9]]
tray_boxes += [bounds_box(x-5,x+5,y-5,y+5,CASE_BOTTOM,CASE_TOP) for x,y in CASE_CORNERS]
tray_boxes += [bounds_box(x-4.5,x+4.5,y-4.5,y+4.5,CASE_BOTTOM,CASE_SPLIT) for x,y in COVER_SEATS]
for x in MOUNT_XS:
 tray_boxes.extend([bounds_box(x-6,x+6,FRONT_MOUNT_Y-6,FRONT_MOUNT_Y+6,CASE_BOTTOM,-3),bounds_box(x-2,x+2,CASE_YMIN,FRONT_MOUNT_Y,CASE_BOTTOM,-3)])
for x in REAR_MOUNT_XS:
 tray_boxes.extend([bounds_box(x-4,x+4,REAR_MOUNT_Y-4,REAR_MOUNT_Y+4,CASE_BOTTOM,-3),bounds_box(x-2,x+2,REAR_MOUNT_Y,CASE_YMAX,CASE_BOTTOM,-3)])
tray_boxes += [bounds_box(x-5,x+5,CASE_YMAX-SIDE_BOSS_DEPTH,CASE_YMAX,CASE_BOTTOM,1.) for x in [CASE_LEFT+7.5,CASE_RIGHT-7.5]]+tray_webs


FRONT_FIXTURE_OPENING=[min(ROOT_Y,24,OUTPUT_PAD_Y-OUTPUT_PAD_SIZE/2)-1,max(BACK_Y,40,OUTPUT_PAD_Y+OUTPUT_PAD_SIZE/2)+1,-10,22]

# Clear obsolete generated meshes rather than leave old-bearing parts in the bundle.
if not a.skip_export:
 expected={p['name'].replace(' ','_')+'.stl' for p in parts if p['printed']}
 for f in (out/'downloads').glob('*.stl'):
  if f.name not in expected:f.unlink()
 scene=[];assembly=cq.Assembly(name=LABEL+'_R24')
 for p in parts:
  s=p['shape'];vs,ts=s.tessellate(.06,.12)
  scene.append({k:p[k] for k in ['name','color','group','printed']}|{k:p[k] for k in ['spinAxis','spinCenter','spinSign','flex_chassis','embedded_host'] if k in p}|{'vertices':[[round(v.x,5),round(v.y,5),round(v.z,5)] for v in vs],'triangles':ts})
  assembly.add(s,name=p['name'].replace(' ','_'),color=cq.Color(p['color']))
  if p['printed']:cq.exporters.export(base_print if p.get('flex_chassis') else s,str(out/'downloads'/(p['name'].replace(' ','_')+'.stl')),tolerance=.04,angularTolerance=.1)
 assembly.save(str(out/'downloads'/(LABEL+'.step')))
 bounds=[p['shape'].BoundingBox() for p in parts]
 envelope=[max(getattr(b,k+'max') for b in bounds)-min(getattr(b,k+'min') for b in bounds) for k in ['x','y','z']]
 data={'geometrySourceSha256':__import__('hashlib').sha256(pathlib.Path(__file__).read_text().split('\n# Clear obsolete generated meshes')[0].encode()).hexdigest(),'revision':24,'enclosureVariant':a.enclosure,'enclosedHousingLength':ENCLOSED_MIN_CASE_LENGTH,'rearOpeningYZ':REAR_OPENING_YZ if PASS_THROUGH else None,'maximumRearProjection':max(0,CASE_LEFT-(left-a.stroke/2)),'envelope':envelope,'motor':MOTOR_NAME,'motorSize':MOTOR_SIZE,'motorPitch':MOTOR_PITCH,'motorDepth':MOTOR_DEPTH,'rotationPivot':list(PIVOT),'pinionTeeth':N,'pressureAngle':PRESSURE_ANGLE,'withdrawal':WITHDRAW,'bearingClearance':BEARING_GAP,'hardwareClearance':HARDWARE_GAP,'chassisFootprint':[CHASSIS_WIDTH,CHASSIS_REAR-CHASSIS_FRONT],'stroke':a.stroke,'rackLength':right-left,'rackLeft':left,'rackRight':right,'rackWithdrawalStart':.10,'rackWithdrawalEnd':.28,'toothModule':MODULE,'toothPitch':pitch,'actuatorLength':CASE_LENGTH,'minimumActuatorLength':MIN_CASE_LENGTH,'caseBounds':[CASE_LEFT,CASE_RIGHT,CASE_YMIN,CASE_YMAX,CASE_BOTTOM,CASE_TOP],'caseMounts':CASE_MOUNTS,'frontMounts':FRONT_MOUNTS,'frontMountX':CASE_RIGHT,'frontMountInsertRecess':FRONT_INSERT_RECESS,'frontFixtureOpeningYZ':FRONT_FIXTURE_OPENING,'sideMountThread':'M3','sideMountY':CASE_YMAX,'sideMountInsertRecess':SIDE_INSERT_RECESS,'topMounts':CASE_CORNERS,'topMountZ':CASE_TOP,'coverScrewCount':len(COVER_SEATS),'insertCount':len(INSERTS)+len(OUTPUT_INSERTS),'enclosureInsertCount':len(INSERTS),'outputInsertCount':len(OUTPUT_INSERTS),'outputMounts':OUTPUT_MOUNTS,'outputMountPitch':OUTPUT_MOUNT_PITCH,'outputMountZ':OUTPUT_PAD_TOP,'outputPadCenterY':OUTPUT_PAD_Y,'rackBackboneCenterY':(ROOT_Y+BACK_Y)/2,'outputPadSize':[OUTPUT_PAD_SIZE,OUTPUT_PAD_SIZE,OUTPUT_PAD_TOP-OUTPUT_PAD_BOTTOM],'outputInsertRecess':OUTPUT_INSERT_RECESS,'insertOD':INSERT_OD,'insertLength':INSERT_LENGTH,'insertPilot':INSERT_PILOT,'motorRearZ':-8-MOTOR_DEPTH,'driverOpening':[MOTOR_SIZE+2,MOTOR_SIZE+2],'toothTravelRight':TOOTH_XMAX+a.stroke/2,'rackBackboneWidth':a.rack_backbone_width,'headReliefEndX':max(STATIONS)+a.stroke/2+4.75+HARDWARE_GAP,'solidRackEndLength':right-(max(STATIONS)+a.stroke/2+4.75+HARDWARE_GAP),'squareInsertionEnd':True,'pitchRadius':rp,'shaftDiameter':a.shaft_diameter,'shaftFlatDepth':a.shaft_flat_depth,'shaftClearance':a.shaft_clearance,'boreDiameter':2*BORE_R,'boreFlatY':BORE_FLAT_Y,'setScrewZ':SET_Z,'chassisReleaseShift':10.,'chassisReleaseLift':6.,'lowerAxleServiceRetraction':10.,'bearingStationRule':'fixed rear station; front station follows exit','exitBearingRimOffset':EXIT_BEARING_OFFSET-8,'stationSpacing':FRONT_STATION-REAR_STATION,'stationXs':STATIONS,'exitBearingOffset':EXIT_BEARING_OFFSET,'chassisScrewCount':len(CHASSIS_MOUNTS),'rearChassisScrewCount':len(REAR_MOUNT_XS),'rearChassisScrewLength':16,'rearChassisInsertRecess':6,'upperBearingAngle':45,'springPreload':SPRING_PRELOAD,'springThickness':SPRING_THICKNESS,'springLeafLength':LEAF_LENGTH,'springLeafWidth':FLOOR_WIDTH,'springLeafSlopeDeg':math.degrees(math.atan(1.5*SPRING_PRELOAD/LEAF_LENGTH)),'springTravelCheck':SPRING_CHECK_TRAVEL,'rampLength':RAMP_LENGTH,'rampRise':RAMP_RISE,'lowerContactY':[31,33],'chassisMounts':CHASSIS_MOUNTS,'bearingType':'625ZZ','bearingCount':6,'preloadPerFlank':a.preload,'wallThickness':wall,'rootRelief':'tangent semicircular end caps','centralReliefRadius':central_relief_radius,'intertoothReliefRadius':intertooth_relief_radius,'tracks':tracks,'stages':stages,'parts':scene}
 # Exact sampled CAD states preserve wall fillets while the floors relax.
 states=[]
 for l,r in [(SPRING_PRELOAD*k/12,0) for k in range(1,13)]+[(SPRING_PRELOAD,SPRING_PRELOAD*k/12) for k in range(1,13)]:
  shape=chassis((SPRING_PRELOAD-l,SPRING_PRELOAD-r));vs,ts=shape.tessellate(.12,.22)
  states.append({'leftLift':l,'rightLift':r,'vertices':[[round(v.x,5),round(v.y,5),round(v.z,5)] for v in vs],'triangles':ts})
 with __import__('gzip').open(out/'assets'/'spring-states.json.gz','wt') as f:f.write(json.dumps(states,separators=(',',':')))
 (out/'assets'/'spring-states.json').unlink(missing_ok=True)
 data['springStateStep']=SPRING_PRELOAD/12
 (out/'assets'/'assembly.json').write_text(json.dumps(data,separators=(',',':')))
 print('Exported',len(parts),'parts / six 625ZZ bearings',flush=True)
if a.check:
 # Remove the already-cut output portal from conservative boxes. Otherwise
 # the empty portal falsely triggers costly full rack/shell booleans.
 def subtract_box(b,c):
  lo=[max(b[k],c[k]) for k in [0,2,4]];hi=[min(b[k],c[k]) for k in [1,3,5]]
  if any(lo[k]>=hi[k] for k in range(3)):return [b]
  x0,x1,y0,y1,z0,z1=b;u,v,w=lo;U,V,W=hi
  candidates=[(x0,u,y0,y1,z0,z1),(U,x1,y0,y1,z0,z1),(u,U,y0,v,z0,z1),(u,U,V,y1,z0,z1),(u,U,v,V,z0,w),(u,U,v,V,W,z1)]
  return [q for q in candidates if all(q[k+1]>q[k] for k in [0,2,4])]
 portal_box=(CASE_RIGHT-CASE_WALL-1,CASE_RIGHT+1,min(ROOT_Y,24)-1,max(BACK_Y,40)+1,-10,22)
 tray_boxes=[q for b in tray_boxes for q in subtract_box(b,portal_box)]
 cover_boxes=[q for b in cover_boxes for q in subtract_box(b,portal_box)]
 if PASS_THROUGH:
  rear_portal_box=(CASE_LEFT-1,CASE_LEFT+CASE_WALL+1,*REAR_OPENING_YZ)
  tray_boxes=[q for b in tray_boxes for q in subtract_box(b,rear_portal_box)]
  cover_boxes=[q for b in cover_boxes for q in subtract_box(b,rear_portal_box)]
 # The rack's teeth sit above the tray opening, while its lower guide runs
 # through it. Separate boxes avoid treating that empty corner as material.
 rack_boxes=[(left,right,TIP_Y-.001,BACK_Y,13,21),(left,right,24,40,-9,14),(right,right+OUTPUT_PAD_SIZE,OUTPUT_PAD_Y-OUTPUT_PAD_SIZE/2,OUTPUT_PAD_Y+OUTPUT_PAD_SIZE/2,OUTPUT_PAD_BOTTOM,OUTPUT_PAD_TOP)]
 shape_boxes={id(cover):cover_boxes,id(tray):tray_boxes,id(rack):rack_boxes}
 def boxes_disjoint(b,c):return b[1]<=c[0]+1e-7 or c[1]<=b[0]+1e-7 or b[3]<=c[2]+1e-7 or c[3]<=b[2]+1e-7 or b[5]<=c[4]+1e-7 or c[5]<=b[4]+1e-7
 # Placed solids are immutable. Retain the shape with its cached bounds so
 # Python cannot recycle its identity while a cached entry is still in use.
 shape_bounds={}
 def solid_box(v):
  key=id(v)
  if key not in shape_bounds:
   b=v.BoundingBox();shape_bounds[key]=(v,(b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax))
  return shape_bounds[key][1]
 proxy_checks=[]
 for shape,boxes,label in [(cover,cover_boxes,'cover'),(tray,tray_boxes,'tray'),(rack,rack_boxes,'rack')]:
  remainder=shape
  for box_bounds in boxes:
   if not remainder.Solids():break
   remainder=remainder.cut(rect_cut(*box_bounds))
  missing=max(0,remainder.Volume()) if remainder.Solids() else 0
  assert missing<.01,('Broad-phase enclosure coverage',label,missing)
  proxy_checks.append({'part':label,'boxes':len(boxes),'uncovered_volume_mm3':missing})
 def overlap(s,t):
  if id(s) in shape_boxes or id(t) in shape_boxes:
   sb=shape_boxes.get(id(s));tb=shape_boxes.get(id(t))
   sb=sb if sb is not None else [solid_box(s)];tb=tb if tb is not None else [solid_box(t)]
   if all(boxes_disjoint(b,c) for b in sb for c in tb):return 0.
  if boxes_disjoint(solid_box(s),solid_box(t)):return 0.
  return max(0,s.intersect(t).Volume())
 # Check the output pockets before the longer motion/explosion scan.
 output_insert_checks=[]
 for spec in OUTPUT_INSERTS:
  p=next(p for p in parts if p['name']==spec['name']);x,y,face=spec['position']
  embedded=overlap(p['shape'],rack)
  nominal=math.pi*((INSERT_OD/2)**2-(INSERT_PILOT/2)**2)*INSERT_LENGTH
  assert abs(embedded-nominal)<.02,('Output insert interference',spec,embedded,nominal)
  approach=overlap(cyl(INSERT_OD/2,30,x,y,face),rack)
  assert approach<.01,('Output insert installation blocked',spec)
  screw=cyl(1.5,INSERT_LENGTH+OUTPUT_INSERT_RECESS,x,y,face-INSERT_LENGTH)
  assert overlap(screw,rack)<.01,('Output screw bottoms in pad',spec)
  backing=face-INSERT_LENGTH-.4-OUTPUT_PAD_BOTTOM
  backing_probe=cyl(INSERT_PILOT/2,backing,x,y,OUTPUT_PAD_BOTTOM)
  assert abs(overlap(backing_probe,rack)-backing_probe.Volume())<.01,('Output pocket lacks backing',spec)
  output_insert_checks.append(dict(position_mm=spec['position'],installation_axis=spec['axis'],interference_mm3=embedded,approach_intersection_mm3=approach,backing_mm=backing))
 assert (OUTPUT_PAD_SIZE-OUTPUT_MOUNT_PITCH-INSERT_OD)/2>=2-1e-8
 assert right-a.stroke/2-CASE_RIGHT>=1.5-1e-8,'Output pad enters the enclosure'
 output_mount_check=dict(center_y_mm=OUTPUT_PAD_Y,rack_backbone_center_y_mm=(ROOT_Y+BACK_Y)/2,thread='M3',count=4,pattern_xy_mm=OUTPUT_MOUNTS,pitch_xy_mm=[OUTPUT_MOUNT_PITCH,OUTPUT_MOUNT_PITCH],pad_size_mm=[OUTPUT_PAD_SIZE,OUTPUT_PAD_SIZE,OUTPUT_PAD_TOP-OUTPUT_PAD_BOTTOM],face_z_mm=OUTPUT_PAD_TOP,insert_recess_mm=OUTPUT_INSERT_RECESS,thread_engagement_mm=[3,INSERT_LENGTH],maximum_screw_penetration_mm=INSERT_LENGTH+OUTPUT_INSERT_RECESS,minimum_knurl_edge_wall_mm=(OUTPUT_PAD_SIZE-OUTPUT_MOUNT_PITCH-INSERT_OD)/2,minimum_retracted_enclosure_gap_mm=right-a.stroke/2-CASE_RIGHT,checks=output_insert_checks)
 # Confirm the manufactured rack includes circular root arcs on both face edges.
 for wanted in [central_relief_radius,intertooth_relief_radius]:
  arcs=[e for e in rack.Edges() if e.geomType()=='CIRCLE' and abs(e.radius()-wanted)<1e-6]
  assert len(arcs)>=2*(len(centers)-1),(wanted,len(arcs))
 # Confirm restored end material and the square underside, not merely mesh appearance.
 square_end_check=rack.isInside(cq.Vector(left+.05,32,-8.95),1e-7)
 assert square_end_check,'Insertion end still has a ramp'
 rack_restoration_checks=[rack.isInside(cq.Vector(x,y,z),1e-7) for x,y,z in [(right-1,30,6),(right+4,30,6),(0,BACK_Y-.05,17)]]
 assert all(rack_restoration_checks),'Missing restored end or backbone material'
 end_solid_probe=box(right-(max(STATIONS)+a.stroke/2+4.75+HARDWARE_GAP),.1,.1,((right+max(STATIONS)+a.stroke/2+4.75+HARDWARE_GAP)/2,32,5))
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
 # Prove rack/pinion periodicity in their only possible contact band, then
 # reuse exact equal-phase intersections while contact stays away from rack ends.
 contact_min_y=rack.BoundingBox().ymin
 contact_x=math.sqrt(max(0,ra*ra-(contact_min_y-MOTOR_Y)**2))+1e-6
 window_left=centers[0]+pitch;window_right=centers[-1]-pitch
 phase_cache={};phase_hits=0
 periodic_check={'enabled':False,'rack_difference_mm3':None,'pinion_difference_mm3':None}
 if window_right-window_left>2*(contact_x+pitch):
  region=rect_cut(window_left,window_right,contact_min_y-1e-6,MOTOR_Y+ra+1e-6,0,21)
  one=rack.intersect(region);two=rack.translate((pitch,0,0)).intersect(region)
  rack_difference=max(0,one.cut(two).Volume())+max(0,two.cut(one).Volume())
  outer=gear.cut(cyl(contact_min_y-MOTOR_Y-1e-5,30,0,MOTOR_Y,-1));turned=rotate_drive(outer,360/N)
  gear_difference=max(0,outer.cut(turned).Volume())+max(0,turned.cut(outer).Volume())
  periodic_check.update(enabled=rack_difference<tolerance and gear_difference<tolerance,rack_difference_mm3=rack_difference,pinion_difference_mm3=gear_difference)
 def mesh_overlap(dx):
  global phase_hits
  phase=dx%pitch
  if min(phase,pitch-phase)<1e-7:phase=0.
  phase=round(phase,7)
  inside=window_left<=-contact_x-dx and contact_x-dx<=window_right
  if periodic_check['enabled'] and inside:
   if phase in phase_cache:phase_hits+=1;return phase_cache[phase]
   phase_cache[phase]=overlap(rack.translate((phase,0,0)),rotate_drive(gear,-phase/rp*180/math.pi))
   return phase_cache[phase]
  return overlap(rack.translate((dx,0,0)),rotate_drive(gear,-dx/rp*180/math.pi))
 # Validate the ideal unloaded tooth profile before allowing elastic preload.
 nominal=make_rack(0);period_vol=[];nominal_vol=[]
 for k in range(17):
  dx=pitch*k/16;g=rotate_drive(gear,-dx/rp*180/math.pi)
  period_vol.append(mesh_overlap(dx))
  nominal_vol.append(overlap(nominal.translate((dx,0,0)),g))
 assert max(nominal_vol)<tolerance,('Nominal involute mesh collides',max(nominal_vol))
 elastic_limit=max(period_vol)*1.05+.02
 for i,j in itertools.combinations(range(len(parts)),2):
  p,q=parts[i],parts[j];v=overlap(p['shape'],q['shape'])
  if v>tolerance:
   rec={'phase':'assembled','a':p['name'],'b':q['name'],'volume_mm3':round(v,5)}
   embedded=p.get('embedded_host')==q['name'] or q.get('embedded_host')==p['name']
   if embedded:rec['reason']='Intentional heat-set knurl/pilot interference; plastic displaced during installation'
   (allowed if embedded or ({p['name'],q['name']}==mesh_pair and v<=elastic_limit) else fail).append(rec)
 print('Assembled rigid failures:',len(fail),fail[:8],'; nominal mesh max:',max(nominal_vol),flush=True)
 # Exact swept outer envelopes for lid screw removal. Socket recesses are
 # filled in the envelope, so zero intersection proves the whole screw clear.
 screw_sweep_pairs=set();screw_sweep_checks=[]
 for i,p in enumerate(parts):
  if p['group']!='cover_screws':continue
  c=p['shape'].Center();x,y=c.x,c.y;hz=CASE_TOP-3.3
  lift=cyl(1.45,55,x,y,hz-20).fuse(cyl(2.75,38,x,y,hz))
  def park(r,h,z):return cq.Workplane('XY').slot2D(180+2*r,2*r,90).extrude(h).translate((x,y-90,z)).val()
  sideways=park(1.45,20,hz+15).fuse(park(2.75,3,hz+35))
  checked=0;worst=0.
  for j,q in enumerate(parts):
   if q['group']=='cover_screws':continue
   v=max(overlap(lift,q['shape']),overlap(sideways,q['shape']))
   worst=max(worst,v)
   assert v<tolerance,('Lid screw swept-envelope collision',p['name'],q['name'],v)
   screw_sweep_pairs.add(tuple(sorted((i,j))));checked+=1
  screw_sweep_checks.append({'part':p['name'],'stationary_part_pairs':checked,'path':'Z +35 mm, then Y -180 mm','maximum_intersection_mm3':worst})
 times={0.,1.};bounds=sorted({0.,1.}|{t[k] for ts in tracks.values() for t in ts for k in ['start','end']})
 for lo,hi in zip(bounds[:-1],bounds[1:]):
  moves=[math.dist(offset(g,lo),offset(g,hi)) for g in tracks]
  moves += [abs(angle(g,hi)-angle(g,lo))*math.pi/180*(ra if g=='gear' else 8) for g in tracks]
  steps=max(2,math.ceil(max(moves)/.5))
  if lo>=.10-1e-9 and hi<=.28+1e-9:
   teeth_moved=round(abs(offset('rack',hi)[0]-offset('rack',lo)[0])/pitch)
   if teeth_moved:steps=math.ceil(steps/teeth_moved)*teeth_moved
  times.update(lo+(hi-lo)*k/steps for k in range(steps+1))
 # The changed enclosure and its hardware retain dense 0.5 mm checks.
 # The tested bearing core is checked at every 1% of the full sequence,
 # all stage boundaries/midpoints, and exact bearing-release positions.
 core_times={k/100 for k in range(101)}|set(bounds)|{(lo+hi)/2 for lo,hi in zip(bounds[:-1],bounds[1:])}
 for x in STATIONS:
  for delta in [-8.]+[k*.5 for k in range(17)]:
   e=.10+.18*(x+delta+L/2)/WITHDRAW
   if .10<=e<=.28:core_times.add(e)
 core_keys={round(e,12) for e in core_times}
 times=sorted(times|core_times);pose_cache={};pair_cache={}
 chassis_cache={(SPRING_PRELOAD,SPRING_PRELOAD):base,(0.,0.):base_print}
 enclosure_groups={'cover','cover_screws','tray','chassis_screws'}
 def placed(i,e):
  p=parts[i];t=offset(p['group'],e);deg=angle(p['group'],e);key=(i,round(deg%360,8))+tuple(round(x,8) for x in t)+(tuple(round(v,8) for v in flex_lifts(e)) if p.get('flex_chassis') else ())
  if key not in pose_cache:
   if p.get('flex_chassis'):
    ds=tuple(round(SPRING_PRELOAD-v,8) for v in flex_lifts(e))
    if ds not in chassis_cache:chassis_cache[ds]=chassis(ds)
    v=chassis_cache[ds]
   else:v=p['shape']
   if abs(deg%360)>1e-7:v=rotate_drive(v,deg)
   if any(abs(x)>1e-8 for x in t):v=v.translate(t)
   if p['shape'] is cover or p['shape'] is tray or p['shape'] is rack:
    assert abs(deg)<1e-7
    shape_boxes[id(v)]=[(b[0]+t[0],b[1]+t[0],b[2]+t[1],b[3]+t[1],b[4]+t[2],b[5]+t[2]) for b in shape_boxes[id(p['shape'])]]
   pose_cache[key]=v
  return pose_cache[key]
 last_phase=-1
 for k,e in enumerate(times):
  if k%100==0:
   pose_cache.clear();shape_bounds.clear();shape_boxes={id(cover):cover_boxes,id(tray):tray_boxes,id(rack):rack_boxes}
  if k%50==0:print('Explosion pose',k+1,'of',len(times),flush=True)
  trans=[offset(p['group'],e) for p in parts];rot=[angle(p['group'],e) for p in parts]
  for i,j in itertools.combinations(range(len(parts)),2):
   if round(e,12) not in core_keys and not ({parts[i]['group'],parts[j]['group']} & enclosure_groups):continue
   if e<=.05+1e-9 and (i,j) in screw_sweep_pairs:continue
   if trans[i]==trans[j] and abs((rot[j]-rot[i])%360)<1e-7 and not (any(parts[q].get('flex_chassis') for q in [i,j]) and max(flex_lifts(e))>1e-8):continue
   # Volume is invariant under a common rigid transform; cache relative poses.
   radians=-rot[i]*math.pi/180;d=[trans[j][q]-trans[i][q] for q in range(3)]
   rel=(d[0]*math.cos(radians)-d[1]*math.sin(radians),d[0]*math.sin(radians)+d[1]*math.cos(radians),d[2])
   key=(i,j,round((rot[j]-rot[i])%360,7))+tuple(round(v,7) for v in rel)+(tuple(round(v,7) for v in flex_lifts(e)) if any(parts[q].get('flex_chassis') for q in [i,j]) else ())
   if key not in pair_cache:
    if {parts[i]['name'],parts[j]['name']}==mesh_pair and e<=.28+1e-9:pair_cache[key]=mesh_overlap(offset('rack',e)[0])
    else:pair_cache[key]=overlap(placed(i,e),placed(j,e))
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
  shape_boxes[id(r)]=[(b[0]+dx,b[1]+dx,b[2],b[3],b[4],b[5]) for b in rack_boxes];solid_box(r)
  g=rotate_drive(gear,deg);shaft_shape=rotate_drive(shaft,deg);set_shape=rotate_drive(next(p['shape'] for p in parts if p['group']=='set_screw'),deg)
  mesh_volumes.append(mesh_overlap(dx))
  output_moving=[(p['name'],p['shape'].translate((dx,0,0))) for p in parts if p.get('embedded_host')=='04 Beveled compliant rack']
  for p in parts:
   if p['group'] in ['rack','gear','set_screw','shaft']:continue
   for label,moving in [('rack',r),('pinion',g),('set screw',set_shape),('D shaft',shaft_shape)]+output_moving:
    v=overlap(moving,p['shape'])
    if v>tolerance:motion_fail.append({'at_mm':dx,'a':label,'b':p['name'],'volume_mm3':round(v,5)})
  for label,moving in output_moving:
   for drive_name,drive in [('pinion',g),('set screw',set_shape),('D shaft',shaft_shape)]:
    v=overlap(moving,drive)
    if v>tolerance:motion_fail.append({'at_mm':dx,'a':label,'b':drive_name,'volume_mm3':round(v,5)})
  # The shaft/gear/screw share a rigid transform; their initial fit also holds during motion.
 print('Motion failures:',len(motion_fail),motion_fail[:10],flush=True)
 contact_checks=[]
 for p in UPPER:
  point=p['contact'];normal=p['normal'];inside=tuple(point[k]-.05*normal[k] for k in range(3));outside=tuple(point[k]+.05*normal[k] for k in range(3))
  contact_checks.extend([rack.isInside(cq.Vector(*inside),1e-7),not rack.isInside(cq.Vector(*outside),1e-7),abs(sum(p['axis'][k]*normal[k] for k in range(3)))<1e-9])
 for p in BOTTOM:
  x=p['x'];contact_checks.extend([rack.isInside(cq.Vector(x,p['center'][1],-8.95),1e-7),not rack.isInside(cq.Vector(x,p['center'][1],-9.05),1e-7)])
 for dx in [-a.stroke/2+a.stroke*k/40 for k in range(41)]:
  for p in UPPER:
   point=p['contact'];normal=p['normal']
   inside=tuple(point[j]-.05*normal[j]-(dx if j==0 else 0) for j in range(3))
   outside=tuple(point[j]+.05*normal[j]-(dx if j==0 else 0) for j in range(3))
   contact_checks.extend([rack.isInside(cq.Vector(*inside),1e-7),not rack.isInside(cq.Vector(*outside),1e-7)])
  for p in BOTTOM:contact_checks.append(rack.isInside(cq.Vector(p['x']-dx,p['center'][1],-8.95),1e-7))
 assert all(contact_checks),'Guide contact geometry is incorrect'
 assert REAR_STATION==-32 and abs(CASE_RIGHT-max(STATIONS)-EXIT_BEARING_OFFSET)<1e-9
 assert min(STATIONS)-(left+a.stroke/2)>=13-1e-9
 assert right-a.stroke/2-max(STATIONS)>=13-1e-9
 if not PASS_THROUGH:assert left-a.stroke/2>=CASE_LEFT+CASE_WALL+1
 assert right-a.stroke/2>=CASE_RIGHT+1.5-1e-9
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
   wall_blend_checks.append(not base_print.isInside(cq.Vector(p['x']+sign*(x-23),front-3,-27+SPRING_THICKNESS+.2),1e-7))
 assert all(wall_blend_checks),'A blend extends beyond its supporting wall'
 compressed=chassis((SPRING_CHECK_TRAVEL,SPRING_CHECK_TRAVEL))
 assert compressed.isValid() and len(compressed.Solids())==1
 spring_check={'integral_with_chassis':True,'free_stl_valid':True,'free_stl_solid_count':1,'preload_deflection_mm':SPRING_PRELOAD,'leaf_thickness_mm':SPRING_THICKNESS,'leaf_width_mm':FLOOR_WIDTH,'root_radius_mm':1.2,'leaf_length_mm':14.,'design':'restored single broad floor','previous_thickness_mm':1.4,'wall_local_blend_checks_passed':len(wall_blend_checks),'rigid_lower_deck':False,'mechanical_downward_stop':False,'checked_deflection_mm':SPRING_CHECK_TRAVEL,'method':'Prescribed nominal displacement, not finite element analysis. Chassis STL is relaxed; STEP/viewer start deflected. No mechanical travel stop.'}
 for d in [0,SPRING_PRELOAD,SPRING_CHECK_TRAVEL]:
  for p in BOTTOM:
   seat=spring_seat(p,d)
   for target,label in [(tray,'tray'),(motor,'motor')]:
    assert overlap(seat,target)<.01,('Flexure travel collision',d,label)
 end_hardware_checks=[]
 for p in parts:
  if not ('angled' in p['name'] or 'lower axle' in p['name']) or float(p['name'].rsplit(' ',1)[-1])!=FRONT_STATION:continue
  for lift in ([0,SPRING_PRELOAD] if 'lower axle' in p['name'] else [0]):
   distance=p['shape'].translate((0,0,lift)).distance(tray)
   assert distance>=HARDWARE_GAP-1e-5,('End-post hardware clearance',p['name'],lift,distance)
   end_hardware_checks.append({'part':p['name'],'lift_mm':lift,'tray_gap_mm':distance})
 hardware_gaps=[]
 for dx in [-a.stroke/2,0,a.stroke/2]:
  r=rack.translate((dx,0,0))
  for p in parts:
   if 'axle' in p['name'] or 'washer' in p['name'] or 'nut' in p['name']:
    hardware_gaps.append({'travel_mm':dx,'part':p['name'],'gap_mm':r.distance(p['shape'])})
 assert min(q['gap_mm'] for q in hardware_gaps)>=HARDWARE_GAP-1e-5,('Hardware clearance',sorted(hardware_gaps,key=lambda q:q['gap_mm'])[:5])
 enclosure_checks={'printed_parts':5,'case_length_mm':CASE_LENGTH,'motor_rear_projection_mm':4,'driver_dimensions_modeled':False,'toothed_rack_extremes_x_mm':[-TOOTH_XMAX-a.stroke/2,TOOTH_XMAX+a.stroke/2],'inner_case_x_mm':[CASE_LEFT+CASE_WALL,CASE_RIGHT-CASE_WALL],'tooth_concealment_pass':TOOTH_XMAX+a.stroke/2<CASE_RIGHT-CASE_WALL,'mounting_face_normal':[0,1,0]}
 assert enclosure_checks['tooth_concealment_pass']
 if not PASS_THROUGH:assert -TOOTH_XMAX-a.stroke/2>CASE_LEFT+CASE_WALL
 enclosure_checks.update(enclosure_variant=a.enclosure,rear_pass_through=PASS_THROUGH,rear_opening_yz_mm=REAR_OPENING_YZ if PASS_THROUGH else None,maximum_rear_rack_projection_mm=max(0,CASE_LEFT-(left-a.stroke/2)))
 controller_gap=min(CASE_BOTTOM+offset('tray',e)[2]-(-8-MOTOR_DEPTH+offset('motor',e)[2]) for e in times)
 assert controller_gap>=4-1e-6,'Enclosure moves through the unmodeled controller region'
 enclosure_checks['minimum_controller_plane_separation_mm']=controller_gap
 insert_checks=[]
 for spec in INSERTS:
  part=next(p for p in parts if p['name']==spec['name'])
  embedded=overlap(part['shape'],tray)
  nominal=math.pi*((INSERT_OD/2)**2-(INSERT_PILOT/2)**2)*INSERT_LENGTH
  assert abs(embedded-nominal)<.02,('Insert pilot interference',spec,embedded,nominal)
  # Follow each insert's installation axis: +Z for top/internal inserts,
  # +Y for side mounts. The full insert envelope must approach unobstructed.
  swept=acyl(INSERT_OD/2,30,spec['position'],spec['axis'])
  approach=overlap(swept,tray)
  assert approach<.01,('Insert installation approach blocked',spec)
  insert_checks.append(dict(purpose=spec['purpose'],position_mm=spec['position'],installation_axis=spec['axis'],interference_mm3=embedded,approach_intersection_mm3=approach))
 rear_chassis_checks=[]
 for x in REAR_MOUNT_XS:
  y=REAR_MOUNT_Y
  # M3x16 spans Z=-16..0; the recessed insert occupies Z=-14..-9.
  bolt=next(p['shape'] for p in parts if p['name']==f'M3x16 rear chassis screw {x}')
  assert overlap(bolt,tray)<.01 and overlap(bolt,base)<.01,'Rear chassis screw fouls printed parts'
  wall_probe=cyl(INSERT_OD/2+1,INSERT_LENGTH,x,y,-9-INSERT_LENGTH).cut(cyl(INSERT_OD/2,INSERT_LENGTH,x,y,-9-INSERT_LENGTH))
  assert wall_probe.cut(tray).Volume()<.01,'Rear insert needs at least 1 mm surrounding plastic'
  seat_probe=ring(3.8,INSERT_OD/2+.1,.1,(x,y,-3.1),(0,0,1))
  supported=overlap(seat_probe,tray)/seat_probe.Volume()
  assert supported>.6,'Rear post lacks bearing area beneath chassis'
  rear_chassis_checks.append({'position_xy_mm':[x,y],'post_top_z_mm':-3,'post_diameter_mm':8,'wall_tie_width_mm':4,'insert_top_z_mm':-9,'insert_recess_mm':6,'screw':'M3x16 socket','insert_engagement_mm':INSERT_LENGTH,'minimum_insert_side_wall_mm':1,'supported_seat_fraction':supported})
 side_mount_checks=[]
 # Tessellated BRep bounds include modeling tolerance; test real material
 # outside the nominal mounting plane rather than its padded bounding box.
 outside_side=rect_cut(CASE_LEFT-1,CASE_RIGHT+1,CASE_YMAX+1e-5,CASE_YMAX+10,CASE_BOTTOM-1,CASE_TOP+1)
 assert max(0,tray.intersect(outside_side).Volume())<.01,'Side mounting face protrudes'
 for x,z in CASE_MOUNTS:
  face=CASE_YMAX-SIDE_INSERT_RECESS
  # Maximum permitted M3 screw penetration stays inside the blind pocket.
  screw=ycyl(1.5,INSERT_LENGTH+SIDE_INSERT_RECESS,x,face-INSERT_LENGTH,z)
  assert overlap(screw,tray)<.01,'Side screw strikes the blind pocket'
  inner_probe=box(.1,.1,.1,(x,face-INSERT_LENGTH-.4-1,z))
  assert abs(overlap(inner_probe,tray)-inner_probe.Volume())<1e-7,'Missing pocket backing'
  side_mount_checks.append(dict(position_xz_mm=[x,z],maximum_screw_penetration_mm=INSERT_LENGTH+SIDE_INSERT_RECESS,blind_backing_mm=2.))
 enclosure_checks.update(side_mount_thread='M3',side_mounts_xz_mm=CASE_MOUNTS,side_mount_plane_y_mm=CASE_YMAX,side_mount_insert_recess_mm=SIDE_INSERT_RECESS,side_mount_engagement_mm=[3,INSERT_LENGTH],side_mount_flush=True,side_mount_checks=side_mount_checks)
 front_checks=[]
 for y,z in FRONT_MOUNTS:
  face=CASE_RIGHT-FRONT_INSERT_RECESS;c=(face,y,z);u=(1,0,0)
  screw=acyl(1.5,INSERT_LENGTH+FRONT_INSERT_RECESS,c,u,-INSERT_LENGTH)
  assert overlap(screw,tray)<.01,'Front screw strikes blind pocket'
  backing=box(.1,.1,.1,(face-INSERT_LENGTH-.4-1,y,z))
  assert abs(overlap(backing,tray)-backing.Volume())<1e-7,'Missing front pocket backing'
  front_checks.append({'position_yz_mm':[y,z],'maximum_screw_penetration_mm':INSERT_LENGTH+FRONT_INSERT_RECESS,'blind_backing_mm':2.})
 enclosure_checks.update(front_mount_thread='M3',front_mounts_yz_mm=FRONT_MOUNTS,front_mount_plane_x_mm=CASE_RIGHT,front_mount_insert_recess_mm=FRONT_INSERT_RECESS,front_mount_checks=front_checks,front_fixture_opening_yz_mm=FRONT_FIXTURE_OPENING)
 enclosure_checks.update(top_mount_thread='M3',top_mounts_xy_mm=CASE_CORNERS,top_mount_plane_z_mm=CASE_TOP,top_mount_load_path='Directly into full-height tray posts; removable cover is bypassed',top_mount_engagement_mm=[3,INSERT_LENGTH],cover_screw_count=len(COVER_SEATS),lid_screw='M3x20 socket, recessed 0.3 mm below mounting face',chassis_screw='Front M3x10 socket; rear M3x16 socket',rear_chassis_mounts=rear_chassis_checks,heat_set_inserts={'thread':'M3','outer_diameter_mm':INSERT_OD,'length_mm':INSERT_LENGTH,'printed_pilot_diameter_mm':INSERT_PILOT,'count':len(INSERTS),'checks':insert_checks})
 references={str(e):{g:{'translation':list(offset(g,e)),'rotation_z_deg':angle(g,e)} for g in tracks} for e in [0,.025,.04,.075,.10,.15,.18,.20,.24,.26,.28,.30,.33,.36,.40,.45,.50,.53,.57,.64,.70,.79,.84,.89,.92,.95,.98,1]}
 report={'revision':24,'enclosure_variant':a.enclosure,'output_mount':output_mount_check,'tooth_module_mm':MODULE,'tooth_pitch_mm':pitch,'actuator_length_mm':CASE_LENGTH,'minimum_actuator_length_mm':MIN_CASE_LENGTH,'motor_depth_mm':MOTOR_DEPTH,'controller_rear_plane_z_mm':-8-MOTOR_DEPTH,'controller_dimensions_modeled':False,'rack_backbone_width_mm':a.rack_backbone_width,'head_relief_end_x_mm':max(STATIONS)+a.stroke/2+4.75+HARDWARE_GAP,'solid_rack_end_length_mm':right-(max(STATIONS)+a.stroke/2+4.75+HARDWARE_GAP),'square_insertion_end':True,'rack_restoration_checks_passed':len(rack_restoration_checks)+int(square_end_check),'stroke_mm':a.stroke,'motor':MOTOR_NAME,'pinion_teeth':N,'pressure_angle_deg':PRESSURE_ANGLE,'bearing_clearance_mm':BEARING_GAP,'hardware_clearance_mm':HARDWARE_GAP,'socket_head_envelope_mm':[9.5,5.0],'chassis_footprint_mm':[CHASSIS_WIDTH,CHASSIS_REAR-CHASSIS_FRONT],'end_post_hardware_clearances':end_hardware_checks,'enclosure':enclosure_checks,'spring_carrier':spring_check,'root_relief':{'shape':'semicircular caps tangent to straight slot walls','central_radius_mm':central_relief_radius,'intertooth_radius_mm':intertooth_relief_radius,'maximum_y_mm':RELIEF_Y,'arc_geometry_checked':True},'shaft_fit':d_fit,'bearing_count':6,'bearing_type':'625ZZ','bearing_dimensions_mm':[5,16,5],'chassis_release_shift_mm':10.,'chassis_release_lift_mm':6.,'lower_axle_service_retraction_mm':10.,'bearing_station_rule':'fixed rear station; front station follows exit','station_spacing_mm':FRONT_STATION-REAR_STATION,'bearing_stations_x_mm':STATIONS,'exit_bearing_center_offset_mm':EXIT_BEARING_OFFSET,'gear_center_x_mm':0,'minimum_guide_edge_margin_mm':13,'upper_bearing_angle_deg':45,'spring_preload_mm':SPRING_PRELOAD,'spring_thickness_mm':SPRING_THICKNESS,'checked_spring_deflection_mm':SPRING_CHECK_TRAVEL,'spring_free_stl':True,'chassis_mounts_mm':CHASSIS_MOUNTS,'motor_face_z_mm':-8,'integral_motor_land_mm':5,'chassis_solid_count':len(base.Solids()),'rack_solid_count':len(rack.Solids()),'insertion_side':'right/output side, plain left end first','rack_withdrawal_mm':WITHDRAW,'contact_checks_passed':len(contact_checks),'upper_force_normals':[[0,SQ,-SQ],[0,-SQ,-SQ]],'lower_force_normal':[0,0,1],'preload_per_flank_mm':a.preload,'nominal_mesh_max_overlap_mm3':max(nominal_vol),'elastic_mesh_limit_mm3':elastic_limit,'elastic_mesh_volume_mm3_range':[min(mesh_volumes),max(mesh_volumes)],'hardware_clearance_samples':hardware_gaps,'minimum_rack_hardware_gap_mm':min(q['gap_mm'] for q in hardware_gaps),'source_sha256':__import__('hashlib').sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'mesh_periodicity':periodic_check|{'cache_hits':phase_hits,'exact_phase_evaluations':len(phase_cache)},'broadphase_coverage_checks':proxy_checks,'lid_screw_swept_envelope_checks':screw_sweep_checks,'mechanism_explosion_samples':len(core_times),'method':'All assembled pairs. Changed enclosure and enclosure-fastener relative motion sampled <=0.5 mm. Mechanism pairs checked at 1% explosion intervals, every stage boundary/midpoint and bearing-release transitions at 0.5 mm spacing; all moving parts checked at 41 travel positions. Exact verified box coverage rejects empty enclosure and rack regions; lid screw removal is proven with continuous swept outer envelopes. Equal-phase mesh intersections are reused only inside an exactly verified periodic rack/pinion region. Same tracks drive viewer. Nominal tooth profile checked separately.','intersection_tolerance_mm3':tolerance,'explosion_samples':len(times),'motion_samples':41,'explosion_failures':fail,'motion_failures':motion_fail,'intentional_contacts':allowed,'minimum_rack_frame_gap_mm':min(p['gap_mm'] for p in gap),'plastic_clearance_samples':gap,'viewer_reference_poses':references,'limits':['2.3 mm default spring deflection is an aggressive physical prototype. Force, elastic recovery and fatigue require testing in the chosen print material.','Sampled rigid geometry, not continuous swept-volume proof or a physical fit test.','Oversized teeth require elastic deflection. No load, backlash or fatigue rating.','The plain insertion end has no axial hard stop; enforce software travel limits.','Viewer chassis uses exact CAD shape samples at one twelfth of the spring preload; bearing translations follow the CAD tracks continuously.',
 'Pinion is free to turn during rack insertion. Remove front and rear angled axles in sequence. Spring carrier supplies passive preload; force, creep and fatigue have not been measured. STL is unloaded; STEP is assembled and deflected.']}
 (out/'downloads'/'validation.json').write_text(json.dumps(report,indent=2))
 assert not fail and not motion_fail,'See validation report'
 assert min(p['gap_mm'] for p in gap)>.25,'Rack rubs frame'

