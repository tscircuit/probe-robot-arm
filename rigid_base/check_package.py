"""Verify the delivered larger-ring kit and removal of the rejected variant."""
import gzip,hashlib,json,pathlib,zipfile
ROOT=pathlib.Path(__file__).resolve().parent.parent

def main():
    out=ROOT/'output/rigid-base';web=ROOT/'site/dist';dest=web/'downloads/rigid-base'
    manifest=json.loads((out/'print-manifest.json').read_text());names={r['name'] for r in manifest}
    assert len(names)==24 and 'Internal_264T_ring' in names and 'Internal_192T_ring' not in names
    assert 'Front_Z_frame' in names and not any(n.startswith(('Printed_front_brace','Printed_rear_brace')) for n in names)
    assert names=={a['name'] for a in json.loads((out/'mesh.json').read_text()) if a['printed']}
    assert {p.stem for p in (dest/'STL').glob('*.stl')}==names
    with zipfile.ZipFile(dest/'print-kit.zip') as z:
        assert z.testzip() is None
        assert {pathlib.Path(n).stem for n in z.namelist() if n.endswith('.stl')}==names
        for row in manifest:
            data=z.read(row['file']);assert data==(dest/row['file']).read_bytes()==(out/row['file']).read_bytes()
            assert hashlib.sha256(data).hexdigest()==row['sha256']
        for n in ['parameters.json','validation.json','print-validation.json','explosion-validation.json','frame-validation.json']:assert z.read(n)==(out/n).read_bytes()
    with zipfile.ZipFile(dest/'rigid-arm-step.zip') as z:assert z.testzip() is None and z.read('rigid-arm.step')==(out/'rigid-arm.step').read_bytes()
    assert gzip.decompress((dest/'mesh.json.gz').read_bytes())==(out/'mesh.json').read_bytes()
    config=json.loads((dest/'config.json').read_text());assert config['ring_teeth']==264 and config['ratio']==22 and config['center_mm']==126
    assert not (web/'hollow-base.html').exists() and not (web/'downloads/hollow-base').exists()
    for name in ['index.html','base-test.html','rigid-base.html']:assert 'hollow-base.html' not in (web/name).read_text()
    assert 'hollow-base' not in (web/'rigid-base.js').read_text()
    report=dict(passed=True,prints=len(names),ring_teeth=264,ratio=22,hollow_variant_removed=True,mesh_sha256=hashlib.sha256((out/'mesh.json').read_bytes()).hexdigest(),print_zip_sha256=hashlib.sha256((dest/'print-kit.zip').read_bytes()).hexdigest(),step_zip_sha256=hashlib.sha256((dest/'rigid-arm-step.zip').read_bytes()).hexdigest())
    (out/'package-validation.json').write_text(json.dumps(report,indent=2));print('24 print files, ZIPs, shared viewer geometry and hollow variant removal passed')
if __name__=='__main__':main()
