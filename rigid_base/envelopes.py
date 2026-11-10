"""Conservative surfaces of revolution for circular gear/bolt clearances."""
import cadquery as cq
from .model import cyl,annulus,V,overlap

def ring_envelope():
    body=annulus(106,94.8,12,24)
    rim=cq.Solid.makeCone(106,112,6,V(0,0,28),V(0,0,1)).fuse(cyl(112,6,(0,0,34))).cut(cyl(105.5,14,(0,0,27)))
    return body.fuse(rim,annulus(108.5,99.5,12.2,36))

def upward_ring_base_proof(base):
    # Covers the ring's entire upward swept volume while near the fixed base.
    # Above the base maximum no material can intersect it.
    top=max(140,base.BoundingBox().zmax+1)
    swept=annulus(106,94.8,top-24,24).fuse(cq.Solid.makeCone(106,112,6,V(0,0,28),V(0,0,1)).cut(cyl(94.8,8,(0,0,27))),annulus(112,94.8,top-34,34))
    vol=overlap(swept,base);assert vol<1e-6,vol
    return dict(proof='Ring is contained in an upward swept annular/conical envelope disjoint from fixed plate and blocks',overlap_mm3=vol)
