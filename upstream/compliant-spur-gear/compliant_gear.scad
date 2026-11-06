// Open-tip compliant spur gear (revision 3)
// Each tooth has two full-width cantilever walls, an open tip and a rounded
// slot extending into the rim. Uses the uncapped tooth concept from
// tscircuit/rack-actuator; the rotary involute and dimensions differ.
// No interleaved fingers, wedge caps or finger-contact travel stop.
// Preload, stiffness and fatigue require physical testing.

/* [Gear] */
module_m       = 3;     // module [mm]
teeth          = 20;
face_width     = 12;    // [mm]
pressure_angle = 20;    // [deg]
bore_d         = 8;

/* [Compliance] */
preload        = 0.10;  // extra flank thickness at pitch circle, per side [mm]
hollow_frac    = 0.55;  // slot width as a fraction of tooth width
slot_depth     = 2.0;   // how far the slot goes below the root circle [mm]
root_fillet    = 0.6;

/* [Mating pinion (for assembly preview)] */
pinion_teeth   = 16;
show           = "assembly"; // [gear, pinion, assembly, tooth_sections, tooth_closeup]

$fn = 96;
STEPS = 24;

// ---------- involute math (radians) ----------
function deg(a) = a * 180 / PI;
function rad(a) = a * PI / 180;
function inv(a_rad) = tan(deg(a_rad)) - a_rad;

function rp(N)  = module_m * N / 2;
function rb(N)  = rp(N) * cos(pressure_angle);
function ra(N)  = rp(N) + module_m;
function rf(N)  = rp(N) - 1.25 * module_m;

// half angular tooth thickness at radius r [rad]
function psi(N, r, pl) =
    let(rr = max(r, rb(N)),
        a_r = acos(rb(N) / rr))
    PI / (2 * N) + pl / rp(N) + inv(rad(pressure_angle)) - inv(rad(a_r));

function polar(r, a_rad) = [r * cos(deg(a_rad)), r * sin(deg(a_rad))];

function radii(r0, r1) = [for (i = [0:STEPS]) r0 + (r1 - r0) * i / STEPS];

// slot half angle at radius r
function slot_a(N, r) = hollow_frac * psi(N, min(r, ra(N)), preload);
function slot_hw(N) = rf(N) * slot_a(N, rf(N));

// ---------- 2D primitives ----------
module tooth2d(N, pl) {
    r0 = rf(N) - 0.5;
    rs = radii(r0, ra(N));
    right = [for (r = rs) polar(r, -psi(N, r, pl))];
    left  = [for (i = [len(rs) - 1:-1:0]) polar(rs[i], psi(N, rs[i], pl))];
    polygon(concat(right, left));
}

module gear2d(N, pl) {
    offset(r = -root_fillet) offset(delta = root_fillet)
    union() {
        circle(r = rf(N));
        for (i = [0:N - 1]) rotate(i * 360 / N) tooth2d(N, pl);
    }
}

// slot (hollow) inside the tooth at angle 0, open at the tip
module slot2d(N) {
    rs = radii(rf(N), ra(N) + 1);
    hw = slot_hw(N);
    right = [for (r = rs) polar(r, -slot_a(N, r))];
    left  = [for (i = [len(rs) - 1:-1:0]) polar(rs[i], slot_a(N, rs[i]))];
    union() {
        polygon(concat(right, left));
        // extension into the rim for a longer, softer cantilever
        translate([rf(N) - slot_depth, -hw]) square([slot_depth + 0.05, 2 * hw]);
        translate([rf(N) - slot_depth, 0]) circle(r = hw, $fn = 32);
    }
}

module compliant_gear(N = teeth) {
    difference() {
        linear_extrude(face_width) gear2d(N, preload);
        translate([0, 0, -1]) cylinder(d = bore_d, h = face_width + 2);
        for (i = [0:N - 1]) rotate(i * 360 / N)
            translate([0, 0, -1]) linear_extrude(face_width + 2) slot2d(N);
    }
}

module pinion(N = pinion_teeth) {
    difference() {
        linear_extrude(face_width) gear2d(N, 0);
        translate([0, 0, -1]) cylinder(d = bore_d, h = face_width + 2);
    }
}

module assembly() {
    color("orange") compliant_gear();
    a = rp(teeth) + rp(pinion_teeth);   // nominal center distance
    color("steelblue", 0.85)
        translate([a, 0, 0]) rotate(180 + 180 / pinion_teeth) pinion();
}

// Identical sections at one-quarter and three-quarters face width.
module tooth_sections() {
    zs = [0.25 * face_width, 0.75 * face_width];
    for (i = [0:1])
        translate([i * 18, 0, 0])
        translate([-rp(teeth), 0, 0])
        projection(cut = true) translate([0, 0, -zs[i]])
            intersection() {
                compliant_gear();
                translate([rp(teeth) - 6, -6, -1]) cube([12, 12, face_width + 2]);
            }
}

if (show == "gear")           compliant_gear();
else if (show == "pinion")    pinion();
else if (show == "assembly")  assembly();
else if (show == "tooth_sections") tooth_sections();
else if (show == "tooth_closeup")
    intersection() {
        compliant_gear();
        translate([rp(teeth) - 4, -5, -1]) cube([8, 10, face_width + 2]);
    }
