"""Continuous translation checks for the exact viewer's service-module path."""
import hashlib,json,math,time
from .model import build,ROOT,overlap,V,parameters,cyl,box
from .check import contacts
from .explosion import timeline
from rotary_base.core import roller_layout
from .envelopes import upward_ring_base_proof
EPS=1e-7

def bounds(s):
    b=s.BoundingBox();return ([b.xmin,b.ymin,b.zmin],[b.xmax,b.ymax,b.zmax])
def disjoint(a,b,lo,hi):
    return any(a[1][i]+max(lo[i],hi[i])<=b[0][i]+EPS or b[1][i]<=a[0][i]+min(lo[i],hi[i])+EPS for i in range(3))
def bevel_proof(a,b,delta,offsets,shapes,info):
    if a!='Internal_192T_ring' or not b.startswith('625ZZ_support_roller_'):return False
    if delta[0] or delta[1] or delta[2]<=0:return False
    if any(abs(v)>EPS for n in [a,b] for v in offsets[n]):return False
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    angle=int(b.rsplit('_',1)[1]);lay=roller_layout(info['roller_parameters'])
    def bb(s):
        s=s.rotate((0,0,0),(0,0,1),-angle).translate((-lay['center_r'],0,-lay['center_z'])).rotate((0,0,0),(0,1,0),45)
        q=Bnd_Box();BRepBndLib.AddOptimal_s(s.wrapped,q,False,False);return q.Get()
    # The low ring body lies radially inside the roller. Only the outer
    # bevel and higher standoffs need the tangent-plane withdrawal bound.
    wheel=shapes[b].rotate((0,0,0),(0,0,1),-angle)
    assert wheel.BoundingBox().xmin>106.001
    outer=shapes[a].cut(cyl(106,100,(0,0,0)))
    r,w=bb(outer),bb(shapes[b]);assert r[2]>=8-EPS and w[5]<=8+EPS,(r,w)
    return True

def main():
    parts,info=build();stages=timeline(parts);shapes={p['name']:p['shape'] for p in parts};bb={n:bounds(s) for n,s in shapes.items()};offsets={n:[0.,0.,0.] for n in shapes};allowed=contacts(parts,info)
    # The nominal M6 nut bore exactly touches its screw: certify axial removal
    # using the bore envelope, since a zero gap cannot satisfy distance bounds.
    screw=shapes['M6x60_axle_bolt'];nut=shapes['M6_axle_nut']
    assert screw.intersect(box(30,30,80,(0,0,40))).cut(cyl(3.000001,81,(0,0,0))).Volume()<1e-6
    assert overlap(nut,cyl(2.999999,80,(0,0,0)))<1e-6
    allowed[frozenset(['M6x60_axle_bolt','M6_axle_nut'])]='Released M6 thread; cylindrical bore envelope proves axial withdrawal'
    ring_base_proof=upward_ring_base_proof(shapes['Rigid_fixed_base'])
    failures=[];unresolved=[];records=[];queries=pruned=proven=0;bevels=[]
    for si,stage in enumerate(stages):
        start=time.time();movers=set(stage['parts']);delta=stage['delta'];length=math.sqrt(sum(d*d for d in delta));count=0
        for a in sorted(movers):
            for b in sorted(shapes.keys()-movers):
                if frozenset([a,b]) in allowed:continue
                if a=='Internal_192T_ring' and b=='Rigid_fixed_base' and delta==[0,0,100]:continue
                if bevel_proof(a,b,delta,offsets,shapes,info):bevels.append([si,a,b]);continue
                rel=[offsets[a][k]-offsets[b][k] for k in range(3)];end=[rel[k]+delta[k] for k in range(3)]
                if disjoint(bb[a],bb[b],rel,end):pruned+=1;continue
                stack=[(0.,1.)];local=0
                while stack:
                    lo,hi=stack.pop();v0=[rel[k]+lo*delta[k] for k in range(3)];v1=[rel[k]+hi*delta[k] for k in range(3)]
                    if disjoint(bb[a],bb[b],v0,v1):pruned+=1;continue
                    mid=(lo+hi)/2;v=[rel[k]+mid*delta[k] for k in range(3)];sa=shapes[a].translate(tuple(v));d=sa.distance(shapes[b]);queries+=1;count+=1;local+=1
                    if d>=length*(hi-lo)/2-EPS:proven+=1;continue
                    if d<EPS:
                        volume=overlap(sa,shapes[b])
                        if volume>.001:failures.append(dict(stage=si,a=a,b=b,t=mid,volume_mm3=volume));break
                    if length*(hi-lo)<.0001 or local>15000:unresolved.append(dict(stage=si,a=a,b=b,interval=[lo,hi],distance=d));break
                    stack.extend([(mid,hi),(lo,mid)])
                if failures or unresolved:break
            if failures or unresolved:break
        records.append(dict(stage=si,label=stage['label'],queries=count,seconds=round(time.time()-start,2)))
        print(records[-1],failures,unresolved,flush=True)
        if failures or unresolved:break
        for n in movers:offsets[n]=[offsets[n][k]+delta[k] for k in range(3)]
    report=dict(passed=not failures and not unresolved and len(records)==len(stages),method='Continuous swept AABB and recursively subdivided midpoint-distance bounds; unresolved intervals fail.',stages=records,collisions=failures,unresolved=unresolved,distance_queries=queries,pruned=pruned,certified_intervals=proven,bevel_withdrawal_proofs=bevels,ring_base_withdrawal_proof=ring_base_proof,exceptions=[dict(parts=sorted(k),reason=v) for k,v in allowed.items()],limits=['Released threads and axial printed press-fit withdrawal are intentional interfaces.','Ring/pinion have separately checked nonintersecting extruded profiles and separate only axially.','Service modules remain assembled internally; this is not a complete fastener disassembly.'],source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['rigid_base/model.py','rigid_base/printed_braces.py','rigid_base/parameters.json','rigid_base/check_explosion.py','rigid_base/explosion.py','rigid_base/envelopes.py']})
    out=ROOT/'output/rigid-base';(out/'explosion-validation.json').write_text(json.dumps(report,indent=2));(out/'explosion.json').write_text(json.dumps(stages));assert report['passed'],report
if __name__=='__main__':main()
