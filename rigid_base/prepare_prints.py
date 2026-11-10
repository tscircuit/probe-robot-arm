"""Put the tessellated print surface at Z=0 (CAD bounds can be conservative)."""
import hashlib,json
import trimesh
from .model import ROOT,build,parameters
import cadquery as cq

def main():
    out=ROOT/'output/rigid-base';manifest=json.loads((out/'print-manifest.json').read_text())
    for row in manifest:
        path=out/row['file'];mesh=trimesh.load_mesh(path);shift=-float(mesh.bounds[0,2])
        if abs(shift)>1e-6:
            mesh.apply_translation([0,0,shift]);mesh.export(path);row['mesh_bed_adjustment_mm']=row.get('mesh_bed_adjustment_mm',0)+shift
        if not mesh.is_watertight:
            # OCC can omit a planar quad between coplanar boolean boundaries.
            # Only fill small holes whose complete added faces lie on the CAD skin.
            assert row['name']=='Rigid_rotating_deck',row['name']
            before=len(mesh.faces);assert mesh.fill_holes() and 0<len(mesh.faces)-before<=8
            parts,_=build();cad=next(a['shape'] for a in parts if a['name']==row['name'])
            cad=cad.rotate((0,0,0),(1,0,0),180).translate((0,0,parameters()['deck_top_mm']))
            repairs=[]
            for face in mesh.faces[before:]:
                points=mesh.vertices[face];assert points[:,2].max()-points[:,2].min()<1e-5
                triangle=cq.Face.makeFromWires(cq.Wire.makePolygon([cq.Vector(*v) for v in [*points,points[0]]]))
                skin=[f for f in cad.Faces() if f.geomType()=='PLANE' and abs(f.normalAt().z)>.999 and abs(f.Center().z-points[:,2].mean())<1e-5]
                outside=triangle.cut(cq.Compound.makeCompound(skin)).Area();assert outside<1e-5,outside
                repairs.append(dict(area_mm2=triangle.Area(),area_outside_cad_skin_mm2=outside))
            assert mesh.is_winding_consistent and abs(mesh.volume-cad.Volume())<max(5,cad.Volume()*.002)
            mesh.export(path);row['cad_verified_planar_mesh_repairs']=repairs
        row['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();row['mesh_size_mm']=mesh.extents.tolist()
    (out/'print-manifest.json').write_text(json.dumps(manifest,indent=2));print('Aligned',len(manifest),'actual STL meshes to print bed')
if __name__=='__main__':main()
