"""Package validated outputs and synchronize the static viewer assets."""
import hashlib,json,pathlib,shutil,zipfile
from .model import ROOT

def main():
    out=ROOT/'output/rigid-base';dest=ROOT/'site/dist/downloads/rigid-base';dest.mkdir(parents=True,exist_ok=True)
    reports=['validation.json','print-validation.json','explosion-validation.json','brace-validation.json','front-brace-validation.json']
    for name in reports:
        report=json.loads((out/name).read_text());assert report['passed'],name
        for src,digest in report['source_sha256'].items():assert hashlib.sha256((ROOT/src).read_bytes()).hexdigest()==digest,('stale check',name,src)
    for row in json.loads((out/'print-manifest.json').read_text()):assert hashlib.sha256((out/row['file']).read_bytes()).hexdigest()==row['sha256'],row['name']
    for row in json.loads((out/'print-validation.json').read_text())['prints']:assert hashlib.sha256((out/'STL'/(row['part']+'.stl')).read_bytes()).hexdigest()==row['sha256'],row['part']
    current={row['name']+'.stl' for row in json.loads((out/'print-manifest.json').read_text())}
    for directory in [out/'STL',dest/'STL']:
        for path in directory.glob('*.stl'):
            if path.name not in current:path.unlink()
    shutil.copytree(out/'STL',dest/'STL',dirs_exist_ok=True)
    for name in ['mesh.json','explosion.json','config.json','print-manifest.json']+reports:shutil.copyfile(out/name,dest/name)
    for name in ['README.md','parameters.json']:shutil.copyfile(ROOT/'rigid_base'/name,out/name)
    with zipfile.ZipFile(dest/'print-kit.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for path in sorted((out/'STL').glob('*.stl')):z.write(path,'STL/'+path.name)
        for name in ['README.md','parameters.json','print-manifest.json']+reports:z.write(out/name,name)
    with zipfile.ZipFile(dest/'rigid-arm-step.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.write(out/'rigid-arm.step','rigid-arm.step');z.write(out/'README.md','README.md')
    for name,ext in [('viewer.html','html'),('viewer.js','js'),('viewer.css','css')]:shutil.copyfile(ROOT/'rigid_base'/name,ROOT/f'site/dist/rigid-base.{ext}')
    assert max(p.stat().st_size for p in dest.rglob('*') if p.is_file())<24*1024*1024
    from compress_site_assets import main as compress_assets
    compress_assets()
    print('Packaged checked variant:',dest)
if __name__=='__main__':main()
