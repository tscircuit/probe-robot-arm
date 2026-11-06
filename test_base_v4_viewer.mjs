import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
process.env.TMPDIR=await fs.mkdtemp('/dev/shm/base-v4-');
const {chromium}=await import('./.qa/node_modules/playwright/index.mjs');
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1280,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto('file://'+path.resolve('output/armature-base-test-v4/VIEWER.html'));await page.waitForFunction(()=>window.baseViewer,{timeout:120000});
 const paths=JSON.parse(await fs.readFile('output/armature-base-test-v4/explosion_path.json','utf8'));
 assert.deepEqual(await page.evaluate(()=>window.baseViewer.stages),paths);
 const progressValues=[0,...paths.flatMap((_,i)=>[(i+.5)/paths.length,(i+1)/paths.length])];
 for(const t of progressValues){
  const expected={};for(let i=0;i<paths.length;i++){let u=Math.max(0,Math.min(1,t*paths.length-i));u=u*u*(3-2*u);for(const n of paths[i].parts){expected[n]??=[0,0,0];for(let k=0;k<3;k++)expected[n][k]+=u*paths[i].delta[k];}}
  const actual=await page.evaluate(t=>{const v=window.baseViewer;v.setProgress(t);return v.parts.map(p=>{const m=v.meshes.get(p.name),a=m.geometry.getAttribute('position'),pt=m.position.clone().set(a.getX(0),a.getY(0),a.getZ(0));m.localToWorld(pt);return {name:p.name,offset:m.position.toArray(),vertex:pt.toArray(),source:p.vertices[0]};});},t);
  for(const p of actual)for(let k=0;k<3;k++){assert.ok(Math.abs(p.offset[k]-(expected[p.name]?.[k]||0))<1e-7,p.name);assert.ok(Math.abs(p.vertex[k]-(p.source[k]+(expected[p.name]?.[k]||0)))<1e-4,p.name+' world mesh');}
 }
 assert.equal(await page.locator('#play').isDisabled(),true);assert.equal(await page.locator('#angle').isDisabled(),true);
 await page.screenshot({path:'output/base-v4-viewer-exploded.png'});
 await page.locator('#assembled').click();await page.screenshot({path:'output/base-v4-viewer-assembled.png'});
 await page.locator('#angle').evaluate(el=>{el.value='10';el.dispatchEvent(new Event('input'));});
 const pinionState=await page.evaluate(()=>{const p=window.baseViewer.meshes.get('Compliant_12T_pinion').parent;return {angle:p.rotation.z,x:p.position.x};});
 assert.ok(Math.abs(pinionState.angle-Math.PI/3)<1e-9);assert.equal(pinionState.x,60);
 await page.locator('#play').click();await page.waitForTimeout(400);assert.ok((await page.evaluate(()=>window.baseViewer.state.theta))>0);await page.locator('#play').click();
 await page.locator('#explode').evaluate(el=>{el.value='50';el.dispatchEvent(new Event('input'));});
 const state=await page.evaluate(()=>window.baseViewer.state);assert.equal(state.progress,.5);assert.equal(state.theta,0);assert.equal(state.playing,false);
 const visibleBefore=await page.evaluate(()=>[...window.baseViewer.meshes.values()].filter(x=>x.visible).length);await page.locator('#hardware').uncheck();assert.ok((await page.evaluate(()=>[...window.baseViewer.meshes.values()].filter(x=>x.visible).length))<visibleBefore);await page.locator('#hardware').check();
 await page.setViewportSize({width:390,height:844});await page.locator('#assembled').click();await page.screenshot({path:'output/base-v4-viewer-mobile.png'});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 assert.deepEqual(errors,[]);const report={passed:true,checked_viewer_states:progressValues.length,checks:['viewer path matches CAD-checked path','actual mesh positions at all stage boundaries and midpoints','rotation disabled and reset during explosion','assembled axis animation','hardware toggle','mobile width','no browser errors']};await fs.writeFile('output/armature-base-test-v4/viewer_validation.json',JSON.stringify(report,null,2));console.log(report);
}finally{await browser.close();await fs.rm(process.env.TMPDIR,{recursive:true,force:true});}
