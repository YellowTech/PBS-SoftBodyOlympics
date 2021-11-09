"""
This file is based upon the example fem99.py from taichi.
"""

import taichi as ti

ti.init(arch=ti.gpu)

N = 8
dt = 1e-4
dx = 1 / N
rho = 4e1
NF = 2 * N ** 2  # number of faces
NV = (N + 1) ** 2  # number of vertices
E, nu = 9e4, 0.2  # Young's modulus and Poisson's ratio
mu, lam = E / 2 / (1 + nu), E * nu / (1 + nu) / (1 - 2 * nu)  # Lame parameters
ball_pos, ball_radius = ti.Vector([0.5, 0.0]), 0.32
gravity = ti.Vector([0, -40])
damping = 2

pos = ti.Vector.field(2, float, NV, needs_grad=True)
vel = ti.Vector.field(2, float, NV)
f2v = ti.Vector.field(3, int, NF)  # ids of three vertices of each face
B = ti.Matrix.field(2, 2, float, NF)
F = ti.Matrix.field(2, 2, float, NF, needs_grad=True)
V = ti.field(float, NF)
phi = ti.field(float, NF)  # potential energy of each face (Neo-Hookean)
U = ti.field(float, (), needs_grad=True)  # total potential energy

w_speed = ti.Vector([0, 40])
s_speed = ti.Vector([0, -40])
a_speed = ti.Vector([-40, 0])
d_speed = ti.Vector([40, 0])

wIsPressed = False
aIsPressed = False
sIsPressed = False
dIsPressed = False


@ti.kernel
def update_u():
    for i in range(NF):
        ia, ib, ic = f2v[i]
        a, b, c = pos[ia], pos[ib], pos[ic]
        V[i] = abs((a - c).cross(b - c))
        d_i = ti.Matrix.cols([a - c, b - c])
        F[i] = d_i @ B[i]
    for i in range(NF):
        f_i = F[i]
        log_j_i = ti.log(f_i.determinant())
        phi_i = mu / 2 * ((f_i.transpose() @ f_i).trace() - 2)
        phi_i -= mu * log_j_i
        phi_i += lam / 2 * log_j_i ** 2
        phi[i] = phi_i
        U[None] += V[i] * phi_i


@ti.kernel
def advance():
    for i in range(NV):
        acc = -pos.grad[i] / (rho * dx ** 2)
        vel[i] += dt * acc
        vel[i] *= ti.exp(-dt * damping)
    for i in range(NV):
        # ball boundary condition:
        disp = pos[i] - ball_pos
        disp2 = disp.norm_sqr()
        if disp2 <= ball_radius ** 2:
            nov = vel[i].dot(disp)
            if nov < 0:
                vel[i] -= nov * disp / disp2
        # rect boundary condition:
        cond = pos[i] < 0 and vel[i] < 0 or pos[i] > 1 and vel[i] > 0
        if cond[0]:
            vel[i][0] = 0
        if cond[1]:
            vel[i][1] = 0

        pos[i] += dt * vel[i]


@ti.kernel
def init_pos():
    """
    initializes the positions and velocities of all vertices and a matrix B which has a col for each face (?!)

    position is based on the id's and a linear offset
    velocities are initialized to 0

    B is use for ... (?!) probably keeping the area the same
    """
    for i, j in ti.ndrange(N + 1, N + 1):
        k = i * (N + 1) + j
        pos[k] = ti.Vector([i, j]) / N * 0.25 + ti.Vector([0.45, 0.45])
        vel[k] = ti.Vector([0, 0])
    for i in range(NF):
        ia, ib, ic = f2v[i]
        a, b, c = pos[ia], pos[ib], pos[ic]
        b_i_inv = ti.Matrix.cols([a - c, b - c])
        B[i] = b_i_inv.inverse()


@ti.kernel
def init_mesh():
    """
    initializes the springy mesh.

    by filling the f2v datastructures, which saves the id's of three vertices of each face
    """
    for i, j in ti.ndrange(N, N):
        k = (i * N + j) * 2
        a = i * (N + 1) + j
        b = a + 1
        c = a + N + 2
        d = a + N + 1
        f2v[k + 0] = [a, b, c]
        f2v[k + 1] = [c, d, a]


@ti.kernel
def w_pressed():
    for i in range(NV):
        vel[i] += dt * w_speed


@ti.kernel
def a_pressed():
    for i in range(NV):
        vel[i] += dt * a_speed


@ti.kernel
def s_pressed():
    for i in range(NV):
        vel[i] += dt * s_speed


@ti.kernel
def d_pressed():
    for i in range(NV):
        vel[i] += dt * d_speed


init_mesh()
init_pos()
gui = ti.GUI('FEM99')
while gui.running:
    for e in gui.get_events():
        # quit the game with escape
        if e.key == gui.ESCAPE:
            gui.running = False
        # reset the game with r
        elif e.key == 'r':
            init_pos()
        elif e.key == 'w':
            wIsPressed = True
        elif e.key == 'a':
            aIsPressed = True
        elif e.key == 's':
            sIsPressed = True
        elif e.key == 'd':
            dIsPressed = True

    for _ in range(10):
        with ti.Tape(loss=U):
            update_u()
        if wIsPressed:
            w_pressed()
        if aIsPressed:
            a_pressed()
        if sIsPressed:
            s_pressed()
        if dIsPressed:
            d_pressed()
        advance()
    wIsPressed = False
    aIsPressed = False
    sIsPressed = False
    dIsPressed = False
    gui.circles(pos.to_numpy(), radius=2, color=0xffaa33)
    gui.circle(ball_pos, radius=ball_radius * 512, color=0x666666)
    gui.show()
