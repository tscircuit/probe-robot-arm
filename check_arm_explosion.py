"""Check every segment of explosion.py using conservative distance bounds.
For a translation interval of length L, distance at its midpoint >= L/2
certifies no positive intersection anywhere in that interval (within tolerance).
Uncertified intervals are subdivided, never silently marked passed.
"""
import argparse,hashlib,itertools,json,math,pathlib,time
from model import build,layout,overlap,box,union,base_contacts,linear_contacts,cyl
from arm_explosion import timeline
ROOT=pathlib.Path(__file__).resolve().parent
EPS=1e-6

def bb(s):
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    b=Bnd_Box();BRepBndLib.AddOptimal_s(s.wrapped,b,False,False);v=b.Get()
    return (list(v[:3]),list(v[3:]))

def disjoint(a,b,lo,hi):
    return any(a[1][i]+max(lo[i],hi[i])<=b[0][i]+EPS or b[1][i]<=a[0][i]+min(lo[i],hi[i])+EPS for i in range(3))

def exceptions(parts,lay):
    import rotary_base
    pairs=base_contacts(parts,rotary_base.parameters())
    for p in parts:
        if p.get('embedded_host'):
            pairs[frozenset([p['name'],p['embedded_host']])]='Intentional heat-set knurl/pilot interference; insert remains in host'
    pairs[frozenset([next(p['name'] for p in parts if p['name'].startswith('Compliant_') and p['group']=='base_drive'),'Internal_72T_ring'])]='Designed tooth preload; drive stays assembled'
    pairs.update(linear_contacts(parts,lay))
    return pairs

def check(parts,stages,lay):
    shapes={p['name']:p['shape'] for p in parts};bounds={n:bb(s) for n,s in shapes.items()}
    subbounds={}
    for p in parts:
        if p.get('sweep_boxes'):
            boxes=p['sweep_boxes']
            enclosing=union([box(*[hi[i]-lo[i] for i in range(3)],tuple((lo[i]+hi[i])/2 for i in range(3))) for lo,hi in boxes])
            assert p['shape'].cut(enclosing).Volume()<1e-6, 'Incomplete conservative bounds: '+p['name']
            subbounds[p['name']]=boxes
    def separated(a,b,lo,hi):
        return all(disjoint(aa,bb,lo,hi) for aa in subbounds.get(a,[bounds[a]]) for bb in subbounds.get(b,[bounds[b]]))
    offsets={n:[0.,0.,0.] for n in shapes};allowed=exceptions(parts,lay)
    failures=[];unresolved=[];records=[];queries=0;pruned=0;proven=0;sweeps=0
    for si,stage in enumerate(stages):
        start=time.time();movers=set(stage['parts']);delta=stage['delta'];length=math.sqrt(sum(d*d for d in delta))
        stage_queries=0;candidates=0
        for a in sorted(movers):
            for b in sorted(shapes.keys()-movers):
                if frozenset([a,b]) in allowed:continue
                rel=[offsets[a][k]-offsets[b][k] for k in range(3)]
                end=[rel[k]+delta[k] for k in range(3)]
                if separated(a,b,rel,end):pruned+=1;continue
                candidates+=1
                # The direct-mount screws are axial cylinders. Their complete
                # swept union is an exact conservative certificate, avoiding
                # thousands of tiny distance intervals in the service wells.
                if a.startswith('Z_output_mount_screw_') and delta[0]==delta[1]==0 and delta[2]>0:
                    bb0=bounds[a];x=(bb0[0][0]+bb0[1][0])/2+rel[0];y=(bb0[0][1]+bb0[1][1])/2+rel[1];z=bb0[0][2]+rel[2]
                    swept=cyl(1.45,12+delta[2],(x,y,z)).fuse(cyl(2.75,3+delta[2],(x,y,z+12)))
                    assert shapes[a].translate(tuple(rel)).cut(swept).Volume()<1e-6
                    if overlap(swept,shapes[b])<1e-6:
                        sweeps+=1;continue
                stack=[(0.,1.)];local_queries=0
                while stack:
                    lo,hi=stack.pop();v0=[rel[k]+lo*delta[k] for k in range(3)];v1=[rel[k]+hi*delta[k] for k in range(3)]
                    if separated(a,b,v0,v1):pruned+=1;continue
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
    return dict(passed=not failures and not unresolved and len(records)==len(stages),method='Continuous linear-translation intervals certified by swept bounding boxes or exact axial screw sweeps or midpoint minimum-distance bounds; recursively subdivided. Unresolved intervals fail.',tolerance_mm=EPS,collision_volume_tolerance_mm3=.001,stages=records,distance_queries=queries,certified_axial_sweeps=sweeps,bounding_box_prunes=pruned,certified_distance_intervals=proven,collisions=failures,unresolved_intervals=unresolved,exceptions=[dict(parts=sorted(k),reason=v) for k,v in allowed.items()],final_offsets_mm=offsets,limits=['Ideal rigid CAD surfaces and reference hardware envelopes; actual print fit not certified.','Fastener threads are represented by receiving pilots. Unscrew fasteners before the depicted withdrawal; actuator lead screws remain engaged and stationary.','Designed compliant tooth interference is intentional and excluded; other rigid pairs are checked.','Explosion is checked at the zero-angle assembled pose; rotation is disabled during explosion.'])

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--config',default=str(ROOT/'parameters.json'));ap.add_argument('--out',default=str(ROOT/'output'));args=ap.parse_args()
    out=pathlib.Path(args.out)
    p=json.loads(pathlib.Path(args.config).read_text());lay=layout(p)
    parts,_=build(p,lay);stages=timeline(parts)
    report=check(parts,stages,lay)
    report['source_sha256']={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['model.py','parameters.json','rotary_base/core.py','rotary_base/gear_geometry.py','rotary_base/parameters.json','arm_explosion.py','check_arm_explosion.py','leadscrew_actuator.py','direct_mount.py']}
    report['source_sha256'][str(pathlib.Path(args.config).resolve().relative_to(ROOT))]=hashlib.sha256(pathlib.Path(args.config).read_bytes()).hexdigest()
    report['z_width']=p.get('z_width',4)
    report['scope']='One arm, module-level separation from base mounting faces. Internal actuator drives and rotary base stay assembled.'
    (out/'arm-explosion-validation.json').write_text(json.dumps(report,indent=2))
    assert report['passed'],(report['collisions'],report['unresolved_intervals'])
    (out/'arm-explosion-path.json').write_text(json.dumps(stages,indent=2))
