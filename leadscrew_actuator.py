"""Adapt pinned upstream revision 24 actuator CAD for arm stroke and full-depth motors."""
import hashlib,json,pathlib,sys,math
import cadquery as cq
ROOT=pathlib.Path(__file__).resolve().parent
SOURCE=ROOT/'upstream/leadscrew-grid31/experiments/t8-leadscrew/model.py'
def grid_y(width):return [31*(j-({1:2,2:4,4:6}[width]-1)/2) for j in range({1:2,2:4,4:6}[width])]
def patterns(width=1,stroke=40,variant='printed',extension=0):
 xs=[10.5+31*j for j in range(5)];ys=grid_y(width)
 return dict(width=width,variant=variant,inferred=False,pitch_mm=[31,31],thread='M3 heat-set insert',base=[(x,y) for x in xs for y in ys],lid=[(x,y) for x in xs for y in ys],side=[],width_mm=80+42*(width-1),output_width_mm={1:42,2:104,4:168}[width],output_holes=[(y,42+z) for y in ys for z in [-15.5,15.5]])
def build(stroke=40,width=1,motor='nema17',depth=48,extension=0):
 assert extension==0 and stroke in [40,120] and motor in ['nema14','nema17']
 original=SOURCE.read_text();source=original.split('def explosion_offset(')[0]
 half,pitch=(17.6,26) if motor=='nema14' else (21,31)
 source=source.replace('motor_holes=[(y,SCREW_Z+z) for y in [-15.5,15.5] for z in [-15.5,15.5]]',f'motor_holes=[(y,SCREW_Z+z) for y in [{-pitch/2},{pitch/2}] for z in [{-pitch/2},{pitch/2}]]')
 source=source.replace('NEMA17 5 mm',motor.upper()+' 5 mm')
 source=source.replace('motor=rect(-40,0,-21,21,SCREW_Z-21,SCREW_Z+21)',f'motor=rect(-{depth},0,-{half},{half},SCREW_Z-{half},SCREW_Z+{half})').replace("'NEMA17 42x42x40 reference'",repr(motor.upper()+' full-depth reference'))
 key=hashlib.sha256((source+str((width,stroke))).encode()).hexdigest()[:20];cache=ROOT/'cache'/('leadscrew-'+key)
 if (cache/'parts.json').exists():
  data=json.loads((cache/'parts.json').read_text());meta=json.loads((cache/'metadata.json').read_text())
  for i,a in enumerate(data):
   a['shape']=cq.Shape.importBrep(str(cache/f'{i}.brep'))
   if a.get('hasFreeShape'):a['freeShape']=cq.Shape.importBrep(str(cache/f'{i}-print.brep'))
  return data,meta
 cache.mkdir(parents=True,exist_ok=True);argv=sys.argv;sys.argv=['model.py','--variant','printed','--travel',str(stroke),'--width',str(width),'--width-build-root',str(cache)]
 ns={'__name__':'arm_actuator','__file__':str(SOURCE)}
 try:exec(compile(source,str(SOURCE),'exec'),ns)
 finally:sys.argv=argv
 data=ns['parts'];meta=dict(extension_mm=extension,stroke=stroke,width=width,motor=motor,depth=depth,lead=8,axis_z=42,end=ns['EXIT_X'],stations=ns['STATIONS'],output_holes=ns['output_holes'],base=ns['BASE_MOUNT_HOLES'],lid=ns['LID_MOUNTS'],side=ns['SIDE_MOUNTS'],body_width=2*ns['HALF_WIDTH'],thread_joints=ns['THREAD_JOINTS'],attachment_pilots=ns['ATTACH_PILOTS'],output_pilots=ns['OUTPUT_PILOTS'],source_sha256=hashlib.sha256(original.encode()).hexdigest(),thread_bands=ns['THREAD_BANDS'],screw_end=ns['ROD_END'],grid_x=ns['GRID_X'],grid_y=ns['GRID_Y'],output_width=ns['OUTPUT_WIDTH'],mount_seats=ns['MOUNT_SEATS'],mount_insert=ns['MOUNT_INSERT'],base_fasteners=[(x,y) for x in [ns['GRID_X'][0],ns['GRID_X'][-1]] for y in [ns['GRID_Y'][0],ns['GRID_Y'][-1]]])
 serial=[]
 for i,a in enumerate(data):
  a['shape'].exportBrep(str(cache/f'{i}.brep'))
  if 'freeShape' in a:a['freeShape'].exportBrep(str(cache/f'{i}-print.brep'));a['hasFreeShape']=True
  serial.append({k:v for k,v in a.items() if k not in ['shape','freeShape']})
 (cache/'metadata.json').write_text(json.dumps(meta));(cache/'parts.json').write_text(json.dumps(serial))
 return data,meta

def metadata(stroke=40,width=1,motor='nema17',depth=48,extension=0):return build(stroke,width,motor,depth,extension)[1]
def home_shape(part,meta,printing=False):
 s=part.get('freeShape',part['shape']) if printing else part['shape']
 if not printing:
  if part['group']=='rotor':s=s.rotate((0,0,42),(1,0,42),-meta['stroke']/2*360/8)
  if part['group']=='carriage':s=s.translate((meta['stroke']/2,0,0))
 return s
