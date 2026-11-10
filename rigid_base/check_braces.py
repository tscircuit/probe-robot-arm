"""Brace interfaces, continuous rear clearance and material accounting."""
import json,hashlib,math
from .model import build,parameters,ROOT,cyl,overlap
from .printed_braces import layout

def main():
    parts,info=build();p=parameters();by={a['name']:a for a in parts};q=layout(p,dict(z_origin=info['arm_parameters']['z_origin']+info['arm_z_shift_mm']))
    support=by['Boxed_Z_support']['shape'];deck=by['Rigid_rotating_deck']['shape'];braces=[by['Printed_rear_brace_'+side]['shape'] for side in ['left','right']]
    assert len(deck.Solids())==1 and abs(support.BoundingBox().ymin+84)<1e-5
    for x,s in zip(q['xs'],braces):
        assert len(s.Solids())==1 and abs(s.BoundingBox().xlen-p['brace_thickness_mm'])<1e-5
        assert overlap(s,support)<1e-6 and overlap(s,deck)<1e-6
        for i,z in enumerate(q['levels']):
            start=-133 if i==1 else -109
            tool=cyl(2.19,-72-start,(x,start,z),(0,1,0));assert overlap(tool,support)<1e-6 and overlap(tool,s)<1e-6
        for y in q['foot_ys']:
            tool=cyl(2.19,35,(x,y,q['bottom']-9));assert overlap(tool,s)<1e-6 and overlap(tool,deck)<1e-6
    # Z/R translation never changes Y. Drive rotation stays within these conservative
    # cylinders from each part's entire bounding box, so this also covers all screw phases.
    clearance=[];drive_z=info['arm_layout']['r_drive_z']+info['arm_z_shift_mm']
    for a in parts:
        motion=a.get('motion')
        if not motion:continue
        b=a['shape'].BoundingBox();minimum=b.ymin
        if motion=='z_drive':minimum=-math.hypot(max(abs(b.xmin),abs(b.xmax)),max(abs(b.ymin),abs(b.ymax)))
        if motion=='r_drive':minimum=-math.hypot(max(abs(b.ymin),abs(b.ymax)),max(abs(b.zmin-drive_z),abs(b.zmax-drive_z)))
        gap=minimum-(-72);assert gap>0,(a['name'],gap)
        clearance.append(dict(part=a['name'],minimum_y_mm=minimum,gap_to_brace_hardware_mm=gap))
    baseline=json.loads((ROOT/'rigid_base/previous-structure.json').read_text());old=sum(a['volume_mm3'] for a in baseline['parts']);new=support.Volume()+deck.Volume()+sum(s.Volume() for s in braces);assert new<old,(old,new)
    report=dict(passed=True,structure_volume_before_mm3=old,structure_volume_after_mm3=new,volume_reduction_percent=100*(1-new/old),brace_tower_holes_per_side=3,brace_deck_holes_per_side=2,foot_location_key_clearance_per_side_mm=.2,brace_thickness_mm=p['brace_thickness_mm'],brace_mount_height_above_deck_mm=q['levels'][-1]-q['bottom'],rear_deck_extent_mm=200,actuator_rear_separation=clearance,physical_stiffness_verified=False,source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['rigid_base/model.py','rigid_base/printed_braces.py','rigid_base/parameters.json','rigid_base/check_braces.py','rigid_base/previous-structure.json']})
    (ROOT/'output/rigid-base/brace-validation.json').write_text(json.dumps(report,indent=2));print('Brace interface and clearance checks passed; material reduction',round(report['volume_reduction_percent'],1),'%',flush=True)
if __name__=='__main__':main()
