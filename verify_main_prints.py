"""Inspect the actual downloadable main-arm STL meshes."""
import argparse,hashlib,json,pathlib
import trimesh
root=pathlib.Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--out',default=str(root/'output'));args=ap.parse_args();out=pathlib.Path(args.out)
parts=[p for p in json.loads((out/'arm-mesh.json').read_text()) if p['printed']]
rows=[]
for p in parts:
 path=out/'prototype-parts'/(p['name']+'.stl');m=trimesh.load_mesh(path)
 row=dict(part=p['name'],watertight=bool(m.is_watertight),consistent_winding=bool(m.is_winding_consistent),solid_shells=len(m.split(only_watertight=False)),positive_volume=bool(m.volume>0),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
 assert row['watertight'] and row['consistent_winding'] and row['solid_shells']==1 and row['positive_volume'],row
 if p.get('base_name'):assert abs(m.bounds[0,2])<1e-5,p['name']
 rows.append(row)
(out/'print-mesh-validation.json').write_text(json.dumps(dict(passed=True,print_count=len(rows),files=rows),indent=2));print('Verified',len(rows),'main-arm STL meshes.')
