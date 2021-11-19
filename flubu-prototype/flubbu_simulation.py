import taichi as ti
import flubbel as fl

ti.init(arch=ti.gpu)

dt = 1e-4
damping = 10
speed = 40 + damping * 2

a_flubbbuu = fl.Flubbel(dt=dt, speed=speed, damping=damping)

a_flubbbuu.init_mesh()
a_flubbbuu.init_pos()

gui = ti.GUI('HAPPY FLUBBBU')
while gui.running:
    x_input, y_input = 0, 0  # encodes the input, (1 , -1) for example means 'S' and 'A' is pressed
    for e in gui.get_events():
        # quit the game with escape
        if e.key == gui.ESCAPE:
            gui.running = False
        # reset the game with r
        elif e.key == 'r':
            a_flubbbuu.init_pos()

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
        with ti.Tape(loss=a_flubbbuu.U):
            a_flubbbuu.update_u()  # update the system
        a_flubbbuu.controller_input(x_input, y_input)  # use the controller input
        a_flubbbuu.advance()  # advance the simulation

    gui.circles(a_flubbbuu.pos.to_numpy(), radius=2, color=0xffaa33)
    gui.show()
