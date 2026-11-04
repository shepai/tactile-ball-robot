// =====================================================================
//  Tyre-tread silicone ball - printable mold set  (OpenSCAD, units mm)
//
//  Set `part`, render (F6), export STL. Printable parts come out already
//  in print orientation.
//    mold_bottom  PLA/PETG  bowl on a flat base - no seams below the pour
//    mold_top     PLA/PETG  lid: pour funnels, core seat, tongue seal
//    core         PVA       hollow shell that forms the inside of the ball;
//                           dissolves out afterwards
//    clip         PLA       holds the core up while you pour
//    ball         preview of the finished silicone part
//    assembly / section     views only
//
//  Design choices
//   * Leaks: split at the equator, so the lower half that holds most of
//     the silicone is one seamless bowl. The joint has a tongue-and-groove
//     seal clamped by M5 bolts (nuts sit in hex pockets).
//   * Thick / fast-setting silicone: no long sprue. You pour through two
//     short, wide funnels straight into the 10 mm gap, which fills from
//     the bottom up by itself. Use a slow-cure grade and degas first.
//   * Air: the only high point is the ring around the opening. Cross
//     vents in the core stalk carry that air up the neck and out.
//     Tread grooves are chevrons with sloped ends - no ledges for
//     bubbles to hide under.
//   * Release: one lift-off lid with pry slots; the core stays rigid
//     while you demold, then dissolves.
//
//  Print: halves 4 walls, 5 top/bottom layers, 15% infill (walls stop
//  seepage). Core in PVA: it is modelled hollow - a 3 mm shell with a
//  central pillar holding up a pointed 45 degree roof, so the inside
//  needs no supports. Slice with 3 walls and 15% infill (~170 g; infill
//  only goes into the thick roof). Tree supports set to "build plate
//  only", so none get put inside the hollow (outside support marks end
//  up inside the ball). Hardware: 8x M5x30 bolts + nuts.
//
//  Use
//   1. Wipe release (or a thin film of petroleum jelly) on the cavity
//      and flange faces.
//   2. Push the core neck up through the lid from below; slide the clip
//      into the neck groove on top.
//   3. Lower the lid onto the bowl, tongue into groove, bolt it up.
//   4. Pour in a thin stream into ONE funnel; the other lets air out.
//      Keep going until both funnels are full to the brim.
//   5. After cure: clip off, unbolt, lever the lid off at the pry slots,
//      lift the ball out with the core still inside.
//   6. Cut the neck off flush, pull out the thin silicone vent string,
//      poke a skewer down the hole to break into the water channel
//      (it runs down the pillar into the hollow), then soak in warm
//      water, opening up, changing the water now and then, until the
//      PVA has gone. Snip the four small vent nubs inside the opening.
//
//  Silicone needed with the defaults: about 600 ml (~650 g). Pick a
//  slow-cure grade (20+ min pot life) and degas before pouring.
// =====================================================================

/* [What to show] */
part = "assembly"; // [assembly, section, mold_bottom, mold_top, core, clip, ball]
explode = 70;      // spacing in the assembly view

/* [Ball] */
ball_r    = 75;    // centre to the outside of the tread
wall      = 10;    // silicone wall thickness
opening_d = 15;    // hole on one side

/* [Tread] */
tread_depth   = 3;   // groove depth into the wall (0 = smooth ball)
tread_width   = 80;  // width of the tread band, measured over the surface
tread_count   = 20;  // chevrons around the ball
groove_w      = 6;   // groove width
chevron_angle = 30;  // 0 = straight across, larger = sharper V

/* [Mold] */
mold_wall  = 6;    // plastic around the cavity
flange_t   = 10;   // clamping flange thickness, each half
top_extra  = 7;    // material above the ball for funnels and core guide
base_extra = 4;    // material below the ball
base_d     = 90;   // flat base diameter (bigger = steadier, more plastic)
fit        = 0.2;  // printing clearance per side

/* [Seal and bolts] */
seal_gap   = 4;    // cavity edge to tongue
tongue_w   = 3;
tongue_h   = 3;
bolt_count = 8;
bolt_d     = 5.5;  // M5 clearance
head_d     = 10.5; // recess for bolt head / washer
nut_af     = 8.2;  // M5 nut across flats + clearance

/* [Pouring] */
inlet_count = 2;
inlet_d     = 14;  // funnel throat
inlet_lat   = 70;  // where inlets enter the ball (90 = top)
funnel_h    = 7;

/* [Core] */
neck_d      = 10;  // stalk above the opening, must be < opening_d
clip_t      = 4;
vent_d      = 2.5; // cross vents through the stalk
vent_bore_d = 3;   // carries vent air up the neck
bore_d      = 8;   // water channel inside the core (dissolves faster)
core_flat_d = 20;  // flat on core bottom for bed contact (0 = none)
hollow      = true; // model the core as a hollow shell
core_shell  = 10;   // shell thickness of the hollow core
pillar_d    = 14;  // central column holding up the roof of the hollow
window_d    = 4;   // holes from the water channel into the hollow

/* [Quality] */
$fn = 96;

/* [Hidden] */
core_r      = ball_r - wall;
mold_r      = ball_r + mold_wall;
open_r      = opening_d / 2;
neck_r      = neck_d / 2;
clip_groove_r = neck_r - 1.5;
band_lat    = min(85, (tread_width / 2) / ball_r * 180 / PI);
z_top       = ball_r + mold_wall + top_extra;
z_base      = ball_r + mold_wall + base_extra;
z_shoulder  = sqrt(ball_r * ball_r - open_r * open_r);
seat_h      = open_r - neck_r;                       // 45 degree seat
z_neck_top  = z_top + clip_t + 0.15 + 5;
tongue_r    = ball_r + seal_gap;
bolt_r      = tongue_r + tongue_w + 3 + head_d / 2;
face_r      = bolt_r + head_d / 2 + 4;
funnel_r    = inlet_d / 2 + funnel_h;                // 45 degree funnel
inlet_r     = max(ball_r * cos(inlet_lat), neck_r + funnel_r + 6);
top_r       = max(inlet_r + funnel_r + 4, neck_r + 15);
z_inlet0    = sqrt(ball_r * ball_r - pow(inlet_r + inlet_d / 2, 2)) - 3;
z_vent      = z_shoulder - vent_d / 2 - 0.1;
z_flat      = core_flat_d > 0
              ? -sqrt(core_r * core_r - core_flat_d * core_flat_d / 4)
              : -core_r - 1;
big         = 4 * (ball_r + 50);
// hollow core: ring-shaped pointed roof with 45 degree faces, held up by
// the central pillar, so the inside prints without supports
r_in        = core_r - core_shell;
pillar_r    = pillar_d / 2;
ridge_lat   = 63;                       // ridge position, near the lightest roof
ridge_x     = r_in * cos(ridge_lat);
ridge_z     = r_in * sin(ridge_lat);
z_floor     = max(z_flat, -core_r) + core_shell;
z_join      = ridge_z - ridge_x + pillar_r;      // roof meets the pillar
z_window    = z_join - window_d / 2 - 1.5;
z_bore_top  = z_vent - vent_d / 2 - 2.5;
z_bore_bot  = hollow ? z_window - window_d / 2 - 1 : z_flat + 8;

assert(neck_d < opening_d, "neck_d must be smaller than opening_d");
assert(!hollow || pillar_d >= bore_d + 4, "pillar_d must be at least bore_d + 4");
assert(!hollow || z_window - window_d / 2 > z_floor + 3, "hollow too small: reduce core_shell or pillar_d");
assert(tread_depth < wall, "tread_depth must be less than wall");
assert(clip_groove_r > vent_bore_d / 2 + 1, "neck_d too small for the vent bore");
assert(inlet_r + inlet_d / 2 < ball_r - 5, "inlets don't fit: raise inlet_lat or shrink inlet_d");

// ------------------------------------------------------------ ball ---

// The slice of the ball's skin where grooves can be: between the groove
// floor and just outside the ball, within +/- band_lat of the equator.
// The latitude limit makes groove ends slope, so they can't trap air.
// Built in 2D and spun once, so it never touches the axis (a solid that
// pinches to a point on the axis breaks CGAL renders).
module tread_zone() {
    L = ball_r + 10;
    rotate_extrude()
        intersection() {
            difference() {
                circle(r = ball_r + 1);
                circle(r = ball_r - tread_depth);
            }
            polygon([[0, 0], [L, -L * tan(band_lat)], [L, L * tan(band_lat)]]);
        }
}

// one chevron: two great-circle grooves meeting on the equator
module chevron() {
    L = ball_r + 10;
    for (s = [1, -1])
        intersection() {
            rotate([s * chevron_angle, 0, 0])
                cube([2 * L, groove_w, 2 * L], center = true);
            translate([0, -L, s > 0 ? -0.01 : -L])
                cube([L, 2 * L, L + 0.01]);
        }
}

module groove_cutters() {
    intersection() {
        tread_zone();
        union() {
            for (i = [0 : tread_count - 1])
                rotate([0, 0, i * 360 / tread_count]) chevron();
        }
    }
}

module ball_outer() {
    difference() {
        sphere(r = ball_r);
        if (tread_depth > 0) groove_cutters();
    }
}

// ------------------------------------------------------------ core ---

module stalk() {
    // plug that forms the opening
    translate([0, 0, core_r - 5])
        cylinder(r = open_r, h = z_shoulder - core_r + 5);
    // 45 degree seat: centres the core and seals when it floats up
    translate([0, 0, z_shoulder - 0.01])
        cylinder(r1 = open_r, r2 = neck_r, h = seat_h + 0.01);
    // neck through the lid
    translate([0, 0, z_shoulder + seat_h - 0.01])
        cylinder(r = neck_r, h = z_neck_top - z_shoulder - seat_h + 0.01);
}

module core_shape() {
    difference() {
        sphere(r = core_r);
        translate([0, 0, z_flat - big / 2]) cube(big, center = true);
    }
    stalk();
}

// the empty space inside the core (a ring around the pillar)
module hollow_space() {
    L = 2 * core_r;
    rotate_extrude()
        intersection() {
            circle(r = r_in);
            translate([pillar_r, z_floor]) square([L, 2 * L]);
            polygon([[0, ridge_z - ridge_x], [ridge_x, ridge_z],
                     [ridge_x + ridge_z + L, -L], [0, -L]]);
        }
}

module core() {
    difference() {
        core_shape();
        if (hollow) {
            hollow_space();
            for (a = [0, 90])                  // windows into the hollow
                translate([0, 0, z_window]) rotate([90, 0, a])
                    cylinder(d = window_d, h = pillar_d + 2, center = true);
        }
        // air vents just under the top of the cavity, then up the neck
        for (a = [0, 90])
            translate([0, 0, z_vent]) rotate([90, 0, a])
                cylinder(d = vent_d, h = 2 * open_r + 2, center = true);
        translate([0, 0, z_vent - vent_d / 2])
            cylinder(d = vent_bore_d, h = big);
        // water channel down the pillar, sealed by a thin skin at the top
        // until you poke through
        translate([0, 0, z_bore_bot])
            cylinder(d = bore_d, h = z_bore_top - z_bore_bot);
        // groove for the clip
        translate([0, 0, z_top - 1])
            difference() {
                cylinder(r = neck_r + 1, h = clip_t + 1.15);
                translate([0, 0, -1]) cylinder(r = clip_groove_r, h = clip_t + 3.15);
            }
    }
}

module clip() {
    difference() {
        hull() {
            cylinder(r = neck_r + 4.5, h = clip_t);
            translate([0, neck_r + 12, 0]) cylinder(r = 5, h = clip_t);
        }
        hull() {
            translate([0, 0, -1])
                cylinder(r = clip_groove_r + fit, h = clip_t + 2);
            translate([0, -2 * neck_r - 10, -1])
                cylinder(r = clip_groove_r + fit, h = clip_t + 2);
        }
    }
}

// ------------------------------------------------------------ mold ---

module top_body() {
    hull() {
        cylinder(r = face_r, h = flange_t);
        intersection() {
            sphere(r = mold_r);
            cylinder(r = mold_r + 1, h = mold_r + 1);
        }
        translate([0, 0, z_top - 0.01]) cylinder(r = top_r, h = 0.01);
    }
}

module bottom_body() {
    hull() {
        translate([0, 0, -flange_t]) cylinder(r = face_r, h = flange_t);
        intersection() {
            sphere(r = mold_r);
            translate([0, 0, -mold_r - 1]) cylinder(r = mold_r + 1, h = mold_r + 1);
        }
        translate([0, 0, -z_base]) cylinder(r = base_d / 2, h = 0.01);
    }
}

module bolt_holes(top) {
    for (i = [0 : bolt_count - 1])
        rotate([0, 0, (i + 0.5) * 360 / bolt_count])
            translate([bolt_r, 0, 0]) {
                cylinder(d = bolt_d, h = big, center = true);
                if (top)
                    translate([0, 0, flange_t]) cylinder(d = head_d, h = big);
                else
                    translate([0, 0, -flange_t - big])
                        cylinder(d = nut_af / cos(30), h = big, $fn = 6);
            }
}

module core_seat() {
    translate([0, 0, z_shoulder - 0.3])
        cylinder(r1 = open_r + fit + 0.3, r2 = neck_r + fit, h = seat_h + 0.3);
    translate([0, 0, z_shoulder + seat_h - 0.01])
        cylinder(r = neck_r + fit, h = big);
}

module inlets() {
    for (i = [0 : inlet_count - 1])
        rotate([0, 0, i * 360 / inlet_count])
            translate([inlet_r, 0, 0]) {
                translate([0, 0, z_inlet0]) cylinder(d = inlet_d, h = big);
                translate([0, 0, z_top - funnel_h])
                    cylinder(r1 = inlet_d / 2, r2 = funnel_r, h = funnel_h + 0.01);
            }
}

module pry_slots() {
    for (a = [0, floor(bolt_count / 2) * 360 / bolt_count])
        rotate([0, 0, a])
            translate([face_r - 8, -7, -0.01]) cube([10, 14, 2.5]);
}

module mold_top() {
    difference() {
        union() {
            top_body();
            translate([0, 0, -tongue_h])       // tongue seal
                difference() {
                    cylinder(r = tongue_r + tongue_w, h = tongue_h + 0.01);
                    translate([0, 0, -1]) cylinder(r = tongue_r, h = tongue_h + 2);
                }
        }
        ball_outer();
        core_seat();
        inlets();
        bolt_holes(true);
        pry_slots();
    }
}

module mold_bottom() {
    difference() {
        bottom_body();
        ball_outer();
        translate([0, 0, -tongue_h - 0.5])      // groove for the tongue
            difference() {
                cylinder(r = tongue_r + tongue_w + fit, h = tongue_h + 0.51);
                translate([0, 0, -1]) cylinder(r = tongue_r - fit, h = tongue_h + 3);
            }
        bolt_holes(false);
    }
}

// finished silicone part
module ball() {
    difference() {
        ball_outer();
        core_shape();
    }
}

// ----------------------------------------------------------- views ---

module cut() {                                  // keep y >= 0
    intersection() {
        children();
        translate([-big / 2, 0, -big / 2]) cube(big);
    }
}

module place_clip() {
    translate([0, 0, z_top])
        rotate([0, 0, 180 / max(inlet_count, 1) - 90]) clip();
}

if (part == "assembly") {
    color("SteelBlue")      mold_bottom();
    color("Orange")         translate([0, 0, explode]) core();
    color("LightSteelBlue") translate([0, 0, 2 * explode]) mold_top();
    color("Gold")           translate([0, 0, 3 * explode]) place_clip();
} else if (part == "section") {
    color("SteelBlue")      cut() mold_bottom();
    color("LightSteelBlue") cut() mold_top();
    color("Orange")         cut() core();
    color("DimGray")        cut() ball();
    color("Gold")           cut() place_clip();
} else if (part == "mold_bottom") {
    translate([0, 0, z_base]) mold_bottom();
} else if (part == "mold_top") {
    rotate([180, 0, 0]) translate([0, 0, -z_top]) mold_top();
} else if (part == "core") {
    translate([0, 0, -z_flat]) core();
} else if (part == "clip") {
    clip();
} else if (part == "ball") {
    ball();
}
