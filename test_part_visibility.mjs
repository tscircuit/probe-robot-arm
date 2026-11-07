import http from 'node:http';import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
process.env.TMPDIR=await fs.mkdtemp('/dev/shm/part-visibility-');
const {chromium}=await import('./.qa/node_modules/playwright/index.mjs');
const root=path.resolve('site/dist'),errors=[];
const server=http.createServer(async(req,res)=>{try{const pathname=new URL(req.url,'http://localhost').pathname;const p=path.resolve(root,'.'+(pathname==='/'?'/index.html':decodeURIComponent(pathname)));if(!p.startsWith(root+path.sep))throw Error();const data=await fs.readFile(p);res.setHeader('Access-Control-Allow-Origin','*');res.setHeader('Content-Type',({'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.stl':'model/stl'})[path.extname(p)]||'application/octet-stream');res.end(data);}catch{res.writeHead(404);res.end();}});
await new Promise(r=>server.listen(4054,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1280,height:950},acceptDownloads:true});page.on('pageerror',e=>errors.push(e.message));
async function clickPart(name){
 const point=await page.evaluate(async name=>{
  const THREE=await import('http://127.0.0.1:4054/vendor/three.module.js');const v=window.probeViewer||window.baseViewer;
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

async function blank(){const r=await page.locator('canvas').boundingBox();await page.mouse.click(r.x+5,r.y+5,{button:'right'});await page.locator('.part-menu').waitFor({state:'visible'});assert.equal(await page.locator('.part-menu strong').textContent(),'3D view');}
async function visible(){return page.evaluate(()=>{const v=window.probeViewer||window.baseViewer;const all=[];v.scene.traverse(m=>{if(m.isMesh&&(m.userData.name||m.name)&&!m.userData.viewEdges)all.push(m);});return all.filter(m=>{for(let p=m;p;p=p.parent)if(!p.visible)return false;return true;}).map(m=>m.userData.name||m.name);});}
async function action(name){await page.locator('.part-menu [data-action="'+name+'"]').click();await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));}
async function showAll(){await blank();await action('show-all');}
try{
 await page.goto('http://127.0.0.1:4054/');await page.waitForFunction(()=>window.probeViewer,{timeout:120000});
 if(await page.evaluate(()=>window.probeViewer.state.playing))await page.locator('#play').click();
 const initial=await visible(),part='R_05_Mounting_enclosure_tray';
 await clickPart(part);await action('isolate');assert.deepEqual(await visible(),[part]);
 await page.locator('#play').click();await page.waitForTimeout(300);await page.locator('#play').click();assert.deepEqual(await visible(),[part]);
 await blank();await page.getByRole('menuitemcheckbox',{name:'Show hidden edges'}).click();assert.deepEqual(await visible(),[part]);
 await page.locator('#explode').evaluate(e=>{e.value=100;e.dispatchEvent(new Event('input'));});assert.deepEqual(await visible(),[part]);
 await page.screenshot({path:'output/isolated-arm-part.png'});
 await clickPart(part);await action('hide');assert.deepEqual(await visible(),[]);
 await blank();assert.equal(await page.locator('[data-action=isolate]').isVisible(),false);assert.equal(await page.locator('[data-action=hide]').isVisible(),false);
 await page.keyboard.press('Home');assert.equal(await page.evaluate(()=>document.activeElement.dataset.action),'show-all');await page.keyboard.press('Enter');await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));assert.deepEqual((await visible()).sort(),initial.sort());
 await clickPart('Rotating_deck');await action('hide');assert.ok(!(await visible()).includes('Rotating_deck'));await showAll();assert.ok((await visible()).includes('Rotating_deck'));
 await page.locator('#four').click();const four=await visible();assert.ok(four.length>initial.length*3);await clickPart('Main_platform');await action('isolate');assert.deepEqual(await visible(),['Main_platform']);await showAll();assert.equal((await visible()).length,four.length);assert.equal(await page.evaluate(()=>window.probeViewer.state.four),true);
 for(const url of ['http://127.0.0.1:4054/base-test.html','file://'+path.resolve('output/armature-base-test-v4/VIEWER.html')]){
  await page.goto(url);await page.waitForFunction(()=>window.baseViewer,{timeout:120000});
  await clickPart('Fixed_base_plate');await action('isolate');assert.deepEqual(await visible(),['Fixed_base_plate']);
  await page.locator('#hardware').uncheck();await page.locator('#hardware').check();await page.locator('#keepouts').check();assert.deepEqual(await visible(),['Fixed_base_plate']);
  await page.evaluate(()=>window.baseViewer.setProgress(1));assert.deepEqual(await visible(),['Fixed_base_plate']);
  await clickPart('Fixed_base_plate');await action('hide');assert.deepEqual(await visible(),[]);await page.locator('#fit').click();
  await showAll();assert.equal((await visible()).length,await page.evaluate(()=>window.baseViewer.parts.length));assert.ok(await page.locator('#hardware').isChecked());assert.ok(await page.locator('#keepouts').isChecked());
 }
 await page.setViewportSize({width:390,height:844});await page.waitForTimeout(300);await blank();const b=await page.locator('.part-menu').boundingBox();assert.ok(b.x>=0&&b.x+b.width<=390&&b.y+b.height<=844);await page.keyboard.press('Escape');
 assert.deepEqual(errors,[]);const report={passed:true,checks:['isolate one selected instance','hide selected and last remaining part','Show All works on empty canvas and restores current view','visibility persists during axis animation and explosion','four-arm and platform instance visibility','hardware and clearance toggles respect isolation; Show All resets them','hidden edges respect hidden parents','keyboard menu recovery','mobile menu fits viewport','hosted and offline base viewers','no browser errors']};await fs.writeFile('output/part-visibility-validation.json',JSON.stringify(report,null,2));console.log(report);
}finally{await browser.close();server.close();await fs.rm(process.env.TMPDIR,{recursive:true,force:true});}
