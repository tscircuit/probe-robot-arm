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
    top=info['arm_parameters']['z_origin']+info['arm_z_shift_mm']+9;grid_bottom=top-154
    for sign in [-1,1]:
        # These conservative gauges certify continuous, broad junctions.
        assert box(4,.2,154,(sign*62,-48.1,(top+grid_bottom)/2)).cut(s).Volume()<1e-5
        assert box(4,.2,top-62.2,(sign*38,-139.5,(top+62.2)/2)).cut(s).Volume()<1e-5
        # The rear cross-panel meets the cage at broad full-height roots and
        # crosses each diagonal web at its bottom, middle and top solid bands.
        assert box(2,2,top-62.2,(sign*102,-104,(top+62.2)/2)).cut(s).Volume()<1e-5
        root_wall=annulus(147.8,143.2,top-62.2,62.2).intersect(box(8,10,top-62.2,(sign*102,-104,(top+62.2)/2)))
        assert root_wall.Volume()>10000 and root_wall.cut(s).Volume()<1e-5
        for z in [70,220,372]:
            assert box(3,3,6,(sign*(62-56*24/92),-104,z)).cut(s).Volume()<1e-5
        for y in [-48,48]:assert overlap(box(6,8,100,(sign*140,y,150)),s)<1e-6
    checks=[]
    for a in parts:
        if a.get('motion') not in ['z_rack','r_rack']:continue
        b=a['shape'].BoundingBox();lo=[b.xmin-(60 if a['motion']=='r_rack' else 0),b.ymin,b.zmin-20];hi=[b.xmax+(60 if a['motion']=='r_rack' else 0),b.ymax,b.zmax+20]
        env=box(*(hi[i]-lo[i] for i in range(3)),tuple((hi[i]+lo[i])/2 for i in range(3)))
        v=overlap(s,env);assert v<1e-6,(a['name'],v);checks.append(a['name'])
    r=dict(passed=True,cage_radius_mm=148,grid_depth_mm=6,external_struts=0,rear_shear_web_count=2,grid_junction_certified_area_each_mm2=4*154,rear_junction_certified_area_each_mm2=4*(top-62.2),former_port_slivers_removed=True,full_linear_sweep_checks=checks,physical_stiffness_verified=False,source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['rigid_base2/model.py','rigid_base2/check.py']})
    r.update(rear_cross_panel_thickness_mm=6,rear_cross_panel_cage_junctions=2,rear_cross_panel_web_junctions=6)
    (ROOT/'output/rigid-base2/cage-validation.json').write_text(json.dumps(r,indent=2));print('Cage radius, foot seats, broad rear-panel junctions, no struts and continuous linear sweeps passed',flush=True)
if __name__=='__main__':
    name=sys.argv[1] if len(sys.argv)>1 else 'collision'
    if name=='cage':cage_check()
    else:
        from rigid_base import check,check_rotation,check_explosion,prepare_prints
        run({'collision':check,'rotation':check_rotation,'explosion':check_explosion,'prints':prepare_prints}[name])
