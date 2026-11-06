"""Shared staged translation path for the CAD checker, renderer and viewer.
All directions are world axes, in mm. Rotation is held at zero while exploded.
Fasteners are assumed unthreaded before their axial withdrawal is shown.
"""
import math,json,pathlib

def timeline(parts):
    all_names={p['name'] for p in parts}
    def select(*prefixes):return sorted(n for n in all_names if n.startswith(prefixes))
    def exact(*names):
        assert set(names)<=all_names,set(names)-all_names
        return list(names)
    stages=[]
    def move(label,names,delta):
        assert names and len(names)==len(set(names)),label
        stages.append(dict(label=label,parts=names,delta=list(delta)))
    move('Withdraw stand screws',select('M5x25_upper_stand_'),(0,0,120))
    stand=exact('Integrated_stand')+select('M5_stand_nut_')
    move('Lower the stand',stand,(0,0,-180))
    move('Set stand aside',stand,(-240,0,0))
    move('Unplug USB cable',exact('USB_cable_KEEPOUT'),(0,0,-90))
    move('Park cable clear of motor',exact('USB_cable_KEEPOUT'),(0,130,0))
    move('Withdraw centre bolt',exact('M6x60_axle_bolt','M6_washer_-1.6'),(0,0,-120))
    move('Lift inner-race clamp',exact('Inner_race_top_washer','M6_washer_50','M6_axle_nut'),(0,0,180))
    rotor=[p['name'] for p in parts if p['group']=='rotor']+exact('6002_bearing_18','6002_bearing_43','Inner_race_spacer')
    move('Lift bearing cartridge off spindle',rotor,(0,0,120))
    move('Move cartridge clear of base',rotor,(0,-220,0))
    move('Remove ring nuts and washers',select('M3_ring_nut_','M3_ring_washer_'),(0,0,120))
    move('Withdraw ring bolts',select('M3x30_ring_'),(0,0,-100))
    move('Set ring bolts aside',select('M3x30_ring_'),(140,0,0))
    move('Lower ring and integral spacers',exact('Internal_72T_ring'),(0,0,-60))
    move('Set ring aside',exact('Internal_72T_ring'),(140,0,0))
    move('Remove housing nuts',select('M3_housing_nut_'),(0,0,120))
    move('Withdraw housing bolts',select('M3x45_housing_'),(0,0,-100))
    move('Set housing bolts aside',select('M3x45_housing_'),(-100,0,0))
    move('Lift upper bearing retainer and deck',exact('Rotating_test_deck'),(0,0,70))
    move('Lift upper bearing out of seat',exact('6002_bearing_43'),(0,0,40))
    move('Lift inner spacer clear',exact('Inner_race_spacer'),(0,0,35))
    move('Lower bottom retainer',exact('Lower_bearing_retainer'),(0,0,-30))
    move('Lower bottom bearing out of seat',exact('6002_bearing_18'),(0,0,-20))
    move('Release pinion set screw',exact('M3x4_pinion_set_screw'),(0,-6,0))
    pinion=exact('Compliant_12T_pinion','M3x4_pinion_set_screw')
    move('Lift pinion off shaft',pinion,(0,0,180))
    move('Set pinion aside',pinion,(130,0,0))
    move('Withdraw motor face screws',select('M3x16_motor_face_'),(0,0,110))
    motor=exact('NEMA17_motor_REFERENCE','Motor_D_shaft_REFERENCE','Rear_controller_PCB_REFERENCE','Controller_component_KEEPOUT')+select('Controller_spacer_')
    move('Lower motor out of fixed plate',motor,(0,0,-110))
    move('Set motor unit aside',motor,(140,0,0))
    move('Withdraw spindle screws',select('M3x12_spindle_flange_'),(0,0,-60))
    move('Lift stationary spindle',exact('Fixed_spindle')+select('M3_spindle_nut_'),(0,0,100))
    # The four bearings slide off the integral axles along their 45-degree axes.
    for i,angle in enumerate(json.loads((pathlib.Path(__file__).parent/'parameters.json').read_text())['roller_angles_deg']):
        q=math.sqrt(.5);a=math.radians(angle)
        move(f'Pull roller {i+1} off printed axle',exact(f'625ZZ_support_roller_{i}'),(60*q*math.cos(a),60*q*math.sin(a),60*q))
    return stages

def offsets(parts,stages,progress):
    # Equal stage durations; smooth easing changes speed, not the checked path.
    result={p['name']:[0.,0.,0.] for p in parts}
    at=max(0,min(1,progress))*len(stages)
    for i,s in enumerate(stages):
        t=max(0,min(1,at-i));t=t*t*(3-2*t)
        for n in s['parts']:result[n]=[v+t*d for v,d in zip(result[n],s['delta'])]
    return result
