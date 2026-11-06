"""Strict assembled-pose audit with the same explicit contact exceptions."""
import itertools,json,pathlib
from build import build,overlap,spindle_fit_checks
from check_explosion import exceptions
ROOT=pathlib.Path(__file__).resolve().parent
p=json.loads((ROOT/'parameters.json').read_text());parts,_=build(p);allowed=exceptions(parts)
checks=0;max_overlap=0.;worst=None;fail=[]
for a,b in itertools.combinations(parts,2):
    if frozenset([a['name'],b['name']]) in allowed:continue
    v=overlap(a['shape'],b['shape']);checks+=1
    if v>max_overlap:max_overlap=v;worst=[a['name'],b['name']]
    if v>1e-6:fail.append(dict(a=a['name'],b=b['name'],overlap_mm3=v))
r=dict(passed=not fail,spindle_print_fit=spindle_fit_checks(parts,p),checked_pairs=checks,maximum_unintended_overlap_mm3=max_overlap,worst_pair=worst,volume_tolerance_mm3=1e-6,failures=fail,exceptions='Same named contact exceptions as explosion_validation.json')
out=ROOT.parent/'output/armature-base-test-v4';(out/'static_precision_validation.json').write_text(json.dumps(r,indent=2));print(r);assert r['passed']
