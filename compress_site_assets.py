"""Losslessly compress viewer data and share identical radial prints across Z widths."""
import gzip,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
SHARED_RADIAL_PARTS=['R_Structural_mounting_lid','R_Adjustable_six-bearing_base','R_Hollow_triangular_carriage','R_Printed_20_mm_lead_screw_with_integral_shaft_clamp']

def main():
    root=ROOT/'site/dist';rows=[];shared=[]
    for name in ['arm-mesh.json','variants/z-1x/arm-mesh.json','variants/z-2x/arm-mesh.json','downloads/rigid-base/mesh.json']:
        raw=root/name;packed=pathlib.Path(str(raw)+'.gz')
        if raw.exists():
            data=raw.read_bytes();packed.write_bytes(gzip.compress(data,compresslevel=9,mtime=0));assert gzip.decompress(packed.read_bytes())==data;raw.unlink()
        else:data=gzip.decompress(packed.read_bytes())
        json.loads(data);rows.append(dict(asset=name+'.gz',uncompressed_sha256=hashlib.sha256(data).hexdigest(),uncompressed_bytes=len(data),compressed_bytes=packed.stat().st_size))
    for name in SHARED_RADIAL_PARTS:
        common=root/'downloads/parts'/(name+'.stl');digest=hashlib.sha256(common.read_bytes()).hexdigest()
        for width in [1,2]:
            duplicate=root/f'downloads/widths/z-{width}x/parts'/(name+'.stl')
            if duplicate.exists():
                assert hashlib.sha256(duplicate.read_bytes()).hexdigest()==digest,('Different radial part must not be aliased',duplicate)
                duplicate.unlink()
            shared.append(dict(previous_path=str(duplicate.relative_to(root)),served_path=str(common.relative_to(root)),sha256=digest))
    report=dict(passed=True,compression='Lossless gzip; decoded bytes retain original hashes',meshes=rows,shared_radial_prints=shared)
    (root/'downloads/asset-compression-validation.json').write_text(json.dumps(report,indent=2))
    size=sum(p.stat().st_size for p in root.rglob('*') if p.is_file());assert size<255*1024*1024,size
    print('Static assets:',round(size/1048576,2),'MiB; geometry and prints preserved')
if __name__=='__main__':main()
