import http from 'node:http';import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
process.env.TMPDIR=await fs.mkdtemp('/dev/shm/width-variants-');
const {chromium}=await import('./.qa/node_modules/playwright/index.mjs');
const root=path.resolve('site/dist'),errors=[];
const server=http.createServer(async(req,res)=>{try{const pathname=new URL(req.url,'http://localhost').pathname;const p=path.resolve(root,'.'+(pathname==='/'?'/index.html':decodeURIComponent(pathname)));if(!p.startsWith(root+path.sep))throw Error();const data=await fs.readFile(p);res.setHeader('Content-Type',({'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.stl':'model/stl'})[path.extname(p)]||'application/octet-stream');res.end(data);}catch{res.writeHead(404);res.end();}});
await new Promise(r=>server.listen(4058,'127.0.0.1',r));
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
 await page.goto('http://127.0.0.1:4058/');await page.waitForFunction(()=>window.probeViewer,{timeout:120000});
 const rows=[];
 for(const width of [1,2,4]){
  await page.selectOption('#width',String(width));
  await page.waitForURL('**/?width='+width);await page.waitForFunction(w=>window.probeViewer?.config.z_width===w,width,{timeout:120000});
  assert.equal(await page.locator('#width').inputValue(),String(width));
  if(await page.evaluate(()=>window.probeViewer.state.playing))await page.locator('#play').click();
  const data=await page.evaluate(()=>{const v=window.probeViewer,m=v.modules[0].meshes,b=m.find(p=>p.userData.name==='Z_Adjustable_six-bearing_base');b.geometry.computeBoundingBox();return {width:v.config.z_width,inverted:v.config.radial_inverted,bodyWidth:b.geometry.boundingBox.max.x-b.geometry.boundingBox.min.x,outputGridHoles:v.config.z_actuator.output_holes.length,outputWidth:v.config.z_actuator.output_width,outputBolts:m.filter(p=>p.userData.name.startsWith('Z_output_mount_screw_')).length,baseBolts:m.filter(p=>p.userData.name.startsWith('Z_base_mount_screw_')).length,oldMounts:m.filter(p=>p.userData.name.startsWith('Z_top_mount_')||p.userData.name.startsWith('Z_enclosure_mount_')).length};});
  assert.equal(data.width,width);assert.equal(data.inverted,false);assert.ok(Math.abs(data.bodyWidth-({1:80,2:122,4:206}[width]))<.01);assert.equal(data.outputGridHoles,({1:4,2:8,4:12}[width]));assert.equal(data.outputWidth,({1:42,2:104,4:168}[width]));assert.equal(data.outputBolts,width===1?4:8);assert.equal(data.baseBolts,4);assert.equal(data.oldMounts,0);
  const prefix=width===4?'downloads/':'downloads/widths/z-'+width+'x/';
  for(const file of ['single-arm.zip','four-arm-platform.zip','actuator-mounts.zip','mounting-patterns.json','z-mount-validation.json']){
   assert.equal(await page.locator('a[href="'+prefix+file+'"]').count(),1);const response=await page.request.get('http://127.0.0.1:4058/'+prefix+file);assert.equal(response.status(),200);assert.ok((await response.body()).length>1000);
  }
  await page.locator('#z').evaluate(e=>{e.value=40;e.dispatchEvent(new Event('input'));});assert.equal(await page.evaluate(()=>window.probeViewer.state.values.z),20);
  await page.locator('#explode').evaluate(e=>{e.value=100;e.dispatchEvent(new Event('input'));});assert.equal(await page.locator('#play').isDisabled(),true);
  await clickPart('Z_Hollow_triangular_carriage');const downloaded=await download();const out=width===4?'output':'output/widths/z-'+width+'x';assert.deepEqual(downloaded.bytes,await fs.readFile(out+'/prototype-parts/Z_Hollow_triangular_carriage.stl'));
  await page.keyboard.press('Escape');await page.locator('#explode').evaluate(e=>{e.value=0;e.dispatchEvent(new Event('input'));});assert.equal(await page.locator('#play').isDisabled(),false);
  await page.locator('#four').click();assert.equal(await page.evaluate(()=>window.probeViewer.tipPositions.length),4);
  rows.push(data);
 }
 await page.setViewportSize({width:375,height:812});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);assert.equal(await page.locator('#width').isVisible(),true);
 await page.screenshot({path:'output/width-selector-mobile.png',fullPage:true});assert.deepEqual(errors,[]);
 const report={passed:true,variants:rows,checks:['dropdown reloads actual width geometry and fasteners','upright radial base','single Z base mounting face','selected STEP and mounting links','selected carriage STL bytes from right-click download','motion and explosion available at every width','four-arm view at every width','mobile selector visible without horizontal overflow']};await fs.writeFile('output/width-selector-validation.json',JSON.stringify(report,null,2));console.log(report);
}finally{await browser.close();server.close();await fs.rm(process.env.TMPDIR,{recursive:true,force:true});}
