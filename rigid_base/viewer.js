import * as THREE from 'three';
import {loadCadJSON} from './cad-json.js';
import {OrbitControls} from 'three/addons/OrbitControls.js';
import {installPartDownloads} from './part-downloads.js';
const $=id=>document.getElementById(id), viewport=$('viewport');
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setClearColor(0xf3f5f6);viewport.prepend(renderer.domElement);
const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(35,1,.1,6000);camera.up.set(0,0,1);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.mouseButtons={LEFT:THREE.MOUSE.ROTATE,MIDDLE:THREE.MOUSE.PAN,RIGHT:null};controls.minDistance=25;controls.maxDistance=3000;
scene.add(new THREE.HemisphereLight(0xffffff,0x788591,2.8));const light=new THREE.DirectionalLight(0xffffff,2.4);light.position.set(200,-300,600);scene.add(light);
const grid=new THREE.GridHelper(800,40,0xc8d4dd,0xe2e9ed);grid.rotation.x=Math.PI/2;grid.position.z=-88.1;scene.add(grid);
const rotor=new THREE.Group(),pinion=new THREE.Group();scene.add(rotor,pinion);const meshes=[];let data,stages,cfg,menu,playing=false,start=0;
function visible(mesh){const a=mesh.userData;return (a.context?$('arm').checked:true)&&(a.keepout?$('keepouts').checked:a.reference?$('hardware').checked:true);}
function fit(){scene.updateMatrixWorld(true);const box=new THREE.Box3();for(const m of meshes)if(m.visible)box.expandByObject(m);if(box.isEmpty())return;const center=box.getCenter(new THREE.Vector3()),size=box.getSize(new THREE.Vector3());const halfFov=Math.min(THREE.MathUtils.degToRad(camera.fov/2),Math.atan(Math.tan(THREE.MathUtils.degToRad(camera.fov/2))*camera.aspect));const distance=size.length()/2/Math.sin(halfFov)*1.08;controls.target.copy(center);camera.position.copy(center).add(new THREE.Vector3(1,1.4,.8).normalize().multiplyScalar(distance));controls.update();}
function resize(){const w=viewport.clientWidth,h=viewport.clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();}new ResizeObserver(resize).observe(viewport);
function pose(){if(!data)return;const e=+$('explode').value/100,a=e?0:+$('angle').value;rotor.rotation.z=THREE.MathUtils.degToRad(a);pinion.rotation.z=rotor.rotation.z*cfg.ratio;const offsets=new Map(data.map(p=>[p.name,[0,0,0]]));const at=e*stages.length;
 for(let i=0;i<stages.length;i++){let t=Math.max(0,Math.min(1,at-i));t=t*t*(3-2*t);for(const name of stages[i].parts){const v=offsets.get(name);stages[i].delta.forEach((d,k)=>v[k]+=t*d);}}
 for(const m of meshes){const v=offsets.get(m.name);m.position.set(v[0]-(m.userData.group==='pinion'?cfg.center_mm:0),v[1],v[2]);}
 $('explodeValue').value=Math.round(e*100)+'%';$('stage').textContent=e?stages[Math.min(stages.length-1,Math.floor(at))].label:'Assembled';$('angleValue').value=a.toFixed(1)+'°';$('angle').disabled=$('play').disabled=e>0;grid.visible=!e;scene.updateMatrixWorld(true);
}
function pause(){playing=false;$('play').textContent='Animate rotation';$('play').setAttribute('aria-pressed','false');}
$('play').onclick=()=>{playing=!playing;start=performance.now();$('play').textContent=playing?'Pause':'Animate rotation';$('play').setAttribute('aria-pressed',String(playing));};
$('explode').oninput=()=>{pause();if(+$('explode').value)$('angle').value=0;pose();};$('angle').oninput=()=>{pause();pose();};$('assembled').onclick=()=>{pause();$('explode').value=$('angle').value=0;pose();fit();};$('fit').onclick=fit;
for(const id of ['arm','hardware','keepouts'])$(id).onchange=()=>{menu?.refreshVisibility();if(id==='arm')fit();};
try{
 [data,stages,cfg]=await Promise.all(['mesh.json','explosion.json','config.json'].map(name=>loadCadJSON('downloads/rigid-base/'+name,name==='mesh.json')));pinion.position.x=cfg.center_mm;
 for(const p of data){const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(p.vertices.flat(),3));g.setIndex(p.triangles.flat());g.computeVertexNormals();const mat=new THREE.MeshStandardMaterial({color:p.color,roughness:.68,metalness:p.reference?.25:.06,transparent:p.keepout,opacity:p.keepout?.18:1,depthWrite:!p.keepout});const m=new THREE.Mesh(g,mat);m.name=p.name;m.userData=p;(p.group==='rotor'?rotor:p.group==='pinion'?pinion:scene).add(m);meshes.push(m);}
 menu=installPartDownloads({THREE,canvas:renderer.domElement,camera,scene,getMeshes:()=>meshes,getPart:m=>({name:m.name,printed:m.userData.printed,keepout:m.userData.keepout,url:m.userData.printed?'downloads/rigid-base/STL/'+m.name+'.stl.gz':undefined}),isEnabled:visible,onShowAll:()=>{for(const id of ['arm','hardware','keepouts'])$(id).checked=true;}});
 pose();resize();fit();$('loading').remove();window.rigidViewer={meshes,rotor,pinion,camera,controls,menu,stages,pose,fit,renderer};
}catch(err){$('loading').textContent='Could not load CAD. Please reload.';console.error(err);}
renderer.setAnimationLoop(t=>{if(playing&&+$('explode').value===0){$('angle').value=(25*Math.sin((t-start)/4500)).toFixed(2);pose();}controls.update();renderer.render(scene,camera);});
