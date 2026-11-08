"""Single-face Z support and upright radial stage; drives stay assembled."""
def timeline(parts):
    names={p['name'] for p in parts};stages=[]
    def select(prefix):return sorted(n for n in names if n.startswith(prefix))
    def add(label,ns,delta):
        assert ns and set(ns)<=names
        stages.append(dict(label=label,parts=sorted(ns),delta=delta))
    bolts=select('R_enclosure_mount_screw_')
    add('Withdraw radial base bolts through access wells',bolts,[0,0,90]);add('Park radial base bolts',bolts,[0,-180,0])
    radial=[p['name'] for p in parts if p.get('actuator')=='R']+select('Probe_output_mount_screw_')+['Triangular_probe_outrigger','Spring_probe_reference']
    add('Lift upright radial actuator off carrier',radial,[0,0,100])
    bolts=select('Z_output_mount_screw_');add('Withdraw recessed output screws',bolts,[0,0,40]);add('Park output screws',bolts,[0,-140,0])
    carrier=['Z_to_radial_carrier']+select('R_base_captive_nut_')
    add('Lift full-width carrier from Z flange',carrier,[0,0,60]);add('Move carrier to service position',carrier,[450,0,0]);add('Move radial module to service position',radial,[450,0,0])
    nuts=select('Z_base_mount_nut_')+select('Z_base_mount_washer_')
    add('Remove Z base nuts and washers',nuts,[0,-30,0]);add('Park Z base nuts and washers',nuts,[-160,0,0])
    bolts=select('Z_base_mount_screw_');add('Withdraw Z base bolts through mounting wells',bolts,[0,100,0]);add('Park Z base bolts',bolts,[300,0,0])
    add('Separate Z actuator from its base mounting face',[p['name'] for p in parts if p.get('actuator')=='Z'],[0,100,0])
    bolts=select('Z_cradle_deck_screw_');add('Unbolt support from rotating deck',bolts,[0,0,25])
    add('Park rear deck screws',[n for n in bolts if int(n.rsplit('_',1)[1])<3],[0,-100,0]);add('Park front deck screws',[n for n in bolts if int(n.rsplit('_',1)[1])>=3],[0,100,0])
    add('Lift single-face support from deck',['Z_support'],[0,0,80])
    return stages
