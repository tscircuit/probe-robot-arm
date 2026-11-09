"""Native-frame direct Z-flange / radial-lid interface, dimensions in mm."""
import hashlib,json,pathlib
import cadquery as cq
import leadscrew_actuator as linear
ROOT=pathlib.Path(__file__).resolve().parent
THREAD_POINTS=[(x,y) for x in [-77.5,-46.5,-15.5,15.5,46.5,77.5] for y in [-15.5,15.5]]
LID_TOP=76.
def output_indices(meta):
 # Keep the 4x lower bearing running faces intact beside the +/-46.5 rows.
 return [i for i,(y,z) in enumerate(meta['output_holes']) if meta['width']!=4 or abs(y)!=46.5]
def cyl(r,h,c,axis=(0,0,1)):return cq.Solid.makeCylinder(r,h,cq.Vector(*c),cq.Vector(*axis))
def box(x,y,z,c):return cq.Workplane('XY').box(x,y,z).translate(c).val()
def m3_thread_cutter():
 path=cq.Wire.makeHelix(.5,7,1.3)
 groove=cq.Workplane('XZ').polyline([(1.27,-.24),(1.60,-.05),(1.60,.05),(1.27,.24)]).close().sweep(path,isFrenet=True).val().translate((0,0,68.5))
 return groove.fuse(cyl(1.3,8,(0,0,68.3)),cq.Solid.makeCone(1.3,1.85,.55,cq.Vector(0,0,75.5),cq.Vector(0,0,1))).clean()
def parts(axis,meta,hx):
 data=[dict(a) for a in linear.build(meta['stroke'],meta['width'],meta['motor'],meta['depth'],meta.get('extension_mm',0))[0]]
 # The custom radial lid uses integral M3 threads instead of the stock lid inserts.
 if axis=='R':data=[a for a in data if not a['name'].startswith('M3 lid mounting insert')]
 name='Structural mounting lid' if axis=='R' else 'Hollow triangular carriage'
 part=next(a for a in data if a['name']==name)
 key=hashlib.sha256((pathlib.Path(__file__).read_text()+pathlib.Path(linear.__file__).read_text()+axis+str(hx)+json.dumps(meta,sort_keys=True)).encode()).hexdigest()[:20]
 cache=ROOT/'cache'/('direct-'+key);cache.mkdir(exist_ok=True)
 if (cache/'assembled.brep').exists():
  part['shape']=cq.Shape.importBrep(str(cache/'assembled.brep'));part['freeShape']=cq.Shape.importBrep(str(cache/'print.brep'));return data
 for label,original in [('assembled',part['shape']),('print',part.get('freeShape',part['shape']))]:
  if axis=='R':
   pad=cq.Workplane('XY').box(168,42,8).edges('|Z').fillet(2).translate((-hx,0,72)).val()
   shape=original.fuse(pad,*[cyl(2.4,4,(x,y,64)) for x,y in meta['lid']])
   cutter=m3_thread_cutter()
   shape=shape.cut(*[cutter.translate((x-hx,y,0)) for x,y in THREAD_POINTS])
   shape=shape.cut(cyl(11.1,2.1,(-hx,0,74)),cyl(3.1,12,(17,5,66)))
   for q in meta['thread_joints']:
    if q['bolt'].startswith('M3x12 button-head lid'):
     x,y,z=q['center'];shape=shape.cut(cyl(3.3,12,(x,y,65)))
  else:
   shape=original;end=meta['end']
   for i in output_indices(meta):
    y,z=meta['output_holes'][i]
    shape=shape.cut(cyl(1.7,8.4,(end+.2,y,z),(-1,0,0)),cyl(2.9,26,(end-4.8,y,z),(-1,0,0)))
    lo,hi=(z-2.9,80) if z>42 else (15,z+2.9)
    shape=shape.cut(box(22,5.8,hi-lo,(end-19,y,(lo+hi)/2)))
  # Remove tiny detached lips exposed by the upper service slots.
  if axis=='Z':
   solids=sorted(shape.Solids(),key=lambda a:a.Volume(),reverse=True)
   assert sum(s.Volume() for s in solids[1:])<300
   shape=solids[0]
  shape=shape.clean();assert shape.isValid() and len(shape.Solids())==1,(axis,label)
  shape.exportBrep(str(cache/(label+'.brep')))
  part['shape' if label=='assembled' else 'freeShape']=shape
 return data
