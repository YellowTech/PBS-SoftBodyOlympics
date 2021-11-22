import taichi as ti
import flubbel as fl
import controller as co

ti.init(arch=ti.gpu)

dt = 1e-4
damping = 10
speed = 40 + damping * 2

flubbbuu1 = fl.Flubbel(dt=dt, speed=speed, damping=damping)
flubbbuu1.init_flubbel()
flubbbuu1_controller = co.Controller(up='w', down='s', left='a', right='d')

# uncommenting the line below throws an error :O .... whyyyyyyy!?!?!
#flubbbuu2 = fl.Flubbel(dt=dt, speed=speed, damping=damping)


#flubbbuu2.init_flubbel()
#flubbbuu2_controller = co.Controller(up='i', down='k', left='j', right='l')

gui = ti.GUI('HAPPY FLUBBBU')
while gui.running:

    for e in gui.get_events():
        # quit the game with escape
        if e.key == gui.ESCAPE:
            gui.running = False
        # reset the game with r
        elif e.key == 'r':
            flubbbuu1.init_pos()
            #flubbbuu2.init_pos()
        flubbbuu1_controller.eventiter(e)
        #flubbbuu2_controller.eventiter(e)
    x1, y1 = flubbbuu1_controller.getinput()
    #x2, y2 = flubbbuu2_controller.getinput()

    for _ in range(10):
        with ti.Tape(loss=flubbbuu1.U):
            flubbbuu1.update_u()  # update the system
        '''with ti.Tape(loss=flubbbuu2.U):
            flubbbuu2.update_u()'''
        flubbbuu1.controller_input(x1, y1)  # use the controller input
        #flubbbuu2.controller_input(x2, y2)
        flubbbuu1.advance()  # advance the simulation
        #flubbbuu2.advance()

    gui.circles(flubbbuu1.pos.to_numpy(), radius=2, color=0xffaa33)
    #gui.circles(flubbbuu2.pos.to_numpy(), radius=2, color=0xfdaa33)
    gui.show()
