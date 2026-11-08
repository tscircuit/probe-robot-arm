import * as THREE from 'three';
import { OrbitControls } from 'three/addons/OrbitControls.js';
import {installPartDownloads} from './part-downloads.js';

const $=id=>document.getElementById(id), viewport=$('viewport');
const scene=new THREE.Scene(); scene.background=new THREE.Color('#f3f5f6');
const camera=new THREE.PerspectiveCamera(34,1,1,5000); camera.up.set(0,0,1);
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:false});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;
viewport.prepend(renderer.domElement);
const controls=new OrbitControls(camera,renderer.domElement);controls.mouseButtons={LEFT:THREE.MOUSE.ROTATE,MIDDLE:THREE.MOUSE.PAN,RIGHT:null};controls.enableDamping=true;controls.dampingFactor=.08;
controls.minDistance=100;controls.maxDistance=2400;
scene.add(new THREE.HemisphereLight(0xffffff,0x9faebb,2.4));
const light=new THREE.DirectionalLight(0xffffff,3);light.position.set(200,-350,500);scene.add(light);
const fill=new THREE.DirectionalLight(0xffffff,1);fill.position.set(-250,100,200);scene.add(fill);
const grid=new THREE.GridHelper(600,24,0xd0d9df,0xe3e8ec);grid.rotation.x=Math.PI/2;grid.position.z=-.1;scene.add(grid);
const modules=[], pickables=[];
let config, explosionPath, ready=false, four=false, exploding=0, playing=!matchMedia('(prefers-reduced-motion: reduce)').matches,phase=0;
let values={theta:0,z:0,r:0};
const referenceGroup=new THREE.Group();scene.add(referenceGroup);referenceGroup.visible=false;
const raycaster=new THREE.Raycaster(), pointer=new THREE.Vector2();
const viewMenu=installPartDownloads({THREE,canvas:renderer.domElement,camera,scene,getMeshes:()=>pickables,getPart:mesh=>({name:mesh.userData.name,printed:mesh.userData.printed,keepout:mesh.userData.keepout,url:mesh.userData.printed?'downloads/parts/'+encodeURIComponent(mesh.userData.name)+'.stl':null}),onSelect:()=>{playing=false;setPlay();},onShowAll:()=>requestAnimationFrame(fit)});
function explosionVector(p,e){
  const v=[0,0,0],t=e*explosionPath.length;
  for(let i=0;i<explosionPath.length;i++){
    const stage=explosionPath[i];if(!stage.parts.includes(p.name))continue;
    let u=Math.max(0,Math.min(1,t-i));u=u*u*(3-2*u);
    for(let k=0;k<3;k++)v[k]+=stage.delta[k]*u;
  }
  return v;
}
const zAxis=new THREE.Vector3(0,0,1),xAxis=new THREE.Vector3(1,0,0);
function around(mesh,pivot,axis,angle){
  mesh.quaternion.setFromAxisAngle(axis,angle);
  mesh.position.copy(pivot).sub(pivot.clone().applyQuaternion(mesh.quaternion));
}
function transformModule(mod,theta,z,r,e){
  mod.rotor.rotation.z=theta*Math.PI/180;
  for(const mesh of mod.meshes){
    const p=mesh.userData,g=p.group;
    mesh.position.set(0,0,0);mesh.quaternion.identity();
    if(g==='base_drive')around(mesh,new THREE.Vector3(config.base_motor_x,0,0),zAxis,theta*Math.PI/180*config.base_gear_ratio);
    if(g==='z_drive')around(mesh,new THREE.Vector3(0,0,config.z_origin),zAxis,-z*2*Math.PI/config.lead_mm);
    if(g==='r_drive')around(mesh,new THREE.Vector3(config.h_origin,0,config.r_drive_z),xAxis,-r*2*Math.PI/config.lead_mm);
    if(g==='r_rack')mesh.position.x+=r;
    if(['z_rack','r_rack','r_drive'].includes(g))mesh.position.z+=z;
    if(e){const v=explosionVector(p,e);mesh.position.add(new THREE.Vector3(...v));}
  }
}
function targets(){const h=config.probe_cluster_pitch/2,x=values.theta,y=values.r;return [[x+h,y+h],[x-h,y+h],[x-h,y-h],[x+h,y-h]];}
function targetPose(i,target){const [x,y,a]=config.mounts[i],dx=target[0]-x,dy=target[1]-y;return {theta:((Math.atan2(dy,dx)*180/Math.PI-a+540)%360)-180,r:Math.hypot(dx,dy)-config.tip_radius,z:values.z};}
function update(){
  if(!ready)return;
  modules.forEach((m,i)=>{
    m.root.visible=four||i===0;
    if(four){const [x,y,a]=config.mounts[i];m.root.position.set(x,y,0);m.root.rotation.z=a*Math.PI/180;}
    else {m.root.position.set(0,0,0);m.root.rotation.z=0;}
    const v=four?targetPose(i,targets()[i]):values;
    transformModule(m,exploding?0:v.theta,exploding?0:v.z,exploding?0:v.r,exploding);
  });
  referenceGroup.visible=four;
  grid.position.z=(four?config.platform_ground_z:Math.min(-60,config.platform_ground_z))-.1-25*exploding;
}
function fit(){
  scene.updateMatrixWorld(true);
  const bounds=new THREE.Box3();
  for(const mesh of pickables.filter(viewMenu.isVisible))bounds.expandByObject(mesh);
  if(bounds.isEmpty())return;
  const size=bounds.getSize(new THREE.Vector3());bounds.getCenter(controls.target);
  const fov=Math.min(camera.fov*Math.PI/180,2*Math.atan(Math.tan(camera.fov*Math.PI/360)*camera.aspect));
  const distance=size.length()/2/Math.sin(fov/2)*1.07;
  camera.position.copy(controls.target).add(new THREE.Vector3(1,-1.3,.8).normalize().multiplyScalar(distance));
  controls.maxDistance=Math.max(2400,distance*3);camera.far=Math.max(5000,distance*5);camera.updateProjectionMatrix();
  controls.update();
}
function setPlay(){
  $('play').textContent=playing?'Pause':'Animate';$('play').setAttribute('aria-pressed',String(playing));
  $('play').disabled=!!exploding||!ready;
}
function labels(){
  $('theta-value').textContent=values.theta.toFixed(1)+(four?' mm':'°');
  $('z-value').textContent=(values.z+20).toFixed(1)+' mm';
  $('r-value').textContent=(values.r+(four?0:config.radial_stroke/2)).toFixed(1)+' mm';
  $('theta').value=values.theta;$('z').value=values.z+20;$('r').value=values.r+(four?0:config.radial_stroke/2);
}
$('single').onclick=()=>switchView(false);$('four').onclick=()=>switchView(true);
function switchView(isFour){
  if(isFour&&exploding){$('explode').value='0';$('explode').dispatchEvent(new Event('input'));}
  four=isFour;phase=0;values={theta:0,z:four?-20:0,r:0};
  $('single').setAttribute('aria-pressed',String(!four));$('four').setAttribute('aria-pressed',String(four));
  const tx=(config.pcb_width-config.probe_cluster_pitch)/2,ty=(config.pcb_depth-config.probe_cluster_pitch)/2;
  $('theta').min=four?-tx:-30;$('theta').max=four?tx:30;$('r').min=four?-ty:0;$('r').max=four?ty:config.radial_stroke;
  $('theta-label').textContent=four?'Target X':'Rotation';$('r-label').textContent=four?'Target Y':'Radial';
  ['all','theta','z','r'].forEach((v,i)=>$('animation').options[i].textContent=(four?['Probe together','Target X','Lift together','Target Y']:['All axes','Rotation','Vertical','Radial'])[i]);
  $('hint').textContent=four?'2 × 2 mm tips · right-click a part to download':'Drag to orbit · right-click a part to download';
  labels();update();fit();
}
$('fit').onclick=fit;
$('tips').onclick=()=>{if(exploding){$('explode').value='0';$('explode').dispatchEvent(new Event('input'));}if(!four)switchView(true);playing=false;setPlay();values={theta:0,z:-20,r:0};labels();update();controls.target.set(0,0,config.board_top+14);camera.position.set(85,-115,config.board_top+95);controls.update();};
$('play').onclick=()=>{playing=!playing;setPlay();};
$('explode').oninput=()=>{
  const was=exploding;exploding=Number($('explode').value)/100;
  if(exploding&&four)switchView(false);
  $('explode-value').textContent=Math.round(exploding*100)+'%';
  $('explosion-state').textContent=exploding?explosionPath[Math.min(explosionPath.length-1,Math.floor(exploding*explosionPath.length))].label:'Assembled';
  for(const id of ['theta','z','r','animation'])$(id).disabled=!!exploding;
  setPlay();update();fit();
};
for(const id of ['theta','z','r'])$(id).oninput=()=>{
  playing=false;setPlay();values[id]=Number($(id).value)-(id==='z'?20:id==='r'&&!four?config.radial_stroke/2:0);labels();update();
};
new ResizeObserver(()=>{const w=viewport.clientWidth,h=viewport.clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();if(ready)fit();}).observe(viewport);
renderer.domElement.addEventListener('pointermove',event=>{
  if(event.buttons||!ready)return;const b=renderer.domElement.getBoundingClientRect();
  pointer.set((event.clientX-b.left)/b.width*2-1,-(event.clientY-b.top)/b.height*2+1);raycaster.setFromCamera(pointer,camera);
  const hit=raycaster.intersectObjects(pickables.filter(viewMenu.isVisible),false).find(h=>h.object.userData.module===undefined?four:h.object.parent.parent.visible&&(four||h.object.userData.module===0));
  $('part-name').textContent=hit?hit.object.userData.name.replaceAll('_',' '):'';
});
renderer.domElement.addEventListener('pointerleave',()=>{$('part-name').textContent='';});
try{
  const responses=await Promise.all([fetch('arm-mesh.json'),fetch('parameters-resolved.json'),fetch('platform-mesh.json'),fetch('arm-explosion-path.json')]);
  if(responses.some(r=>!r.ok))throw Error('Assembly files unavailable');
  const [data,p,platform,path]=await Promise.all(responses.map(r=>r.json()));config=p;explosionPath=path;
  $('r').max=config.radial_stroke;
  const geometries=data.map(p=>{const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(p.vertices.flat(),3));g.setIndex(p.triangles.flat());g.computeVertexNormals();return g;});
  const materials=data.map(p=>new THREE.MeshStandardMaterial({color:p.color,roughness:.52,metalness:/shaft|625ZZ|6002|axle|washer|nut|probe/i.test(p.name)?.55:.08,transparent:!!p.keepout,opacity:p.keepout?.18:1,depthWrite:!p.keepout}));
  for(let i=0;i<4;i++){
    const root=new THREE.Group(),rotor=new THREE.Group();root.add(rotor);scene.add(root);
    const mod={root,rotor,meshes:[]};
    data.forEach((p,j)=>{const mesh=new THREE.Mesh(geometries[j],materials[j]);mesh.userData={...p,module:i};delete mesh.userData.vertices;delete mesh.userData.triangles;
      (['fixed','base_drive'].includes(p.group)?root:rotor).add(mesh);mod.meshes.push(mesh);pickables.push(mesh);});
    modules.push(mod);
  }
  for(const part of platform){const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(part.vertices.flat(),3));g.setIndex(part.triangles.flat());g.computeVertexNormals();const mesh=new THREE.Mesh(g,new THREE.MeshStandardMaterial({color:part.color,roughness:.7}));mesh.userData={name:part.name,reference:true};referenceGroup.add(mesh);pickables.push(mesh);}
  viewMenu.refresh();ready=true;$('loading').hidden=true;setPlay();labels();update();fit();
  window.probeViewer={scene,camera,controls,modules,config,explosionPath,get tipPositions(){scene.updateMatrixWorld(true);return modules.map(m=>m.meshes.find(x=>x.userData.name==='Spring_probe_reference').localToWorld(new THREE.Vector3(config.tip_radius,0,config.probe_mount_z-config.probe_drop)).toArray());},get state(){return {four,exploding,playing,values:{...values}};}};
}catch(error){$('loading').textContent='Could not load the 3D assembly. Reload to try again.';console.error(error);}
let last=performance.now();
renderer.setAnimationLoop(now=>{
  const dt=Math.min((now-last)/1000,.05);last=now;
  if(ready&&playing&&!exploding){phase+=dt;const axis=$('animation').value;
    if(four&&axis==='all'){
      const stops=[[0,0],[25,25],[-25,25],[-25,-25],[25,-25]],k=Math.floor(phase/12),t=phase/12-k;
      const start=stops[k%stops.length],end=stops[(k+1)%stops.length];
      const ease=x=>{x=Math.max(0,Math.min(1,x));return x*x*(3-2*x);},u=ease(t/.35);
      values.theta=start[0]+(end[0]-start[0])*u;values.r=start[1]+(end[1]-start[1])*u;
      const lift=t<.35?20:t<.5?20*(1-ease((t-.35)/.15)):t<.7?0:t<.85?20*ease((t-.7)/.15):20;
      values.z=lift-20;
    }else{
      const a=phase*.45;
      if(axis==='all'||axis==='theta')values.theta=(four?25:24)*Math.sin(a);
      if(axis==='all'||axis==='z')values.z=20*Math.sin(a*.8);
      if(axis==='all'||axis==='r')values.r=(four?25:config.radial_stroke/2)*Math.sin(a*.7);
      if(four&&axis!=='z')values.z=0;
    }
    labels();update();
  }
  controls.update();renderer.render(scene,camera);
});
