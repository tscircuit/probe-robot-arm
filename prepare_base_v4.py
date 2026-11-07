"""Package the checked 12T standalone fixture, including an offline viewer."""
import csv,datetime,hashlib,json,pathlib,shutil,sys,zipfile
import markdown
root=pathlib.Path(__file__).resolve().parent;out=root/'output/armature-base-test-v4';src=root/'base_test_kit_v4'
if '--publish-assets' not in sys.argv:
 for n in ['LICENSE_compliant-spur-gear.txt']:
  shutil.copyfile(root/'upstream/compliant-spur-gear/LICENSE',out/n)
 shutil.copyfile(src/'HARDWARE_LIST.csv',out/'HARDWARE_LIST.csv')
 shutil.copyfile(src/'PRINT_AND_ASSEMBLY.md',out/'PRINT_AND_ASSEMBLY.md')
 shutil.copyfile(root/'output/base-drive-validation.json',out/'base-drive-validation.json')
 report=json.loads((root/'output/validation.json').read_text())
 assert report['geometry_checks_passed'] and report['layout']['base_gear_ratio']==6
 (out/'gear_mesh_validation.json').write_text(json.dumps(dict(passed=True,samples=report['nominal_base_mesh'],scope='Same gear geometry as full arm; one complete tooth engagement without intentional elastic preload'),indent=2))
 manifest=json.loads((out/'print_manifest.json').read_text())
 with (out/'PRINT_LIST.csv').open('w') as f:
  w=csv.writer(f);w.writerow(['File','Quantity','X mm','Y mm','Z mm']);w.writerows([[p['file'],p['quantity'],*p['size_mm']] for p in manifest])
 header=(src/'guide_header.html').read_text()
 (out/'START_HERE.html').write_text(header+markdown.markdown((out/'PRINT_AND_ASSEMBLY.md').read_text(),extensions=['tables','fenced_code'])+'</main></html>')
 (out/'source').mkdir(exist_ok=True)
 for p in src.rglob('*'):
  if p.is_file() and not any(x in p.parts for x in ['__pycache__','cache']):
   target=out/'source'/p.relative_to(src);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
 shutil.copytree(root/'rotary_base',out/'source/rotary_base',dirs_exist_ok=True,ignore=shutil.ignore_patterns('cache','__pycache__'))
 (out/'BUILD_INFO.json').write_text(json.dumps(dict(kit='Armature base standalone test',revision='4.7-roller-track-fit',roller_track_overlap_mm=.4,changed_prints_from_v4_6=['01 module base: roller blocks moved 0.4 mm toward track'],changed_prints_from_v4_5=['01 module base: roller blocks moved 0.4 mm toward track','10 rotating deck with five rounded windows'],changed_prints_from_v4_4=['01 base with five rounded cutouts','10 rotating deck with five rounded windows'],spindle_diameter_mm=15.25,spindle_top_chamfer_mm=.5,spacer_bore_mm=15.8,nominal_bearing_bore_mm=15,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),main_stl_designs=10,main_print_quantity=10,bearing='2 x 6002, 15 x 32 x 9 mm; 4 x 625ZZ, 5 x 16 x 5 mm',pinion_teeth=12,ring_teeth=72,ratio=6,motor_offset_mm=60,changed_prints_from_v3=['01 flat base with four single 45-degree axle blocks','10 shared structural deck with Z mounts','11 ring: larger outer radius and continuous 45-degree track'],shared_base_source='rotary_base/core.py',removed_prints=['04 NEMA17 mount'],rotor_drop_mm=4,base_plate_thickness_mm=11,changed_prints_from_v4_1=['01 flat module base with four integral axles','05 spindle 15.25 mm with 0.5 mm top chamfer','10 rotating deck with five rounded windows','11 outer-track ring'],changed_prints_from_v4_2=['01 base: four integral 45-degree axles','05 spindle 15.25 mm with 0.5 mm top chamfer','10 rotating deck with five rounded windows','11 ring: 176 mm OD, 45-degree track, straight bolt holes'],roller_count=4,roller_tilt_deg=45,roller_axle_diameter_mm=5.1,roller_fasteners=0,physical_testing='Roller-supported v4 untested; bearing fit, support adjustment, stiffness and track wear require physical testing'),indent=2))
 print('Prepared v4 guide and source')
else:
 for n in ['validation.json','static_precision_validation.json','explosion_validation.json','mesh_validation.json','spindle_print_validation.json','revision_validation.json','roller_print_validation.json','base-cutouts-validation.json','deck-cutouts-validation.json','flat-base-validation.json']:
  assert json.loads((out/n).read_text())['passed'],n
 for n,digest in json.loads((out/'explosion_validation.json').read_text())['source_sha256'].items():
  assert hashlib.sha256((src/n).read_bytes()).hexdigest()==digest,n
 for n,digest in json.loads((out/'revision_validation.json').read_text())['source_sha256'].items():
  assert hashlib.sha256((src/n).read_bytes()).hexdigest()==digest,n
 assert json.loads((out/'viewer_validation.json').read_text())['passed']
 for n,digest in json.loads((out/'base-cutouts-validation.json').read_text())['source_sha256'].items():
  assert hashlib.sha256((root/n).read_bytes()).hexdigest()==digest,n
 for n,digest in json.loads((out/'deck-cutouts-validation.json').read_text())['source_sha256'].items():
  assert hashlib.sha256((root/n).read_bytes()).hexdigest()==digest,n
 flat=json.loads((out/'flat-base-validation.json').read_text())
 for n,digest in flat['source_sha256'].items():assert hashlib.sha256((root/n).read_bytes()).hexdigest()==digest,n
 for row in flat['files']:assert hashlib.sha256((root/row['file']).read_bytes()).hexdigest()==row['sha256']
 files=sorted(p for p in out.rglob('*') if p.is_file() and p.name not in ['preview_mesh.json','SHA256SUMS.txt'])
 (out/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(out))+'\n' for p in files));files.append(out/'SHA256SUMS.txt')
 archive=root/'output/armature-base-test-v4.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in files:z.write(p,str(pathlib.Path(out.name)/p.relative_to(out)))
 with zipfile.ZipFile(archive) as z:assert z.testzip() is None
 dest=root/'site/dist/downloads/base-v4';dest.mkdir(exist_ok=True)
 (dest/'STL').mkdir(exist_ok=True)
 for stale in (dest/'STL').glob('*.stl'):
  if not (out/'STL'/stale.name).exists():stale.unlink()
 shutil.copytree(out/'STL',dest/'STL',dirs_exist_ok=True)
 for n in ['PRINT_AND_ASSEMBLY.pdf','validation.json','explosion_validation.json','static_precision_validation.json','mesh_validation.json','viewer_validation.json','base-drive-validation.json','spindle_print_validation.json','revision_validation.json','roller_print_validation.json','base-cutouts-validation.json','deck-cutouts-validation.json','flat-base-validation.json']:
  shutil.copyfile(out/n,dest/n)
 shutil.copyfile(out/'VIEWER.html',root/'site/dist/base-test.html')
 shutil.copyfile(archive,root/'site/dist/downloads'/archive.name)
 assert all(p.stat().st_size<24*1024*1024 for p in (root/'site/dist').rglob('*') if p.is_file())
 print('Packaged',archive.name,archive.stat().st_size,'bytes')
