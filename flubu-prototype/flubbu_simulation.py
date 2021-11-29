import taichi as ti
import flubbel as fl
import controller as co
import time
from codetiming import Timer
from typing import List, Set, Dict, Tuple, Optional

ti.init(arch=ti.cpu)

damping = 50
speed = 400 + damping * 2

Flubbels: List[fl.Flubbel] = [
    fl.Flubbel(speed=speed, damping=damping),
    fl.Flubbel(speed=speed, damping=damping)
] # type: List[fl.Flubbel]

FlubbelControllers = [
    co.Controller(up='w', down='s', left='a', right='d'),
    co.Controller(up='i', down='k', left='j', right='l')
]

for flubbel in Flubbels:
    flubbel.init_flubbel()

gui = ti.GUI('HAPPY FLUBBBU')
gui.background_color = 0xffffff
gui.fps_limit = 500 # unlimit the fps
lastFrame = time.time() - (1000/60)

while gui.running:
    current = time.time()
    # dt = 0.0001
    dt = (current - lastFrame) * 1000 * 0.00000833 # dt = 0.005 for 60 fps
    lastFrame = current

    if dt > 0.001: #slowdown if under 30 fps
        dt = 0.001

    with Timer(text="EVE {:.8f}"):
        for e in gui.get_events():
            # quit the game with escape
            if e.key == gui.ESCAPE:
                gui.running = False
            # reset the game with r
            elif e.key == 'r':
                for flubel in Flubbels:
                    flubel.ini

            for controller in FlubbelControllers:
                controller.eventiter(e)

    with Timer(text="SIM {:.8f}"):
        for _ in range(3):
            for i, flubbel in enumerate(Flubbels):
                with ti.Tape(loss=flubbel.U):
                    flubbel.update_u()  # update the system
                x1, y1 = FlubbelControllers[i].getinput()
                flubbel.controller_input(dt, x1, y1)  # use the controller input
                flubbel.advance(dt)  # advance the simulation

    with Timer(text="GUI {:.8f}"):
        for flubbel in Flubbels:
            gui.circles(flubbel.pos.to_numpy(), radius=10, color=0x0097a7)
            # gui.circles(flubbbuu2.pos.to_numpy(), radius=10, color=0xffab40) the second color
        gui.show()
