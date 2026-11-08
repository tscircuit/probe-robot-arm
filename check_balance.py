"""Compare mass-weighted upper-stage balance using explicit, adjustable assumptions.
This is not a measured centre of gravity. CAD mass properties include no wiring,
infill toolpaths, or selected probe/motor datasheets.
"""
import hashlib,itertools,json,pathlib
from model import build,layout
root=pathlib.Path(__file__).resolve().parent
p=json.loads((root/'parameters.json').read_text())
def measure(config):
 lay=layout(config);parts,_=build(config,lay);rows=[]
 for a in parts:
  if a['group'] not in ['z_rack','r_rack','r_drive'] or a.get('keepout'):continue
  s=a['shape'];rows.append(dict(name=a['name'],group=a['group'],printed=a['printed'],volume_mm3=s.Volume(),center_x_mm=s.Center().x))
 return rows,lay
before,old=measure(p|{'radial_setback_mm':0,'z_origin':None})
after,new=measure(p.copy())
def result(rows,motor,plastic,travel):
 mass=moment=0
 for a in rows:
  g=motor if a['name']=='R_NEMA14_full-depth_reference' else a['volume_mm3']*(plastic if a['printed'] else 7.85)/1000
  x=a['center_x_mm']+(travel if a['group']=='r_rack' else 0)
  mass+=g;moment+=g*x
 return dict(mass_g=mass,com_x_mm=moment/mass,gravity_moment_nm=moment*9.80665e-6)
assert p['radial_setback_mm']>0
assert abs(new['h_origin']-(p['radial_motor_depth']/2-p['radial_setback_mm']))<1e-6
assert abs(new['h_origin']+new['r_actuator']['end']-(old['h_origin']+old['r_actuator']['end']))<1e-6
assert new['radial_stroke']==old['radial_stroke']==120
rows=[]
for motor,plastic,travel in itertools.product([140,180,250],[.2,.45,.65],[-60,0,60]):
 a=result(before,motor,plastic,travel);b=result(after,motor,plastic,travel)
 assert abs(b['gravity_moment_nm'])<abs(a['gravity_moment_nm']),(motor,plastic,travel,a,b)
 rows.append(dict(motor_mass_g=motor,effective_print_density_g_cm3=plastic,radial_displacement_mm=travel,before=a,after=b))
nominal=[r for r in rows if r['motor_mass_g']==180 and r['effective_print_density_g_cm3']==.45]
report=dict(passed=True,radial_setback_mm=p['radial_setback_mm'],body_extension_mm=new['r_actuator']['extension_mm'],radial_travel_mm=new['radial_stroke'],tip_reach_mm=[new['rmin'],new['rmax']],nominal_sensitivity_case=nominal,sensitivity_samples=rows,limits=['Assumed motor masses 140/180/250 g, effective printed density 0.2/0.45/0.65 g/cm3, reference hardware approximated as steel at 7.85 g/cm3.','The full Z carriage is included in the lifted assembly. Wiring and actual infill/toolpaths are not modeled.','Reduced estimated gravity moment does not establish strength, stiffness or physical balance. Weigh printed parts and the selected motor to refine.'],source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ['model.py','leadscrew_actuator.py','parameters.json','check_balance.py']})
(root/'output/balance-validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(dict(passed=True,nominal=nominal),indent=2))
