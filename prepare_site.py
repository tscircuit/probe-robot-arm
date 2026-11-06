"""Package generated, checked CAD and pinned viewer libraries for static hosting."""
import pathlib,shutil,json,urllib.request,zipfile,os
root=pathlib.Path(__file__).resolve().parent
report_path=root/'output/validation.json'
report=json.loads(report_path.read_text())
assert report.get('geometry_checks_passed'), 'CAD checks must pass before packaging'
assert report_path.stat().st_mtime >= (root/'model.py').stat().st_mtime, 'Regenerate checks for the current source'
platform_report=json.loads((root/'output/platform-validation.json').read_text())
assert platform_report['passed'], 'Parked platform checks must pass'
for stem in ['single-arm','four-arm-platform']:
 assert (root/'output'/(stem+'.step')).stat().st_mtime >= (root/'parameters.json').stat().st_mtime, 'Regenerate CAD for these parameters'
dist=root/'site/dist';(dist/'vendor').mkdir(parents=True,exist_ok=True)
base='https://cdn.jsdelivr.net/npm/three@0.180.0/'
for name,url in [('three.module.js','build/three.module.js'),('three.core.js','build/three.core.js'),('OrbitControls.js','examples/jsm/controls/OrbitControls.js'),('LICENSE','LICENSE')]:
 p=dist/'vendor'/name
 if not p.exists():
  with urllib.request.urlopen(base+url) as r:p.write_bytes(r.read())
explosion_report=json.loads((root/'output/arm-explosion-validation.json').read_text())
assert explosion_report['passed'], 'Module explosion checks must pass'
import hashlib
for name,digest in explosion_report['source_sha256'].items():
 assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest, 'Stale explosion check: '+name
mount_report=json.loads((root/'output/z-mount-validation.json').read_text())
assert mount_report['passed'], 'Z mount checks must pass'
for name,digest in mount_report['source_sha256'].items():
 assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest, 'Stale Z mount check: '+name
drive_report=json.loads((root/'output/base-drive-validation.json').read_text())
assert drive_report['passed']
for name,digest in drive_report['source_sha256'].items():
 assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest, 'Stale base drive check: '+name
for name in ['arm-mesh.json','platform-mesh.json','parameters-resolved.json','arm-explosion-path.json']:shutil.copyfile(root/'output'/name,dist/name)
download=dist/'downloads';download.mkdir(exist_ok=True)
part_downloads=download/'parts';part_downloads.mkdir(exist_ok=True)
main_parts=json.loads((root/'output/arm-mesh.json').read_text())
# Publish one canonical print export for each shared component on both pages.
bench_root=root/'output/armature-base-test-v4'
bench_parts={p['name']:p for p in json.loads((bench_root/'preview_mesh.json').read_text())}
bench_manifest={p['file']:p for p in json.loads((bench_root/'print_manifest.json').read_text())}
shared_exports=[]
for p in main_parts:
 if p.get('base_name') and p['printed']:
  file=bench_parts[p['base_name']]['printFile'];source=bench_root/file
  digest=hashlib.sha256(source.read_bytes()).hexdigest();assert digest==bench_manifest[file]['sha256']
  shutil.copyfile(source,root/'output/prototype-parts'/(p['name']+'.stl'))
  shared_exports.append(dict(main_part=p['name'],base_file=file,sha256=digest))
(root/'output/shared-print-exports.json').write_text(json.dumps(dict(passed=True,files=shared_exports),indent=2))
flat=json.loads((root/'output/flat-base-validation.json').read_text());assert flat['passed']
for name,digest in flat['source_sha256'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
for row in flat['files']:assert hashlib.sha256((root/row['file']).read_bytes()).hexdigest()==row['sha256']
current_prints={p['name']+'.stl' for p in main_parts if p['printed']}
for p in (root/'output/prototype-parts').glob('*.stl'):
 if p.name not in current_prints:p.unlink()
assert current_prints=={p.name for p in (root/'output/prototype-parts').glob('*.stl')}
for p in part_downloads.glob('*.stl'):
 if p.name not in current_prints:p.unlink()
for p in (root/'output/prototype-parts').glob('*.stl'):shutil.copyfile(p,part_downloads/p.name)
shutil.copyfile(root/'viewer_part_downloads.js',dist/'part-downloads.js')
for stem in ['single-arm','four-arm-platform']:
 with zipfile.ZipFile(download/(stem+'.zip'),'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  z.write(root/'output'/(stem+'.step'),stem+'.step')
  z.write(root/'README.md','README.md')
with zipfile.ZipFile(download/'source.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for name in ['model.py','check_platform.py','arm_explosion.py','check_arm_explosion.py','check_z_mount.py','check_base_drive.py','check_base_sync.py','check_flat_base.py','parameters.json','requirements.txt','requirements-dev.txt','README.md','THIRD_PARTY_NOTICES.md','prepare_site.py','prepare_base_v4.py','verify_main_prints.py','viewer_part_downloads.js','test_viewer.mjs','test_base_v4_viewer.mjs','test_part_downloads.mjs','test_hidden_edges.mjs','test_mouse_controls.mjs']:
  z.write(root/name,name)
 for name in ['.qa/package.json','.qa/package-lock.json','site/dist/index.html','site/dist/app.js','site/dist/style.css','site/dist/part-downloads.js']:z.write(root/name,name)
 for directory in ['upstream','rotary_base','base_test_kit_v4','scripts','site/dist/vendor','output/prototype-parts']:
  for p in (root/directory).rglob('*'):
   if any(x in p.parts for x in ['cache','__pycache__']) or p.name=='viewer.bundle.js':continue
   if p.is_symlink():
    info=zipfile.ZipInfo(str(p.relative_to(root)));info.create_system=3;info.external_attr=0o120777<<16;z.writestr(info,os.readlink(p))
   elif p.is_file():z.write(p,str(p.relative_to(root)))
 z.write(root/'output/validation.json','validation.json')
 z.write(root/'output/platform-validation.json','platform-validation.json')
 z.write(root/'output/arm-explosion-validation.json','arm-explosion-validation.json')
 z.write(root/'output/arm-explosion-path.json','arm-explosion-path.json')
 z.write(root/'output/z-mount-validation.json','z-mount-validation.json')
 z.write(root/'output/base-drive-validation.json','base-drive-validation.json')
shutil.copyfile(root/'output/validation.json',download/'validation.json')
shutil.copyfile(root/'output/platform-validation.json',download/'platform-validation.json')
shutil.copyfile(root/'output/arm-explosion-validation.json',download/'arm-explosion-validation.json')
shutil.copyfile(root/'output/z-mount-validation.json',download/'z-mount-validation.json')
shutil.copyfile(root/'output/base-drive-validation.json',download/'base-drive-validation.json')
bench=json.loads((root/'output/armature-base-test-v4/explosion_validation.json').read_text());assert bench['passed']
for name,digest in bench['source_sha256'].items():assert hashlib.sha256((root/'base_test_kit_v4'/name).read_bytes()).hexdigest()==digest,'Stale shared base: '+name
sync=json.loads((root/'output/base-sync-validation.json').read_text());assert sync['passed']
for name,digest in sync['source_sha256'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
shutil.copyfile(root/'output/base-sync-validation.json',download/'base-sync-validation.json')
shutil.copyfile(root/'output/flat-base-validation.json',download/'flat-base-validation.json')
for p in dist.rglob('*'):
 if p.is_file() and p.stat().st_size>24*1024*1024:raise ValueError(f'Asset exceeds hosting limit: {p}')
print('Packaged:',{p.name:p.stat().st_size for p in download.iterdir()})
