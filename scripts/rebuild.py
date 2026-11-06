"""Rebuild CAD and checks, optionally the complete static viewer and print ZIP."""
import argparse,json,pathlib,shutil,subprocess,sys
root=pathlib.Path(__file__).resolve().parent.parent
ap=argparse.ArgumentParser();ap.add_argument('--site',action='store_true',help='Also build the local site, PDF guide and run browser checks (Node + Chromium required)');args=ap.parse_args()
(root/'output').mkdir(exist_ok=True)
def run(*args,report=None):
 print('+',' '.join(str(a) for a in args),flush=True)
 if report:
  with (root/report).open('w') as f:subprocess.run(args,cwd=root,stdout=f,check=True)
 else:subprocess.run(args,cwd=root,check=True)
def py(script,*args):run(sys.executable,script,*args)
py('model.py','--check')
py('base_test_kit_v4/build.py')
for script in ['check_arm_explosion.py','check_z_mount.py','check_base_drive.py','check_base_sync.py','check_platform.py','base_test_kit_v4/check_explosion.py','base_test_kit_v4/check_static_precision.py','base_test_kit_v4/check_revision.py']:
 py(script)
py('base_test_kit_v4/verify_prints.py','output/armature-base-test-v4')
py('base_test_kit_v4/check_spindle_print.py')
py('base_test_kit_v4/check_roller_print.py')
bench=root/'output/armature-base-test-v4'
refs={p['name']:p for p in json.loads((bench/'preview_mesh.json').read_text())}
for p in json.loads((root/'output/arm-mesh.json').read_text()):
 if p.get('base_name') and p['printed']:
  shutil.copyfile(bench/refs[p['base_name']]['printFile'],root/'output/prototype-parts'/(p['name']+'.stl'))
py('check_flat_base.py');py('verify_main_prints.py')
if args.site:
 run(str(root/'.qa/node_modules/.bin/esbuild'),'base_test_kit_v4/viewer.js','--bundle','--format=iife','--minify','--alias:three=./base_test_kit_v4/vendor/three.module.js','--outfile=base_test_kit_v4/viewer.bundle.js')
 py('prepare_base_v4.py')
 py('base_test_kit_v4/make_viewer.py',str(bench));py('base_test_kit_v4/render.py',str(bench))
 run('node','base_test_kit_v4/print_guide.mjs')
 run('node','test_base_v4_viewer.mjs')
 py('prepare_site.py')
 shutil.copyfile(root/'output/flat-base-validation.json',bench/'flat-base-validation.json')
 py('prepare_base_v4.py','--publish-assets')
 run('node','test_viewer.mjs',report='output/current-viewer-validation.json')
 run('node','test_part_downloads.mjs');run('node','test_hidden_edges.mjs');run('node','test_mouse_controls.mjs')
 print('Local site ready: python -m http.server 8000 --directory site/dist')
else:print('CAD and checks complete. Use --site to build and test the local website.')
