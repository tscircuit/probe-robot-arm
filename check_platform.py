"""Check simultaneous four-probe clusters against all arm/frame solids."""
import itertools,json,pathlib,math
import cadquery as cq
from model import build,layout,pose,overlap,platform_parts,cluster_targets,target_pose
p=json.loads(pathlib.Path('parameters.json').read_text());lay=layout(p)
parts,_=build(p,lay)
frame=[(a['name'],a['shape'],a['shape'].BoundingBox()) for a in platform_parts(p,lay)]
def disjoint(a,b):
 return any(getattr(a,k+'max')<=getattr(b,k+'min')+1e-6 or getattr(b,k+'max')<=getattr(a,k+'min')+1e-6 for k in 'xyz')
def placed(q,i):
 x,y,deg=lay['mounts'][i];loc=cq.Location(cq.Vector(x,y,0),cq.Vector(0,0,1),deg)
 result=[]
 for a in pose(parts,p,lay,**q):
  s=a['shape'].located(loc)
  result.append((a['name'],s,s.BoundingBox(),a['group']))
 return result
reports=[];static_cache={};all_fail=[];minimum_probe_gap=1e9
samples=[(x,y,-20) for x,y in itertools.product([-49,0,49],repeat=2)]
samples += [(x,y,z) for x,y in [(0,0),(-49,-49),(49,49)] for z in [0,20]]
for cx,cy,z in samples:
 targets=cluster_targets(p,cx,cy);qs=[target_pose(lay,i,t,z) for i,t in enumerate(targets)]
 arms=[placed(q,i) for i,q in enumerate(qs)];fail=[];candidates=0;tip_errors=[]
 for i,q in enumerate(qs):
  bx,by,deg=lay['mounts'][i];a=math.radians(deg+q['yaw']);r=lay['tip_radius']+q['r']
  actual=(bx+r*math.cos(a),by+r*math.sin(a),lay['probe_mount_z']-p['probe_drop']+q['z'])
  tip_errors.append(math.dist(actual,(*targets[i],lay['board_top']+z+20)))
 for i,j in itertools.combinations(range(4),2):
  for an,a,ab,ag in arms[i]:
   for bn,b,bb,bg in arms[j]:
    if disjoint(ab,bb):continue
    candidates+=1;key=(i,j,an,bn)
    if ag=='fixed' and bg=='fixed' and key in static_cache:v=static_cache[key]
    else:
     v=overlap(a,b)
     if ag=='fixed' and bg=='fixed':static_cache[key]=v
    if v>.01:fail.append({'arms':[i+1,j+1],'a':an,'b':bn,'overlap_mm3':v})
  pa=next(a for n,a,_,_ in arms[i] if n=='Spring_probe_reference')
  pb=next(a for n,a,_,_ in arms[j] if n=='Spring_probe_reference')
  minimum_probe_gap=min(minimum_probe_gap,pa.distance(pb))
 for i,arm in enumerate(arms):
  for an,a,ab,ag in arm:
   for bn,b,bb in frame:
    if disjoint(ab,bb):continue
    key=(i,an,bn)
    if ag=='fixed' and key in static_cache:v=static_cache[key]
    else:
     v=overlap(a,b)
     if ag=='fixed':static_cache[key]=v
    if v>.01:fail.append({'arm':i+1,'a':an,'b':bn,'overlap_mm3':v})
 reports.append({'cluster_center_mm':[cx,cy],'height_above_board_mm':z+20,'tip_targets_mm':targets,'poses':qs,'maximum_tip_error_mm':max(tip_errors),'candidate_pairs':candidates,'collisions':fail})
 all_fail.extend(fail);print('Cluster',cx,cy,'clearance',z+20,'collisions',len(fail),fail[:3],flush=True)
rear=-p['base_motor_depth'];component_bottom=rear-p['controller_spacer']-1.6-p['controller_component_height']
report={'cluster_pitch_mm':p['probe_cluster_pitch'],'samples':reports,'minimum_probe_solid_gap_mm':minimum_probe_gap,'collisions':all_fail,'motor_reference_depths_mm':{'base_NEMA17':p['base_motor_depth'],'Z_NEMA17':p['z_motor_depth'],'radial_NEMA14':p['radial_motor_depth']},'horizontal_motor_center_xy_mm':[lay['h_origin'],lay['r_drive_y']],'controller_component_clearance_above_ground_mm':component_bottom-p['platform_ground_z'],'passed':not all_fail and max(r['maximum_tip_error_mm'] for r in reports)<1e-6,'limits':['Sampled rigid geometry; no continuous swept-volume, compliance, wire motion, print-fit or force validation.','PCB envelope is dimensioned from the linked controller; component height, spacer and cable allowances are engineering assumptions.','Angled spring probes require a selected part and contact-force/scrub testing.']}
pathlib.Path('output/platform-validation.json').write_text(json.dumps(report,indent=2))
print('Passed:',report['passed'],'minimum probe gap:',minimum_probe_gap,flush=True)
assert report['passed']
