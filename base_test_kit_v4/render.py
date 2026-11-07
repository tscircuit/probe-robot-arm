"""Draw actual tessellated CAD for the assembly instructions."""
import argparse,json,pathlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
ap=argparse.ArgumentParser();ap.add_argument('directory');args=ap.parse_args();root=pathlib.Path(args.directory)
parts=json.loads((root/'preview_mesh.json').read_text())
fig=plt.figure(figsize=(16,10),facecolor='#f4f6f7')
ax=fig.add_subplot(121,projection='3d');bx=fig.add_subplot(122,projection='3d')
from explosion import offsets
stages=json.loads((root/'explosion_path.json').read_text())
final_offsets=offsets(parts,stages,1)
def offset(p):return np.array(final_offsets[p['name']])
for a,exploded in [(ax,False),(bx,True)]:
    all_tri=[];all_colors=[]
    for p in parts:
        if p['keepout']:continue
        if p['name'].startswith(('M3_','M3x','M5_','M5x','M6')):continue
        vs=np.array(p['vertices'])+(offset(p) if exploded else 0)
        tri=vs[np.array(p['triangles'])]
        n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12)
        shade=.60+.40*np.abs(n@np.array([.3,-.4,.866]));color=np.array(matplotlib.colors.to_rgb(p['color']))
        all_tri.append(tri);all_colors.append(np.clip(shade[:,None]*color,0,1))
    a.add_collection3d(Poly3DCollection(np.concatenate(all_tri),facecolors=np.concatenate(all_colors),edgecolors='none',rasterized=True))
    a.set_facecolor('#f4f6f7');a.set_axis_off();a.view_init(29,-53)
    a.set(xlim=(-350,240) if exploded else (-115,125),ylim=(-320,120) if exploded else (-110,110),zlim=(-280,320) if exploded else (-100,80))
    a.set_box_aspect((590,440,600) if exploded else (240,220,180))
ax.set_title('ASSEMBLED · one independent rotary base',fontsize=14,pad=10)
bx.set_title('CHECKED EXPLOSION · hardware omitted for clarity',fontsize=14,pad=10)
fig.suptitle('LIGHTWEIGHT BASE + DECK / FOUR 45° ROLLERS',fontsize=21,y=.96)
fig.text(.5,.065,'200 × 200 mm stand  •  2 × 6002 + 4 × 625ZZ  •  Direct NEMA17 mount  •  12T / 72T drive',ha='center',fontsize=12)
fig.text(.5,.035,'Actual CAD geometry. Unloaded prototype test; print fits and running clearance must be checked.',ha='center',fontsize=10,color='#52616d')
fig.savefig(root/'ASSEMBLY_PREVIEW.png',dpi=150,bbox_inches='tight');print('Preview written')
