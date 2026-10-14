// ---------- Parameters ----------
bore_d        = 51;     // central opening diameter
gear_extra_r  = 13;     // gear outer radius = bore radius + this
belt_pitch    = 6;      // T5
pitch_offset  = 0.6;    // T5 pulley OD = pitch diameter - 0.6
tooth_depth   = 1.2;    // T5 tooth height
tooth_r       = 1.3;    // groove radius (clearance incl.)

wheel_r       = 65;     // outer radius of wheel
wheel_w       = 9;      // width of rim/hub body
web_t         = 6;      // thickness of web between hub and rim
rim_radial    = 6;      // radial thickness of rim
gear_h        = 10;     // toothed section standing up above the wheel

step_drop     = 5;      // inner part of the raised section sits this much lower than the teeth
step_split    = 0.5;    // 0.5 = inner half (radially) is lowered

screw_r       = 2.5;    // radial screw hole radius
screw_depth   = 12;     // how far holes go inwards from the edge
screw_count   = 12;

truss_count   = 15;     // number of triangle pairs around the web
truss_rib     = 2;      // width of the ribs left between cutouts
truss_corner  = 1.5;    // rounding on cutout corners (reduces stress points)
web_margin    = 4;      // solid margin kept next to hub and rim

$fn = 120;

// ---------- Derived ----------
bore_r    = bore_d / 2;
target_od = 2 * (bore_r + gear_extra_r);
teeth_n   = round((target_od + pitch_offset) * PI / belt_pitch);
pitch_d   = teeth_n * belt_pitch / PI;
gear_od   = pitch_d - pitch_offset;
gear_r    = gear_od / 2;
rim_in_r  = wheel_r - rim_radial;
split_r   = bore_r + (gear_r - bore_r) * step_split;
echo(str("T5 teeth: ", teeth_n, "  Gear OD: ", gear_od, " mm"));

// ---------- 2D toothed profile ----------
module t5_profile() {
    difference() {
        circle(r = gear_r);
        for (i = [0 : teeth_n - 1])
            rotate(i * 360 / teeth_n)
                translate([gear_r - tooth_depth + tooth_r, 0])
                    circle(r = tooth_r, $fn = 24);
    }
}

// ---------- Truss pattern (triangles alternating up/down) ----------
module truss_cutouts() {
    ri = gear_r + web_margin;
    ro = rim_in_r - web_margin;
    s  = 360 / truss_count;
    function P(r, a) = [r * cos(a), r * sin(a)];

    for (k = [0 : truss_count - 1]) {
        a = k * s;
        // triangle with base on inner ring, tip pointing outward
        shrink_round([P(ri, a), P(ri, a + s), P(ro, a + s / 2)]);
        // triangle with base on outer ring, tip pointing inward
        shrink_round([P(ro, a + s / 2), P(ro, a + 1.5 * s), P(ri, a + s)]);
    }
}

// shrinks a polygon so the ribs between neighbours are truss_rib wide, with rounded corners
module shrink_round(pts) {
    offset(r = truss_corner)
        offset(delta = -(truss_rib / 2 + truss_corner))
            polygon(pts);
}

// ---------- Wheel ----------
module wheel() {
    difference() {
        union() {
            // hub (plain cylinder below the raised section)
            cylinder(r = gear_r, h = wheel_w);

            // raised section, outer ring with T5 teeth at full height
            translate([0, 0, wheel_w])
                linear_extrude(height = gear_h)
                    difference() {
                        t5_profile();
                        circle(r = split_r);
                    }

            // raised section, inner part stepped down
            translate([0, 0, wheel_w])
                linear_extrude(height = gear_h - step_drop)
                    circle(r = split_r);

            // web with truss cutouts
            translate([0, 0, (wheel_w - web_t) / 2])
                linear_extrude(height = web_t)
                    difference() {
                        circle(r = rim_in_r + 1);
                        truss_cutouts();
                    }

            // rim
            difference() {
                cylinder(r = wheel_r, h = wheel_w);
                translate([0, 0, -1]) cylinder(r = rim_in_r, h = wheel_w + 2);
            }
        }

        // central bore through everything
        translate([0, 0, -1]) cylinder(r = bore_r, h = wheel_w + gear_h + 2);

        // radial screw holes going inwards from the outer edge
        for (i = [0 : screw_count - 1])
            rotate([0, 0, i * 360 / screw_count + 180 / screw_count])
                translate([wheel_r - screw_depth, 0, wheel_w / 2])
                    rotate([0, 90, 0])
                        cylinder(r = screw_r, h = screw_depth + 1, $fn = 32);
    }
}

wheel();