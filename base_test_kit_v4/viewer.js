import * as THREE from './vendor/three.module.js';
import {OrbitControls} from './vendor/OrbitControls.js';
import {installPartDownloads} from './viewer_part_downloads.js';
const payload=JSON.parse(document.querySelector('#cad-data').textContent),parts=payload.parts,stages=payload.stages;
const scene=new THREE.Scene();scene.background=new THREE.Color('#f3f5f6');
const camera=new THREE.PerspectiveCamera(38,1,.1,4000);camera.up.set(0,0,1);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;document.querySelector('#viewport').append(renderer.domElement);
const controls=new OrbitControls(camera,renderer.domElement);controls.mouseButtons={LEFT:THREE.MOUSE.ROTATE,MIDDLE:THREE.MOUSE.PAN,RIGHT:null};controls.enableDamping=true;controls.minDistance=80;controls.maxDistance=2500;
scene.add(new THREE.HemisphereLight(0xffffff,0x647382,2.1));const light=new THREE.DirectionalLight(0xffffff,2.8);light.position.set(180,-220,400);scene.add(light);
const grid=new THREE.GridHelper(700,28,0xc5ced5,0xe1e7eb);grid.rotation.x=Math.PI/2;grid.position.z=-89;scene.add(grid);
const rotor=new THREE.Group(),pinion=new THREE.Group();pinion.position.x=60;scene.add(rotor,pinion);
const meshes=new Map(),bounds=new Map();
for(const p of parts){const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(p.vertices.flat(),3));geo.setIndex(p.triangles.flat());geo.computeVertexNormals();geo.computeBoundingBox();bounds.set(p.name,geo.boundingBox.clone());
 if(p.group==='pinion')geo.translate(-60,0,0);
 const mat=new THREE.MeshStandardMaterial({color:p.color,metalness:p.reference?.35:.08,roughness:.55,transparent:p.keepout,opacity:p.keepout?.18:1});
 const mesh=new THREE.Mesh(geo,mat);mesh.name=p.name;mesh.userData=p;mesh.visible=!p.keepout;
 (p.group==='rotor'?rotor:p.group==='pinion'?pinion:scene).add(mesh);meshes.set(p.name,mesh);
}
const $=id=>document.getElementById(id);let progress=0,theta=0,playing=false,last=performance.now();
function getOffsets(t){const o=Object.fromEntries(parts.map(p=>[p.name,[0,0,0]]));const at=Math.max(0,Math.min(1,t))*stages.length;
 for(let i=0;i<stages.length;i++){let u=Math.max(0,Math.min(1,at-i));u=u*u*(3-2*u);for(const n of stages[i].parts)for(let k=0;k<3;k++)o[n][k]+=u*stages[i].delta[k];}return o;}
const sweepBounds=new THREE.Box3();for(let i=0;i<=stages.length;i++){const o=getOffsets(i/stages.length);for(const p of parts)if(!p.keepout)sweepBounds.union(bounds.get(p.name).clone().translate(new THREE.Vector3(...o[p.name])));}
function fit(all=false){const b=all?sweepBounds.clone():new THREE.Box3();if(!all){scene.updateMatrixWorld(true);for(const mesh of meshes.values())if(mesh.visible)b.expandByObject(mesh);}if(b.isEmpty())return;
 const center=b.getCenter(new THREE.Vector3()),dir=new THREE.Vector3(1.2,-1.7,1.15).normalize(),right=new THREE.Vector3().crossVectors(camera.up,dir).normalize(),up=new THREE.Vector3().crossVectors(dir,right).normalize();
 const tanV=Math.tan(THREE.MathUtils.degToRad(camera.fov/2)),tanH=tanV*camera.aspect;let distance=0;
 for(const x of [b.min.x,b.max.x])for(const y of [b.min.y,b.max.y])for(const z of [b.min.z,b.max.z]){const v=new THREE.Vector3(x,y,z).sub(center);distance=Math.max(distance,v.dot(dir)+Math.abs(v.dot(right))/tanH,v.dot(dir)+Math.abs(v.dot(up))/tanV);}
 controls.target.copy(center);camera.position.copy(center).add(dir.multiplyScalar(distance*1.08));controls.update();}
function update(){grid.position.z=progress?sweepBounds.min.z-2:-89;const o=getOffsets(progress);for(const [name,m] of meshes)m.position.set(...o[name]);rotor.rotation.z=progress?0:THREE.MathUtils.degToRad(theta);pinion.rotation.z=progress?0:THREE.MathUtils.degToRad(theta*6);
 $('explodeValue').textContent=Math.round(progress*100)+'%';$('angleValue').textContent=theta.toFixed(1)+'°';$('angle').value=theta;
 $('play').disabled=progress>0;$('angle').disabled=progress>0;$('play').textContent=playing?'Pause rotation':'Animate rotation';
 $('stage').textContent=progress===0?'Assembled':progress===1?'Fully exploded':stages[Math.min(stages.length-1,Math.floor(progress*stages.length))].label;
 scene.updateMatrixWorld(true);}
function setProgress(v){const was=progress;progress=Math.max(0,Math.min(1,v));if(progress){theta=0;playing=false;}$('explode').value=progress*100;update();if((was===0)!==(progress===0))fit(progress>0);}
$('explode').oninput=e=>setProgress(+e.target.value/100);$('angle').oninput=e=>{theta=+e.target.value;playing=false;update();};$('play').onclick=()=>{if(!progress){playing=!playing;update();}};$('fit').onclick=()=>fit(progress>0);
$('assembled').onclick=()=>setProgress(0);$('hardware').onchange=()=>viewMenu.refreshVisibility();$('keepouts').onchange=()=>viewMenu.refreshVisibility();
const web=location.protocol!=='file:';if(!web)$('download').hidden=true;const prefix=web?'downloads/base-v4/':'';
if(!web){document.querySelector('#assemblyPage').href='https://modular-flying-probe-arm.seveibar.chatgpt.site/';document.querySelector('#basePage').href='https://modular-flying-probe-arm.seveibar.chatgpt.site/base-test.html';}
const viewMenu=installPartDownloads({THREE,canvas:renderer.domElement,camera,scene,getMeshes:()=>[...meshes.values()],getPart:mesh=>({name:mesh.name,printed:!!mesh.userData.printFile,keepout:mesh.userData.keepout,url:mesh.userData.printFile?prefix+mesh.userData.printFile:null,filename:mesh.userData.printFile?.split('/').pop()}),onSelect:()=>{playing=false;update();},isEnabled:mesh=>mesh.userData.keepout?$('keepouts').checked:!mesh.userData.reference||$('hardware').checked,onShowAll:()=>{$('hardware').checked=true;$('keepouts').checked=true;requestAnimationFrame(()=>fit(progress>0));}});
$('guide').href=prefix+'PRINT_AND_ASSEMBLY.pdf';$('staticReport').href=prefix+'validation.json';$('explosionReport').href=prefix+'explosion_validation.json';
const ray=new THREE.Raycaster(),mouse=new THREE.Vector2();renderer.domElement.addEventListener('pointermove',e=>{const rect=renderer.domElement.getBoundingClientRect();mouse.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);ray.setFromCamera(mouse,camera);const hit=ray.intersectObjects([...meshes.values()].filter(x=>x.visible),false)[0];$('partName').textContent=hit?hit.object.name.replaceAll('_',' '):'Drag to orbit · right-click a part to download';});
function resize(){const r=$('viewport').getBoundingClientRect();camera.aspect=r.width/r.height;camera.updateProjectionMatrix();renderer.setSize(r.width,r.height);}
new ResizeObserver(resize).observe($('viewport'));resize();update();fit();
window.baseViewer={scene,camera,controls,meshes,parts,stages,getOffsets,setProgress,get state(){return {progress,theta,playing};}};
renderer.setAnimationLoop(t=>{const dt=Math.min(.05,(t-last)/1000);last=t;if(playing&&!progress){theta=(theta+dt*12)%360;update();}controls.update();renderer.render(scene,camera);});
