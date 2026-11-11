"""Package the cage variant, reusing byte-identical print files from Rigid base."""
import gzip,hashlib,json,shutil,zipfile
from .model import ROOT

def main():
    out=ROOT/'output/rigid-base2';dest=ROOT/'site/dist/downloads/rigid-base2';dest.mkdir(parents=True,exist_ok=True)
    reports=['validation.json','print-validation.json','explosion-validation.json','cage-validation.json','analysis-validation.json']
    for name in reports:
        report=json.loads((out/name).read_text());assert report['passed'],name
        for src,digest in report['source_sha256'].items():assert hashlib.sha256((ROOT/src).read_bytes()).hexdigest()==digest,('stale',name,src)
    parent={r['name']:r for r in json.loads((ROOT/'output/rigid-base/print-manifest.json').read_text())};manifest=json.loads((out/'print-manifest.json').read_text());urls={}
    for row in manifest:
        data=(out/row['file']).read_bytes();assert hashlib.sha256(data).hexdigest()==row['sha256']
        if row['name'] in parent and parent[row['name']]['sha256']==row['sha256']:
            urls[row['name']]='downloads/rigid-base/'+row['file']+'.gz'
        else:
            path=dest/(row['file']+'.gz');path.parent.mkdir(exist_ok=True);path.write_bytes(gzip.compress(data,compresslevel=9,mtime=0));urls[row['name']]='downloads/rigid-base2/'+row['file']+'.gz'
        packed=ROOT/'site/dist'/urls[row['name']];assert gzip.decompress(packed.read_bytes())==data
    mesh=(out/'mesh.json').read_bytes();(dest/'mesh.json.gz').write_bytes(gzip.compress(mesh,compresslevel=9,mtime=0))
    config=json.loads((out/'config.json').read_text())|dict(variant='Rigid Base 2',print_urls=urls)
    (dest/'config.json').write_text(json.dumps(config,indent=2))
    for name in ['explosion.json','print-manifest.json']+reports:shutil.copyfile(out/name,dest/name)
    (dest/'analysis').mkdir(exist_ok=True)
    for name in ['report.html','comparison.png','displacement.png']:shutil.copyfile(out/'analysis'/name,dest/'analysis'/name)
    with zipfile.ZipFile(dest/'print-kit.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for r in manifest:z.write(out/r['file'],r['file'])
        z.write(ROOT/'rigid_base2/README.md','README.md');z.write(ROOT/'rigid_base/parameters.json','parameters.json')
        for name in ['print-manifest.json']+reports:z.write(out/name,name)
        for name in ['report.html','comparison.png','displacement.png']:z.write(out/'analysis'/name,'analysis/'+name)
    with zipfile.ZipFile(dest/'rigid-arm-step.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.write(out/'rigid-arm.step','rigid-arm.step');z.write(ROOT/'rigid_base2/README.md','README.md')
    web=ROOT/'site/dist';shutil.copyfile(ROOT/'rigid_base2/viewer.html',web/'rigid-base2.html');shutil.copyfile(ROOT/'rigid_base/viewer.css',web/'rigid-base2.css')
    js=(ROOT/'rigid_base/viewer.js').read_text().replace("'downloads/rigid-base/", "'downloads/rigid-base2/")
    js=js.replace("m.userData.printed?'downloads/rigid-base2/STL/'+m.name+'.stl.gz':undefined", "m.userData.printed?cfg.print_urls[m.name]:undefined")
    (web/'rigid-base2.js').write_text(js)
    for n in ['index.html','base-test.html','variants/z-1x/index.html','variants/z-2x/index.html']:
        path=web/n
        if not path.exists():continue
        s=path.read_text()
        if 'rigid-base2.html' not in s:
            # Existing page navigation uses top-level links, including on width pages.
            marker='<a href="rigid-base.html">Rigid base</a>'
            if marker in s:s=s.replace(marker,marker+'<a href="rigid-base2.html">Rigid Base 2</a>')
            else:
                import re
                s=re.sub(r'(<a[^>]+href="[^\"]*rigid-base.html"[^>]*>.*?</a>)',r'\1<a href="rigid-base2.html">Rigid Base 2</a>',s,count=1)
            path.write_text(s)
    size=sum(p.stat().st_size for p in web.rglob('*') if p.is_file());assert size<255*1024*1024,size
    for file in dest.rglob('*'):
        if file.is_file():assert file.stat().st_size<24*1024*1024,file
    with zipfile.ZipFile(dest/'print-kit.zip') as z:
        assert z.testzip() is None
        for r in manifest:assert z.read(r['file'])==(out/r['file']).read_bytes()
    with zipfile.ZipFile(dest/'rigid-arm-step.zip') as z:assert z.read('rigid-arm.step')==(out/'rigid-arm.step').read_bytes()
    (out/'package-validation.json').write_text(json.dumps(dict(passed=True,prints=len(manifest),shared_print_files=sum('/rigid-base/' in u for u in urls.values()),site_size_mib=size/1048576),indent=2))
    print('Cage package and exact download bytes passed; total site',round(size/1048576,2),'MiB')
if __name__=='__main__':main()
