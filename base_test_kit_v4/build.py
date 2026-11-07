"""Standalone exporter using the shared rotary-base CAD."""
import sys,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
if not (ROOT/"rotary_base").exists():sys.path.insert(0,str(ROOT.parent))
from rotary_base.core import *
ROOT=pathlib.Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default=str(ROOT.parent/'output/armature-base-test-v4'));ap.add_argument('--config',default=str(ROOT/'parameters.json'));ap.add_argument('--check-only',action='store_true');args=ap.parse_args()
    p=json.loads(pathlib.Path(args.config).read_text());out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    parts,nominal=build(p);report=validate(parts,p);report['parameters']=p
    (out/'validation.json').write_text(json.dumps(report,indent=2))
    assert report['passed'],report['collisions']
    if args.check_only:return
    stl=out/'STL';stl.mkdir(exist_ok=True);manifest=[]
    current={q['print_id']+'.stl' for q in parts if q['print_id']}
    for stale in stl.glob('*.stl'):
        if stale.name not in current:stale.unlink()
    for q in parts:
        if not q['print_id']:continue
        s=print_shape(q);b=s.BoundingBox();path=stl/(q['print_id']+'.stl')
        assert s.isValid() and len(s.Solids())==1 and abs(b.zmin)<1e-6
        assert max(b.xlen,b.ylen)<=p['stand_size']+.01
        cq.exporters.export(s,str(path),tolerance=.025,angularTolerance=.06)
        manifest.append(dict(file=str(path.relative_to(out)),quantity=q['qty'],size_mm=[round(b.xlen,2),round(b.ylen,2),round(b.zlen,2)],volume_mm3=round(s.Volume(),2),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    fits=out/'OPTIONAL_fit_tests';fits.mkdir(exist_ok=True)
    for stale in fits.glob('*.stl'):stale.unlink()
    for d in [32,32.1,32.2,32.3]:
        coupon=annulus(20,14.6,11,0).cut(cyl(d/2,9.2,(0,0,1.8)))
        cq.exporters.export(coupon,str(fits/f'bearing_seat_coupon_{d:.1f}mm.stl'))
        if abs(d-p['bearing_seat_diameter'])>.001:
            cq.exporters.export(print_shape(dict(shape=make_housing(p,d),flip=False)),str(fits/f'ALTERNATE_housing_seat_{d:.1f}mm_USE_INSTEAD_OF_08.stl'))
    for d in [14.7,14.8,14.9,15.0,15.1,15.25,15.5]:
        coupon=box(22,22,2,(0,0,1)).fuse(chamfered_shaft(d/2,10,2,p['spindle_top_chamfer_mm'])).cut(cyl(3.3,14,(0,0,-1)))
        cuts=spindle_relief_cutters(p,d,height=10,z=2)
        if cuts:coupon=coupon.cut(*cuts).clean()
        cq.exporters.export(coupon,str(fits/f'spindle_coupon_{d:g}mm.stl'))
        if abs(d-p['spindle_diameter'])>.001:
            cq.exporters.export(print_shape(dict(shape=make_spindle(p,d),flip=False)),str(fits/f'ALTERNATE_spindle_{d:g}mm_USE_INSTEAD_OF_05.stl'))
    for d in [4.9,5.0,5.1]:
        coupon=roller_block(p|{'roller_axle_diameter_mm':d})
        cq.exporters.export(print_shape(dict(shape=coupon,flip=False)),str(fits/f'625_axle_coupon_{d:.1f}mm_45deg.stl'),tolerance=.025,angularTolerance=.06)
    for path in fits.glob('*.stl'):assert path.stat().st_size>100
    (out/'print_manifest.json').write_text(json.dumps(manifest,indent=2))
    assembly=cq.Assembly(name='Armature_base_standalone_test')
    for q in parts:
        if not q['keepout']:assembly.add(q['shape'],name=q['name'],color=cq.Color(q['color']))
    assembly.save(str(out/'ASSEMBLY_reference_DO_NOT_PRINT.step'))
    from explosion import timeline
    stages=timeline(parts)
    (out/'explosion_path.json').write_text(json.dumps(stages,indent=2))
    data=[]
    for q in parts:
        vertices,triangles=q['shape'].tessellate(.15,.15)
        data.append(dict(printFile=('STL/'+q['print_id']+'.stl') if q['print_id'] else None,reference=q['reference'],name=q['name'],color=q['color'],group=q['group'],keepout=q['keepout'],vertices=[v.toTuple() for v in vertices],triangles=triangles))
    (out/'preview_mesh.json').write_text(json.dumps(data,separators=(',',':')))
    print('Exported',len(manifest),'STL designs;',sum(q['quantity'] for q in manifest),'printed pieces',flush=True)

if __name__=='__main__':main()
