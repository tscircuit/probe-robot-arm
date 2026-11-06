import hashlib,json,math,pathlib
import cadquery as cq
ROOT=pathlib.Path(__file__).resolve().parent
V=cq.Vector

def box(x, y, z, c):
    return cq.Workplane("XY").box(x, y, z).translate(c).val()

def cyl(r, h, c=(0, 0, 0), axis=(0, 0, 1)):
    return cq.Solid.makeCylinder(r, h, V(*c), V(*axis))

def annulus(ro, ri, h, z):
    return cyl(ro, h, (0, 0, z)).cut(cyl(ri, h, (0, 0, z)))

def union(shapes):
    first, *rest = shapes
    return first.fuse(*rest).clean() if rest else first

def holes(shape, points, r, z, height):
    return shape.cut(*[cyl(r, height, (x, y, z)) for x, y in points]).clean()

def overlap(a, b):
    x, y = a.BoundingBox(), b.BoundingBox()
    if any(getattr(x, k+"max") <= getattr(y, k+"min")+1e-6 or
           getattr(y, k+"max") <= getattr(x, k+"min")+1e-6 for k in "xyz"):
        return 0.0
    return max(0.0, a.intersect(b).Volume())

def inv(r, rb):
    return math.sqrt(max(0, (r/rb)**2-1))-math.acos(min(1, rb/r))

def polar(r, t):
    return (r*math.cos(t), r*math.sin(t))

def pinion_profile(m, n, pa, preload=0):
    rp=m*n/2; rb=rp*math.cos(math.radians(pa)); rr=rp-1.25*m; ra=rp+m
    def half(r):
        return math.pi/(2*n)+preload/rp+inv(rp,rb)-inv(max(r,rb),rb)
    pts=[]
    for i in range(n):
        t=2*math.pi*i/n
        rs=[rr]+[rb+(ra-rb)*k/24 for k in range(25)]
        pts += [polar(r,t-half(r)) for r in rs]
        pts += [polar(r,t+half(r)) for r in reversed(rs)]
    return cq.Workplane("XY").polyline(pts).close().extrude(12).val(), half

def base_drive_center(p):
    return p['gear_module']*(p['ring_teeth']-p['pinion_teeth'])/2

def base_drive_cache(p):
    settings={k:p[k] for k in ['gear_module','pinion_teeth','ring_teeth','pressure_angle','tooth_preload','base_tooth_slot_fraction']}
    return ROOT/'cache'/('base-drive-r8-'+hashlib.sha256(json.dumps(settings,sort_keys=True).encode()).hexdigest()[:16])

def drive_gears(p):
    m=p["gear_module"]; n=p["pinion_teeth"]; nr=p["ring_teeth"]; pa=p["pressure_angle"]
    if (m,nr,pa)!=(2,72,25) or not 12<=n<=20 or int(n)!=n:
        raise ValueError("Base supports module 2, 12..20 pinion teeth / 72 ring teeth, 25 degrees")
    assert n>=math.ceil(2/math.sin(math.radians(pa))**2), 'Unshifted full-depth tooth undercut limit'
    assert 0<p['base_tooth_slot_fraction']<1
    center=base_drive_center(p)
    cache=base_drive_cache(p)
    bolt_pts=[polar(78,math.radians(30+60*i)) for i in range(6)]
    if (cache/"complete").exists():
        return (*[cq.Shape.importBrep(str(cache/(n+".brep"))) for n in ["pinion","ring","nominal"]],bolt_pts)
    print("Building compliant base pinion and internal ring",flush=True)
    rp=m*n/2; rr=rp-1.25*m; ra=rp+m
    outer, half=pinion_profile(m,n,pa,p["tooth_preload"])
    nominal,_=pinion_profile(m,n,pa,0)
    # Adapt the source open-tip hollow tooth: full-width walls, no finger caps.
    # Dimensions scaled for module 2; compliance remains experimentally unqualified.
    depth=1.3
    slot_a=lambda r: p['base_tooth_slot_fraction']*half(min(ra,r))
    hw=rr*slot_a(rr)
    rs=[rr+(ra+1-rr)*k/24 for k in range(25)]
    points=[polar(r,-slot_a(r)) for r in rs]+[polar(r,slot_a(r)) for r in reversed(rs)]
    slot=cq.Workplane("XY").polyline(points).close().extrude(12.2).translate((0,0,-.1)).val()
    slot=union([slot,box(depth+.1,2*hw,12.2,(rr-depth/2,0,6)),cyl(hw,12.2,(rr-depth,0,-.1))])
    slots=[slot.rotate((0,0,0),(0,0,1),360*i/n) for i in range(n)]
    gear=outer.cut(*slots)
    # A regression check across every complete slot catches any tip cap.
    assert all(overlap(gear, cut) < 1e-7 for cut in slots), "Obstructed open tooth slot"
    hub=cyl(6,11,(0,0,-11))
    gear=gear.fuse(hub)
    bore=cyl(2.65,25,(0,0,-12)).intersect(box(8,5.3,25,(0,.5,-12+12.5)))
    gear=gear.cut(bore).cut(cyl(1.25,8,(0,-7,-6),(0,1,0))).clean()
    # Internal involute: thickness grows toward the outer root circle.
    R=m*nr/2; rb=R*math.cos(math.radians(pa)); tip=R-m; root=R+1.25*m
    def ih(r): return math.pi/(2*nr)+inv(r,rb)-inv(R,rb)
    pts=[]
    # Phase places a ring tooth space on +X opposite the pinion tooth.
    for i in range(nr):
        t=2*math.pi*(i+.5)/nr
        rs=[root+(tip-root)*k/24 for k in range(25)]
        pts += [polar(r,t-ih(r)) for r in rs]
        pts += [polar(r,t+ih(r)) for r in reversed(rs)]
    cavity=cq.Workplane("XY").polyline(pts).close().extrude(14).translate((0,0,-1)).val()
    ring=cyl(82,12).cut(cavity).clean()
    ring=holes(ring,bolt_pts,1.7,-1,14)
    shapes=[gear.translate((center,0,32)),ring.translate((0,0,32)),nominal.translate((center,0,32))]
    cache.mkdir(parents=True,exist_ok=True)
    for name,s in zip(["pinion","ring","nominal"],shapes): s.exportBrep(str(cache/(name+".brep")))
    (cache/"complete").write_text("1")
    return (*shapes,bolt_pts)

