"""Comparative small-strain solid FEA. mm, N, MPa; assumed effective material.
Not a strength certification or an infill/layer/bearing/joint model.
"""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='2'
import argparse,json,hashlib,pathlib,time
import numpy as np
import gmsh,meshio
from skfem import MeshTet,ElementTetP1,ElementVector,Basis,asm
from skfem.models.elasticity import linear_elasticity,lame_parameters
from scipy.sparse.linalg import cg
import pyamg
ROOT=pathlib.Path(__file__).resolve().parent.parent
OUT=ROOT/'output/rigid-base2/analysis'

def mesh(step,size):
    path=step.with_name(step.stem+f'-h{size:g}.msh')
    digest=hashlib.sha256(step.read_bytes()).hexdigest();stamp=path.with_suffix('.sha256')
    if path.exists() and stamp.exists() and stamp.read_text()==digest:return path
    gmsh.initialize();gmsh.option.setNumber('General.NumThreads',2)
    gmsh.model.occ.importShapes(str(step));gmsh.model.occ.synchronize()
    gmsh.option.setNumber('Mesh.MeshSizeMin',size*.35);gmsh.option.setNumber('Mesh.MeshSizeMax',size)
    gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',12);gmsh.option.setNumber('Mesh.MeshSizeExtendFromBoundary',0)
    gmsh.option.setNumber('Mesh.Algorithm3D',1);gmsh.option.setNumber('Mesh.Optimize',1)
    gmsh.model.mesh.generate(3);gmsh.write(str(path));gmsh.finalize();stamp.write_text(digest);return path

def run(label,size):
    start=time.time();step=OUT/(label+'.step');path=mesh(step,size)
    raw=meshio.read(path);tet=np.concatenate([c.data for c in raw.cells if c.type=='tetra']);m=MeshTet(raw.points.T,tet.T)
    basis=Basis(m,ElementVector(ElementTetP1()),intorder=1);lam,mu=lame_parameters(1000,.35)
    print(label,size,'nodes',m.p.shape[1],'tets',m.t.shape[1],flush=True)
    K=asm(linear_elasticity(lam,mu),basis).tocsr();pts=m.p.T
    mounts=json.loads((ROOT/'rigid_base/parameters.json').read_text())['support_mounts_mm']+[[0,-138]]
    anchor=np.zeros(len(pts),bool)
    for x,y in mounts:anchor|=((pts[:,0]-x)**2+(pts[:,1]-y)**2<=8**2)&(abs(pts[:,2]-56.2)<1e-4)
    fixed=basis.nodal_dofs[:,anchor].ravel();free=np.setdiff1d(np.arange(basis.N),fixed)
    assert anchor.sum()>20
    boundary=m.facets[:,m.boundary_facets()].T;v=pts[boundary];centers=v.mean(axis=1);areas=np.linalg.norm(np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0]),axis=1)/2
    patches=[];patch_meta=[]
    for x,z in [(-77.5,236.7),(77.5,236.7),(-77.5,360.7),(77.5,360.7)]:
        mask=(abs(v[:,:,1]+42).max(axis=1)<1e-4)&((centers[:,0]-x)**2+(centers[:,2]-z)**2<7.5**2)
        w=np.zeros(len(pts));np.add.at(w,boundary[mask].ravel(),np.repeat(areas[mask]/3,3));assert w.sum()>20
        patches.append(w/w.sum());patch_meta.append(dict(x=x,z=z,area_mm2=float(w.sum()),nodes=int(np.count_nonzero(w))))
    # Six rigid-body modes improve the elastic multigrid preconditioner.
    x,y,z=(pts-pts.mean(axis=0)).T
    A=K[free][:,free].tocsr()
    modes=np.zeros((basis.N,6))
    for d in range(3):modes[basis.nodal_dofs[d],d]=1
    modes[basis.nodal_dofs[1],3]=-z;modes[basis.nodal_dofs[2],3]=y
    modes[basis.nodal_dofs[0],4]=z;modes[basis.nodal_dofs[2],4]=-x
    modes[basis.nodal_dofs[0],5]=-y;modes[basis.nodal_dofs[1],5]=x
    ml=pyamg.smoothed_aggregation_solver(A,B=modes[free],symmetry='symmetric',max_coarse=150);M=ml.aspreconditioner();del modes
    results=[];fields={}
    scenarios={'radial_10N':[(2.5,0,0)]*4,'normal_10N':[(0,2.5,0)]*4,'payload_20N_150mm':[(0,0,-5-3000*p['x']/(4*77.5**2)) for p in patch_meta],'yaw_1Nm':[(0,1000*p['x']/(4*77.5**2),0) for p in patch_meta]}
    for name,loads in scenarios.items():
        f=np.zeros(basis.N)
        for weights,force in zip(patches,loads):
            for d in range(3):f[basis.nodal_dofs[d]]+=weights*force[d]
        residuals=[]
        ufree,flag=cg(A,f[free],M=M,rtol=1e-8,atol=1e-12,maxiter=1800,callback=lambda x:residuals.append(0))
        assert flag==0,(name,'unconverged CG',flag)
        u=np.zeros(basis.N);u[free]=ufree;disp=u[basis.nodal_dofs].T
        residual=float(np.linalg.norm((K@u-f)[free])/np.linalg.norm(f[free]));assert residual<1e-6
        strain=basis.interpolate(u).grad.mean(axis=-1);strain=(strain+strain.swapaxes(0,1))/2
        tr=np.einsum('iik->k',strain);stress=2*mu*strain+lam*np.eye(3)[:,:,None]*tr
        dev=stress-np.eye(3)[:,:,None]*np.einsum('iik->k',stress)[None,None,:]/3;vm=np.sqrt(1.5*np.einsum('ijk,ijk->k',dev,dev))
        patch_disps=np.array([w@disp for w in patches]);reaction=(K@u-f)[basis.nodal_dofs].T
        forces=np.sum(f[basis.nodal_dofs],axis=1);reaction_sum=reaction[anchor].sum(axis=0);assert np.linalg.norm(forces+reaction_sum)<1e-4
        row=dict(case=name,mount_patch_mean_displacements_mm=patch_disps.tolist(),largest_mount_displacement_mm=float(np.linalg.norm(patch_disps,axis=1).max()),maximum_displacement_mm=float(np.linalg.norm(disp,axis=1).max()),strain_energy_Nmm=float(.5*u@(K@u)),peak_von_mises_MPa=float(vm.max()),element_p95_von_mises_MPa=float(np.percentile(vm,95)),linear_residual=residual,cg_iterations=len(residuals),load_force_N=forces.tolist(),reaction_force_N=reaction_sum.tolist())
        results.append(row);fields[name]=disp
        print(label,size,name,'max mount mm',row['largest_mount_displacement_mm'],'peak MPa',row['peak_von_mises_MPa'],'iterations',len(residuals),flush=True)
    report=dict(label=label,mesh_size_mm=size,nodes=len(pts),tetrahedra=len(tet),effective_E_MPa=1000,poisson_ratio=.35,fixed_nodes=int(anchor.sum()),boundary='All DOFs fixed on bottom-face nodes within 8 mm of each of ten bolt centres. Rigid deck, no contact or bolt slip.',patches=patch_meta,cases=results,elapsed_s=time.time()-start,step_sha256=hashlib.sha256(step.read_bytes()).hexdigest(),limits=['Homogeneous isotropic linear material at assumed E=1 GPa; not measured filament or infill properties.','Linear tetrahedra require mesh-sensitivity assessment; peak stress at sharp edges/constraints is not a design allowable.','No plasticity, creep, layer delamination, screw/insert compliance, vibration modes or fatigue.','Loads are stated design comparisons, not measured machine loads.'])
    (OUT/f'{label}-h{size:g}.json').write_text(json.dumps(report,indent=2));np.savez_compressed(OUT/f'{label}-h{size:g}-fields.npz',points=pts,**fields)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('label',choices=['before','after']);p.add_argument('--size',type=float,default=6);a=p.parse_args();run(a.label,a.size)
