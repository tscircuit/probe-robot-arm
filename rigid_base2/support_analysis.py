"""Upright geometric layer-support audit. Not slicer-generated support material."""
import argparse,json,math,pathlib,hashlib
import numpy as np,trimesh
from shapely.geometry import GeometryCollection
from shapely.ops import unary_union
ROOT=pathlib.Path(__file__).resolve().parent.parent;OUT=ROOT/'output/rigid-base2/analysis'

def run(label,layer=.2):
    path=OUT/(label+'.stl');m=trimesh.load_mesh(path);m.apply_translation([0,0,-m.bounds[0,2]])
    over=(m.face_normals[:,2]<-.72)&(m.triangles[:,:,2].mean(axis=1)>layer)
    previous=GeometryCollection();total=0.;peak=0.;bad=[];islands=[];rows=[]
    for k,z in enumerate(np.arange(layer/2,m.bounds[1,2],layer)):
        section=m.section(plane_origin=[0,0,float(z)],plane_normal=[0,0,1])
        if section is None:continue
        flat=trimesh.path.Path2D(entities=section.entities,vertices=section.vertices[:,:2])
        current=unary_union(flat.polygons_full)
        if not current.is_valid:current=current.buffer(0)
        if k:
            unsupported=current.difference(previous.buffer(layer*1.05+.025))
            area=unsupported.area;total+=area*layer
            if area>.05:
                distance=0
                for part in getattr(unsupported,'geoms',[unsupported]):
                    if part.area<.05:continue
                    samples=[part.representative_point()]
                    from shapely.geometry import Point
                    samples += [Point(x,y) for x,y in list(part.exterior.coords)[::max(1,len(part.exterior.coords)//20)]]
                    d=max(previous.distance(pt) for pt in samples);distance=max(distance,d)
                peak=max(peak,distance)
                rows.append(dict(z_mm=round(float(z),3),unsupported_growth_area_mm2=round(area,4),sampled_distance_to_previous_layer_mm=round(distance,4)))
                if distance>2.5 and area>1:bad.append(rows[-1])
            for part in getattr(current,'geoms',[current]):
                if part.area>1 and not part.intersects(previous.buffer(layer*1.05+.025)):islands.append(dict(z_mm=round(float(z),3),area_mm2=part.area))
        previous=current
        if k%200==0:print(label,'layer',k,'/',round(m.bounds[1,2]/layer),flush=True)
    report=dict(label=label,layer_height_mm=layer,nominal_overhang_angle_deg=45,xy_allowance_mm=layer*1.05+.025,steep_downward_surface_area_mm2=float(m.area_faces[over].sum()),unsupported_layer_growth_volume_mm3=total,max_sampled_distance_to_previous_layer_mm=peak,large_overhang_layers=bad,floating_regions=islands,flagged_layers=rows,stl_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),limits=['Geometry-only 0.2 mm upright layer comparison, with 0.035 mm tessellation/XY tolerance.','Distances sampled on unsupported polygons; not an exhaustive maximum-span proof.','Unsupported layer growth is not slicer support volume, filament use or a bridging guarantee.','Small horizontal mounting holes still require short bridging. Roof seams, material, cooling and actual slicer settings must be checked.'])
    (OUT/(label+'-supports.json')).write_text(json.dumps(report,indent=2));print(label,'support audit',report['steep_downward_surface_area_mm2'],total,peak,len(bad),len(islands),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('label',choices=['before','after']);a=p.parse_args();run(a.label)
