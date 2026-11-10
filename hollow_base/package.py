"""Small independent variant payload; shared geometry is addressed by name and hash."""
import gzip,hashlib,json,pathlib,shutil,zipfile
from .model import ROOT,OUT

def main():
    dest=ROOT/'site/dist/downloads/hollow-base';dest.mkdir(parents=True,exist_ok=True)
    for name in ['validation.json','explosion-validation.json']:
        report=json.loads((OUT/name).read_text());assert report['passed'],name
        for src,h in report['source_sha256'].items():assert hashlib.sha256((ROOT/src).read_bytes()).hexdigest()==h,('Stale',src)
    for row in json.loads((OUT/'print-manifest.json').read_text()):assert hashlib.sha256((OUT/row['file']).read_bytes()).hexdigest()==row['sha256']
    shutil.copytree(OUT/'STL',dest/'STL',dirs_exist_ok=True)
    for name in ['validation.json','explosion-validation.json','explosion.json','config.json','print-manifest.json']:shutil.copyfile(OUT/name,dest/name)
    data=(OUT/'delta.json').read_bytes();(dest/'delta.json.gz').write_bytes(gzip.compress(data,compresslevel=9,mtime=0))
    parent=ROOT/'site/dist/downloads/rigid-base/mesh.json.gz'
    assert gzip.decompress(parent.read_bytes())==(ROOT/'output/rigid-base/mesh.json').read_bytes(),'Shared mesh differs from the validated rigid-base export'
    (dest/'shared-assets.json').write_text(json.dumps(dict(base_mesh='downloads/rigid-base/mesh.json.gz',uncompressed_sha256=hashlib.sha256(gzip.decompress(parent.read_bytes())).hexdigest(),delta_sha256=hashlib.sha256(data).hexdigest()),indent=2))
    with zipfile.ZipFile(dest/'structure-print-kit.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted((OUT/'STL').glob('*.stl')):z.write(p,'STL/'+p.name)
        for name in ['validation.json','explosion-validation.json','print-manifest.json']:z.write(OUT/name,name)
        z.write(ROOT/'hollow_base/README.md','README.md');z.write(ROOT/'hollow_base/model.py','source/model.py')
    with zipfile.ZipFile(dest/'structure-step.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.write(OUT/'backbone-structure.step','backbone-structure.step');z.write(ROOT/'hollow_base/README.md','README.md')
    shutil.copyfile(ROOT/'hollow_base/viewer.html',ROOT/'site/dist/hollow-base.html')
    for src,target in [('viewer.js','rigid-base.js'),('viewer.html','rigid-base.html')]:shutil.copyfile(ROOT/'rigid_base'/src,ROOT/'site/dist'/target)
    # Add the comparison page to every existing top-level navigation.
    for path in (ROOT/'site/dist').glob('*.html'):
        s=path.read_text()
        if 'class="page-nav"' in s and 'href="hollow-base.html"' not in s:
            start=s.index('class="page-nav"');end=s.index('</nav>',start)
            path.write_text(s[:end]+'<a href="hollow-base.html">Hollow backbone</a>'+s[end:])
    total=sum(p.stat().st_size for p in (ROOT/'site/dist').rglob('*') if p.is_file());assert total<256*1024*1024,total
    print('Published payload prepared; site MiB',round(total/1048576,2))
if __name__=='__main__':main()
