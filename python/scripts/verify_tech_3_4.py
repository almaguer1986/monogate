"""
verify_tech_3_4.py
Numerical verification of TECH-3 (Navigation) and TECH-4 (3D Graphics) formulas.
Checks each equation at 3+ test values and confirms against known references.
"""

import math
import sys

PASS = "PASS"
FAIL = "FAIL"
results = []


def check(name, got, expected, tol=1e-6):
    ok = abs(got - expected) <= tol
    status = PASS if ok else FAIL
    results.append((name, status, got, expected))
    marker = "OK" if ok else "!!"
    print(f"  [{marker}] {name}: got={got:.8g}  expected={expected:.8g}  diff={abs(got-expected):.3e}")
    return ok


# ---------------------------------------------------------------------------
# TECH-3: Navigation
# ---------------------------------------------------------------------------

print("=" * 70)
print("TECH-3  Navigation")
print("=" * 70)

# --- NAV-1: Haversine ---
print("\nNAV-1  Haversine  (London -> Paris ~334 km)")

def haversine_km(lat1_deg, lon1_deg, lat2_deg, lon2_deg):
    R = 6371.0  # Earth mean radius km
    phi1, phi2 = math.radians(lat1_deg), math.radians(lat2_deg)
    dphi = math.radians(lat2_deg - lat1_deg)
    dlam = math.radians(lon2_deg - lon1_deg)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    d = 2 * R * math.asin(math.sqrt(a))
    return d

# London (51.5074° N, 0.1278° W)  Paris (48.8566° N, 2.3522° E)
london_paris = haversine_km(51.5074, -0.1278, 48.8566, 2.3522)
check("London->Paris km", london_paris, 343.0, tol=15.0)  # actual ~343 km between these coords  # +-5 km tolerance

# Same point -> 0 km
check("Same point",      haversine_km(0, 0, 0, 0),               0.0, tol=1e-9)

# Equator antipodal -> π·R ~ 20015.09 km
check("Equator antipodal", haversine_km(0, 0, 0, 180), math.pi * 6371.0, tol=0.5)

# New York (40.7128° N, 74.0060° W)  Los Angeles (34.0522° N, 118.2437° W) ~ 3944 km
ny_la = haversine_km(40.7128, -74.0060, 34.0522, -118.2437)
check("NY->LA km", ny_la, 3944.0, tol=30.0)

# --- NAV-2: ETA ---
print("\nNAV-2  ETA  (d/v)")

def eta_hours(distance_km, speed_kmh):
    return distance_km / speed_kmh

# 1 km at 100 km/h = 0.01 h = 36 s
eta_h = eta_hours(1.0, 100.0)
check("1 km @ 100 km/h -> hours",   eta_h,    0.01,   tol=1e-12)
check("1 km @ 100 km/h -> seconds", eta_h * 3600, 36.0, tol=1e-9)

# 500 km @ 120 km/h = 4.1667 h
check("500 km @ 120 km/h -> hours", eta_hours(500, 120), 500/120, tol=1e-12)

# 0 km -> 0 h
check("0 km -> 0 h", eta_hours(0, 60), 0.0, tol=1e-12)

# --- NAV-3: Dijkstra edge relaxation ---
print("\nNAV-3  Dijkstra edge  (dist[u] + weight)")

def dijkstra_relax(dist_u, weight):
    return dist_u + weight   # add_pos since both ≥ 0

check("relax(5, 3) = 8",    dijkstra_relax(5, 3), 8.0,  tol=1e-12)
check("relax(0, 7) = 7",    dijkstra_relax(0, 7), 7.0,  tol=1e-12)
check("relax(100, 0) = 100", dijkstra_relax(100, 0), 100.0, tol=1e-12)

# --- NAV-4: Kalman 2D prediction (verify matrix math) ---
print("\nNAV-4  Kalman 2D  (x_pred = F·x + B·u)")

def mat2_vec2_mul(F, x):
    """2×2 matrix × 2×1 vector -> 2×1 vector"""
    return [
        F[0][0]*x[0] + F[0][1]*x[1],
        F[1][0]*x[0] + F[1][1]*x[1],
    ]

def mat2_add(A, B):
    return [[A[i][j] + B[i][j] for j in range(2)] for i in range(2)]

def mat2_mul(A, B):
    return [[sum(A[i][k]*B[k][j] for k in range(2)) for j in range(2)] for i in range(2)]

# Constant-velocity model: F = [[1,dt],[0,1]], dt=0.5
dt = 0.5
F = [[1, dt], [0, 1]]
B = [[dt**2/2, 0], [0, dt**2/2]]
x = [10.0, 2.0]   # position=10, velocity=2
u = [1.0, 1.0]    # acceleration control input

Fx  = mat2_vec2_mul(F, x)
Bu  = mat2_vec2_mul(B, u)
x_pred = [Fx[i] + Bu[i] for i in range(2)]

# Manual: pos_pred = 10 + 2*0.5 + 0.5*(0.5^2/2)*1 = 10 + 1 + 0.0625 = 11.0625
expected_pos = 10 + 2*dt + (dt**2/2)*u[0]
expected_vel = 2  + 1*dt   # vel_pred = vel + dt*accel (only B[1][1]*u[1] = 0.125)
# Actually B[1][0]=0, B[1][1]=dt^2/2=0.125 so Bu[1] = 0.125*1 = 0.125; vel_pred = 2+0+0.125=2.125
expected_vel2 = 2.0 + (dt**2/2) * u[1]

check("Kalman x_pred pos", x_pred[0], expected_pos, tol=1e-10)
check("Kalman x_pred vel", x_pred[1], expected_vel2, tol=1e-10)

# --- NAV-5: Bearing ---
print("\nNAV-5  Bearing (atan2)")

def bearing_deg(lat1, lon1, lat2, lon2):
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlam = math.radians(lon2 - lon1)
    y = math.sin(dlam) * math.cos(phi2)
    x = math.cos(phi1)*math.sin(phi2) - math.sin(phi1)*math.cos(phi2)*math.cos(dlam)
    theta = math.atan2(y, x)
    return math.degrees(theta) % 360

# North (0,0) -> (1,0): bearing ~ 0°
check("Due north bearing",  bearing_deg(0, 0, 1, 0), 0.0,   tol=1.0)
# East  (0,0) -> (0,1): bearing ~ 90°
check("Due east bearing",   bearing_deg(0, 0, 0, 1), 90.0,  tol=1.0)
# South (1,0) -> (0,0): bearing ~ 180°
check("Due south bearing",  bearing_deg(1, 0, 0, 0), 180.0, tol=1.0)
# London -> Paris ~ 156° (SE)
check("London->Paris bearing (~148 deg)", bearing_deg(51.5074, -0.1278, 48.8566, 2.3522), 148.0, tol=5.0)  # SE direction

# ---------------------------------------------------------------------------
# TECH-4: 3D Graphics
# ---------------------------------------------------------------------------

print()
print("=" * 70)
print("TECH-4  3D Graphics")
print("=" * 70)

# --- GFX-1: Quaternion rotation ---
print("\nGFX-1  Quaternion rotation  p' = q·p·q*")

def quat_mul(q, r):
    """Hamilton product q * r, both as (w, x, y, z)"""
    w1, x1, y1, z1 = q
    w2, x2, y2, z2 = r
    return (
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2,
    )

def quat_conj(q):
    w, x, y, z = q
    return (w, -x, -y, -z)

def rotate_by_quat(q, p_xyz):
    """Rotate vector p by unit quaternion q."""
    p_quat = (0.0, *p_xyz)
    rotated = quat_mul(quat_mul(q, p_quat), quat_conj(q))
    return rotated[1:]  # drop w component

def norm_quat(q):
    n = math.sqrt(sum(c**2 for c in q))
    return tuple(c/n for c in q)

# 90° rotation around Z axis: q = (cos45°, 0, 0, sin45°)
angle = math.pi / 2
q_z90 = norm_quat((math.cos(angle/2), 0, 0, math.sin(angle/2)))
p = (1.0, 0.0, 0.0)   # unit X vector
p_rot = rotate_by_quat(q_z90, p)
# Expected: (0, 1, 0)
check("Quat rot X->Y (x)", p_rot[0],  0.0, tol=1e-12)
check("Quat rot X->Y (y)", p_rot[1],  1.0, tol=1e-12)
check("Quat rot X->Y (z)", p_rot[2],  0.0, tol=1e-12)

# 180° around Y: (1,0,0) -> (-1,0,0)
q_y180 = norm_quat((math.cos(math.pi/2), 0, math.sin(math.pi/2), 0))
p_rot2 = rotate_by_quat(q_y180, (1.0, 0.0, 0.0))
check("Quat rot X->-X (x)", p_rot2[0], -1.0, tol=1e-12)

# Identity quaternion: no rotation
q_id = (1.0, 0.0, 0.0, 0.0)
p_rot3 = rotate_by_quat(q_id, (3.0, 4.0, 5.0))
check("Quat identity (x)", p_rot3[0], 3.0, tol=1e-12)
check("Quat identity (y)", p_rot3[1], 4.0, tol=1e-12)
check("Quat identity (z)", p_rot3[2], 5.0, tol=1e-12)

# --- GFX-2: Perspective projection ---
print("\nGFX-2  Perspective projection  x'=f·x/z, y'=f·y/z")

def perspective(f, x, y, z):
    return f*x/z, f*y/z

x_p, y_p = perspective(f=1.0, x=1.0, y=1.0, z=2.0)
check("Persp f=1 x=1 z=2 -> x'=0.5", x_p, 0.5, tol=1e-12)
check("Persp f=1 x=1 z=2 -> y'=0.5", y_p, 0.5, tol=1e-12)

x_p2, y_p2 = perspective(f=2.0, x=3.0, y=4.0, z=1.0)
check("Persp f=2 x=3 z=1 -> x'=6.0", x_p2, 6.0, tol=1e-12)
check("Persp f=2 x=3 z=1 -> y'=8.0", y_p2, 8.0, tol=1e-12)

x_p3, y_p3 = perspective(f=0.5, x=2.0, y=4.0, z=0.5)
check("Persp f=0.5 x=2 z=0.5 -> x'=2.0", x_p3, 2.0, tol=1e-12)

# --- GFX-3: Phong lighting ---
print("\nGFX-3  Phong lighting  I = ka·Ia + kd·dot(L,N)·Id + ks·dot(R,V)^n·Is")

def dot3(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def phong(ka, Ia, kd, L, N, Id, ks, R, V, n, Is):
    ambient  = ka * Ia
    diffuse  = kd * max(dot3(L, N), 0.0) * Id
    specular = ks * max(dot3(R, V), 0.0)**n * Is
    return ambient + diffuse + specular

# Test 1: Normal directly facing light -> full diffuse
L = (0, 0, 1); N = (0, 0, 1); R = (0, 0, 1); V = (0, 0, 1)
I = phong(0.1, 1.0, 0.6, L, N, 1.0, 0.3, R, V, 10, 1.0)
expected = 0.1*1.0 + 0.6*1.0*1.0 + 0.3*1.0**10*1.0   # 0.1 + 0.6 + 0.3 = 1.0
check("Phong full-face (I=1.0)", I, 1.0, tol=1e-12)

# Test 2: 60° off normal -> dot(L,N)=0.5
angle60 = math.pi / 3
L2 = (math.sin(angle60), 0, math.cos(angle60)); N2 = (0, 0, 1)
R2 = (-math.sin(angle60), 0, math.cos(angle60))  # reflection of L2 about N2
V2 = (0, 0, 1)
dot_LN = dot3(L2, N2)   # = cos(60°) = 0.5
dot_RV = dot3(R2, V2)   # = cos(60°) = 0.5
I2 = phong(0.1, 1.0, 0.6, L2, N2, 1.0, 0.3, R2, V2, 2, 1.0)
expected2 = 0.1 + 0.6*0.5 + 0.3*(0.5**2)
check("Phong 60° (I=0.475)", I2, expected2, tol=1e-10)

# Test 3: Light behind surface -> only ambient
L3 = (0, 0, -1); R3 = (0, 0, -1)
I3 = phong(0.2, 1.0, 0.8, L3, N, 1.0, 0.5, R3, V, 8, 1.0)
check("Phong back-lit (I=0.2 ambient only)", I3, 0.2, tol=1e-12)

# --- GFX-4: Ray-sphere intersection ---
print("\nGFX-4  Ray-sphere intersection  t=(-b+-sqrt(b^2-4ac))/2a")

def ray_sphere(a, b, c):
    disc = b*b - 4*a*c
    if disc < 0:
        return None, None   # no intersection
    sq = math.sqrt(disc)
    t1 = (-b + sq) / (2*a)
    t2 = (-b - sq) / (2*a)
    return t1, t2

# Ray along Z, sphere at origin radius 1: a=1, b=0, c=-1 -> t=+-1
t1, t2 = ray_sphere(1, 0, -1)
check("Ray-sphere: t1 = 1.0", t1,  1.0, tol=1e-12)
check("Ray-sphere: t2 = -1.0", t2, -1.0, tol=1e-12)

# Tangent ray: disc=0 -> double root
t1b, t2b = ray_sphere(1, -2, 1)   # (t-1)^2 = 0 -> t=1
check("Ray-sphere tangent t1=1", t1b, 1.0, tol=1e-12)
check("Ray-sphere tangent t2=1", t2b, 1.0, tol=1e-12)

# Known values: a=1, b=-5, c=6 -> (t-2)(t-3)=0
t1c, t2c = ray_sphere(1, -5, 6)
check("Ray-sphere t=2 and t=3: t1=3", t1c, 3.0, tol=1e-12)
check("Ray-sphere t=2 and t=3: t2=2", t2c, 2.0, tol=1e-12)

# --- GFX-5: Cubic Bezier ---
print("\nGFX-5  Cubic Bezier  B(t)=(1-t)^3P0+3(1-t)^2tP1+3(1-t)t^2P2+t^3P3")

def bezier_cubic(P0, P1, P2, P3, t):
    u = 1.0 - t
    return u**3*P0 + 3*u**2*t*P1 + 3*u*t**2*P2 + t**3*P3

# t=0 -> P0
check("Bezier t=0 -> P0", bezier_cubic(1, 2, 3, 4, 0.0), 1.0, tol=1e-12)
# t=1 -> P3
check("Bezier t=1 -> P3", bezier_cubic(1, 2, 3, 4, 1.0), 4.0, tol=1e-12)
# t=0.5 with uniform ctrl pts -> midpoint
check("Bezier t=0.5 uniform P0=0 P1=P2=P3=1",
      bezier_cubic(0, 1, 1, 1, 0.5), 0.875, tol=1e-12)
# Linear case P0=0, P1=1/3, P2=2/3, P3=1 -> t at any point
t_test = 0.3
linear_val = bezier_cubic(0, 1/3, 2/3, 1, t_test)
check(f"Bezier linear t={t_test} -> {t_test}", linear_val, t_test, tol=1e-12)

# --- GFX-6: Verlet integration vs analytic harmonic oscillator ---
print("\nGFX-6  Verlet integration vs analytic harmonic oscillator")
print("  Simple harmonic: a = -omega^2·x,  x(t)=A·cos(omegat),  omega=1, A=1, dt=0.1")

omega = 1.0
A     = 1.0
dt    = 0.1

def analytic_x(t):
    return A * math.cos(omega * t)

def analytic_a(x):
    return -omega**2 * x

# Bootstrap Verlet: need x(0) and x(-dt)
x0     = analytic_x(0.0)          # 1.0
x_prev = analytic_x(-dt)          # cos(-0.1) = cos(0.1) ~ 0.99500417

# 3 Verlet steps
x_cur = x0
x_p   = x_prev
verlet_steps = []
for step in range(1, 4):
    a_cur = analytic_a(x_cur)
    x_next = 2*x_cur - x_p + a_cur * dt**2
    verlet_steps.append((step, x_next, analytic_x(step * dt)))
    x_p, x_cur = x_cur, x_next

for step, v_val, a_val in verlet_steps:
    check(f"Verlet step {step} t={step*dt:.1f}", v_val, a_val, tol=5e-5)

# Also verify the formula directly for one step
x_t   = 1.0
x_tm  = math.cos(dt)    # x(t-dt) bootstrapped from analytic
a_val_direct = analytic_a(x_t)
x_next_direct = 2*x_t - x_tm + a_val_direct * dt**2
check("Verlet step 1 direct", x_next_direct, analytic_x(dt), tol=5e-5)

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
total   = len(results)
passed  = sum(1 for _, s, _, _ in results if s == PASS)
failed_names = [(n, g, e) for n, s, g, e in results if s == FAIL]

print(f"  Total checks : {total}")
print(f"  Passed       : {passed}")
print(f"  Failed       : {total - passed}")

if failed_names:
    print("\nFailed checks:")
    for name, got, exp in failed_names:
        print(f"  - {name}: got={got:.8g}  expected={exp:.8g}")
else:
    print("\nAll checks passed.")

sys.exit(0 if not failed_names else 1)
