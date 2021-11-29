import taichi as ti
import numpy as np
import player as pl
import controller as co
import time
from codetiming import Timer
from typing import List, Set, Dict, Tuple, Optional

ti.init(arch=ti.cpu) # , excepthook=True)

renderScale = 20

Players = np.array([
    pl.Player(id=0),
    pl.Player(id=1),
])


PlayerControllers = [
    co.Controller(up='w', down='s', left='a', right='d'),
    co.Controller(up='i', down='k', left='j', right='l')
]

for player in Players:
    player.init()

gui = ti.GUI('Game')
gui.background_color = 0xffffff
# gui.fps_limit = 500 # unlimit the fps
lastFrame = time.time() - (1000/60)

while gui.running:
    current = time.time()
    # dt = 0.0001
    dt = (current - lastFrame) * 1000 * 0.00001667 # dt = 0.001 for 60 fps
    lastFrame = current

    if dt > 0.002: #slowdown if under 30 fps
        dt = 0.002

    with Timer(text="EVE {:.8f}"):
        for e in gui.get_events():
            # quit the game with escape
            if e.key == gui.ESCAPE:
                gui.running = False
            # reset the game with r
            elif e.key == 'r':
                for player in Players:
                    player.init()

            for controller in PlayerControllers:
                controller.eventiter(e)

    with Timer(text="SIM {:.8f}"):
        for _ in range(10):
            for i, player in enumerate(Players):
                x1, y1 = PlayerControllers[i].getinput()
                player.controller_input(dt, x1, y1)  # use the controller input
                player.advance(dt)  # advance the simulation

    with Timer(text="GUI {:.8f}"):
        for player in Players:
            mask = player.enabled.to_numpy()
            mask = list(map(lambda x: False if x > 0 else True,mask))
            dots = player.pos.to_numpy()
            dots = np.delete(dots, list(mask), axis=0)
            dots = dots/renderScale

            # Draw the forces
            forces = player.f.to_numpy()
            vel = player.vel.to_numpy()
            forces = np.delete(forces, mask, axis=0)
            vel = np.delete(vel, mask, axis=0)
            for i in range(len(forces)):
                gui.line(begin=dots[i], end=dots[i] + forces[i]/renderScale * 0.01, radius=2, color=0xff0000)
                gui.line(begin=dots[i], end=dots[i] + vel[i]/renderScale * 0.1, radius=2, color=0x00ff00)


            links = player.links.to_numpy()
            mask = list(map(lambda x: x[0] == -1,links))
            links = np.delete(links, mask, axis=0)

            # Draw the springs
            for i in range(len(links)):
                gui.line(begin=dots[links[i,0]], end=dots[links[i,1]], radius=2, color=0x444444)
                
            gui.circles(dots, radius=5, color=0x0097a7)
            # gui.circles(flubbbuu2.pos.to_numpy(), radius=10, color=0xffab40) the second color
            print(dots)
        gui.show()
