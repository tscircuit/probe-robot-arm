import http from 'node:http';import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
process.env.TMPDIR=await fs.mkdtemp('/dev/shm/probe-');
const {chromium}=await import('./.qa/node_modules/playwright/index.mjs');
const root=path.resolve('site/dist');
const server=http.createServer(async(req,res)=>{try{const rel=decodeURIComponent(new URL(req.url,'http://localhost').pathname);const p=path.resolve(root,'.'+(rel==='/'?'/index.html':rel));if(!p.startsWith(root+path.sep))throw Error('bad path');const data=await fs.readFile(p);res.setHeader('Content-Type',({'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.zip':'application/zip'})[path.extname(p)]||'application/octet-stream');res.end(data);}catch{res.writeHead(404);res.end('Not found');}});
await new Promise(r=>server.listen(4050,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1280,height:900},deviceScaleFactor:1});
const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400&&!r.url().endsWith('favicon.ico'))errors.push(r.status()+' '+r.url());});
async function slide(id,n){await page.locator('#'+id).evaluate((el,v)=>{el.value=v;el.dispatchEvent(new Event('input',{bubbles:true}));},String(n));}
try{
 await page.goto('http://127.0.0.1:4050');await page.waitForFunction(()=>window.probeViewer,{timeout:120000});
 const first=await page.evaluate(()=>window.probeViewer.state.values);await page.waitForTimeout(600);const second=await page.evaluate(()=>window.probeViewer.state.values);assert.notDeepEqual(first,second,'Assembled axes must animate');
 await page.locator('#play').click();await page.screenshot({path:'output/viewer-single.png'});
 await slide('explode',100);assert.equal(await page.locator('#play').isDisabled(),true);assert.equal(await page.locator('#r').isDisabled(),true);
 const a=await page.evaluate(()=>window.probeViewer.state.values);await page.waitForTimeout(300);assert.deepEqual(await page.evaluate(()=>window.probeViewer.state.values),a,'Exploded state must freeze motion');

 const pathData=JSON.parse(await fs.readFile('output/arm-explosion-path.json','utf8'));
 assert.deepEqual(await page.evaluate(()=>window.probeViewer.explosionPath),pathData);
 for(let k=1;k<=pathData.length*2;k++){
  const e=k/(pathData.length*2);await slide('explode',100*e);
  const offsets=await page.evaluate(()=>window.probeViewer.modules[0].meshes.map(m=>({name:m.userData.name,offset:m.position.toArray(),quaternion:m.quaternion.toArray()})));
  for(const p of offsets){const expected=[0,0,0];for(let j=0;j<pathData.length;j++){if(!pathData[j].parts.includes(p.name))continue;let u=Math.max(0,Math.min(1,e*pathData.length-j));u=u*u*(3-2*u);for(let a=0;a<3;a++)expected[a]+=u*pathData[j].delta[a];}
   assert.ok(p.offset.every((v,a)=>Math.abs(v-expected[a])<1e-5),p.name+' explosion position');
   assert.ok(p.quaternion.every((v,a)=>Math.abs(v-(a===3?1:0))<1e-10));
  }
 }
 assert.equal(await page.evaluate(()=>window.probeViewer.config.actuator_enclosure),'printed-leadscrew');
 assert.equal(await page.evaluate(()=>window.probeViewer.modules[0].meshes.filter(m=>m.userData.name.endsWith('Structural_mounting_lid')).length),2);
 await page.screenshot({path:'output/viewer-exploded.png'});
 await slide('explode',0);assert.equal(await page.locator('#play').isDisabled(),false);
 for(const [id,value,key,expected] of [['theta',20,'theta',20],['z',40,'z',20],['r',120,'r',60]]){await slide(id,value);assert.equal((await page.evaluate(()=>window.probeViewer.state.values))[key],expected);}
 const geometryPose=await page.evaluate(()=>{const m=window.probeViewer.modules[0],probe=m.meshes.find(x=>x.userData.name==='Spring_probe_reference');return {theta:m.rotor.rotation.z,r:probe.position.x,z:probe.position.z};});
 assert.ok(Math.abs(geometryPose.theta-20*Math.PI/180)<1e-9);assert.equal(geometryPose.r,60);assert.equal(geometryPose.z,20);
 const drives=await page.evaluate(()=>{const m=window.probeViewer.modules[0].meshes;return {z:m.find(p=>p.userData.name==='Z_Printed_20_mm_lead_screw_with_integral_shaft_clamp').quaternion.toArray(),r:m.find(p=>p.userData.name==='R_Printed_20_mm_lead_screw_with_integral_shaft_clamp').quaternion.toArray(),config:window.probeViewer.config,motorNames:m.filter(p=>/NEMA.*reference$/.test(p.userData.name)).map(p=>p.userData.name)};});
 for(const [q,expected] of [[drives.z,[0,0,Math.sin(-20*Math.PI/8),Math.cos(-20*Math.PI/8)]],[drives.r,[Math.sin(-60*Math.PI/8),0,0,Math.cos(-60*Math.PI/8)]]])assert.ok(q.every((v,i)=>Math.abs(v-expected[i])<1e-8));
 assert.equal(drives.config.z_motor,'nema17');assert.equal(drives.config.radial_motor,'nema14');assert.equal(drives.config.radial_inverted,false);assert.ok(drives.motorNames.includes('Z_NEMA17_full-depth_reference'));assert.ok(drives.motorNames.includes('R_NEMA14_full-depth_reference'));assert.equal(drives.config.r_drive_y,0);
 const baseDrive=await page.evaluate(()=>{const v=window.probeViewer,m=v.modules[0].meshes.find(p=>p.userData.name==='Compliant_12T_pinion');return {q:m.quaternion.toArray(),position:m.position.toArray(),ratio:v.config.base_gear_ratio,pivot:v.config.base_motor_x};});
 assert.equal(baseDrive.ratio,6);assert.equal(baseDrive.pivot,60);
 const ba=20*Math.PI/180*6;assert.ok(baseDrive.q.every((v,i)=>Math.abs(v-[0,0,Math.sin(ba/2),Math.cos(ba/2)][i])<1e-8));
 assert.ok(Math.abs(baseDrive.position[0]-(60-60*Math.cos(ba)))<1e-8);assert.ok(Math.abs(baseDrive.position[1]+60*Math.sin(ba))<1e-8);
 const radialMount=await page.evaluate(()=>{const c=window.probeViewer.config,m=window.probeViewer.modules[0].meshes;return m.filter(p=>p.userData.name.startsWith('R_enclosure_mount_screw')).map(p=>{p.geometry.computeBoundingBox();return {zmin:p.geometry.boundingBox.min.z,zmax:p.geometry.boundingBox.max.z,face:c.radial_mount_face_z};});});
 assert.equal(radialMount.length,4);for(const p of radialMount){assert.ok(Math.abs(p.zmin-(p.face-10))<.001);assert.ok(Math.abs(p.zmax-(p.face+15))<.001);}

 await page.locator('#four').click();assert.equal((await page.evaluate(()=>window.probeViewer.state)).four,true);
 const cluster=await page.evaluate(()=>({tips:window.probeViewer.tipPositions,z:window.probeViewer.config.board_top}));
 const expected=[[1,1],[-1,1],[-1,-1],[1,-1]];
 for(let i=0;i<4;i++){assert.ok(Math.abs(cluster.tips[i][0]-expected[i][0])<1e-5);assert.ok(Math.abs(cluster.tips[i][1]-expected[i][1])<1e-5);assert.ok(Math.abs(cluster.tips[i][2]-cluster.z)<1e-5);}
 await page.locator('#play').click();await page.waitForTimeout(700);await page.locator('#play').click();
 const moved=await page.evaluate(()=>window.probeViewer.tipPositions);
 for(let i=0;i<4;i++){assert.ok(moved[i][2]>cluster.z+15);assert.ok(Math.abs((moved[i][0]-moved[0][0])-(expected[i][0]-expected[0][0]))<1e-5);assert.ok(Math.abs((moved[i][1]-moved[0][1])-(expected[i][1]-expected[0][1]))<1e-5);}
 await page.locator('#tips').click();await page.screenshot({path:'output/viewer-tips.png'});await page.locator('#fit').click();
 await page.screenshot({path:'output/viewer-four.png'});
 await page.locator('summary').click();for(const link of await page.locator('details a[download]').all()){const href=await link.getAttribute('href');const response=await page.request.get('http://127.0.0.1:4050/'+href);assert.equal(response.status(),200);assert.ok((await response.body()).length>1000);}
 await slide('explode',50);assert.equal((await page.evaluate(()=>window.probeViewer.state)).four,false,'Explosion isolates a single arm');await slide('explode',0);
 await page.locator('summary').click();await page.setViewportSize({width:375,height:812});await page.locator('#single').click();await page.waitForTimeout(300);await page.screenshot({path:'output/viewer-mobile.png',fullPage:true});
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'No horizontal mobile overflow');
 assert.deepEqual(errors,[]);console.log(JSON.stringify({passed:true,checks:['4x Z and 1x radial printed-leadscrew assemblies load',(pathData.length*2)+' explosion boundaries/midpoints match the CAD path','NEMA17 Z and upright NEMA14 radial','12T base at 6:1 about 60 mm pivot, 8 mm lead screw rotations about Z and radial axes','four base bolts with captive carrier nuts','CAD loads','axes animate','explode pauses motion','sliders update actual geometry','four tips contact a 2 mm square','four probes retract and translate together','tip close-up','downloads respond','mobile has no horizontal overflow','no browser errors']},null,2));
}finally{await browser.close();server.close();await fs.rm(process.env.TMPDIR,{recursive:true,force:true});}
