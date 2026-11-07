"""Check relief windows, retained mounting lands and material reduction."""
import hashlib,itertools,json,math,pathlib
import rotary_base
from rotary_base.core import base_relief_cutters,box,cyl,plate
root=pathlib.Path(__file__).resolve().parent
p=rotary_base.parameters();parts,_=rotary_base.build(p);original,_=rotary_base.build(p|{'base_cutouts':False})
base=next(q['shape'] for q in parts if q['name']=='Fixed_base_plate')
old=next(q['shape'] for q in original if q['name']=='Fixed_base_plate')
assert base.isValid() and len(base.Solids())==1
assert base.cut(old).Volume()<1e-6,'Relief must only remove material'
cutters=base_relief_cutters(p);assert len(cutters)==5
for c in cutters:assert c.intersect(base).Volume()<1e-6,'Window is not open through the plate'
lands=[('spindle hub',cyl(35,13,(0,0,-1))),('motor pad',box(56,58,13,(60,0,5.5)))]
for x,y in itertools.product([-75,75],repeat=2):lands.append((f'platform mount {x},{y}',cyl(12,13,(x,y,-1))))
for x,y in itertools.product([-60,60],repeat=2):lands.append((f'inner mount {x},{y}',cyl(8,13,(x,y,-1))))
for angle in p['roller_angles_deg']:lands.append((f'bearing block foot {angle}',box(26,20,11,(89,0,5.5)).rotate((0,0,0),(0,0,1),angle)))
for angle in [45,135]:lands.append((f'diagonal web {angle}',box(280,24,11,(0,0,5.5)).rotate((0,0,0),(0,0,1),angle)))
frame=plate(190,190,11,0).cut(box(170,170,13,(0,0,5.5)));lands.append(('10 mm perimeter',frame))
rows=[]
for name,region in lands:
 lost=old.intersect(region).cut(base).Volume();assert lost<1e-5,(name,lost)
 rows.append(dict(region=name,removed_material_mm3=max(0,lost)))
removed=old.Volume()-base.Volume();fraction=removed/old.Volume();assert fraction>.3
assert abs(removed-sum(c.intersect(old).Volume() for c in cutters))<1e-4
r=dict(passed=True,cutouts=5,corner_radius_mm=p['base_cutout_corner_radius_mm'],original_volume_mm3=old.Volume(),new_volume_mm3=base.Volume(),removed_volume_mm3=removed,volume_reduction_percent=100*fraction,perimeter_width_mm=10,diagonal_web_width_mm=20*math.sqrt(2),retained_regions=rows,one_connected_solid=True,material_removal_only=True,limits=['Geometric support continuity and clearances checked; stiffness and load capacity are not measured.'],source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ['check_base_cutouts.py','rotary_base/core.py','rotary_base/parameters.json']})
(root/'output/base-cutouts-validation.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
