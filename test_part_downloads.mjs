import http from 'node:http';import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
process.env.TMPDIR=await fs.mkdtemp('/dev/shm/part-downloads-');
const {chromium}=await import('./.qa/node_modules/playwright/index.mjs');
const root=path.resolve('site/dist'),errors=[];
const server=http.createServer(async(req,res)=>{try{const pathname=new URL(req.url,'http://localhost').pathname;const p=path.resolve(root,'.'+(pathname==='/'?'/index.html':decodeURIComponent(pathname)));if(!p.startsWith(root+path.sep))throw Error();const data=await fs.readFile(p);res.setHeader('Content-Type',({'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.stl':'model/stl'})[path.extname(p)]||'application/octet-stream');res.end(data);}catch{res.writeHead(404);res.end();}});
await new Promise(r=>server.listen(4051,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1280,height:950},acceptDownloads:true});page.on('pageerror',e=>errors.push(e.message));
async function clickPart(name){
 const point=await page.evaluate(async name=>{
  const THREE=await import('/vendor/three.module.js');const v=window.probeViewer||window.baseViewer;
  const meshes=window.probeViewer?[...v.modules.flatMap(m=>m.meshes),...v.scene.children.filter(x=>x.type==='Group').flatMap(g=>g.children.filter(x=>x.isMesh))]:[...v.meshes.values()];
  const visible=m=>{for(let p=m;p;p=p.parent)if(!p.visible)return false;return true;};
  const all=[...new Set(meshes)].filter(visible),mesh=all.find(m=>(m.userData.name||m.name)===name);if(!mesh)throw Error('Missing '+name);
  v.scene.updateMatrixWorld(true);v.camera.updateMatrixWorld(true);const rect=document.querySelector('canvas').getBoundingClientRect(),pos=mesh.geometry.getAttribute('position'),idx=mesh.geometry.index,ray=new THREE.Raycaster();
  const count=(idx?idx.count:pos.count)/3,step=Math.max(1,Math.floor(count/800));
  for(let i=0;i<count;i+=step){const p=new THREE.Vector3();for(let j=0;j<3;j++)p.add(new THREE.Vector3().fromBufferAttribute(pos,idx?idx.getX(i*3+j):i*3+j));p.divideScalar(3);mesh.localToWorld(p);p.project(v.camera);if(Math.abs(p.x)>.97||Math.abs(p.y)>.97)continue;
   const x=Math.round(rect.left+(p.x+1)*rect.width/2),y=Math.round(rect.top+(1-p.y)*rect.height/2);let interior=true;const inset=name==='Fixed_base_plate'?2:0;for(const dx of [-inset,0,inset])for(const dy of [-inset,0,inset]){ray.setFromCamera(new THREE.Vector2((x+dx-rect.left)/rect.width*2-1,-(y+dy-rect.top)/rect.height*2+1),v.camera);if(ray.intersectObjects(all,false)[0]?.object!==mesh)interior=false;}if(interior)return {x,y};}
  throw Error('No exposed triangle for '+name);
 },name);
 await page.mouse.click(point.x,point.y,{button:'right'});await page.locator('.part-menu').waitFor({state:'visible'});assert.equal(await page.locator('.part-menu strong').textContent(),name.replaceAll('_',' '));
}
async function download(){const event=page.waitForEvent('download');await page.locator('.part-menu [data-action=download]').click();const d=await event;const bytes=await fs.readFile(await d.path());assert.ok(bytes.length>84);return {bytes,name:d.suggestedFilename()};}
try{
 await page.goto('http://127.0.0.1:4051/');await page.waitForFunction(()=>window.probeViewer);
 if((await page.evaluate(()=>window.probeViewer.state.playing)))await page.locator('#play').click();
 assert.equal(await page.locator('.page-nav a').count(),2);assert.equal(await page.locator('.page-nav [aria-current=page]').textContent(),'Assembly');
 const printed=await page.evaluate(()=>window.probeViewer.modules[0].meshes.filter(m=>m.userData.printed).map(m=>m.userData.name));
 for(const name of printed)assert.equal((await page.request.get('http://127.0.0.1:4051/downloads/parts/'+encodeURIComponent(name)+'.stl')).status(),200);
 const name='R_05_Mounting_enclosure_tray';await clickPart(name);const assembled=await download();assert.deepEqual(assembled.bytes,await fs.readFile('output/prototype-parts/'+name+'.stl'));
 await page.locator('#explode').evaluate(e=>{e.value=100;e.dispatchEvent(new Event('input'));});await clickPart(name);const exploded=await download();assert.deepEqual(exploded.bytes,assembled.bytes,'Explosion cannot alter downloaded part');
 for(const part of ['Z_support','Rotating_deck','Z_to_radial_carrier','Z_04_Beveled_compliant_rack','Compliant_12T_pinion']){await clickPart(part);const file=await download();assert.deepEqual(file.bytes,await fs.readFile('output/prototype-parts/'+part+'.stl'));}
 await page.keyboard.press('Escape');await page.locator('#four').click();await clickPart('Main_platform');const frame=await download();assert.equal(frame.name,'Main_platform_reference.stl');assert.equal(frame.bytes.length,84+50*frame.bytes.readUInt32LE(80));
 await page.locator('.page-nav a').filter({hasText:'Base test'}).click();await page.waitForFunction(()=>window.baseViewer);
 assert.equal(await page.locator('.page-nav [aria-current=page]').textContent(),'Base test');
 const baseParts=await page.evaluate(()=>window.baseViewer.parts.filter(p=>p.printFile).map(p=>p.printFile));assert.equal(baseParts.length,10);
 for(const file of baseParts)assert.equal((await page.request.get('http://127.0.0.1:4051/downloads/base-v4/'+file)).status(),200);
 await clickPart('Fixed_base_plate');const base=await download();assert.equal(base.name,'01_cutout_base_four_45deg_axles_qty1.stl');assert.deepEqual(base.bytes,await fs.readFile('output/armature-base-test-v4/STL/01_cutout_base_four_45deg_axles_qty1.stl'));
 await clickPart('Integrated_stand');const stand=await download();assert.deepEqual(stand.bytes,await fs.readFile('output/armature-base-test-v4/STL/02_integrated_stand_qty1.stl'));
 await page.evaluate(()=>window.baseViewer.setProgress(1));await clickPart('6002_bearing_18');const bearing=await download();assert.equal(bearing.bytes.length,84+50*bearing.bytes.readUInt32LE(80));assert.ok(bearing.name.endsWith('_reference.stl'));
 await clickPart('Internal_72T_ring');const ring=await download();assert.equal(ring.name,'11_ring_176mm_45deg_track_qty1.stl');assert.deepEqual(ring.bytes,await fs.readFile('output/armature-base-test-v4/STL/11_ring_176mm_45deg_track_qty1.stl'));
 await clickPart('Fixed_spindle');const spindle=await download();assert.equal(spindle.name,'05_fixed_spindle_15p25_chamfer0p5_qty1.stl');assert.deepEqual(spindle.bytes,await fs.readFile('output/armature-base-test-v4/STL/05_fixed_spindle_15p25_chamfer0p5_qty1.stl'));
 await clickPart('Inner_race_spacer');const spacer=await download();assert.equal(spacer.name,'06_inner_race_spacer_15p8_bore_qty1.stl');assert.deepEqual(spacer.bytes,await fs.readFile('output/armature-base-test-v4/STL/06_inner_race_spacer_15p8_bore_qty1.stl'));
 await clickPart('Integrated_stand');await page.keyboard.press('Escape');assert.equal(await page.locator('.part-menu').isVisible(),false);
 await page.locator('.page-nav a').filter({hasText:'Assembly',exact:true}).click();await page.waitForFunction(()=>window.probeViewer);
 await page.setViewportSize({width:390,height:844});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await page.screenshot({path:'output/part-downloads-mobile.png',fullPage:true});
 assert.deepEqual(errors,[]);const report={passed:true,main_print_files:printed.length,base_print_files:baseParts.length,checks:['right-click selects actual visible meshes','STL bytes match original print files','current cradle, deck, U carrier and through-bolt rack downloads','explosion-independent downloads','reference binary STL','platform parts selectable','both directions of top page navigation','Escape closes menu','mobile width','no browser errors']};await fs.writeFile('output/part-download-validation.json',JSON.stringify(report,null,2));console.log(report);
}finally{await browser.close();server.close();await fs.rm(process.env.TMPDIR,{recursive:true,force:true});}
