"""Check the lightened deck's mounting lands, flange support and print surface."""
import hashlib,json,pathlib
import cadquery as cq
import rotary_base
from rotary_base.core import annulus,box,cyl,deck_relief_cutters,polar,rotor_bolts
from model import build,layout
root=pathlib.Path(__file__).resolve().parent
p=rotary_base.parameters()
parts,_=rotary_base.build(p)
previous,_=rotary_base.build(p|{'deck_cutouts':False})
by={q['name']:q['shape'] for q in parts}
old={q['name']:q['shape'] for q in previous}
s=by['Rotating_test_deck'];before=old['Rotating_test_deck']
assert s.isValid() and len(s.Solids())==1
assert s.cut(before).Volume()<1e-6, 'Deck relief may only remove material'
for name in by:
 if name!='Rotating_test_deck':
  assert abs(by[name].Volume()-old[name].Volume())<1e-6,name
windows=[q.translate((0,0,-p['rotor_drop_mm'])) for q in deck_relief_cutters(p)]
assert len(windows)==5
for q in windows:assert q.intersect(s).Volume()<1e-6, 'Window not fully open'
top=58.2-p['rotor_drop_mm'];z=top-12
regions=[('central bearing hub',cyl(28,14,(0,0,z))),('continuous outer rim',annulus(82,72,14,z))]
for i,(x,y) in enumerate(p['z_deck_mounts']):regions.append((f'Z insert seat {i}',cyl(7,14,(x,y,z))))
for i,(x,y) in enumerate(rotor_bolts()):regions.append((f'bearing housing fastener {i}',cyl(4.5,14,(x,y,z))))
import math
for angle in [30,90,150]:regions.append((f'radial ribs {angle}/{angle+180}',box(164,14,14,(0,0,z+7)).rotate((0,0,0),(0,0,1),angle)))
for i in range(6):
 x,y=polar(78,math.radians(30+60*i));regions.append((f'ring fastener seat {i}',cyl(4.5,14,(x,y,z))))
# Check the complete actual cradle footprint, including its joining corner.
main_p=json.loads((root/'parameters.json').read_text());lay=layout(main_p);main,_=build(main_p,lay)
support=next(q['shape'] for q in main if q['name']=='Z_support')
footprint=support.intersect(box(200,200,1,(0,0,top+.5))).translate((0,0,-1))
assert before.intersect(footprint).cut(s).Volume()<1e-6, 'Relief removes cradle flange support'
regions.append(('full side flange footprint',box(88,23.6,14,(-13,-50.2,z+7))))
front=lay['z_actuator']['CASE_TOP']
regions.append(('full front flange footprint',box(52-front,104,14,((52+front)/2,2,z+7))))
rows=[]
for name,region in regions:
 lost=before.intersect(region).cut(s).Volume();assert lost<1e-5,(name,lost)
 rows.append(dict(region=name,removed_material_mm3=max(0,lost)))
removed=before.Volume()-s.Volume();fraction=removed/before.Volume();assert fraction>.2
assert abs(removed-sum(w.intersect(before).Volume() for w in windows))<1e-4
# The flipped deck prints on its original continuous top face.
part=next(q for q in parts if q['name']=='Rotating_test_deck');printed=rotary_base.core.print_shape(part)
bed=[f for f in printed.Faces() if f.geomType()=='PLANE' and abs(f.Center().z)<1e-6 and f.normalAt().z<-.999]
assert abs(printed.BoundingBox().zmin)<1e-6 and len(bed)==1
r=dict(passed=True,cutouts=len(windows),original_volume_mm3=before.Volume(),new_volume_mm3=s.Volume(),removed_volume_mm3=removed,volume_reduction_percent=fraction*100,corner_radius_mm=p['deck_cutout_corner_radius_mm'],rim_width_mm=10,hub_radius_mm=28,radial_rib_width_mm=14,one_connected_solid=True,material_removal_only=True,full_cradle_footprint_supported=True,print_bed_face_count=len(bed),print_bed_area_mm2=sum(f.Area() for f in bed),retained_regions=rows,limits=['CAD material reduction is not a measured stiffness rating or an exact slicer filament saving.'],source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ['check_deck_cutouts.py','model.py','parameters.json','rotary_base/core.py','rotary_base/parameters.json']})
(root/'output/deck-cutouts-validation.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
