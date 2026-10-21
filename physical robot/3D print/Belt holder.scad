// ---------- T5 pulley, 8 mm bore, set screw ----------
// Matches the belt profile from the spiral-belt generator:
//   pitch 5 mm, belt width 10, tooth height 1.2, root 2.4, tip 1.7

$fn = 120;

// ---------- Parameters ----------
teeth        = 16;     // number of teeth on the pulley (CHANGE ME)
belt_pitch   = 5;      // T5
belt_w       = 10;     // belt width (must match belt code)
pitch_offset = 0.6;    // T5 pitch-line offset (belt tooth root to pitch line)

// groove (a bit larger than the belt tooth so it meshes freely)
groove_w_top = 2.6;    // groove width at outer surface (belt root is 2.4)
groove_w_bot = 1.9;    // groove width at bottom (belt tip is 1.7)
groove_d     = 1.4;    // groove depth (belt tooth is 1.2)

// flanges
flange_t     = 1.5;    // flange thickness
flange_extra = 2.0;    // flange radius beyond pulley OD

// shaft / hub
shaft_d      = 8;      // motor shaft
bore_tol     = 0.25;   // added clearance on the bore (tune for your printer)
hub_d        = 16;     // hub diameter
hub_h        = 8;      // hub height
screw_d      = 3.2;    // M3 clearance hole (use 4.2 for M4)
nut_w        = 5.7;    // M3 nut across flats (+clearance); M4 = 7.2
nut_t        = 2.6;    // nut thickness (M3 = 2.4 + clearance)
nut_trap     = true;   // hex nut trap on set screw hole

// ---------- Derived ----------
pitch_d = teeth * belt_pitch / PI;
od      = pitch_d - 2 * pitch_offset;      // outside (tooth tip) diameter
toothw  = belt_w + 1;                      // toothed section length
total_h = hub_h + flange_t + toothw + flange_t;

echo(str("Pitch diameter: ", pitch_d, " mm"));
echo(str("Outside diameter: ", od, " mm"));
echo(str("Total height: ", total_h, " mm"));

// ---------- Modules ----------
// one groove, trapezoid in the XY plane, opening towards +x (outer surface)
module groove2d() {
    polygon([
        [od / 2 - groove_d, -groove_w_bot / 2],
        [od / 2 - groove_d,  groove_w_bot / 2],
        [od / 2 + 0.01,      groove_w_top / 2],
        [od / 2 + 0.01,     -groove_w_top / 2]
    ]);
}

module toothed_section() {
    linear_extrude(height = toothw)
        difference() {
            circle(d = od);
            for (i = [0 : teeth - 1])
                rotate(i * 360 / teeth) groove2d();
        }
}

module set_screw() {
    // horizontal hole through the hub wall, pointing +x
    translate([0, 0, hub_h / 2])
        rotate([0, 90, 0]) {
            cylinder(d = screw_d, h = hub_d);
            if (nut_trap)
                // hex nut trap, pocket starts a little outside the bore
                translate([0, 0, shaft_d / 2 + 1.5])
                    rotate(90)
                        cylinder(d = nut_w / cos(30), h = nut_t, $fn = 6);
        }
    // slot so the nut can be slid in from above (open towards +z)
    if (nut_trap)
        translate([shaft_d / 2 + 1.5, -nut_w / 2, hub_h / 2])
            cube([nut_t, nut_w, hub_h]);
}

// ---------- Pulley ----------
difference() {
    union() {
        // hub
        cylinder(d = hub_d, h = hub_h);
        // bottom flange
        translate([0, 0, hub_h])
            cylinder(d = od + 2 * flange_extra, h = flange_t);
        // teeth
        translate([0, 0, hub_h + flange_t])
            toothed_section();
        // top flange
        translate([0, 0, hub_h + flange_t + toothw])
            cylinder(d = od + 2 * flange_extra, h = flange_t);
    }
    // bore
    translate([0, 0, -1])
        cylinder(d = shaft_d + bore_tol, h = total_h + 2);
    // set screw + nut trap
    set_screw();
}
