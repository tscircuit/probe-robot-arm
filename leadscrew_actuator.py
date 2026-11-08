"""Adapt pinned Site v61 actuator CAD for arm stroke and full-depth motors."""
import hashlib,json,pathlib,sys,math
import cadquery as cq
ROOT=pathlib.Path(__file__).resolve().parent
SOURCE=ROOT/'upstream/leadscrew-r16/experiments/t8-leadscrew/model.py'
def patterns(width=1,stroke=40,variant='printed'):
 extra=stroke-40;end=(155 if variant=='printed' else 121)+extra;stations=[63+extra,end-18];w=21*(width-1)
 return dict(width=width,variant=variant,inferred=variant=='t8' and (width!=1 or stroke!=40),
  base=[(x,y) for x in [-3,end-6] for y in [-34-w,34+w]],
  lid=[(x,y) for x in [36,sum(stations)/2-4] for y in [-27-w,27+w]],
  side=[(22,12),(36,12)]+[(x-5,z) for x in stations for z in [44,56]],
  width_mm=80+2*w,end=end)
def build(stroke=40,width=1,motor='nema17',depth=48):
 assert stroke>=40 and motor in ['nema14','nema17']
 original=SOURCE.read_text();source=original.split('def explosion_offset(')[0]
 extra=stroke-40
 source=source.replace('STROKE=40.;','STROKE='+str(float(stroke))+';').replace('EXIT_X=155. if PRINTED else 121.;',f'EXIT_X={155.+extra} if PRINTED else {121.+extra};').replace('STATIONS=[63.,EXIT_X-18]',f'STATIONS=[{63.+extra},EXIT_X-18]').replace('ROD_END=152. if PRINTED else 96.',f'ROD_END={152.+extra} if PRINTED else {96.+extra}')
 source=source.replace('2.5,1,122)',f'2.5,1,{122+extra})').replace('xcyl(8,122,30)',f'xcyl(8,{122+extra},30)').replace('xcyl(10.1,122,30)',f'xcyl(10.1,{122+extra},30)').replace('2.75,1.25,122)',f'2.75,1.25,{122+extra})').replace('xcyl(8.35,124,29)',f'xcyl(8.35,{124+extra},29)')
 half,pitch=(17.6,26) if motor=='nema14' else (21,31)
 source=source.replace('motor_holes=[(y,SCREW_Z+z) for y in [-15.5,15.5] for z in [-15.5,15.5]]',f'motor_holes=[(y,SCREW_Z+z) for y in [{-pitch/2},{pitch/2}] for z in [{-pitch/2},{pitch/2}]]')
 source=source.replace('motor=rect(-40,0,-21,21,SCREW_Z-21,SCREW_Z+21)',f'motor=rect(-{depth},0,-{half},{half},SCREW_Z-{half},SCREW_Z+{half})').replace("'NEMA17 42x42x40 reference'",repr(motor.upper()+' full-depth reference'))
 key=hashlib.sha256((source+str(width)).encode()).hexdigest()[:20];cache=ROOT/'cache'/('leadscrew-'+key)
 if (cache/'parts.json').exists():
  data=json.loads((cache/'parts.json').read_text());meta=json.loads((cache/'metadata.json').read_text())
  for i,a in enumerate(data):
   a['shape']=cq.Shape.importBrep(str(cache/f'{i}.brep'))
   if a.get('hasFreeShape'):a['freeShape']=cq.Shape.importBrep(str(cache/f'{i}-print.brep'))
  return data,meta
 cache.mkdir(parents=True,exist_ok=True);argv=sys.argv;sys.argv=['model.py','--variant','printed','--width',str(width),'--width-build-root',str(cache)]
 ns={'__name__':'arm_actuator','__file__':str(SOURCE)}
 try:exec(compile(source,str(SOURCE),'exec'),ns)
 finally:sys.argv=argv
 data=ns['parts'];meta=dict(stroke=stroke,width=width,motor=motor,depth=depth,lead=8,axis_z=42,end=ns['EXIT_X'],stations=ns['STATIONS'],output_holes=ns['output_holes'],base=ns['BASE_MOUNT_HOLES'],lid=ns['LID_MOUNTS'],side=ns['SIDE_MOUNTS'],body_width=2*ns['HALF_WIDTH'],thread_joints=ns['THREAD_JOINTS'],attachment_pilots=ns['ATTACH_PILOTS'],output_pilots=ns['OUTPUT_PILOTS'],source_sha256=hashlib.sha256(original.encode()).hexdigest(),thread_bands=ns['THREAD_BANDS'],screw_end=ns['ROD_END'])
 serial=[]
 for i,a in enumerate(data):
  a['shape'].exportBrep(str(cache/f'{i}.brep'))
  if 'freeShape' in a:a['freeShape'].exportBrep(str(cache/f'{i}-print.brep'));a['hasFreeShape']=True
  serial.append({k:v for k,v in a.items() if k not in ['shape','freeShape']})
 (cache/'metadata.json').write_text(json.dumps(meta));(cache/'parts.json').write_text(json.dumps(serial))
 return data,meta

def metadata(stroke=40,width=1,motor='nema17',depth=48):return build(stroke,width,motor,depth)[1]
def home_shape(part,meta,printing=False):
 s=part.get('freeShape',part['shape']) if printing else part['shape']
 if not printing:
  if part['group']=='rotor':s=s.rotate((0,0,42),(1,0,42),-meta['stroke']/2*360/8)
  if part['group']=='carriage':s=s.translate((meta['stroke']/2,0,0))
 return s
