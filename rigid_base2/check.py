"""Reuse common gear/motion/mesh proofs, then validate the cage interfaces."""
import hashlib,json,sys
from .model import ROOT,build,parameters,box,cyl,annulus,overlap
class OutputRoot:
    def __truediv__(self,name):return ROOT/('output/rigid-base2' if name=='output/rigid-base' else name)
def run(module):
    module.ROOT=OutputRoot();module.build=build;module.main()
    report={'check':'validation.json','check_rotation':'print-validation.json','check_explosion':'explosion-validation.json'}.get(module.__name__.rsplit('.',1)[-1])
    # Sign only the report this invocation generated. Never refresh another
    # check's source hashes: stale checks must keep failing package validation.
    for path in ([ROOT/'output/rigid-base2'/report] if report else []):
        r=json.loads(path.read_text());r.setdefault('source_sha256',{}).update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['rigid_base2/model.py','rigid_base2/check.py']});path.write_text(json.dumps(r,indent=2))
def cage_check():
    parts,info=build();by={a['name']:a for a in parts};s=by['Cylindrical_Z_support']['shape'];p=parameters()
    assert s.isValid() and len(s.Solids())==1
    assert not any('strut' in a['name'].lower() or 'front_frame' in a['name'].lower() or a['name']=='Front_Z_frame' for a in parts)
    assert s.cut(cyl(148,400,(0,0,0))).Volume()<1e-5
    for x,y in p['support_mounts_mm']+[[0,-138]]:
        assert annulus(3.5,2.2,.1,p['deck_top_mm']+5.9).translate((x,y,0)).cut(s).Volume()<1e-6,(x,y)
    checks=[]
    for a in parts:
        if a.get('motion') not in ['z_rack','r_rack']:continue
        b=a['shape'].BoundingBox();lo=[b.xmin-(60 if a['motion']=='r_rack' else 0),b.ymin,b.zmin-20];hi=[b.xmax+(60 if a['motion']=='r_rack' else 0),b.ymax,b.zmax+20]
        env=box(*(hi[i]-lo[i] for i in range(3)),tuple((hi[i]+lo[i])/2 for i in range(3)))
        v=overlap(s,env);assert v<1e-6,(a['name'],v);checks.append(a['name'])
    r=dict(passed=True,cage_radius_mm=148,grid_depth_mm=6,external_struts=0,full_linear_sweep_checks=checks,physical_stiffness_verified=False,source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['rigid_base2/model.py','rigid_base2/check.py']})
    (ROOT/'output/rigid-base2/cage-validation.json').write_text(json.dumps(r,indent=2));print('Cage radius, foot seats, no struts and continuous linear sweeps passed',flush=True)
if __name__=='__main__':
    name=sys.argv[1] if len(sys.argv)>1 else 'collision'
    if name=='cage':cage_check()
    else:
        from rigid_base import check,check_rotation,check_explosion,prepare_prints
        run({'collision':check,'rotation':check_rotation,'explosion':check_explosion,'prints':prepare_prints}[name])
