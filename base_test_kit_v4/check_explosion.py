"""Check every segment of explosion.py using conservative distance bounds.
For a translation interval of length L, distance at its midpoint >= L/2
certifies no positive intersection anywhere in that interval (within tolerance).
Uncertified intervals are subdivided, never silently marked passed.
"""
import argparse,hashlib,itertools,json,math,pathlib,time
from build import build,overlap,spindle_fit_checks
from gear_geometry import cyl,polar,box
import cadquery as cq
from explosion import timeline
ROOT=pathlib.Path(__file__).resolve().parent
EPS=1e-7

def bb(s):
    b=s.BoundingBox();return ([b.xmin,b.ymin,b.zmin],[b.xmax,b.ymax,b.zmax])

def disjoint(a,b,lo,hi):
    return any(a[1][i]+max(lo[i],hi[i])<=b[0][i]+EPS or b[1][i]<=a[0][i]+min(lo[i],hi[i])+EPS for i in range(3))

def exceptions(parts):
    from rotary_base.core import contact_exceptions
    return contact_exceptions(parts,json.loads((ROOT/'parameters.json').read_text()))

def bevel_withdrawal(a,b,delta,offsets,shapes):
    if a!='Internal_72T_ring' or not b.startswith('625ZZ_support_roller_'):return False
    if abs(delta[0])+abs(delta[1])>1e-7 or delta[2]<=0:return False
    if any(abs(x)>1e-7 for n in [a,b] for x in offsets[n]):return False
    from rotary_base.core import roller_layout
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    p=json.loads((ROOT/'parameters.json').read_text());i=int(b.rsplit('_',1)[1]);angle=p['roller_angles_deg'][i];lay=roller_layout(p)
    def bounds(s):
        s=s.rotate((0,0,0),(0,0,1),-angle).translate((-lay['center_r'],0,-lay['center_z'])).rotate((0,0,0),(0,1,0),45)
        box=Bnd_Box();BRepBndLib.AddOptimal_s(s.wrapped,box,False,False);return box.Get()
    ring=bounds(shapes[a]);bearing=bounds(shapes[b])
    assert ring[2]>=8-1e-6 and bearing[5]<=8+1e-6,(ring,bearing)
    # In this axle frame the track's tangent plane is Z=8. Raising the ring
    # increases its minimum local Z by dz/sqrt(2), so contact opens monotonically.
    return True

def button_withdrawal(a,b,delta,offsets,shapes):
    if not a.startswith('M3x30_ring_') or b!='Internal_72T_ring':return False
    if abs(delta[0])+abs(delta[1])>1e-7 or delta[2]>=0:return False
    if any(abs(offsets[a][k]-offsets[b][k])>1e-7 for k in range(3)):return False
    p=json.loads((ROOT/'parameters.json').read_text());i=int(a.rsplit('_',1)[1]);x,y=polar(78,math.radians(30+60*i));z=32-p['rotor_drop_mm']
    assert shapes[b].BoundingBox().zmin>=z-1e-7
    upper=shapes[a].intersect(box(400,400,80,(0,0,z+40)))
    assert upper.cut(cyl(1.500001,31,(x,y,z))).Volume()<1e-6
    assert overlap(shapes[b],cyl(1.7,40,(x,y,z)))<1e-6
    # All screw material above the flat seating plane is the narrow shank.
    # Pulling down keeps the head below the ring and the shank inside its bore.
    return True

def check(parts,stages):
    shapes={p['name']:p['shape'] for p in parts};bounds={n:bb(s) for n,s in shapes.items()}
    offsets={n:[0.,0.,0.] for n in shapes};allowed=exceptions(parts)
    failures=[];unresolved=[];records=[];queries=0;pruned=0;proven=0;bevel_proofs=[];button_proofs=[]
    for si,stage in enumerate(stages):
        start=time.time();movers=set(stage['parts']);delta=stage['delta'];length=math.sqrt(sum(d*d for d in delta))
        stage_queries=0;candidates=0
        for a in sorted(movers):
            for b in sorted(shapes.keys()-movers):
                if frozenset([a,b]) in allowed:continue
                if button_withdrawal(a,b,delta,offsets,shapes):
                    button_proofs.append(dict(stage=si,screw=a,ring=b,proof='Head remains below the flat seating plane; the translated shank stays inside the straight bore'))
                    continue
                if bevel_withdrawal(a,b,delta,offsets,shapes):
                    bevel_proofs.append(dict(stage=si,ring=a,bearing=b,proof='Exact tangent-plane bounds separate the ring and tilted bearing for every upward displacement'))
                    continue
                rel=[offsets[a][k]-offsets[b][k] for k in range(3)]
                end=[rel[k]+delta[k] for k in range(3)]
                if disjoint(bounds[a],bounds[b],rel,end):pruned+=1;continue
                candidates+=1
                stack=[(0.,1.)];local_queries=0
                while stack:
                    lo,hi=stack.pop();v0=[rel[k]+lo*delta[k] for k in range(3)];v1=[rel[k]+hi*delta[k] for k in range(3)]
                    if disjoint(bounds[a],bounds[b],v0,v1):pruned+=1;continue
                    mid=(lo+hi)/2;v=[rel[k]+mid*delta[k] for k in range(3)]
                    sa=shapes[a].translate(tuple(v));d=sa.distance(shapes[b]);queries+=1;stage_queries+=1;local_queries+=1
                    if d>=length*(hi-lo)/2-EPS:proven+=1;continue
                    if d<EPS:
                        volume=overlap(sa,shapes[b])
                        if volume>.001:
                            failures.append(dict(stage=si,label=stage['label'],a=a,b=b,stage_fraction=mid,overlap_mm3=volume));break
                    if length*(hi-lo)<.0001 or local_queries>20000:
                        unresolved.append(dict(stage=si,label=stage['label'],a=a,b=b,interval=[lo,hi],distance_mm=d));break
                    stack.extend([(mid,hi),(lo,mid)])
                if failures or unresolved:break
            if failures or unresolved:break
        records.append(dict(index=si,label=stage['label'],travel_mm=length,candidate_pairs=candidates,distance_queries=stage_queries,seconds=round(time.time()-start,2)))
        print(si+1,stage['label'],'queries',stage_queries,'failures',len(failures),'unresolved',len(unresolved),flush=True)
        if failures or unresolved:break
        for n in movers:offsets[n]=[offsets[n][k]+delta[k] for k in range(3)]
    return dict(passed=not failures and not unresolved and len(records)==len(stages),method='Continuous linear-translation intervals certified by swept bounding boxes or midpoint minimum-distance bounds; recursively subdivided. Unresolved intervals fail.',tolerance_mm=EPS,collision_volume_tolerance_mm3=.001,stages=records,distance_queries=queries,bounding_box_prunes=pruned,certified_distance_intervals=proven,certified_bevel_withdrawals=bevel_proofs,certified_button_withdrawals=button_proofs,collisions=failures,unresolved_intervals=unresolved,exceptions=[dict(parts=sorted(k),reason=v) for k,v in allowed.items()],final_offsets_mm=offsets,limits=['Ideal rigid CAD surfaces and reference hardware envelopes; actual print fit not certified.','Threads are not modeled. Fasteners must be unthreaded before the depicted withdrawal.','Designed compliant tooth interference is intentional and excluded; other rigid pairs are checked.','Explosion is checked at the zero-angle assembled pose; rotation is disabled during explosion.'])

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',default=str(ROOT.parent/'output/armature-base-test-v4'));a=ap.parse_args()
    out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
    p=json.loads((ROOT/'parameters.json').read_text());parts,_=build(p);stages=timeline(parts)
    report=check(parts,stages);report['spindle_print_fit']=spindle_fit_checks(parts,p);report['source_sha256']={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['build.py','rotary_base/core.py','rotary_base/gear_geometry.py','explosion.py','parameters.json','check_explosion.py']}
    (out/'explosion_validation.json').write_text(json.dumps(report,indent=2))
    assert report['passed'],(report['collisions'],report['unresolved_intervals'])
    (out/'explosion_path.json').write_text(json.dumps(stages,indent=2))
