import taichi as ti

ti.init(arch=ti.gpu)


@ti.data_oriented
class Flubbel:
    def __init__(self, dt: float, speed: float, damping: float):
        self.dt = dt
        self.speed = speed
        self.damping = damping
        self.N = 16  # number of edges in one row i.e. number of vertices - 1
        self.dx = 1 / self.N  # horizontal and vertical edge length
        self.rho = 1e1  # very small rho is basically a rigid body and a big rho results in a liquid
        self.NF = 2 * self.N ** 2  # number of faces
        self.NV = (self.N + 1) ** 2  # number of vertices
        self.E, self.nu = 5e4, 0.4  # Young's modulus and Poisson's ratio
        self.collider_center_idx = int(self.NV / 2)
        # the poisson's ratio determines how much the volume changes when the material is being stretched
        # 0.5 = no volume change
        # <0.5 = volume bigger
        # <0 = material gets thicken when stretched
        # the higher the youngs thingy the stiffer the material
        self.mu, self.lam = self.E / 2 / (1 + self.nu), self.E * self.nu / (1 + self.nu) / (1 - 2 * self.nu)
        # Lame parameters, based on the phys-parameters above
        self.pos = ti.Vector.field(2, float, self.NV, needs_grad=True)  # position of the vertices
        self.vel = ti.Vector.field(2, float, self.NV)  # velocity of the vertices
        self.f2v = ti.Vector.field(3, int, self.NF)  # ids of three vertices of each face
        self.B = ti.Matrix.field(2, 2, float, self.NF)  # inverse matrix based upon the starting state of each triangle,
        # used to calculate the scissor like force which brings the flubbbu back into the starting position
        self.F = ti.Matrix.field(2, 2, float, self.NF, needs_grad=True)  # forces acting on the faces (scissor force)
        # F is also called: deformation gradient
        self.V = ti.field(float, self.NF)  # area of each face (times 2 because it is calculated with the vector cross product)
        self.phi = ti.field(float, self.NF)  # potential energy of each face (Neo-Hookean)
        self.U = ti.field(float, (), needs_grad=True)  # total potential energy

    @ti.kernel
    def update_u(self):
        for i in range(self.NF):
            ia, ib, ic = self.f2v[i]  # id's of face vertices
            a, b, c = self.pos[ia], self.pos[ib], self.pos[ic]  # position of face vertices
            self.V[i] = abs((a - c).cross(b - c))  # calculate the area
            d_i = ti.Matrix.cols([a - c, b - c])  # calculate two triangle edges
            self.F[i] = d_i @ self.B[i]  # scissor force based on starting position difference
        for i in range(self.NF):
            f_i = self.F[i]
            # calculate the total potential energy phi
            # this formulae can be found on:
            # https://en.wikipedia.org/wiki/Neo-Hookean_solid
            # they call it W
            log_j_i = ti.log(f_i.determinant())
            phi_i = self.mu / 2 * ((f_i.transpose() @ f_i).trace() - 2)
            phi_i -= self.mu * log_j_i
            phi_i += self.lam / 2 * log_j_i ** 2  # this part is called the cauchy-green deformation tensor
            self.phi[i] = phi_i
            # total energy is updated by multiplying the strain energy with the area size the strain is on
            self.U[None] += self.V[i] * phi_i

    @ti.kernel
    def advance(self):
        for i in range(self.NV):
            acc = -self.pos.grad[i] / (self.rho * self.dx ** 2)  # acceleration based on the negative gradient of the position
            self.vel[i] += self.dt * acc  # apply the acceleration
            self.vel[i] *= ti.exp(-self.dt * self.damping)  # apply exp-dampening
        for i in range(self.NV):
            # rect boundary condition (the window edges):
            cond = self.pos[i] < 0 and self.vel[i] < 0 or self.pos[i] > 1 and self.vel[i] > 0
            # in case of collision set the vertices velocity equal to 0
            if cond[0]:
                self.vel[i][0] = 0
            if cond[1]:
                self.vel[i][1] = 0
            # update the position based on the velocity
            self.pos[i] += self.dt * self.vel[i]

    @ti.kernel
    def init_pos(self):
        """
        initializes the positions and velocities of all vertices and
        a matrix B inverse matrix based upon the starting state of each triangle

        position is based on the id's and a linear offset
        velocities are initialized to 0

        B is use for to calculate the scissor like force which brings the flubbbu back into the starting position
        """
        for i, j in ti.ndrange(self.N + 1, self.N + 1):
            k = i * (self.N + 1) + j
            self.pos[k] = ti.Vector([i, j]) / self.N * 0.25 + ti.Vector([0.45, 0.45])  # staring position based on id's
            self.vel[k] = ti.Vector([0, 0])  # init velocity is 0
        for i in range(self.NF):  # foreach face ...
            ia, ib, ic = self.f2v[i]
            a, b, c = self.pos[ia], self.pos[ib], self.pos[ic]
            b_i_inv = ti.Matrix.cols([a - c, b - c])  # calculate the two edges of each face
            self.B[i] = b_i_inv.inverse()  # invert it because we need it later multiple times to calculate the differences

    @ti.kernel
    def init_mesh(self):
        """
        initializes the springy mesh.

        by filling the f2v datastructures, which saves the id's of three vertices of each face
        """
        for i, j in ti.ndrange(self.N, self.N):
            k = (i * self.N + j) * 2
            a = i * (self.N + 1) + j
            b = a + 1
            c = a + self.N + 2
            d = a + self.N + 1
            self.f2v[k + 0] = [a, b, c]  # first triangle of each square
            self.f2v[k + 1] = [c, d, a]  # second triangle "  "     "


    def init_flubbel(self):
        self.init_mesh()
        self.init_pos()


    @ti.kernel
    def controller_input(self, x_input: int, y_input: int) -> int:
        """
        applies the controller input,

        the input for both axis are either -1,0,1

        needs a return type for early termination
        """
        if x_input == 0 and y_input == 0:
            return 0
        for i in range(self.NV):
            self.vel[i] += self.dt * ti.Vector([x_input * self.speed, y_input * self.speed])  # apply the controller input
        return 0

