"""Conservative surfaces of revolution for circular gear/bolt clearances."""
import cadquery as cq
from .model import cyl,annulus,V,overlap,parameters

def ring_envelope():
    p=parameters();ro=p['ring_outer_radius_mm'];rb=ro-6;ri=p['module_mm']*(p['ring_teeth']/2-1)-.2;rbolt=p['ring_bolt_radius_mm']
    body=annulus(rb,ri,12,24)
    rim=cq.Solid.makeCone(rb,ro,6,V(0,0,28),V(0,0,1)).fuse(cyl(ro,6,(0,0,34))).cut(cyl(rb-.5,14,(0,0,27)))
    return body.fuse(rim,annulus(rbolt+4.5,rbolt-4.5,12.2,36))

def upward_ring_base_proof(base):
    # Covers the ring's entire upward swept volume while near the fixed base.
    # Above the base maximum no material can intersect it.
    p=parameters();ro=p['ring_outer_radius_mm'];rb=ro-6;ri=p['module_mm']*(p['ring_teeth']/2-1)-.2
    top=max(140,base.BoundingBox().zmax+1)
    swept=annulus(rb,ri,top-24,24).fuse(cq.Solid.makeCone(rb,ro,6,V(0,0,28),V(0,0,1)).cut(cyl(ri,8,(0,0,27))),annulus(ro,ri,top-34,34))
    vol=overlap(swept,base);assert vol<1e-6,vol
    return dict(proof='Ring is contained in an upward swept annular/conical envelope disjoint from fixed plate and blocks',overlap_mm3=vol)
