import http from 'node:http';import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
process.env.TMPDIR=await fs.mkdtemp('/dev/shm/hidden-edges-');
const {chromium}=await import('./.qa/node_modules/playwright/index.mjs');
const root=path.resolve('site/dist'),errors=[];
const server=http.createServer(async(req,res)=>{try{const pathname=new URL(req.url,'http://localhost').pathname,p=path.resolve(root,'.'+(pathname==='/'?'/index.html':decodeURIComponent(pathname)));if(!p.startsWith(root+path.sep))throw Error();res.setHeader('Content-Type',({'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json'})[path.extname(p)]||'application/octet-stream');res.end(await fs.readFile(p));}catch{res.writeHead(404);res.end();}});
await new Promise(r=>server.listen(4052,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1280,height:950}});page.on('pageerror',e=>errors.push(e.message));
async function openBlank(){const rect=await page.locator('canvas').boundingBox();await page.mouse.click(rect.x+8,rect.y+8,{button:'right'});await page.getByRole('menuitemcheckbox',{name:'Show hidden edges'}).waitFor();assert.equal(await page.locator('.part-menu strong').textContent(),'3D view');assert.equal(await page.locator('[data-action=download]').isVisible(),false);}
async function stats(){return page.evaluate(()=>{const v=window.probeViewer||window.baseViewer,meshes=window.probeViewer?v.modules.flatMap(m=>m.meshes):[...v.meshes.values()];const overlays=meshes.flatMap(m=>m.children.filter(c=>c.userData.viewEdges));return {count:overlays.length,visible:overlays.filter(o=>o.visible).length,allAttached:overlays.every(o=>o.parent.isMesh),allDepthTested:overlays.every(o=>o.children.every(l=>l.material.depthTest&&!l.material.depthWrite)),dashed:overlays.every(o=>o.children[0].material.isLineDashedMaterial),sourceTriangles:meshes.reduce((a,m)=>a+m.geometry.getIndex().count,0)};});}
try{
 await page.goto('http://127.0.0.1:4052/');await page.waitForFunction(()=>window.probeViewer);
 if(await page.evaluate(()=>window.probeViewer.state.playing))await page.locator('#play').click();
 await openBlank();assert.equal(await page.getByRole('menuitemcheckbox').getAttribute('aria-checked'),'false');const initial=await stats();assert.equal(initial.count,0);
 await page.getByRole('menuitemcheckbox').click();const active=await stats();assert.ok(active.count>0&&active.visible===active.count&&active.allAttached&&active.allDepthTested&&active.dashed);assert.equal(active.sourceTriangles,initial.sourceTriangles);
 await page.screenshot({path:'output/hidden-edges-arm.png'});
 await page.locator('#four').click();await page.locator('#play').click();await page.waitForTimeout(300);await page.locator('#play').click();assert.equal((await stats()).count,active.count);
 await page.locator('#explode').evaluate(el=>{el.value='65';el.dispatchEvent(new Event('input'));});assert.equal((await stats()).visible,active.count);
 await openBlank();await page.keyboard.press('Enter');assert.equal((await stats()).visible,0);
 await openBlank();await page.getByRole('menuitemcheckbox').click();assert.equal((await stats()).count,active.count,'No duplicate overlays');
 await page.reload();await page.waitForFunction(()=>window.probeViewer);assert.equal((await stats()).visible,active.count,'Preference applied after asynchronous CAD load');
 await page.locator('.page-nav a').filter({hasText:'Base test'}).click();await page.waitForFunction(()=>window.baseViewer);assert.ok((await stats()).visible>0);
 await page.screenshot({path:'output/hidden-edges-base.png'});
 await page.evaluate(()=>window.baseViewer.setProgress(.7));assert.ok((await stats()).visible>0);
 await page.locator('#hardware').uncheck();assert.ok(await page.evaluate(()=>[...window.baseViewer.meshes.values()].filter(m=>m.userData.reference&&!m.userData.keepout).every(m=>!m.visible&&m.children.every(o=>o.parent===m))));
 await openBlank();await page.keyboard.press('Enter');assert.equal((await stats()).visible,0);
 await page.setViewportSize({width:390,height:844});await page.waitForTimeout(300);await page.waitForFunction(()=>document.querySelector('canvas').getBoundingClientRect().width<=390);const r=await page.locator('canvas').boundingBox();await page.mouse.click(r.x+r.width-5,r.y+r.height/2,{button:'right'});await page.locator('.part-menu').waitFor({state:'visible'});const b=await page.locator('.part-menu').boundingBox();assert.ok(b.x>=0&&b.x+b.width<=390&&b.y+b.height<=844);await page.keyboard.press('Escape');assert.equal(await page.locator('.part-menu').isVisible(),false);
 await page.goto('file://'+path.resolve('output/armature-base-test-v4/VIEWER.html'));await page.waitForFunction(()=>window.baseViewer);await openBlank();await page.getByRole('menuitemcheckbox').click();assert.ok((await stats()).visible>0,'Offline viewer toggle');
 assert.deepEqual(errors,[]);const report={passed:true,checks:['blank-space context menu','accessible checkbox and keyboard toggle','depth-tested dashed occluded edges','overlays follow parent motion, explosion and visibility','source geometry untouched','no duplicate overlays','preference persists across reload and both pages','mobile menu stays in viewport','offline viewer toggle','no browser errors']};await fs.writeFile('output/hidden-edges-validation.json',JSON.stringify(report,null,2));console.log(report);
}finally{await browser.close();server.close();await fs.rm(process.env.TMPDIR,{recursive:true,force:true});}
