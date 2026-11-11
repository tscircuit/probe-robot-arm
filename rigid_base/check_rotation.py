"""Changed base rotation, printed fit envelopes, and actual STL validation."""
import itertools,json,math,hashlib
import trimesh
from .model import build,parameters,ROOT,cyl,annulus,box,overlap
from .check import contacts
from rotary_base import core
from .envelopes import ring_envelope

def main():
    parts,info=build();by={a['name']:a for a in parts};out=ROOT/'output/rigid-base';allowed=contacts(parts,info)
    # Reuse the original spindle and integral-axle fit assertions with canonical names.
    adapted=[]
    for a in parts:
        name=a['name']
        if name=='Rigid_fixed_base':name='Fixed_base_plate'
        if name.startswith('625ZZ_support_roller_'):name='625ZZ_support_roller_'+str([45,135,225,315].index(int(name.rsplit('_',1)[1])))
        adapted.append(a|dict(name=name))
    roller_fit=core.roller_fit_checks(adapted,info['roller_parameters'])
    s=by['Solid_12T_module1_pinion']['shape'].intersect(by['688ZZ_pinion_bearing']['shape']);shell=annulus(4.025,4,5,17).translate((info['center_mm'],0,0));assert s.cut(shell).Volume()<1e-6
    assert abs(s.Volume()-math.pi*(4.025**2-4**2)*5)<1e-5
    envelope=ring_envelope();envelope_checks=[]
    assert by['Internal_264T_ring']['shape'].cut(envelope).Volume()<1e-5
    for a in parts:
        if a['group']!='fixed':continue
        vol=overlap(envelope,a['shape']);assert vol<1e-6,(a['name'],vol)
        allowed[frozenset(['Internal_264T_ring',a['name']])]='Continuous full-revolution ring envelope clearance'
        envelope_checks.append(dict(part=a['name'],overlap_mm3=vol))
    # Ring fasteners sweep circles too. Check a conservative continuous envelope,
    # including flat button heads, rather than relying on angular samples alone.
    p=parameters();r=p['ring_bolt_radius_mm']
    screw_orbit=annulus(r+2.85,r-2.85,1.65,22.35).fuse(annulus(r+1.45,r-1.45,40,24))
    nut_orbit=annulus(r+3.5,r-3.5,2.9,56.2)
    deck_orbit=annulus(p['deck_radius_mm'],14.6,8,48.2).fuse(annulus(p['deck_radius_mm']-2,57,12,44.2))
    orbit_checks={}
    for a in parts:
        env=screw_orbit if a['name'].startswith('M3x40_ring_') else nut_orbit if a['name'].startswith(('M3_ring_nut_','M3_ring_washer_')) else deck_orbit if a['name']=='Rigid_rotating_deck' else None
        if env is None:continue
        assert a['shape'].cut(env).Volume()<1e-5,a['name']
        for b in parts:
            if b['group']!='fixed':continue
            key=(id(env),b['name'])
            if key not in orbit_checks:orbit_checks[key]=overlap(env,b['shape'])
            vol=orbit_checks[key];assert vol<1e-6,(a['name'],b['name'],vol)
            allowed[frozenset([a['name'],b['name']])]='Continuous circular hardware/deck envelope clearance'
    rows=[];checks=0;symmetric_cache={}
    symmetric={'Inner_race_spacer','Inner_race_top_washer','6002_bearing_18','6002_bearing_43','M6x60_axle_bolt','M6_washer_-1.6','M6_washer_50'}
    # Only parts in unlike rotation groups can change their relative position.
    pairs=[(a,b) for a,b in itertools.combinations(parts,2) if a['group']!=b['group'] and frozenset([a['name'],b['name']]) not in allowed]
    for angle in range(0,360,15):
        posed={}
        for a in parts:
            s=a['shape']
            if a['group']=='rotor':s=s.rotate((0,0,0),(0,0,1),angle)
            if a['group']=='pinion':s=s.rotate((info['center_mm'],0,0),(info['center_mm'],0,1),angle*info['ratio'])
            posed[a['name']]=s
        fail=[];bounds={n:s.BoundingBox() for n,s in posed.items()}
        for a,b in pairs:
            ba,bb=bounds[a['name']],bounds[b['name']]
            if any(getattr(ba,k+'max')<=getattr(bb,k+'min')+1e-6 or getattr(bb,k+'max')<=getattr(ba,k+'min')+1e-6 for k in 'xyz'):continue
            key=(a['name'],b['name']);invariant=(a['name'] in symmetric and b['group']=='rotor') or (b['name'] in symmetric and a['group']=='rotor')
            if invariant and key in symmetric_cache:vol=symmetric_cache[key]
            else:
                vol=overlap(posed[a['name']],posed[b['name']]);checks+=1
                if invariant:symmetric_cache[key]=vol
            if vol>.01:fail.append([a['name'],b['name'],vol])
        rows.append(dict(angle_deg=angle,collisions=fail));print('Rotation',angle,'collisions',fail,flush=True);assert not fail,fail
    meshrows=[]
    for a in parts:
        if not a['printed']:continue
        path=out/'STL'/(a['name']+'.stl');m=trimesh.load_mesh(path)
        row=dict(part=a['name'],watertight=bool(m.is_watertight),consistent_winding=bool(m.is_winding_consistent),solid_shells=len(m.split(only_watertight=False)),positive_volume=bool(m.volume>0),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        assert row['watertight'] and row['consistent_winding'] and row['solid_shells']==1 and row['positive_volume'],row
        assert abs(m.bounds[0,2])<1e-5,a['name']
        if a['name']=='Boxed_Z_support':
            bed=(abs(m.triangles[:,:,2]).max(axis=1)<1e-5)&(m.face_normals[:,2]<-.999)
            row['flat_bed_area_mm2']=float(m.area_faces[bed].sum());assert row['flat_bed_area_mm2']>15000
        x,y,z=map(float,m.extents);row['size_mm']=[x,y,z]
        row['fits_H2S_with_4mm_bed_margin']=(z<=340+1e-5 and ((x+8<=340+1e-5 and y+8<=320+1e-5) or (y+8<=340+1e-5 and x+8<=320+1e-5)))
        assert row['fits_H2S_with_4mm_bed_margin'],row
        meshrows.append(row)
    report=dict(passed=True,rotation_samples=rows,continuous_ring_envelope_checks=envelope_checks,collision_pair_checks=checks,roller_axle_fit=roller_fit,pinion_journal_fit=dict(diameter_mm=8.05,bearing_bore_mm=8,overlap_mm3=shell.Volume()),physical_fit_verified=False,prints=meshrows,source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['rigid_base/model.py','rigid_base/front_frame.py','rigid_base/frame_struts.py','rigid_base/check_rotation.py','rigid_base/prepare_prints.py','rigid_base/parameters.json','rigid_base/envelopes.py']})
    (out/'print-validation.json').write_text(json.dumps(report,indent=2));print('Rotation and print checks passed',flush=True)
if __name__=='__main__':main()
