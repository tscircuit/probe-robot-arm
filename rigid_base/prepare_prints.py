"""Put the tessellated print surface at Z=0 (CAD bounds can be conservative)."""
import hashlib,json
import trimesh
from .model import ROOT

def main():
    out=ROOT/'output/rigid-base';manifest=json.loads((out/'print-manifest.json').read_text())
    for row in manifest:
        path=out/row['file'];mesh=trimesh.load_mesh(path);shift=-float(mesh.bounds[0,2])
        if abs(shift)>1e-6:
            mesh.apply_translation([0,0,shift]);mesh.export(path);row['mesh_bed_adjustment_mm']=row.get('mesh_bed_adjustment_mm',0)+shift
        row['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();row['mesh_size_mm']=mesh.extents.tolist()
    (out/'print-manifest.json').write_text(json.dumps(manifest,indent=2));print('Aligned',len(manifest),'actual STL meshes to print bed')
if __name__=='__main__':main()
