"""Validate adapted helix clearances, bearing engagement, and bounded pilot contact."""
import hashlib,json,pathlib
import leadscrew_actuator as linear
from model import build,layout,cyl,overlap
root=pathlib.Path(__file__).resolve().parent
p=json.loads((root/'parameters.json').read_text());lay=layout(p);parts,_=build(p,lay);by={a['name']:a for a in parts};rows=[];contacts=[]
for axis,meta in [('Z',lay['z_actuator']),('R',lay['r_actuator'])]:
 data,_=linear.build(meta['stroke'],meta['width'],meta['motor'],meta['depth']);local={a['name']:a for a in data}
 screw=local['Printed 20 mm lead screw with integral shaft clamp']['shape'];carriage=local['Hollow triangular carriage']['shape']
 for travel in sorted(set([0,1,2,3,4,20,meta['stroke']/2,meta['stroke']])):
  v=overlap(screw.rotate((0,0,42),(1,0,42),-travel*360/8),carriage.translate((travel,0,0)))
  assert v<.01,(axis,travel,v);rows.append(dict(axis=axis,travel_mm=travel,thread_overlap_mm3=v))
 assert all(lo>=30 and hi+meta['stroke']<=meta['screw_end'] for lo,hi in meta['thread_bands'])
 assert 10+meta['stroke']<meta['stations'][0] and meta['stations'][-1]<meta['end']-8
 for joint in meta['thread_joints']:
  host=local[joint['host']];bolt=local[joint['bolt']];mask=cyl(joint['diameter']/2+.2,joint['length'],joint['center'],joint['axis'])
  extra=host['shape'].intersect(bolt['shape']).cut(mask).Volume();assert extra<1e-6,(axis,joint,extra)
  contacts.append(dict(axis=axis,host=joint['host'],bolt=joint['bolt'],outside_pilot_mm3=max(0,extra)))
# External receiving pilots are independently bounded in assembled world coordinates.
for a in parts:
 if not a.get('thread_host'):continue
 name=a['name'];i=int(name.rsplit('_',1)[1]);zo=p['z_origin'];zp=lay['zpad'];hz=lay['horizontal_z'];hx=lay['h_origin'];face=lay['radial_mount_face_z']
 if name.startswith('Z_top_'):
  x,y=lay['z_actuator']['lid'][i];mask=cyl(2.7,9,(17,-y,zo+x),(1,0,0))
 elif name.startswith('Z_enclosure_'):
  x,z=lay['z_actuator']['side'][i];mask=cyl(2.7,9,(z-42,-103,zo+x),(0,1,0))
 elif name.startswith('R_enclosure_'):
  x,y=lay['r_actuator']['lid'][i];mask=cyl(2.7,9,(hx+x,-y,face))
 elif name.startswith('Z_output_'):
  y,z=lay['z_actuator']['output_holes'][i];mask=cyl(1.7,8,(z-42,-y,zp-8))
 else:
  y,z=lay['r_actuator']['output_holes'][i];end=hx+lay['r_actuator']['end']+lay['radial_stroke']/2;mask=cyl(1.7,8,(end-8,-y,hz-z),(1,0,0))
 extra=a['shape'].intersect(by[a['thread_host']]['shape']).cut(mask).Volume();assert extra<1e-6,(name,extra)
 contacts.append(dict(bolt=name,host=a['thread_host'],outside_pilot_mm3=max(0,extra)))
r=dict(passed=True,samples=rows,contacts=contacts,lead_mm=8,full_thread_and_bearing_engagement=True,source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ['model.py','parameters.json','leadscrew_actuator.py','check_leadscrew.py','upstream/leadscrew-r16/experiments/t8-leadscrew/model.py']})
(root/'output/leadscrew-thread-validation.json').write_text(json.dumps(r,indent=2));print('Adapted threads and bounded pilot contacts passed',flush=True)
