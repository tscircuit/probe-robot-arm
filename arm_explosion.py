"""Single-face Z support and upright radial stage; drives stay assembled."""
def timeline(parts):
    names={p['name'] for p in parts};stages=[]
    def select(prefix):return sorted(n for n in names if n.startswith(prefix))
    def add(label,ns,delta):
        assert ns and set(ns)<=names
        stages.append(dict(label=label,parts=sorted(ns),delta=delta))
    bolts=select('Z_output_mount_screw_')
    add('Withdraw direct lid screws into Z flange access wells',bolts,[0,0,18])
    radial=[p['name'] for p in parts if p.get('actuator')=='R']+select('Probe_output_mount_screw_')+['Triangular_probe_outrigger','Spring_probe_reference']
    add('Separate radial lid from inverted Z flange',radial,[0,180,0])
    add('Move radial module to service position',radial,[450,0,0])
    bolts=select('Z_base_mount_screw_');add('Withdraw Z base screws from grid inserts',bolts,[0,-40,0]);add('Park Z base screws',bolts,[-160,0,0])
    add('Separate Z actuator from its base mounting face',[p['name'] for p in parts if p.get('actuator')=='Z']+select('Z_output_mount_screw_'),[0,100,0])
    bolts=select('Z_cradle_deck_screw_');add('Unbolt support from rotating deck',bolts,[0,0,40])
    add('Park rear deck screws',[n for n in bolts if int(n.rsplit('_',1)[1]) in [0,2]],[0,-100,0]);add('Park front center deck screw',[n for n in bolts if n.endswith('_1')],[0,140,0]);add('Park right deck screws',[n for n in bolts if 3<=int(n.rsplit('_',1)[1])<6],[180,0,0])
    add('Park left deck screws',[n for n in bolts if int(n.rsplit('_',1)[1])>=6],[-180,0,0])
    add('Lift single-face support from deck',['Z_support'],[0,0,80])
    return stages
