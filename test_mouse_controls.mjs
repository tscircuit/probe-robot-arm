import http from 'node:http';import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
process.env.TMPDIR=await fs.mkdtemp('/dev/shm/probe-mouse-');
const {chromium}=await import('./.qa/node_modules/playwright/index.mjs');
const root=path.resolve('site/dist'),errors=[];
const server=http.createServer(async(req,res)=>{try{const rel=decodeURIComponent(new URL(req.url,'http://localhost').pathname),p=path.resolve(root,'.'+(rel==='/'?'/index.html':rel));if(!p.startsWith(root+path.sep))throw Error();res.setHeader('Content-Type',({'.html':'text/html','.js':'text/javascript','.json':'application/json','.css':'text/css'})[path.extname(p)]||'application/octet-stream');res.end(await fs.readFile(p));}catch{res.writeHead(404);res.end();}});
await new Promise(r=>server.listen(4053,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1280,height:950}});page.on('pageerror',e=>errors.push(e.message));
const snapshot=()=>page.evaluate(()=>{const v=window.probeViewer||window.baseViewer;return {position:v.camera.position.toArray(),target:v.controls.target.toArray(),quaternion:v.camera.quaternion.toArray(),distance:v.camera.position.distanceTo(v.controls.target),buttons:v.controls.mouseButtons};});
const delta=(a,b)=>a.map((v,i)=>v-b[i]);const length=a=>Math.hypot(...a);
async function drag(button){await page.mouse.move(400,400);await page.mouse.down({button});await page.mouse.move(470,440,{steps:12});await page.mouse.up({button});await page.waitForTimeout(600);}
try{
 for(const url of ['http://127.0.0.1:4053/','http://127.0.0.1:4053/base-test.html']){
  await page.goto(url);await page.waitForFunction(()=>window.probeViewer||window.baseViewer,{timeout:120000});
  const before=await snapshot();assert.equal(before.buttons.MIDDLE,2);assert.equal(before.buttons.RIGHT,null);
  await drag('right');const right=await snapshot();assert.ok(length(delta(right.position,before.position))<1e-6);assert.ok(length(delta(right.target,before.target))<1e-6);await page.keyboard.press('Escape');
  await drag('middle');const pan=await snapshot(),dp=delta(pan.position,right.position),dt=delta(pan.target,right.target);
  assert.ok(length(dt)>1,'Middle drag must pan');assert.ok(length(delta(dp,dt))<1e-6,'Camera and target must translate equally');assert.ok(Math.abs(pan.distance-right.distance)<1e-6,'Middle drag must not zoom');assert.ok(length(delta(pan.quaternion,right.quaternion))<1e-6);
  await page.mouse.wheel(0,-200);await page.waitForTimeout(500);const wheel=await snapshot();assert.ok(wheel.distance<pan.distance,'Wheel zoom must remain enabled');
 }
 assert.deepEqual(errors,[]);const report={passed:true,pages:2,checks:['middle drag pans without zoom','right drag does not pan','wheel zoom remains enabled']};await fs.writeFile('output/mouse-controls-validation.json',JSON.stringify(report,null,2));console.log(report);
}finally{await browser.close();server.close();await fs.rm(process.env.TMPDIR,{recursive:true,force:true});}
