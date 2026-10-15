// ---------- Parameters ----------
belt_teeth   = 350;    // number of teeth = belt length / 5 mm (CHANGE ME)
belt_pitch   = 5;      // T5
belt_w       = 10;     // belt width (print height)
back_t       = 1.0;    // thickness of the flat backing
tooth_h      = 1.2;    // T5 tooth height (total belt thickness = 2.2)
tooth_w_base = 2.4;    // tooth width at the root (groove on gear is 2.6)
tooth_w_tip  = 1.7;    // tooth width at the tip

gap          = 0.8;    // clearance between neighbouring turns of the spiral
r0           = 45;     // radius where the spiral starts (inner surface of backing)

sub          = 10;     // sample points per tooth pitch (smoothness of the curve)

// ---------- Derived ----------
turn_pitch = back_t + tooth_h + gap;     // radial growth per full turn
a          = turn_pitch / (2 * PI);      // radial growth per radian
N          = belt_teeth * sub;
ds         = belt_pitch / sub;

function deg(t)      = t * 180 / PI;
function rad_at(t)   = r0 + a * t;                       // inner surface radius
function pt(r, t)    = [r * cos(deg(t)), r * sin(deg(t))];
function nxt(t)      = t + ds / sqrt(pow(rad_at(t), 2) + a * a);
function walk(n, t = 0, acc = []) =
    n < 0 ? acc : walk(n - 1, nxt(t), concat(acc, [t]));

ts = walk(N);                                            // angle at each sample point

echo(str("Belt length: ", belt_teeth * belt_pitch, " mm"));
echo(str("Spiral outer diameter: ", 2 * (rad_at(ts[N]) + back_t), " mm"));
echo(str("Turns: ", ts[N] / (2 * PI)));

// ---------- 2D shapes ----------
module back2d() {
    polygon(concat(
        [for (t = ts) pt(rad_at(t) + back_t, t)],
        [for (i = [len(ts) - 1 : -1 : 0]) pt(rad_at(ts[i]), ts[i])]
    ));
}

// local frame: +x points radially outward, teeth point inward (-x)
module tooth2d() {
    polygon([
        [0.3, -tooth_w_base / 2], [0, -tooth_w_base / 2],
        [-tooth_h, -tooth_w_tip / 2], [-tooth_h, tooth_w_tip / 2],
        [0, tooth_w_base / 2], [0.3, tooth_w_base / 2]
    ]);
}

module teeth2d() {
    for (k = [0 : belt_teeth - 1]) {
        t = ts[k * sub + sub / 2];          // tooth centred in its pitch cell
        translate(pt(rad_at(t), t))
            rotate(deg(t))
                tooth2d();
    }
}

// ---------- Belt ----------
linear_extrude(height = belt_w) {
    back2d();
    teeth2d();
}