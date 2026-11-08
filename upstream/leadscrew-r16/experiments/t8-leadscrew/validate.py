"""Solid geometry checks for the isolated T8 carriage, not structural analysis."""
def validate():
 import itertools,time
 import numpy as np
 report={'passed':False,'units':'mm','intersection_tolerance_mm3':.01,'source_sha256':hashlib.sha256((ROOT/'experiments/t8-leadscrew/model.py').read_bytes()).hexdigest(),'validation_source_sha256':hashlib.sha256((ROOT/'experiments/t8-leadscrew/validate.py').read_bytes()).hexdigest()}
 def save(): (OUT/'validation.json').write_text(json.dumps(report,indent=2))
 # Only screw/rib intersections are intentional. Verify the actual intersection
 # is confined to those three ribs; never waive an entire fastener/host pair.
 joints=[];joint_pairs=set();by_name={p['name']:p for p in parts}
 for j in THREAD_JOINTS:
  host=by_name[j['host']]['shape'];screw=by_name[j['bolt']]['shape']
  ribs=ridge_material(j['diameter'],j['length'],j['center'],j['axis'],j['start'])
  intersection=host.intersect(screw)
  extra=intersection.cut(ribs).Volume();missing=ribs.cut(host).Volume()
  rib_contacts=[overlap(r,screw) for r in ribs.Solids()]
  spec=THREAD_PROFILES[j['diameter']]
  projections=[sum((v.toTuple()[i]-j['center'][i])*j['axis'][i] for i in range(3)) for v in screw.Vertices()]
  engagement=max(0,min(j['start']+j['length'],max(projections))-max(j['start']+spec['lead_in'],min(projections)))
  row={k:v for k,v in j.items()};row.update(ridge_count=len(ribs.Solids()),missing_ridge_mm3=missing,unexpected_overlap_mm3=extra,ridge_contact_volumes_mm3=rib_contacts,full_depth_engagement_mm=engagement)
  row['passed']=len(rib_contacts)==3 and min(rib_contacts)>0 and extra<.01 and missing<.01 and engagement>=j['diameter']*1.5
  joints.append(row)
  if row['passed']:joint_pairs.add(frozenset([j['host'],j['bolt']]))
 output_seats=[]
 for j in OUTPUT_PILOTS:
  ribs=ridge_material(j['diameter'],j['length'],j['center'],j['axis'])
  hole=ridge_hole(j['diameter'],j['length'],j['center'],j['axis'])
  wall=ring(3.45,1.75,8,j['center'],j['axis'])
  q=dict(center_mm=j['center'],ridge_count=len(ribs.Solids()),missing_ridge_mm3=ribs.cut(beam).Volume(),blocked_pilot_mm3=overlap(beam,hole),missing_wall_mm3=wall.cut(beam).Volume())
  q['passed']=q['ridge_count']==3 and max(q[k] for k in ['missing_ridge_mm3','blocked_pilot_mm3','missing_wall_mm3'])<.01
  output_seats.append(q)
 report['output_mount']={'pattern':'Central NEMA17 mounting pitch with extra outer holes on wider plates','pitch_mm':[31,31],'outer_pitch_mm':[31+2*WIDEN,31] if WIDTH>1 else None,'thread':'M3 three-ridge plastic forming pilot','pilot_depth_mm':8,'full_depth_thread_length_mm':7.4,'maximum_screw_entry_mm':8,'face_size_mm':[42*WIDTH,42],'face_home_x_mm':EXIT_X,'holes':output_seats,'passed':len(output_seats)==(8 if WIDTH>1 else 4) and all(q['passed'] for q in output_seats)}
 report['plastic_thread_seats']={'method':'Three axial rounded ribs at 120 degrees, with tapered entry. Unformed rib/shaft overlap is intentional and bounded to each verified rib solid. Thread forming and stripping torque are not simulated.',
  'profiles':THREAD_PROFILES,'fastener_nuts':0,'joints':joints,'passed':all(q['passed'] for q in joints) and len(joints)==(7 if PRINTED else 10)}
 save();print('Three-ridge seats',report['plastic_thread_seats']['passed'],flush=True)
 if not report['plastic_thread_seats']['passed'] or not report['output_mount']['passed']:return report
 insert_checks=[];printed_carrier=by_name[CARRIER_NAME]['freeShape'];installed_carrier=by_name[CARRIER_NAME]['shape']
 for j,(x,y) in enumerate(ADJUST_CENTERS):
  insert=by_name[f'M5 heat-set insert {j+1}']['shape']
  pilot=cyl(3.2,10.5,(x,y,9.5));wall=ring(5.8,3.61,9.5,(x,y,10.5));approach=cyl(4.3,55,(x,y,20.01))
  row=dict(center_mm=[x,y,20],blocked_printed_pilot_mm3=overlap(pilot,printed_carrier),missing_wall_mm3=wall.cut(printed_carrier).Volume(),installed_interference_mm3=overlap(insert,installed_carrier),tool_approach_blockage_mm3=overlap(approach,printed_carrier),insert_to_pilot_bottom_mm=1,engagement_mm=9.5)
  row['passed']=max(row[k] for k in ['blocked_printed_pilot_mm3','missing_wall_mm3','installed_interference_mm3','tool_approach_blockage_mm3'])<.01;insert_checks.append(row)
 displacement=printed_carrier.cut(installed_carrier)
 for x,y in ADJUST_CENTERS:displacement=displacement.cut(cyl(3.57,9.5,(x,y,10.5)))
 report['carrier_heat_set_inserts']={'specification':INSERT,'count':4,'checks':insert_checks,'unexpected_plastic_change_mm3':displacement.Volume(),'installation':'Heat set into the loose carrier before assembling it. Inserts stay bonded to the carrier during adjustment and exploded disassembly. STL uses Ø6.4 mm pilots; assembly cavity represents displaced plastic.','passed':all(q['passed'] for q in insert_checks) and displacement.Volume()<.01}
 if not report['carrier_heat_set_inserts']['passed']:save();return report
 collisions=[]
 for a,b in itertools.combinations(parts,2):
  if frozenset([a['name'],b['name']]) in joint_pairs:continue

  v=overlap(a['shape'],b['shape'])
  if v>.01:collisions.append({'parts':[a['name'],b['name']],'overlap_mm3':v})
 report['assembled_collisions']=collisions;save();print('Static collisions',collisions,flush=True)
 if collisions:return report
 # The printed support contacts only a small annular inner-race land.
 # Check the full land volume and both bearing-face clearance regions against
 # every printed part, not just a nominal support diameter in metadata.
 seats=[]
 for b in bearings:
  c,u=b['center'],b['axis'];host=by_name[BASE_NAME if b['kind']=='upper' else CARRIER_NAME]['shape']
  land=ring(3.7,2.8,2,c,u,2.5)
  back=ring(7.95,4.15,1.95,c,u,2.5);front=ring(7.95,4.15,.75,c,u,-3.25)
  blocked=[]
  for p in parts:
   if not p['printed']:continue
   # Retaining rails intentionally flank the rim 0.5 mm from its faces.
   rear_probe=ring(7.95,4.15,.45,c,u,2.5) if p['group']=='carriage' else back
   front_probe=ring(7.95,4.15,.45,c,u,-2.95) if p['group']=='carriage' else front
   v=overlap(rear_probe,p['shape'])+overlap(front_probe,p['shape'])
   if v>.01:blocked.append({'part':p['name'],'overlap_mm3':v})
  missing=land.cut(host).Volume()
  seats.append({'station_x_mm':b['station'],'kind':b['kind'],'side':b['sign'],'land_diameter_mm':7.4,'support_face_recess_mm':2,'missing_land_mm3':missing,'blocked_face_clearance':blocked,'passed':missing<.01 and not blocked})
 report['bearing_face_relief']={'inner_race_land_diameter_mm':7.4,'surrounding_relief_diameter_mm':17,'recess_depth_mm':2,'loose_support_spacers':0,'seats':seats,'passed':len(seats)==len(bearings) and all(q['passed'] for q in seats)}
 print('Bearing face relief',report['bearing_face_relief']['passed'],flush=True)
 if not report['bearing_face_relief']['passed']:save();return report
 # Verify both retention and the deflected snap-through path. No bearing/axle
 # intersections are waived. The shear is a schematic deformation envelope.
 snaps=[]
 for b in bearings:
  c,u=b['center'],b['axis'];kind=b['kind']
  bearing=ring(8,2.5,5,c,u,-2.5);pin=snap_pin(c,u);compressed=snap_pin(c,u,SNAP['compression'])
  support=chassis_without_pins if kind=='upper' else carrier_without_pins
  retention=overlap(pin,bearing.translate(tuple(-.65*q for q in u)))
  swept=ring(8,2.5,5+SNAP['bearing_release_mm'],c,u,-2.5-SNAP['bearing_release_mm'])
  passages=[overlap(swept,compressed)+overlap(swept,support)]
  journal=pin.intersect(local_box(c,u,-5,5,-5,5,-2.5,2.5));journal_error=journal.cut(cyl(2.4,5,c,u,-2.5)).Volume()
  shoulder=pin.intersect(local_box(c,u,-5,5,-5,5,SNAP['head_back_t']-.02,SNAP['head_back_t']-.01)).BoundingBox().xlen
  tip_width=pin.intersect(local_box(c,u,-5,5,-5,5,SNAP['tip_t']+.05,SNAP['tip_t']+.06)).BoundingBox().xlen
  widest=pin.BoundingBox().xlen
  snaps.append(dict(shoulder_width_mm=shoulder,tip_width_mm=tip_width,maximum_width_mm=widest,straight_journal_error_mm3=journal_error,station_x_mm=b['station'],kind=kind,side=b['sign'],retaining_interference_mm3=retention,max_compressed_path_overlap_mm3=max(passages),passed=abs(shoulder-6.4)<.001 and abs(widest-shoulder)<.001 and tip_width<shoulder-1.5 and journal_error<.0001 and retention>.01 and max(passages)<.01 and compressed.isValid()))
 report['snap_axles']={'count':len(bearings),'bearing_axle_bolts':0,'material':'PETG prototype','shaft_diameter_mm':4.8,'retaining_head_diameter_mm':6.4,'tip_diameter_mm':4.6,'slot_width_mm':1.2,'slot_end_radius_mm':.6,'head_axial_clearance_mm':.25,'widest_at_bearing_facing_shoulder':True,'bend_start_beyond_bearing_mm':1.25,'tip_bend_degrees':30,'extension_mm':3,'bearing_removal_distance_mm':12,'deflection_per_prong_at_head_mm':SNAP['compression'],'shaft_bias_degrees':0,'slot_width_at_head_mm':2.,'slot_width_at_tip_mm':2.2,'checks':snaps,'passed':all(q['passed'] for q in snaps),'note':'Schematic prong pinching and tip straightening verify geometric passage and retention only; print fit, insertion force, strain, fatigue and PETG creep require physical testing.'}
 print('Snap axle retention / insertion',report['snap_axles']['passed'],flush=True)
 if not report['snap_axles']['passed']:save();return report
 # Rails must stop axial escape while leaving the nominal bearing envelope clear.
 rail_checks=[]
 for b in bearings:
  c,u=b['center'],b['axis'];bearing=ring(8,2.5,5,c,u,-2.5)
  nominal=overlap(beam,bearing)
  stopped=overlap(beam,bearing.translate(tuple(-3.2*q for q in u)))
  rail_checks.append(dict(station_x_mm=b['station'],kind=b['kind'],side=b['sign'],nominal_overlap_mm3=nominal,escape_stop_overlap_mm3=stopped,passed=nominal<.01 and stopped>.01))
 gauges=[]
 for track in TRACKS:
  for side in [-1,1]:
   full=track_rail(track,side).intersect(rect(TAIL_HOME+18,TAIL_HOME+19,-200,200,0,100))
   missing=full.cut(beam).Volume();gauges.append(dict(section_area_mm2=full.Volume(),missing_mm3=missing,passed=abs(full.Volume()-18.4)<.01 and missing<.01))
 report['track_retention']={'rail_width_mm':4,'rail_height_above_track_mm':4,'embedded_depth_mm':.6,'entrance_ramp_length_mm':4,'support_normal_gap_mm':.2,'bearing_side_gap_mm':.5,'one_x_lower_lane_side_gap_mm':[.5,2.5],'checks':rail_checks,'rail_sections':gauges,'passed':all(q['passed'] for q in rail_checks+gauges)}
 print('Track retention',report['track_retention']['passed'],flush=True)
 if not report['track_retention']['passed']:save();return report
 # Lid and side attachment receivers have three full axial ribs and a blind
 # end. Screw/thread interference is checked only against those actual ribs.
 mounts=[];attachment_access=[]
 for j in ATTACH_PILOTS:
  c,u=j['center'],j['axis'];host=by_name[j['host']]['shape'];length=j['length']
  ribs=ridge_material(5,length,c,u);hole=ridge_hole(5,length,c,u);wall=ring(4.5,2.8,length,c,u)
  row=dict(kind=j['kind'],host=j['host'],center_mm=list(c),axis=list(u),diameter=5,pilot_depth_mm=length,ridge_count=len(ribs.Solids()),missing_ridge_mm3=ribs.cut(host).Volume(),blocked_pilot_mm3=overlap(hole,host),missing_wall_mm3=wall.cut(host).Volume())
  row['passed']=row['ridge_count']==3 and max(row[k] for k in ['missing_ridge_mm3','blocked_pilot_mm3','missing_wall_mm3'])<.01;mounts.append(row)
  # Enter from outside, leaving 0.6 mm to the blind bottom. Tool/head above face.
  probe=cyl(2.45,length-.6,c,u).fuse(cyl(5.2,65,c,tuple(-q for q in u),.01))
  for travel in [0,20,40]:
   for p in parts:
    body=pose(p,travel)
    if overlap(probe,body)<.01:continue
    hit=probe.intersect(body)
    if p['name']==j['host']:hit=hit.cut(ribs)
    if hit.Volume()>.01:attachment_access.append(dict(mount=j['kind'],center_mm=list(c),travel_mm=travel,part=p['name'],overlap_mm3=hit.Volume()))
 # The top of the original motor plate was 68 mm before adding a lid.
 height=max(p['shape'].BoundingBox().zmax for p in parts)
 closed_walls=[]
 for x in STATIONS:
  for sign in [-1,1]:
   region=cyl(5,6,(x,wide(sign*34),18),(0,sign,0))
   closed_walls.append(region.cut(chassis_shape).Volume())
 report['lid_and_attachment']={'lid_fixings':len(LID_FIXINGS),'lid_fixing_thread':'M3 three-ridge, 12 mm pilot depth','lid_thickness_mm':4,'lid_bottom_z_mm':64,'lid_top_z_mm':68,'assembly_height_mm':height,'original_height_limit_mm':68,'external_mount_thread':'M5 three-ridge blind pilot','external_pilot_depth_mm':9,'top_mount_count':len(LID_MOUNTS),'side_mount_count':2*len(SIDE_MOUNTS),'floor_mount_count':len(BASE_MOUNT_HOLES),'floor_mount_type':'plain Ø5.5 mm through-hole','checks':mounts,'insertion_collisions':attachment_access,'closed_lower_access_missing_mm3':closed_walls,'passed':not attachment_access and all(q['passed'] for q in mounts) and height<=68.00001 and max(closed_walls)<.01}
 print('Low lid / threaded mounts / closed walls',report['lid_and_attachment']['passed'],flush=True)
 if not report['lid_and_attachment']['passed']:save();return report
 # Adjustment is a rigid guided translation, not flexure deformation.
 adjustment_checks=[]
 for values in [(0,),(.25,),(.5,),(.75,),(1,)]:
  hits=[]
  for i,a in enumerate(parts):
   for b in parts[i+1:]:
    if 'adjustIndex' not in a and 'adjustIndex' not in b:continue
    for travel in [0,40]:
     aa=pose(a,travel,values);bb=pose(b,travel,values)
     if overlap(aa,bb)<.01:continue
     hit=aa.intersect(bb)
     for j in THREAD_JOINTS:
      if frozenset([a['name'],b['name']])!=frozenset([j['host'],j['bolt']]):continue
      host=by_name[j['host']]
      ribs=ridge_material(j['diameter'],j['length'],j['center'],j['axis'],j['start'])
      if 'adjustIndex' in host:ribs=ribs.translate((0,0,values[host['adjustIndex']]-1))
      hit=hit.cut(ribs)
     if hit.Volume()>.01:hits.append({'parts':[a['name'],b['name']],'travel_mm':travel,'overlap_mm3':hit.Volume()})
  adjustment_checks.append({'settings_mm':values,'collisions':hits,'passed':not hits})
 report['adjustable_bearings']={'count':LOWER_COUNT,'carrier_count':1,'adjustment_bolts':4,'travel_mm':[0,1],'mechanism':'Four top-entry M5x25 bolts bear on fixed shelves and pull one rigid carrier holding all lower bearings upward into M5 heat-set inserts; nominal contact at 1 mm. Tighten evenly. No elastic preload or carrier tilt is simulated.','flexures':0,'checks':adjustment_checks,'passed':all(q['passed'] for q in adjustment_checks)}
 print('Adjustment checks',report['adjustable_bearings']['passed'],flush=True)
 if not report['adjustable_bearings']['passed']:save();return report
 # Accelerate exact confirmation with precise triangle screening. Cylindrical
 # references are conservative screw/nut envelopes; thread flank contact is not modeled.
 import fcl,numpy as np
 from OCP.BRepTools import BRepTools
 from OCP.BRepMesh import BRepMesh_IncrementalMesh
 def bvh(s):
  BRepTools.Clean_s(s.wrapped);BRepMesh_IncrementalMesh(s.wrapped,.02,False,.12,True).Perform();vs,ts=s.tessellate(1,.12)
  m=fcl.BVHModel();m.beginModel(len(vs),len(ts));m.addSubModel(np.array([v.toTuple() for v in vs]),np.array(ts));m.endModel();return m
 models=[fcl.CollisionObject(bvh(p['shape'])) for p in parts]
 moving=[i for i,p in enumerate(parts) if p['group']=='carriage'];fixed=[i for i,p in enumerate(parts) if p['group']!='carriage']
 motion=[]
 for travel in np.linspace(0,40,81):
  for i,p in enumerate(parts):
   if p['group']=='carriage':models[i].setTransform(fcl.Transform(np.array([travel,0.,0.])))
   elif p['group']=='rotor':
    angle=-travel*2*math.pi/LEAD;c=math.cos(angle);ss=math.sin(angle);r=np.array([[1,0,0],[0,c,-ss],[0,ss,c]]);pivot=np.array([0.,0.,SCREW_Z]);models[i].setTransform(fcl.Transform(r,pivot-r@pivot))
  for i in moving:
   for j in fixed:
    if not fcl.collide(models[i],models[j],fcl.CollisionRequest(),fcl.CollisionResult()):continue
    v=overlap(pose(parts[i],float(travel)),pose(parts[j],float(travel)))
    if v>.01:motion.append({'travel_mm':float(travel),'parts':[parts[i]['name'],parts[j]['name']],'overlap_mm3':v})
  if travel%10==0:print('Travel',travel,'collisions',len(motion),flush=True)
 report['motion']={'samples':81,'increment_mm':.5,'travel_mm':[0,40],'collisions':motion,'passed':not motion}
 contacts=[]
 for b in bearings:
  n=(0,b['sign']*math.sqrt(3)/2,.5) if b['kind']=='upper' else (0,0,-1)
  center=np.array(b['center']);contact=center-8*np.array(n)
  expected=float(np.dot(contact-np.array([b['station'],0,SCREW_Z]),np.array(n))-16-(WIDEN*math.sqrt(3)/2 if b['kind']=='upper' else 0))
  contacts.append({'kind':b['kind'],'station_x_mm':b['station'],'normal':list(n),'contact_mm':list(contact),'plane_error_mm':float(abs(expected)),'rear_end_margin_at_full_extension_mm':b['station']-8-(TAIL_HOME+STROKE),'rear_running_face_margin_mm':b['station']-8-(TAIL_HOME+STROKE+4),'front_end_margin_at_retraction_mm':GUIDE_END-(b['station']+8)})
 running_faces=[]
 for q in contacts:
  c=q['contact_mm'];n=q['normal'];plane=cq.Plane(origin=(TAIL_HOME+4,c[1],c[2]),xDir=(1,0,0),normal=tuple(n))
  strip=cq.Workplane(plane).center((GUIDE_END-TAIL_HOME-4)/2,0).rect(GUIDE_END-TAIL_HOME-4,7).extrude(-2).val()
  missing=strip.cut(beam).Volume();running_faces.append(dict(kind=q['kind'],contact_mm=c,missing_track_mm3=missing,passed=missing<.01))
 report['running_faces']={'checks':running_faces,'skin_thickness_mm':2,'track_width_mm':7,'passed':all(q['passed'] for q in running_faces)}
 rows=[]
 for q in contacts:
  n=np.array(q['normal']);r=np.array(q['contact_mm']);r[2]-=SCREW_Z
  torque=np.cross(r,n);rows.append([n[1],n[2],*torque])
 constraint_rank=int(np.linalg.matrix_rank(np.array(rows)))
 report['guidance']={'screw_axis_yz_mm':[0,SCREW_Z],'section_reference_yz_mm':[0,SCREW_Z],'width_multiple':WIDTH,'external_screw_bearings':0,'bearing_mount':'fixed base','carriage_type':'moving chamfered tube with two integral threaded bands' if PRINTED else 'moving hollow triangular tube with internal flange nut','transverse_constraint_rank':constraint_rank,'fully_constrained':True,'note':'At nominal contact, the two triangles provide rank-5 constraint, leaving X translation free. This is not a stiffness or load rating.','lower_contact_y_mm':[lower_positions(x) for x in STATIONS],'bearing_count':len(bearings),'bearing_type':'625ZZ, 5x16x5','station_count':2,'bearings_per_station':len(bearings)//2,'station_spacing_mm':STATIONS[-1]-STATIONS[0],'contacts':contacts,'passed':constraint_rank==5 and STATIONS[1]-STATIONS[0]>=40 and all(q['plane_error_mm']<1e-7 and q['rear_running_face_margin_mm']>=1-1e-7 and q['front_end_margin_at_retraction_mm']>=2-1e-7 for q in contacts)}
 # Straight tool approaches to motor, flange and guide axles. Each probe begins
 # outside the head/socket; screw bodies and sockets are not compared to themselves.
 probes=[]
 # Extend the carriage to expose the two lower motor bolts. Their heads
 # still clear the retracted carriage by 1 mm in the assembled fit check.
 for y,z in motor_holes:probes.append(('motor at full extension',xcyl(1.5,20,9.1,y,z),40))
 for y,z in motor_holes:probes.append(('motor key long leg at full extension',cyl(1.5,45,(29,y,z),(0,1 if y>0 else -1,0)),40))
 for travel in [0,40]:
  for y,z in nut_holes:probes.append(('flange',xcyl(1.5,100,NUT_HOME+6.6+travel,y,z),travel))
  for x,y in LID_FIXINGS:probes.append(('lid screw',cyl(1.2,55,(x,y,67.95)),travel))
 for x,y in ADJUST_CENTERS:probes.append(('carrier adjustment',cyl(2.35,75,(x,y,38.1)),0))
 if PRINTED:probes.append(('shaft clamp at full extension',cyl(1.5,65,(17,5,49.1)),40))
 access=[]
 for name,tool,travel in probes:
  for p in parts:
   v=overlap(tool,pose(p,travel))
   if v>.01:access.append({'tool':name,'extension_mm':travel,'part':p['name'],'overlap_mm3':v})
 # Verify each outer floor bore is clear through the entire pad and sweep
 # the 11 mm top driver through every travel position and lid edge opening.
 mounting=[]
 for x,y in BASE_MOUNT_HOLES:
  swept=cyl(5.5,120,(x,y,10.01));landing=ring(5,2.8,1,(x,y,9))
  row={'center_xy_mm':[x,y],'missing_washer_landing_mm3':landing.cut(chassis_shape).Volume(),'blocked_through_bore_mm3':overlap(cyl(2.75,12,(x,y,-1)),chassis_shape),'collisions':[]}
  for p in parts:
   for travel in (np.linspace(0,40,81) if p['group']=='carriage' else [0]):
    v=overlap(swept,pose(p,float(travel)))
    if v>.01:row['collisions'].append({'part':p['name'],'travel_mm':float(travel),'overlap_mm3':v})
  row['passed']=not row['collisions'] and row['missing_washer_landing_mm3']<.01 and row['blocked_through_bore_mm3']<.01;mounting.append(row)
 report['base_mount_access']={'insertion_direction':'vertical from above (-Z)','thread':None,'hole_type':'plain through-hole','clearance_diameter_mm':5.5,'through_depth_mm':10,'washer_diameter_mm':10,'socket_head_diameter_mm':8.5,'driver_diameter_mm':11,'access_well_diameter_mm':12,'travel_samples':81,'holes':mounting,'passed':len(mounting)==4 and all(q['passed'] for q in mounting)}
 print('Base mounting access',report['base_mount_access']['passed'],flush=True)
 report['tool_access']={'probe_count':len(probes),'collisions':access,'passed':not access}
 exploded=[]
 compressed_models={}
 explosion_samples=sorted(set([round(float(t),6) for t in np.linspace(0,1,101)]+EXPLODE_KEYS))
 for t in explosion_samples:
  offsets=[explosion_offset(p,float(t)) for p in parts]
  local=max(0,min(1,(float(t)-.2)/.8));distance=200*max(0,min(1,local/.2))
  for i,m in enumerate(models):
   if parts[i].get('snapBearings'):
    compression=round(snap_compression(t),6);key=(i,compression)
    if key not in compressed_models:compressed_models[key]=fcl.CollisionObject(bvh(compressed_support(parts[i],compression) if compression else parts[i]['shape']))
    m=models[i]=compressed_models[key]
   if parts[i]['group']=='rotor':
    angle=-distance*2*math.pi/LEAD;c=math.cos(angle);ss=math.sin(angle);r=np.array([[1,0,0],[0,c,-ss],[0,ss,c]]);pivot=np.array([0.,0.,SCREW_Z]);m.setTransform(fcl.Transform(r,np.array(offsets[i])+pivot-r@pivot))
   else:m.setTransform(fcl.Transform(np.array(offsets[i])))
  for i,j in itertools.combinations(range(len(parts)),2):
   if offsets[i]==offsets[j] and (parts[i]['group']=='rotor')==(parts[j]['group']=='rotor') and not(snap_compression(t) and (parts[i].get('snapBearings') or parts[j].get('snapBearings'))):continue
   if not fcl.collide(models[i],models[j],fcl.CollisionRequest(),fcl.CollisionResult()):continue
   a=exploded_pose(parts[i],float(t));b=exploded_pose(parts[j],float(t));hit=a.intersect(b);v=hit.Volume()
   if v<.01:continue
   for seat in THREAD_JOINTS:
    if frozenset([parts[i]['name'],parts[j]['name']])==frozenset([seat['host'],seat['bolt']]):
     host_i=i if parts[i]['name']==seat['host'] else j
     ribs=ridge_material(seat['diameter'],seat['length'],seat['center'],seat['axis'],seat['start'])
     if parts[host_i]['group']=='rotor':ribs=ribs.rotate((0,0,SCREW_Z),(1,0,SCREW_Z),-distance*360/LEAD)
     ribs=ribs.translate(tuple(offsets[host_i]));v=max(0,v-overlap(hit,ribs))
   if v>.01:exploded.append({'fraction':float(t),'parts':[parts[i]['name'],parts[j]['name']],'overlap_mm3':v})
 report['explosion']={'samples':len(explosion_samples),'collisions':exploded,'passed':not exploded,'note':'Staged disassembly with synchronized screw rotation during carriage withdrawal. Extended tips straighten and split ears pinch schematically during the 12 mm bearing removal. Thread forming is schematic; plastic rib contact is bounded separately.'}
 print('Explosion collisions',exploded[:15],flush=True)
 report['valid_single_solids']=all(p['shape'].isValid() and len(p['shape'].Solids())==1 for p in parts)
 output_positions=[]
 for travel in [0,40]:
  face=pose(by_name['Hollow triangular carriage'],travel).BoundingBox().xmax
  output_positions.append({'travel_mm':travel,'output_face_x_mm':face,'extension_beyond_base_mm':face-EXIT_X})
 report['compact_layout']={'base_length_mm':EXIT_X-(-36 if PRINTED else BASE_REAR),'base_width_mm':2*HALF_WIDTH,'width_multiple':WIDTH,'output_plate_width_mm':42*WIDTH,'upper_bearing_span_mm':24*math.sqrt(3)+2*WIDEN,'retracted_overall_length_mm':EXIT_X+40,'extended_overall_length_mm':EXIT_X+80,'motor_front_x_mm':0,'bearing_station_x_mm':STATIONS,'exit_plane_x_mm':EXIT_X,'screw_end_x_mm':ROD_END,'tip_recess_at_home_mm':EXIT_X-ROD_END,'output_positions':output_positions,'passed':all(abs(q['extension_beyond_base_mm']-q['travel_mm'])<1e-5 for q in output_positions) and abs(chassis_shape.BoundingBox().xmax-EXIT_X)<1e-5}
 upper_centers=[p['shape'].Center().toTuple() for p in parts if p.get('bearing') and p['name'].startswith('625ZZ upper')]
 lower_centers=[p['shape'].Center().toTuple() for p in parts if p.get('bearing') and p['name'].startswith('625ZZ lower')]
 measured_span=max(c[1] for c in upper_centers)-min(c[1] for c in upper_centers)
 # Clear the collision-screening triangulation before exact CAD bounds.
 BRepTools.Clean_s(beam.wrapped);BRepTools.Clean_s(chassis_shape.wrapped)
 measured_width=beam.BoundingBox().ylen
 report['width_variant']={'multiple':WIDTH,'output_plate_width_mm':measured_width,'base_width_mm':chassis_shape.BoundingBox().ylen,'upper_bearing_center_span_mm':measured_span,'upper_bearing_centers_mm':upper_centers,'lower_bearing_centers_mm':lower_centers,'outward_shift_per_side_mm':WIDEN,'motor_and_screw_center_y_mm':0,'height_mm':height,'passed':abs(measured_width-42*WIDTH)<1e-5 and abs(chassis_shape.BoundingBox().ylen-2*HALF_WIDTH)<1e-5 and abs(measured_span-(24*math.sqrt(3)+2*WIDEN))<1e-5 and len(upper_centers)==4 and len(lower_centers)==LOWER_COUNT and all(min(abs(c[1]-y) for y in lower_positions(STATIONS[0] if abs(c[0]-STATIONS[0])<.01 else STATIONS[1]))<1e-5 and abs(c[2]-18)<1e-5 for c in lower_centers) and height<=68.00001}
 if PRINTED:
  light_checks=[]
  for name,shape in [('base',chassis_shape),('carriage',beam)]:
   blocked=sum(overlap(cut,shape) for cut in CUTOUTS[name]);row=dict(part=name,**LIGHTENING[name],blocked_cutouts_mm3=blocked);row['passed']=blocked<.01 and row['removed_mm3']>0;light_checks.append(row)
  motor_keepout=rect(-40,0,-22.49,22.49,21,63)
  brace_intrusion=sum(overlap(brace,motor_keepout) for brace in MOTOR_BRACES)
  report['lightening']={'checks':light_checks,'carriage_pocket_floor_mm':4,'passed':all(q['passed'] for q in light_checks) and report['running_faces']['passed']}
  report['motor_bracing']={'length_mm':42,'width_mm':12,'motor_side_margin_mm':1.5,'rear_x_mm':-36,'motor_keepout_intersection_mm3':brace_intrusion,'passed':len(MOTOR_BRACES)==2 and brace_intrusion<.01}
 report['kinematics']={'lead_mm_per_rev':8,'pitch_mm':8 if PRINTED else 2,'starts':1 if PRINTED else 4,'revolutions_over_stroke':5,'full_step_mm':.04,'sixteenth_microstep_mm':.0025,'microsteps_are_command_resolution_not_accuracy':True}
 if PRINTED:
  thread_checks=[]
  screw=by_name['Printed 20 mm lead screw with integral shaft clamp']
  for travel in [0,1,2,3,4,8,20,40]:
   thread_checks.append({'travel_mm':travel,'screw_angle_deg':-travel*360/LEAD,'overlap_mm3':overlap(pose(screw,travel),pose(by_name['Hollow triangular carriage'],travel))})
  bands=[{'home_x_mm':[lo,hi],'full_extension_x_mm':[lo+40,hi+40],'fully_engaged':lo>=30 and hi+40<=ROD_END} for lo,hi in THREAD_BANDS]
  report['printed_thread']={'major_diameter_mm':20,'root_diameter_mm':16,'lead_mm':8,'starts':1,'radial_relief_mm':.35,'axial_relief_per_flank_mm':.25,'smooth_bore_diameter_mm':21.2,'threaded_bands':bands,'checks':thread_checks,'tip_recess_mm':EXIT_X-ROD_END,'passed':all(q['overlap_mm3']<.01 for q in thread_checks) and len(bands)==2 and all(q['fully_engaged'] for q in bands) and EXIT_X-ROD_END>=3}
  print('Printed thread',report['printed_thread']['passed'],flush=True)
 report['limits']=['Geometry prototype; no stress, stiffness, fatigue or physical fit validation.',('Printed screw and female bands have real helices and synchronized motion; thread clearance is checked, but friction, wear and print fit require testing.' if PRINTED else 'T8 screw and nut use smooth fit envelopes; helical thread engagement, backlash and friction are not simulated.'),'Motor and purchased hardware dimensions are reference assumptions; confirm actual parts. No external screw-support bearings are modeled.','Bearing-block adjustment is rigid translation; clamp force, stiffness and print creep require physical testing.','Three-ridge pilot dimensions are prototype values; test forming torque and pull-out with the actual screw and print material. Unformed ridge overlap is intentional, not a simulated formed thread.']
 report['passed']=report['track_retention']['passed'] and report['carrier_heat_set_inserts']['passed'] and report['running_faces']['passed'] and (not PRINTED or (report['lightening']['passed'] and report['motor_bracing']['passed'])) and report['width_variant']['passed'] and not(collisions or motion or access or exploded) and report['adjustable_bearings']['passed'] and report['bearing_face_relief']['passed'] and report['snap_axles']['passed'] and report['lid_and_attachment']['passed'] and report['guidance']['passed'] and report['valid_single_solids'] and report['compact_layout']['passed'] and report['output_mount']['passed'] and report['base_mount_access']['passed'] and (not PRINTED or report['printed_thread']['passed'])
 save();print('Validation',report['passed'],flush=True);return report
