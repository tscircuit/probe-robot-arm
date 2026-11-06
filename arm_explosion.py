"""Module-level service sequence. Drives stay assembled inside their trays."""
def timeline(parts):
    names={p['name'] for p in parts}
    stages=[]
    def select(prefix):return sorted(n for n in names if n.startswith(prefix))
    def add(label,parts,delta):
        assert parts and set(parts)<=names
        stages.append(dict(label=label,parts=sorted(parts),delta=delta))
    zs=select('Z_output_mount_screw_')
    r=select('R_')+select('Probe_output_mount_screw_')+['Triangular_probe_outrigger','Spring_probe_reference','Z_to_radial_carrier']
    nuts=select('Z_output_nut_');front=select('Z_output_front_washer_');rear=select('Z_output_rear_washer_')
    add('Remove Z output nuts',nuts,[-12,0,0])
    add('Park Z output nuts',nuts,[0,-120,0])
    add('Withdraw Z through-bolts and front washers',zs+front,[40,0,0])
    add('Park Z through-bolts and front washers',zs+front,[0,-100,0])
    add('Remove Z rear washers',rear,[-12,0,0])
    add('Park Z rear washers',rear,[0,-100,0])
    add('Lift U carrier off Z output pad',r,[0,0,60])
    add('Separate horizontal assembly from Z output',r,[100,0,0])
    add('Lift horizontal assembly clear',r,[0,0,120])
    add('Move horizontal assembly to service position',r,[250,0,0])
    rs=select('R_enclosure_mount_screw_')
    add('Release horizontal enclosure screws',rs,[0,0,-20])
    add('Park horizontal enclosure screws',rs,[0,-150,0])
    runit=[n for n in r if n not in rs+['Z_to_radial_carrier']]
    add('Separate horizontal enclosure from carrier',runit,[0,0,140])
    for axis,withdraw,park,lift in [('R',[0,0,-35],[0,180,0],[0,0,-70]),('Z',[35,0,0],[0,180,0],[70,0,0])]:
        if axis=='Z':
            top_screws=select('Z_top_mount_screw_')
            add('Release Z top-face screws',top_screws,[20,0,0])
            add('Park Z top-face screws',top_screws,[0,160,0])
            screws=select('Z_enclosure_mount_screw_')
            add('Release vertical enclosure screws',screws,[0,-20,0])
            add('Park vertical enclosure screws',screws,[-80,0,0])
            unit=[p['name'] for p in parts if p.get('actuator')=='Z']
            add('Separate vertical enclosure from both cradle faces',unit,[-90,100,0])
            deck_screws=select('Z_cradle_deck_screw_')
            add('Unbolt cradle flanges from deck inserts',deck_screws,[0,0,30])
            add('Park cradle flange screws',deck_screws,[150,0,0])
            add('Lift flanged cradle off rotating deck',['Z_support'],[0,0,60])
        screws=[p['name'] for p in parts if p.get('actuator')==axis and p.get('actuator_group')=='cover_screws']
        cover=[p['name'] for p in parts if p.get('actuator')==axis and p.get('actuator_group')=='cover']
        add(axis+' — release lid screws',screws,withdraw)
        add(axis+' — park lid screws',screws,park)
        add(axis+' — open enclosure lid',cover,lift)
    return stages
