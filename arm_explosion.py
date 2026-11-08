"""Module service sequence; screw drives remain assembled and threaded."""
def timeline(parts):
    names={p['name'] for p in parts};stages=[]
    def select(prefix):return sorted(n for n in names if n.startswith(prefix))
    def add(label,ns,delta):
        assert ns and set(ns)<=names
        stages.append(dict(label=label,parts=sorted(ns),delta=delta))
    bolts=select('Z_output_mount_screw_');output_bolts=bolts
    radial=output_bolts+select('R_')+select('Probe_output_mount_screw_')+['Triangular_probe_outrigger','Spring_probe_reference','Z_to_radial_carrier']
    add('Unscrew Z output bolts; retain in carrier',bolts,[0,0,6])
    add('Lift radial stage off output flange',radial,[0,0,100]);add('Move radial assembly to service position',radial,[450,0,0])
    bolts=select('R_enclosure_mount_screw_');add('Release radial bottom mounting screws',bolts,[0,0,-25]);add('Park radial mounting screws',bolts,[0,-160,0])
    add('Lift radial actuator from carrier',[n for n in radial if n not in bolts+output_bolts+['Z_to_radial_carrier']],[0,0,100])
    add('Withdraw retained Z output bolts',output_bolts,[0,0,20]);add('Park Z output bolts',output_bolts,[0,-240,0])
    bolts=select('Z_top_mount_screw_');add('Release Z lid-face mounting screws',bolts,[25,0,0]);add('Park Z lid-face screws',bolts,[0,220,0])
    bolts=select('Z_enclosure_mount_screw_');add('Release Z side mounting screws',bolts,[0,-30,0]);add('Park Z side screws',bolts,[-140,0,0])
    add('Slide Z actuator out of open cradle',[p['name'] for p in parts if p.get('actuator')=='Z'],[0,300,0])
    bolts=select('Z_cradle_deck_screw_');add('Unbolt cradle from deck',bolts,[0,0,25]);add('Park left cradle screws',[n for n in bolts if int(n.rsplit('_',1)[1])<3],[-160,0,0]);add('Park right cradle screws',[n for n in bolts if int(n.rsplit('_',1)[1])>=3],[160,0,0])
    add('Lift cradle off rotating deck',['Z_support'],[0,0,80])
    return stages
