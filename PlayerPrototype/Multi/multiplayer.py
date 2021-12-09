import numpy as np
import taichi as ti

zero = ti.Vector([0.0, 0.0])

@ti.data_oriented
class MultiPlayer:
    def __init__(self, playerCount: int = 1, speed: float = 1500.0, damping: float = 15.0):
        self.playerCount = ti.static(playerCount)

        self.speed = speed
        self.damping = damping
        self.spring = 3000
        
        self.radius = 1 # normal distance of springs
        self.collRadius = 0.95 # self and intercollision distance of vertices

        self.input = ti.Vector.field(2, float, self.playerCount) # current inputs

        self.vertPerPlayer = ti.static(32)
        self.vertCount = ti.static(self.vertPerPlayer * self.playerCount)
        
        self.linkPerPlayer = ti.static(self.vertPerPlayer * 3)
        self.linkCount = ti.static(self.linkPerPlayer * self.playerCount)

        self.pos = ti.Vector.field(2, float, self.vertCount)  # position of the vertices
        self.enabled = ti.field(int, self.vertCount) # 1 if enabled, 0 if disabled
        self.vel = ti.Vector.field(2, float, self.vertCount)  # velocity of the vertices
        self.f = ti.Vector.field(2, float, self.vertCount)  # forces of the vertices
        self.links = ti.Vector.field(2, int, self.linkCount)  # if first = -1, then no link

        self.playerCenters = ti.Vector.field(2, float, self.playerCount) # center of all players vertices
        self.playerVertsActive = ti.field(int, self.playerCount) # number of active verts per player

        self.frame = ti.field(int, 1) # current frame

    @ti.pyfunc
    # player vert to vert
    def pl2l(self, playerId: int, link: int) -> int:
        return self.vertPerPlayer * 3 * playerId + link

    @ti.pyfunc
    # player vert to vert
    def pv2v(self, playerId: int, vert: int) -> int:
        return self.vertPerPlayer * playerId + vert

    @ti.pyfunc
    # vert to player id
    def v2p(self, vert: int) -> int:
        return vert // self.vertPerPlayer

    @ti.pyfunc
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
                for l in range(self.pl2l(p, 0), self.pl2l(p, self.linkPerPlayer)):
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
                            # print("Colliding:",i,j,dist,self.collRadius,sep=",",end="\n")
                            # Todo : optimize such that 2 points must only be compared once, not twice like right now
                            self.f[i] -= diff.normalized() * (self.spring  * (-1 + (1.0 + self.collRadius - dist)**5)) # * self.spring * diff.normalized()


        # simplectiv Euler
        for i in range(self.vertCount):
            if self.enabled[i]:
                # print("Force",i,self.f[i], sep=",", end="\n")
                # damping
                self.f[i] -= self.damping * self.vel[i]
                self.vel[i] += self.f[i] * dt
                self.pos[i] += dt * self.vel[i]

        # calculate the mean center
        # x = self.frame[0] % self.playerCount
        # for p in range(x, x+1):
        for p in range(self.playerCount):
            self.playerCenters[p] = zero # reset position
            self.playerVertsActive[p] = 0
            # add to centers
            for i in range(self.pv2v(p,0), self.pv2v(p,self.vertPerPlayer)):
                if(self.enabled[i]):
                    self.playerCenters[p] += self.pos[i]
                    self.playerVertsActive[p] += 1


            # self.playerCenters[p] /= ti.Vector([self.playerVertsActive[p],  self.playerVertsActive[p]])
            self.playerCenters[p] /= self.playerVertsActive[p]

        
        self.frame[0] += 1

    @ti.kernel
    def destruction(self, x:float, y:float, r:float):
        deathCenter = ti.Vector([x,y])
        # loop through all points and disable those in range
        for i in range(self.vertCount):     
            if(self.enabled[i]):
                # check if in death distance
                diff = self.pos[i] - deathCenter
                dist = diff.norm()
                if (dist < r + self.collRadius):
                    self.enabled[i] = False

        # disable all links with a disabled points
        for l in range(self.linkCount):
            if(self.links[l][0] != -1):
                a = self.links[l][0]
                b = self.links[l][1]
                if not self.enabled[a] or not self.enabled[b]:
                    self.links[l] = ti.Vector([-1,-1])

    # disable all player verts and links
    @ti.kernel
    def killPlayer(self, p:int):
        for i in range(self.pv2v(p,0), self.pv2v(p,self.vertPerPlayer)):
            self.enabled[i] = False
        
        for l in range(self.pl2l(p,0), self.pl2l(p,self.linkPerPlayer)):
            self.links[l] = ti.Vector([-1,-1])

    # destroy all points that are outside play area
    @ti.kernel
    def killBorders(self, offsetX: float, offsetY: float, size: float):
        minim = ti.Vector([offsetX,offsetY])
        maxim = ti.Vector([offsetX + size,offsetY + size])
        # loop through all points and disable those outside the area
        for i in range(self.vertCount):     
            if(self.enabled[i]):
                # check if outside the area
                pos = self.pos[i]
                if (pos[0] < minim[0] or pos[0] > maxim[0]
                    or pos[1] < minim[1] or pos[1] > maxim[1] ):
                    self.enabled[i] = False

        # disable all links with a disabled points
        for l in range(self.linkCount):
            if(self.links[l][0] != -1):
                a = self.links[l][0]
                b = self.links[l][1]
                if not self.enabled[a] or not self.enabled[b]:
                    self.links[l] = ti.Vector([-1,-1])

    @ti.kernel
    def init_default(self):
        for p in range(self.playerCount):
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

            for i in range(self.pv2v(p,0), self.pv2v(p,self.vertPerPlayer)):
                j = self.v2pv(i)
                self.pos[i] = ti.Vector([self.radius/2 * j + 1, self.radius/2 * j + 1 + p])
                self.vel[i] = ti.Vector([0.0,0.0])

    @ti.kernel
    def init_mesh(self):
        for p in range(self.playerCount):
            for i in range(self.pl2l(p,0), self.pl2l(p,self.linkPerPlayer)):
                # deactivate all links
                self.links[i] = ti.Vector([-1,-1])

            for i in range(self.pv2v(p,0), self.pv2v(p,self.vertPerPlayer)):
                # disable all points
                self.enabled[i] = False

    # not a kernel because of numpy
    def init_with_numpy(self, points, links):
        for p in range(self.playerCount):
            for i, point in enumerate(points):
                self.enabled[self.pv2v(p,i)] = True

                # move and scale
                point *= self.radius
                # point[0] += 5

                x = point[0] + 3*p
                y = point[1]
                self.pos[self.pv2v(p,i)] = ti.Vector([x,y])

            for i, link in enumerate(links):
                # find points to link and add link
                a = self.pv2v(p, link[0])
                b = self.pv2v(p, link[1])
                self.links[self.pl2l(p,i)] = ti.Vector([a,b])


    def init(self, points, links):
        if self == None and links == None:
            points, links = self.roundMesh()
            
        self.init_mesh()
        # self.init_default()
        self.init_with_numpy(points, links)

    def set_input(self, externalInput):
        # print("external " + str(externalInput))
        self.input.from_numpy(externalInput)

    def roundMesh(self):
        points = np.array([
            [1,0],
            [2,0],
            [0,1],
            [1.5,1],
            [2.5,1],
            [1,2],
            [2,2]
        ], dtype=np.float32)

        links = np.array([
            [0,1], # 0
            [0,2],
            [0,3],
            [1,3], # 3
            [1,4],
            [2,3],
            [3,4], # 6
            [2,5],
            [3,5],
            [3,6], # 9
            [4,6],
            [5,6],
        ], dtype=int)

        return points, links

