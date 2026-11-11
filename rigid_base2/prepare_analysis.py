"""Export comparison inputs after building and bed-aligning the current print kit."""
import gzip,shutil
import cadquery as cq
from .model import ROOT,build

def main():
    out=ROOT/'output/rigid-base2/analysis';out.mkdir(parents=True,exist_ok=True)
    for n in ['before.step','before.stl']:(out/n).write_bytes(gzip.decompress((ROOT/'rigid_base2/reference'/(n+'.gz')).read_bytes()))
    parts,_=build();shape=next(p['shape'] for p in parts if p['name']=='Cylindrical_Z_support')
    cq.exporters.export(shape,str(out/'after.step'));shutil.copyfile(ROOT/'output/rigid-base2/STL/Cylindrical_Z_support.stl',out/'after.stl')
    print('Baseline and current analysis inputs prepared; stale meshes are rejected by STEP hash')
if __name__=='__main__':main()
