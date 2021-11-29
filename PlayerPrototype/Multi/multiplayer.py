import taichi as ti

zero = ti.Vector([0.0, 0.0])

@ti.data_oriented
class MultiPlayer:
    def __init__(self, playerCount: int = 1, speed: float = 1000.0, damping: float = 20.0):
        self.playerCount = ti.static(playerCount)

        self.speed = speed
        self.damping = damping
        self.spring = 1000
        
        self.radius = 1 # normal distance of springs
        self.collRadius = 0.9 # self and intercollision distance of vertices

        self.input = ti.Vector.field(2, float, self.playerCount) # current inputs

        self.vertPerPlayer = ti.static(3)
        self.vertCount = ti.static(self.vertPerPlayer * self.playerCount)
        self.numLinks = ti.static(self.vertPerPlayer * 3)

        self.pos = ti.Vector.field(2, float, self.vertCount)  # position of the vertices
        self.enabled = ti.field(int, self.vertCount) # 1 if enabled, 0 if disabled
        self.vel = ti.Vector.field(2, float, self.vertCount)  # velocity of the vertices
        self.f = ti.Vector.field(2, float, self.vertCount)  # forces of the vertices
        self.links = ti.Vector.field(2, int, self.numLinks * self.playerCount)  # if first = -1, then no link

    @ti.func
    # player vert to vert
    def pl2l(self, playerId: int, link: int) -> int:
        return self.vertPerPlayer * 3 * playerId + link

    @ti.func
    # player vert to vert
    def pv2v(self, playerId: int, vert: int) -> int:
        return self.vertPerPlayer * playerId + vert

    @ti.func
    # vert to player id
    def v2p(self, vert: int) -> int:
        return vert // self.vertPerPlayer

    @ti.func
    # vert to player vert offset
    def v2pv(self, vert: int) -> int:
        return vert % self.vertPerPlayer

    

    @ti.kernel
    def advance(self, dt: float):
        # apply input
        for i in range(self.vertCount):
            # find which player and do input update
            p = self.v2p(i)
            self.vel[i] += dt * self.speed * self.input[p]  # apply the controller input

        for i in range(self.vertCount):
            self.f[i] = zero # reset force

        # internal forces
        for i in range(self.vertCount):
            if self.enabled[i]:
                # find player number
                p = self.v2p(i)

                # loop through all links of the player
                for l in range(self.pl2l(p, 0), self.pl2l(p, self.numLinks)):
                    link = self.links[l]
                    if link[0] == i:
                        diff = self.pos[link[1]] - self.pos[i]
                        dist = diff.norm()#_sqr()
                        # print("Dist", dist, (self.radius - dist), sep=", ", end="\n")
                        self.f[i] -= diff.normalized() * (self.spring * (self.radius - dist)) # * self.spring * diff.normalized()

                        self.f[link[1]] += diff.normalized() * (self.spring * (self.radius - dist))
                
                # intercolliding forces
                # very slow, loop through aaaaaaall points
                for j in range(self.vertCount):
                    if self.enabled[j] and j != i: # self.v2p(j) != p:
                        diff = self.pos[j] - self.pos[i]
                        dist = diff.norm()
                        if dist < self.collRadius:
                            # colliding, push apart
                            print("Colliding:",i,j,dist,self.collRadius,sep=",",end="\n")
                            # Todo : optimize such that 2 points must only be compared once, not twice like right now
                            self.f[i] -= diff.normalized() * (self.spring * 10 * (self.collRadius - dist)) # * self.spring * diff.normalized()


        # simplectiv Euler
        for i in range(self.vertCount):
            if self.enabled[i]:
                # print("Force",i,self.f[i], sep=",", end="\n")
                # damping
                self.f[i] -= self.damping * self.vel[i]
                self.vel[i] += self.f[i] * dt
                self.pos[i] += dt * self.vel[i]

    @ti.kernel
    def init_pos(self):
        for p in range(self.playerCount):
            for i in range(self.pv2v(p,0), self.pv2v(p,self.vertPerPlayer)):
                j = self.v2pv(i)
                self.pos[i] = ti.Vector([self.radius/2 * j + 1, self.radius/2 * j + 1 + p])
                self.vel[i] = ti.Vector([0.0,0.0])

    @ti.kernel
    def init_mesh(self):
        for p in range(self.playerCount):
            for i in range(self.pl2l(p,0), self.pl2l(p,self.numLinks)):
                # deactivate all links
                self.links[i] = ti.Vector([-1,-1])

            for i in range(self.pv2v(p,0), self.pv2v(p,self.vertPerPlayer)):
                # disable all points
                self.enabled[i] = False
                # self.enabled[i] = 1
                # self.links[i] = ti.Vector([i,(i+1) % self.vertCount])

            # first player specific vert
            x = self.pv2v(p,0)
            self.enabled[x] = True
            self.enabled[x+1] = True
            self.enabled[x+2] = True

            # first player specific link
            l = self.pl2l(p,0)
            self.links[l] =   ti.Vector([x,  x+1])
            self.links[l+1] = ti.Vector([x+1,x+2])
            self.links[l+2] = ti.Vector([x+2,x  ])


    def init(self):
        self.init_mesh()
        self.init_pos()

    def set_input(self, externalInput):
        # print("external " + str(externalInput))
        self.input.from_numpy(externalInput)

