/** View options and per-part STL downloads. Exports use neutral source geometry. */
export function installPartDownloads({THREE,canvas,camera,scene,getMeshes,getPart,onSelect}) {
  const style=document.createElement('style');
  style.textContent='.part-menu{position:fixed;z-index:1000;max-width:min(330px,calc(100vw - 20px));padding:12px;background:#fff;color:#293843;border:1px solid #d4dde3;border-radius:8px;box-shadow:0 8px 28px #182b4020;font:13px system-ui,sans-serif}.part-menu[hidden],.part-menu [hidden]{display:none}.part-menu strong{display:block;overflow-wrap:anywhere;font-weight:550}.part-menu small{display:block;margin:5px 0 10px;color:#70808c}.part-menu button{display:block;width:100%;text-align:left;padding:9px 12px;border:1px solid #d4dde3;border-radius:5px;background:#f3f5f6;color:inherit;font:inherit;cursor:pointer}.part-menu button+button{margin-top:7px}.part-menu button[aria-checked="true"]::before{content:"✓ ";font-weight:700}.part-menu button:hover{background:#e6edf1}.part-menu button:focus-visible{outline:2px solid #517e99;outline-offset:2px}';
  document.head.append(style);
  const menu=document.createElement('div');menu.className='part-menu';menu.hidden=true;menu.setAttribute('role','menu');menu.setAttribute('aria-label','3D view options');
  const title=document.createElement('strong'),note=document.createElement('small'),button=document.createElement('button');
  button.type='button';button.textContent='Download STL';button.setAttribute('role','menuitem');button.dataset.action='download';
  const edgeButton=document.createElement('button');edgeButton.type='button';edgeButton.textContent='Show hidden edges';edgeButton.setAttribute('role','menuitemcheckbox');
  menu.append(title,note,button,edgeButton);document.body.append(menu);
  const preferenceKey='probe-viewer-hidden-edges';let hiddenEdges=false;
  try{hiddenEdges=localStorage.getItem(preferenceKey)==='true';}catch{}
  const edgeGeometry=new WeakMap(),overlays=new Map();
  const hiddenMaterial=new THREE.LineDashedMaterial({color:0x47677e,transparent:true,opacity:.48,depthTest:true,depthFunc:THREE.GreaterDepth,depthWrite:false,dashSize:2,gapSize:1.5});
  const visibleMaterial=new THREE.LineBasicMaterial({color:0x304957,transparent:true,opacity:.45,depthTest:true,depthFunc:THREE.LessEqualDepth,depthWrite:false});
  function refresh(){
    for(const mesh of getMeshes()){
      if(mesh.userData.keepout)continue;
      let group=overlays.get(mesh);
      if(hiddenEdges&&!group){
        let geometry=edgeGeometry.get(mesh.geometry);
        if(!geometry){
          geometry=new THREE.EdgesGeometry(mesh.geometry,20);
          // Shared edge geometry and line distances are computed once per source mesh.
          const lines=new THREE.LineSegments(geometry);lines.computeLineDistances();edgeGeometry.set(mesh.geometry,geometry);
        }
        group=new THREE.Group();group.name='View_edge_overlay';group.userData.viewEdges=true;
        for(const [material,order] of [[hiddenMaterial,1000],[visibleMaterial,1001]]){
          const lines=new THREE.LineSegments(geometry,material);lines.renderOrder=order;lines.raycast=()=>{};group.add(lines);
        }
        mesh.add(group);overlays.set(mesh,group);
      }
      if(group)group.visible=hiddenEdges;
    }
    edgeButton.setAttribute('aria-checked',String(hiddenEdges));
  }
  edgeButton.onclick=()=>{hiddenEdges=!hiddenEdges;refresh();try{localStorage.setItem(preferenceKey,String(hiddenEdges));}catch{}close();canvas.focus({preventScroll:true});};
  refresh();
  const ray=new THREE.Raycaster(),pointer=new THREE.Vector2();let selection=null;
  function visible(mesh){for(let p=mesh;p;p=p.parent)if(!p.visible)return false;return true;}
  function pick(e){const rect=canvas.getBoundingClientRect();pointer.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);scene.updateMatrixWorld(true);ray.setFromCamera(pointer,camera);return ray.intersectObjects(getMeshes().filter(visible),false)[0]?.object;}
  function close(){menu.hidden=true;selection=null;}
  canvas.addEventListener('pointerdown',e=>{if(e.button===2&&pick(e))e.stopImmediatePropagation();},true);
  canvas.addEventListener('contextmenu',e=>{
    e.preventDefault();const mesh=pick(e);
    if(mesh)onSelect?.(mesh);selection=mesh?{mesh,...getPart(mesh)}:null;
    title.textContent=selection?selection.name.replaceAll('_',' '):'3D view';
    button.hidden=note.hidden=!selection;
    note.textContent=selection?(selection.note||(selection.keepout?'Clearance envelope · mm':selection.printed?'Prototype part · mm':'Reference part · mm')):'';
    menu.hidden=false;menu.style.left='0px';menu.style.top='0px';
    const box=menu.getBoundingClientRect();menu.style.left=Math.max(10,Math.min(e.clientX,innerWidth-box.width-10))+'px';menu.style.top=Math.max(10,Math.min(e.clientY,innerHeight-box.height-10))+'px';(selection?button:edgeButton).focus({preventScroll:true});
  });
  button.onclick=()=>{
    if(!selection)return;const {mesh,name,url,filename,printed,keepout}=selection;
    const a=document.createElement('a');let objectURL;
    a.href=url||(objectURL=URL.createObjectURL(new Blob([binarySTL(THREE,mesh.geometry,name)],{type:'model/stl'})));
    a.download=filename||name.replace(/[^a-zA-Z0-9_.-]/g,'_')+(url||printed?'':keepout?'_clearance':'_reference')+'.stl';
    document.body.append(a);a.click();a.remove();if(objectURL)setTimeout(()=>URL.revokeObjectURL(objectURL),30000);close();canvas.focus({preventScroll:true});
  };
  document.addEventListener('pointerdown',e=>{if(!menu.contains(e.target))close();});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!menu.hidden){close();canvas.focus({preventScroll:true});}});
  menu.addEventListener('keydown',e=>{
    const items=[button,edgeButton].filter(item=>!item.hidden),index=items.indexOf(document.activeElement);
    if(['ArrowDown','ArrowUp','Home','End'].includes(e.key)){
      e.preventDefault();items[e.key==='Home'?0:e.key==='End'?items.length-1:(index+(e.key==='ArrowDown'?1:items.length-1))%items.length].focus();
    }
  });
  addEventListener('resize',close);addEventListener('scroll',close,true);
  canvas.tabIndex=0;
  return {close,refresh,get hiddenEdges(){return hiddenEdges;}};
}

function binarySTL(THREE,geometry,name){
  const position=geometry.getAttribute('position'),index=geometry.getIndex(),count=(index?index.count:position.count)/3;
  const buffer=new ArrayBuffer(84+50*count),view=new DataView(buffer);
  new Uint8Array(buffer,0,80).set(new TextEncoder().encode('STL mm '+name).slice(0,80));view.setUint32(80,count,true);
  geometry.computeBoundingBox();const center=geometry.boundingBox.getCenter(new THREE.Vector3());center.z=geometry.boundingBox.min.z;
  const a=new THREE.Vector3(),b=new THREE.Vector3(),c=new THREE.Vector3(),normal=new THREE.Vector3(),edge=new THREE.Vector3();
  let offset=84;
  for(let i=0;i<count;i++){
    [a,b,c].forEach((v,j)=>v.fromBufferAttribute(position,index?index.getX(i*3+j):i*3+j).sub(center));
    normal.subVectors(b,a).cross(edge.subVectors(c,a)).normalize();
    for(const vector of [normal,a,b,c])for(const value of [vector.x,vector.y,vector.z]){view.setFloat32(offset,value,true);offset+=4;}
    view.setUint16(offset,0,true);offset+=2;
  }
  return buffer;
}
