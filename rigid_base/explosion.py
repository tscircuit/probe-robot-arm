"""Service-module explosion: fasteners are released before axial withdrawal.
Actuators, bearing cartridge and ring/deck/support remain assembled internally.
"""
def timeline(parts):
    names={p['name'] for p in parts}; stages=[]
    def pick(*prefixes):return sorted(n for n in names if n.startswith(prefixes))
    def move(label,ns,delta):
        assert set(ns)<=names and len(ns)==len(set(ns)) and ns
        stages.append(dict(label=label,parts=ns,delta=list(delta)))
    stand=['Braced_test_stand']+pick('M5_stand_nut_')
    move('Lower stand after releasing its four nuts',stand,(0,0,-140))
    move('Set stand aside',stand,(-300,0,0))
    move('Withdraw centre bolt', ['M6x60_axle_bolt','M6_washer_-1.6'],(0,0,-100))
    rotor=[p['name'] for p in parts if p['group']=='rotor']+['6002_bearing_18','6002_bearing_43','Inner_race_spacer','Inner_race_top_washer','M6_washer_50','M6_axle_nut']
    move('Lift arm, ring and bearing cartridge off spindle',rotor,(0,0,100))
    move('Set arm module aside',rotor,(0,340,0))
    move('Withdraw pinion bearing-cap screws',pick('M3x8_pinion_cap_'),(0,0,110))
    move('Loosen pinion set screw half a turn',['M3x4_pinion_set_screw'],(0,-.25,0))
    move('Lift pinion and support bearing together',['Solid_12T_module1_pinion','688ZZ_pinion_bearing','Pinion_bearing_cap','M3x4_pinion_set_screw'],(0,0,75))
    move('Withdraw motor mounting screws',pick('M3x20_motor_face_'),(0,0,45))
    motor=pick('NEMA17_motor','Motor_D_shaft','Rear_controller','Controller_','USB_')
    move('Lower motor and rear controller',motor,(0,0,-95))
    return stages
