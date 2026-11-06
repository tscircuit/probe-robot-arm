"""Check the minimum-tooth design, motor relocation and print-critical gear dimensions."""
import hashlib,json,math,pathlib
from model import drive_gears,base_drive_center,annulus,overlap,inv
root=pathlib.Path(__file__).resolve().parent
p=json.loads((root/'parameters.json').read_text());gear,ring,nominal,_=drive_gears(p)
m,n,nr,pa=[p[k] for k in ['gear_module','pinion_teeth','ring_teeth','pressure_angle']]
a=math.radians(pa);rp=m*n/2;R=m*nr/2;rb=rp*math.cos(a);ra=rp+m;rr=rp-1.25*m
minimum=math.ceil(2/math.sin(a)**2);assert n==minimum==12
center=base_drive_center(p);assert abs(center-60)<1e-9 and abs((R-rp)-center)<1e-9
half=lambda r: math.pi/(2*n)+p['tooth_preload']/rp+inv(rp,rb)-inv(max(r,rb),rb)
f=p['base_tooth_slot_fraction'];wall_tip=ra*(1-f)*half(ra);gap_tip=2*ra*f*half(ra)
assert wall_tip>.4 and gap_tip>.25
core=rr-1.3-rr*f*half(rr)
# A full annular load path remains between the tooth slots and shaft bore.
core_probe=annulus(core-.02,2.67,10,33).translate((center,0,0))
assert core_probe.cut(gear).Volume()<1e-6
assert gear.isValid() and len(gear.Solids())==1
contact=(math.sqrt(ra**2-rb**2)-math.sqrt((R-m)**2-(R*math.cos(a))**2)+center*math.sin(a))/(math.pi*m*math.cos(a))
assert contact>1.4
report=dict(passed=True,pinion_teeth=n,ring_teeth=nr,total_ratio=nr/n,unshifted_minimum_teeth=minimum,undercut_formula='ceil(2/sin(pressure_angle)^2)',formula_source='https://sdp-si.com/D805/D805_PDFS/sections/technical.pdf, equation 4-3',motor_offset_mm=center,previous_offset_mm=52,pitch_diameter_mm=2*rp,tip_diameter_mm=2*ra,slot_half_angle_fraction=f,tangential_tip_wall_mm=wall_tip,tangential_tip_slot_mm=gap_tip,conservative_core_to_bore_wall_mm=core-2.65,nominal_transverse_contact_ratio=contact,tip_motion_per_1_16_microstep_mm={str(r):r*math.radians(1.8/16/(nr/n)) for r in [195,250,315]},limits=['Tangential wall figures are profile dimensions, not a printer qualification. Inspect sliced toolpaths and open slots.','Narrower slots change tooth stiffness; no load, fatigue, backlash or absolute accuracy qualification.','Nominal gear collision samples are recorded separately in validation.json.'])
report['source_sha256']={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ['model.py','parameters.json','rotary_base/core.py','rotary_base/gear_geometry.py','rotary_base/parameters.json','check_base_drive.py']}
(root/'output/base-drive-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
