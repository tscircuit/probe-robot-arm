"""Verify delivered replacements, shared mesh identity and all local download links."""
import gzip,hashlib,json,re,zipfile
from .model import ROOT,OUT

def main():
    web=ROOT/'site/dist';dest=web/'downloads/hollow-base';manifest=json.loads((OUT/'print-manifest.json').read_text())
    with zipfile.ZipFile(dest/'structure-print-kit.zip') as z:
        assert z.testzip() is None
        for row in manifest:
            direct=(dest/row['file']).read_bytes();assert direct==(OUT/row['file']).read_bytes()==z.read(row['file'])
            assert hashlib.sha256(direct).hexdigest()==row['sha256']
    with zipfile.ZipFile(dest/'structure-step.zip') as z:assert z.testzip() is None and z.read('backbone-structure.step')==(OUT/'backbone-structure.step').read_bytes()
    shared=json.loads((dest/'shared-assets.json').read_text());assert hashlib.sha256(gzip.decompress((web/shared['base_mesh']).read_bytes())).hexdigest()==shared['uncompressed_sha256']
    assert hashlib.sha256(gzip.decompress((dest/'delta.json.gz').read_bytes())).hexdigest()==shared['delta_sha256']
    urls=re.findall(r'href="(downloads/[^"]+)"',(web/'hollow-base.html').read_text())
    for url in urls:assert (web/url).is_file(),url
    for page in ['index.html','base-test.html','rigid-base.html','hollow-base.html']:assert 'href="hollow-base.html"' in (web/page).read_text(),page
    report=dict(passed=True,checked_prints=[r['name'] for r in manifest],verified_local_downloads=urls,shared_assets=shared,viewer_check=json.loads((OUT/'viewer-validation.json').read_text()))
    (OUT/'package-validation.json').write_text(json.dumps(report,indent=2));print('Archive bytes, shared mesh hashes, print downloads and four-page navigation passed')
if __name__=='__main__':main()
