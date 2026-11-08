"""Publish checked, real-width CAD bundles for the viewer's Z width selector."""
import hashlib,json,pathlib,shutil,subprocess,sys,zipfile
root=pathlib.Path(__file__).resolve().parent
dist=root/'site/dist'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def checked(out,name,key='passed'):
 p=out/name;r=json.loads(p.read_text());assert r[key],name
 assert p.stat().st_mtime>=max((root/'model.py').stat().st_mtime,(root/'leadscrew_actuator.py').stat().st_mtime,(root/'direct_mount.py').stat().st_mtime),('Stale CAD report',p)
 for n,h in r.get('source_sha256',{}).items():assert digest(root/n)==h,('stale',n)
 return r
bench=root/'output/armature-base-test-v4'
bench_parts={p['name']:p for p in json.loads((bench/'preview_mesh.json').read_text())}
bench_manifest={p['file']:p for p in json.loads((bench/'print_manifest.json').read_text())}
rows=[]
for width in [1,2,4]:
 if width!=4:assert json.loads((root/f'configs/z-{width}x.json').read_text())==json.loads((root/'parameters.json').read_text())|{'z_width':width},'Width configs must stay synchronized'
 out=root/'output' if width==4 else root/f'output/widths/z-{width}x'
 assets=dist if width==4 else dist/f'variants/z-{width}x'
 downloads=dist/'downloads' if width==4 else dist/f'downloads/widths/z-{width}x'
 assets.mkdir(parents=True,exist_ok=True);(downloads/'parts').mkdir(parents=True,exist_ok=True)
 checked(out,'validation.json','geometry_checks_passed');checked(out,'platform-validation.json')
 for name in ['arm-explosion-validation.json','z-mount-validation.json']:
  assert checked(out,name)['z_width']==width
 config=json.loads((out/'parameters-resolved.json').read_text());assert config['z_width']==width and not config['radial_inverted']
 assert (out/'validation.json').stat().st_mtime>=(root/'model.py').stat().st_mtime
 for name in ['arm-mesh.json','platform-mesh.json','parameters-resolved.json','arm-explosion-path.json']:
  shutil.copyfile(out/name,assets/name)
 parts=json.loads((out/'arm-mesh.json').read_text());names={p['name']+'.stl' for p in parts if p['printed']}
 for p in parts:
  if p.get('base_name') and p['printed']:
   file=bench_parts[p['base_name']]['printFile'];assert digest(bench/file)==bench_manifest[file]['sha256']
   shutil.copyfile(bench/file,out/'prototype-parts'/(p['name']+'.stl'))
 for directory in [out/'prototype-parts',downloads/'parts']:
  for p in directory.glob('*.stl'):
   if p.name not in names:p.unlink()
 previous=json.loads((out/'print-mesh-validation.json').read_text()) if (out/'print-mesh-validation.json').exists() else {}
 fresh=previous.get('passed') and {r['part']+'.stl' for r in previous['files']}==names and all(digest(out/'prototype-parts'/(r['part']+'.stl'))==r['sha256'] for r in previous['files'])
 if not fresh:subprocess.run([sys.executable,str(root/'verify_main_prints.py'),'--out',str(out)],check=True)
 for name in names:shutil.copyfile(out/'prototype-parts'/name,downloads/'parts'/name)
 for name in ['validation.json','platform-validation.json','arm-explosion-validation.json','z-mount-validation.json','mounting-patterns.json','print-mesh-validation.json']:
  shutil.copyfile(out/name,downloads/name)
 for stem in ['single-arm','four-arm-platform']:
  assert (out/(stem+'.step')).stat().st_mtime>=(root/'model.py').stat().st_mtime
  with zipfile.ZipFile(downloads/(stem+'.zip'),'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
   z.write(out/(stem+'.step'),stem+'.step');z.write(root/'README.md','README.md');z.write(out/'parameters-resolved.json','parameters-resolved.json')
 with zipfile.ZipFile(downloads/'actuator-mounts.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name in ['Z_support','R_Structural_mounting_lid','Z_Hollow_triangular_carriage','Triangular_probe_outrigger']:z.write(out/'prototype-parts'/(name+'.stl'),name+'.stl')
  z.write(out/'mounting-patterns.json','mounting-patterns.json');z.write(root/'README.md','README.md')
 rows.append(dict(width=width,passed=True,parts=len(parts),print_count=len(names),asset_path=str(assets.relative_to(dist)),download_path=str(downloads.relative_to(dist)),files={name:digest(out/name) for name in ['validation.json','arm-mesh.json','arm-explosion-validation.json','z-mount-validation.json','platform-validation.json','print-mesh-validation.json']}))
report=dict(passed=True,variants=rows)
(root/'output/width-variants-validation.json').write_text(json.dumps(report,indent=2));(dist/'downloads/width-variants-validation.json').write_text(json.dumps(report,indent=2))
# Include alternative configurations' validation evidence in the source archive.
with zipfile.ZipFile(dist/'downloads/source.zip','a',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 assert 'width-variants-validation.json' not in z.namelist(),'Run prepare_site.py before repackaging widths'
 z.write(root/'output/width-variants-validation.json','width-variants-validation.json')
 for width in [1,2]:
  for name in ['validation.json','arm-explosion-validation.json','z-mount-validation.json','platform-validation.json','print-mesh-validation.json']:
   z.write(root/f'output/widths/z-{width}x'/name,f'widths/z-{width}x/{name}')
for p in dist.rglob('*'):
 if p.is_file():assert p.stat().st_size<=24*1024*1024,('Hosting asset too large',p)
print('Published checked widths:',[r['width'] for r in rows])
