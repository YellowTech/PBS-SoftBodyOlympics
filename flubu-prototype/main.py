"""
This file is based upon the example fem99.py from taichi.
"""

import taichi as ti

ti.init(arch=ti.gpu)

N = 8  # number of edges in one row i.e. number of vertices - 1
dt = 1e-4  # simulation rate
dx = 1 / N  # horizontal and vertical edge length
rho = 6e1  # very small rho is basically a rigid body and a big rho results in a liquid
NF = 2 * N ** 2  # number of faces
NV = (N + 1) ** 2  # number of vertices
E, nu = 5e3, 0.4  # Young's modulus and Poisson's ratio
# the poisson's ratio determines how much the volume changes when the material is being stretched
# 0.5 = no volume change
# <0.5 = volume bigger
# <0 = material gets thicken when stretched
# the higher the youngs thingy the stiffer the material
mu, lam = E / 2 / (1 + nu), E * nu / (1 + nu) / (1 - 2 * nu)  # Lame parameters, based on the phys-parameters above
ball_pos, ball_radius = ti.Vector([0.5, 0.0]), 0.32  # position and size of the gray ball
damping = 10  # global damping parameter

pos = ti.Vector.field(2, float, NV, needs_grad=True)  # position of the vertices
vel = ti.Vector.field(2, float, NV)  # velocity of the vertices
f2v = ti.Vector.field(3, int, NF)  # ids of three vertices of each face
B = ti.Matrix.field(2, 2, float, NF)  # inverse matrix based upon the starting state of each triangle,
# used to calculate the scissor like force which brings the flubbbu back into the starting position
F = ti.Matrix.field(2, 2, float, NF, needs_grad=True)  # forces acting on the faces (scissor force)
# F is also called: deformation gradient
V = ti.field(float, NF)  # area of each face (times 2 because it is calculated with the vector cross product)
phi = ti.field(float, NF)  # potential energy of each face (Neo-Hookean)
U = ti.field(float, (), needs_grad=True)  # total potential energy

speed = 40 + damping * 2

w_speed = ti.Vector([0, 40 + damping * 2])
s_speed = ti.Vector([0, -40 - damping * 2])
a_speed = ti.Vector([-40 - damping * 2, 0])
d_speed = ti.Vector([40 + damping * 2, 0])

wIsPressed = False
aIsPressed = False
sIsPressed = False
dIsPressed = False


@ti.kernel
def update_u():
    for i in range(NF):
        ia, ib, ic = f2v[i]  # id's of face vertices
        a, b, c = pos[ia], pos[ib], pos[ic]  # position of face vertices
        V[i] = abs((a - c).cross(b - c))  # calculate the area
        d_i = ti.Matrix.cols([a - c, b - c])  # calculate two triangle edges
        F[i] = d_i @ B[i]  # scissor force based on starting position difference
    for i in range(NF):
        f_i = F[i]
        # calculate the total potential energy phi
        # this formulae can be found on:
        # https://en.wikipedia.org/wiki/Neo-Hookean_solid
        # they call it W
        log_j_i = ti.log(f_i.determinant())
        phi_i = mu / 2 * ((f_i.transpose() @ f_i).trace() - 2)
        phi_i -= mu * log_j_i
        phi_i += lam / 2 * log_j_i ** 2  # this part is called the cauchy-green deformation tensor
        phi[i] = phi_i
        # total energy is updated by multiplying the strain energy with the area size the strain is on
        U[None] += V[i] * phi_i


@ti.kernel
def advance():
    for i in range(NV):
        acc = -pos.grad[i] / (rho * dx ** 2)  # acceleration based on the negative gradient of the position
        vel[i] += dt * acc  # apply the acceleration
        vel[i] *= ti.exp(-dt * damping)  # apply exp-dampening
    for i in range(NV):
        # ball boundary condition:
        disp = pos[i] - ball_pos
        disp2 = disp.norm_sqr()
        if disp2 <= ball_radius ** 2:
            nov = vel[i].dot(disp)
            if nov < 0:
                vel[i] -= nov * disp / disp2
        # rect boundary condition (the window edges):
        cond = pos[i] < 0 and vel[i] < 0 or pos[i] > 1 and vel[i] > 0
        # in case of collision set the vertices velocity equal to 0
        if cond[0]:
            vel[i][0] = 0
        if cond[1]:
            vel[i][1] = 0
        # update the position based on the velocity
        pos[i] += dt * vel[i]


@ti.kernel
def init_pos():
    """
    initializes the positions and velocities of all vertices and
    a matrix B inverse matrix based upon the starting state of each triangle

    position is based on the id's and a linear offset
    velocities are initialized to 0

    B is use for to calculate the scissor like force which brings the flubbbu back into the starting position
    """
    for i, j in ti.ndrange(N + 1, N + 1):
        k = i * (N + 1) + j
        pos[k] = ti.Vector([i, j]) / N * 0.25 + ti.Vector([0.45, 0.45])  # staring position based on id's
        vel[k] = ti.Vector([0, 0])  # init velocity is 0
    for i in range(NF):  # foreach face ...
        ia, ib, ic = f2v[i]
        a, b, c = pos[ia], pos[ib], pos[ic]
        b_i_inv = ti.Matrix.cols([a - c, b - c])  # calculate the two edges of each face
        B[i] = b_i_inv.inverse()  # invert it because we need it later multiple times to calculate the differences


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
        f2v[k + 0] = [a, b, c]  # first triangle of each square
        f2v[k + 1] = [c, d, a]  # second triangle "  "     "


@ti.kernel
def controller_input(x: int, y: int) -> int:
    """
    applies the controller input,

    the input for both axis are either -1,0,1

    needs a return type for early termination
    """
    if x == 0 and y == 0:
        return 0
    for i in range(NV):
        vel[i] += dt * ti.Vector([x*speed, y*speed])  # apply the controller input
    return 0


init_mesh()
init_pos()
gui = ti.GUI('HAPPY FLUBBBU')
while gui.running:
    x_input, y_input = 0, 0  # encodes the input, (1 , -1) for example means 'S' and 'A' is pressed
    for e in gui.get_events():
        # quit the game with escape
        if e.key == gui.ESCAPE:
            gui.running = False
        # reset the game with r
        elif e.key == 'r':
            init_pos()

        # WASD input
        elif e.key == 'w':
            y_input += 1
        elif e.key == 'a':
            x_input -= 1
        elif e.key == 's':
            y_input -= 1
        elif e.key == 'd':
            x_input += 1

    for _ in range(10):
        with ti.Tape(loss=U):
            update_u()  # update the system
        controller_input(x_input, y_input)  # use the controller input
        advance()  # advance the simulation

    gui.circles(pos.to_numpy(), radius=2, color=0xffaa33)
    gui.circle(ball_pos, radius=ball_radius * 512, color=0x666666)
    gui.show()
