"""Write a self-contained HTML viewer from exported CAD and the checked path."""
import argparse,ast,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('directory');args=ap.parse_args();out=pathlib.Path(args.directory)
parts=json.loads((out/'preview_mesh.json').read_text());stages=json.loads((out/'explosion_path.json').read_text())
assert sum(bool(p.get('printFile')) for p in parts)==10
html=(ROOT/'viewer_template.html').read_text().replace('__DATA__',json.dumps(dict(parts=parts,stages=stages),separators=(',',':'))).replace('__BUNDLE__',(ROOT/'viewer.bundle.js').read_text())
(out/'VIEWER.html').write_text(html);print('Standalone viewer:',len(html),'bytes')
