"""Changed-structure interference, interfaces, continuous travel envelopes and mesh checks."""
import hashlib,itertools,json,math
import trimesh
from .model import build,OUT,ROOT,prism,band,yhole,BOTTOM,TOP,LEVELS
from rigid_base.model import build as previous,overlap,cyl,annulus

def main():
    parts,info=build();old,_=previous();oldnames={a['name'] for a in old};changed=[a for a in parts if a['name'] not in oldnames];by={a['name']:a for a in parts}
    issues=[];count=0;bounds={a['name']:a['shape'].BoundingBox() for a in parts}
    for a,b in itertools.combinations(parts,2):
        if a not in changed and b not in changed:continue
        ba,bb=bounds[a['name']],bounds[b['name']]
        if any(getattr(ba,k+'max')<=getattr(bb,k+'min')+1e-6 or getattr(bb,k+'max')<=getattr(ba,k+'min')+1e-6 for k in 'xyz'):continue
        vol=overlap(a['shape'],b['shape']);count+=1
        if vol>.01:issues.append([a['name'],b['name'],vol]);print('Collision',issues[-1],flush=True)
    print('Static checks',count,'collisions',len(issues),flush=True)
    # New backbone lies entirely behind every moving actuator throughout travel.
    motionrows=[]
    for a in parts:
        if not a.get('motion'):continue
        b=bounds[a['name']];moving_ymin=b.ymin
        if a['motion']=='z_drive':moving_ymin=-math.hypot(max(abs(b.xmin),abs(b.xmax)),max(abs(b.ymin),abs(b.ymax)))
        if a['motion']=='r_drive':
            axis_z=info['arm_layout']['r_drive_z']+info['arm_z_shift_mm']
            moving_ymin=-math.hypot(max(abs(b.ymin),abs(b.ymax)),max(abs(b.zmin-axis_z),abs(b.zmax-axis_z)))
        if a['motion'] in ['z_rack','r_rack','r_drive','z_drive']:
            for structure in changed:
                q=bounds[structure['name']]
                # Spinning parts use conservative bounding-box corner radii;
                # linear translation cannot change their swept Y envelope.
                if q.ymax<=moving_ymin+1e-6:
                    motionrows.append(dict(part=a['name'],structure=structure['name'],gap_mm=moving_ymin-q.ymax))
                elif q.zmax<=b.zmin-20+1e-6:motionrows.append(dict(part=a['name'],structure=structure['name'],vertical_gap_mm=b.zmin-20-q.zmax))
                elif q.zmin>=b.zmax+20-1e-6:motionrows.append(dict(part=a['name'],structure=structure['name'],vertical_gap_mm=q.zmin-b.zmax-20))
                else:issues.append(['unproven continuous motion',a['name'],structure['name']])
    front=by['Backbone_front_tray']['shape'];back=by['Backbone_rear_tray']['shape'];deck=by['Socket_rotating_deck']['shape']
    for a in changed:
        assert a['shape'].isValid() and len(a['shape'].Solids())==1,a['name']
    assert front.intersect(back).Volume()<1e-6
    # Male socket remains within its female shell, with the specified 0.3 mm nominal gap.
    assert band(3.3,8.3,BOTTOM,12).intersect(front.fuse(back)).Volume()<1e-6
    # Deck and tower fit inside a 224 mm circular plan envelope (hardware excluded).
    env=cyl(112,500,(0,0,0))
    for name in ['Backbone_front_tray','Backbone_rear_tray','Socket_rotating_deck']:assert by[name]['shape'].cut(env).Volume()<1e-5,name
    # Continuous full-turn envelope for all replacement rotor parts.
    orbit=annulus(114,36,TOP-BOTTOM,BOTTOM).fuse(annulus(112,14.6,8,48.2))
    for a in changed:assert a['shape'].cut(orbit).Volume()<1e-5,a['name']
    rotation=[]
    for a in parts:
        if a['group']!='rotor':
            vol=overlap(orbit,a['shape']);rotation.append(dict(part=a['name'],overlap_mm3=vol))
            if vol>.001:issues.append(['rotation envelope',a['name'],vol])
    # Audit every retained print too; only planar 90-degree bed rotations allowed.
    fit=[]
    shared=json.loads((ROOT/'output/rigid-base/print-manifest.json').read_text())
    retained={a['name'] for a in parts if a['printed']}
    for row in shared+json.loads((OUT/'print-manifest.json').read_text()):
        if row['name'] not in retained:continue
        dims=row.get('mesh_size_mm',row['size_mm']);x,y,z=dims
        ok=z<=340 and ((x+8<=340 and y+8<=320) or (y+8<=340 and x+8<=320))
        fit.append(dict(part=row['name'],size_mm=dims,fits_H2S_with_4mm_bed_margin=ok))
        if not ok:issues.append(['H2S fit',row['name'],dims])
    meshrows=[]
    for row in json.loads((OUT/'print-manifest.json').read_text()):
        mesh=trimesh.load_mesh(OUT/row['file']);bed=(abs(mesh.triangles[:,:,2]).max(axis=1)<1e-5)&(mesh.face_normals[:,2]<-.999)
        mr=dict(part=row['name'],watertight=bool(mesh.is_watertight),consistent_winding=bool(mesh.is_winding_consistent),shells=len(mesh.split(only_watertight=False)),volume_mm3=float(mesh.volume),size_mm=mesh.extents.tolist(),bed_area_mm2=float(mesh.area_faces[bed].sum()),sha256=hashlib.sha256((OUT/row['file']).read_bytes()).hexdigest())
        if not (mr['watertight'] and mr['consistent_winding'] and mr['shells']==1 and mr['volume_mm3']>0 and abs(mesh.bounds[0,2])<1e-5):issues.append(['print',mr])
        meshrows.append(mr)
    before=sum(a['shape'].Volume() for a in old if a['name'] in ['Boxed_Z_support','Rigid_rotating_deck'] or a['name'].startswith('Printed_rear_brace_'))
    after=sum(a['shape'].Volume() for a in changed if a['printed'])
    report=dict(passed=not issues,issues=issues,static_pair_checks=count,continuous_rotation_envelope=rotation,H2S_fit=fit,continuous_motion_separation=motionrows,prints=meshrows,comparison=dict(previous_structure_volume_mm3=before,new_structure_volume_mm3=after,reduction_percent=100*(1-after/before)),physical_stiffness_verified=False,limits=['CAD checks do not measure stiffness, creep or printed fit.','Continuous travel proofs cover the replacement structure; existing unchanged actuator and gear checks are inherited.'],source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['hollow_base/model.py','hollow_base/check.py','rigid_base/model.py','rigid_base/printed_braces.py']})
    (OUT/'validation.json').write_text(json.dumps(report,indent=2));print(report['comparison'],flush=True);assert report['passed'],issues
if __name__=='__main__':main()
