from os import sep
import taichi as ti

# ti.init(arch=ti.gpu)

zero = ti.Vector([0.0, 0.0])

@ti.data_oriented
class Player:
    def __init__(self, id:int, speed: float = 1000.0, damping: float = 20.0):
        self.id = id
        self.speed = speed
        self.damping = damping

        self.spring = 1000
        
        self.radius = 1 # normal distance of springs
        self.collRadius = 0.8 # self and intercollision distance of vertices

        self.vertCount = 32
        self.numLinks = self.vertCount * 3
        self.pos = ti.Vector.field(2, float, self.vertCount)  # position of the vertices
        self.enabled = ti.field(int, self.vertCount) # 1 if enabled, 0 if disabled
        self.vel = ti.Vector.field(2, float, self.vertCount)  # velocity of the vertices
        self.f = ti.Vector.field(2, float, self.vertCount)  # forces of the vertices
        self.links = ti.Vector.field(2, int, self.numLinks)  # if first = -1, then no link

    @ti.kernel
    def advance(self, dt: float):
        for i in range(self.vertCount):
            self.f[i] = zero # reset force

        # internal forces
        for i in range(self.vertCount):
            if self.enabled[i] == 1:

                # loop through all links
                for l in range(self.numLinks):
                    link = self.links[l]
                    if link[0] == i:
                        diff = self.pos[link[1]] - self.pos[i]
                        dist = diff.norm()#_sqr()
                        print("Dist", dist, (self.radius - dist), sep=", ", end="\n")
                        self.f[i] -= diff.normalized() * (self.spring * (self.radius - dist)) # * self.spring * diff.normalized()

                        self.f[link[1]] += diff.normalized() * (self.spring * (self.radius - dist))

        # simplectiv Euler
        for i in range(self.vertCount):
            if(self.enabled[i] == 1):
                print("Force",i,self.f[i], sep=",", end="\n")
                # damping
                self.f[i] -= self.damping * self.vel[i]
                self.vel[i] += self.f[i] * dt
                self.pos[i] += dt * self.vel[i]

    @ti.kernel
    def init_pos(self):
        for i in range(self.vertCount):
            self.pos[i] = ti.Vector([self.radius/2 * i + 1, self.radius/2 * i + 1])
            self.vel[i] = ti.Vector([0.0,0.0])

    @ti.kernel
    def init_mesh(self):
        for i in range(self.numLinks):
            # deactivate all links
            self.links[i] = ti.Vector([-1,-1])

        for i in range(self.vertCount):
            # disable all points
            self.enabled[i] = 0
            # self.enabled[i] = 1
            # self.links[i] = ti.Vector([i,(i+1) % self.vertCount])

        
        self.enabled[0] = 1
        self.enabled[1] = 1
        self.enabled[2] = 1

        self.links[0] = ti.Vector([0,1])
        self.links[1] = ti.Vector([1,2])
        self.links[2] = ti.Vector([2,0])


    def init(self):
        self.init_mesh()
        self.init_pos()


    @ti.kernel
    def controller_input(self, dt: float, x_input: int, y_input: int) -> int:
        """
        applies the controller input,

        the input for both axis are either -1,0,1

        needs a return type for early termination
        """
        if x_input == 0 and y_input == 0:
            return 0
        for i in range(self.vertCount):
        # for i in range(1):
            self.vel[i] += dt * ti.Vector([x_input * self.speed, y_input * self.speed])  # apply the controller input
        return 0

