from pygame.constants import QUIT, KEYDOWN
import taichi as ti
import numpy as np
import multiplayer as mpl
import controller as co
import time
from codetiming import Timer
from requests_futures.sessions import FuturesSession
import ujson as json
import pygame as pg

def blend(color, alpha, base=[255,255,255]):
    '''
    color should be a 3-element iterable,  elements in [0,255]
    alpha should be a float in [0,1]
    base should be a 3-element iterable, elements in [0,255] (defaults to white)
    '''
    out = [int(round((alpha * color[i]) + ((1 - alpha) * base[i]))) for i in range(3)]

    return out[0] * 16**4 + out[1] * 255 * 16**2 + out[2]

ti.init(arch=ti.cpu) # , excepthook=True)

players = 2 # number of players

# the big boy
multiPlayer = mpl.MultiPlayer(playerCount=players)

requestsSession = FuturesSession(max_workers=4)

# array to store all inputs in
input = np.zeros((players, 2), dtype=np.float32)

multiPlayer.init()

pg.init()
clock = pg.time.Clock()
running = True
screenRes = 1000
window = pg.display.set_mode((screenRes, screenRes))
renderScale = screenRes / 1000 * 30
window.fill((255, 255, 255))
btn = pg.Rect(0, 0, 100, 30)
rect1 = pg.Rect(0, 30, 100, 100)


# frame timer to find dt
lastFrame = time.time() - (1000/60)
gameBegin = time.time()
deathTimer = 5.0
nextDeath = gameBegin + deathTimer
inputRequest = requestsSession.get('https://input.yellowtech.ch/input')

while running:
    for event in pg.event.get():
        if event.type == QUIT:
            running = False
    
    window.fill((255, 255, 255))

    current = time.time()
    # calculate dt from time since last frame
    dt = (current - lastFrame) * 1000 * 0.0001667 # dt = 0.01 for 60 fps
    lastFrame = current

    if dt > 0.02: # slowdown if under 30 fps
        dt = 0.02 # keep the matrix from glitching

# ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
# ▀█▄░▄█░░░█▄▄▐▀█▀▌▐▀█░▀█░▀█▄░▐▀░ 
# ░█▐█▀▐░░▐▄██░░▌░░▐▄▌░░▌░░░██▀░░ 
# ░█░▌░▐░░▌▀██░░▌░░▐▀▄░░▌░▐▀░▀█▄░ 
# ▄▌░░░▀░▀░░▀▀░▀▀▀░▀░▀▀░▀░▀░░░░▀▀
# ░░░░░░░░░░▄▄▄▄▄▄░░░░░░░░░░░░░░░
# ░░░░░░░░████▀▀███░░░░░░░░░░░░░░
# ░░░░░░░███░░░░░▀██░░░░░░░░░░░░░
# ░░░░░░░███▄░▄▄▄▄██░░░░░░░░░░░░░
# ░░░░░░░████▀▀████▀░░░░░░░░░░░░░
# ░░░░░░░██▄█▄▄░░░░░░░░░░░░░░░░░░
# ░░░░░░░░████▄▄░░░░░░░░░░░░░░░░░
# ░░░░░░░░░██▀░░▄█▄░░░░░░░░░░░░░░
# ░░░░░░░░░████████▄░░░░░░░░░░░░░
# ░░░░░░░░░█████████▄▄▄▄░░░░░░░░░
# ░░░░░░░░▄████████████████▄▄░░░░
# ░░░░░░▄████████████████████░░░░
# ░░░▄████████████████████████░░░
# ░░██████████████████████████▄░░
# ░████████████████████████████░░
# ░████████████████████████████░░
# ░█████████████████████████████░
# ░█████████████████████████████░
# ██████████████████████████████░
# ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

    with Timer(text="INP {:.8f}"):
        if inputRequest.done():
            print("new inputs!")
            inputJSON = json.loads(inputRequest.result().content)
            inputRequest = requestsSession.get('https://input.yellowtech.ch/input')
            
            for p in range(players):
                # if input is current
                if inputJSON[p]["lastInput"] > current - 3:
                    if inputJSON[p]["input"] != "":
                        inp = np.fromstring(inputJSON[p]["input"], dtype=np.float32, sep=",")
                        input[p] = [inp[0],inp[1]]
                        print(input[p])
                else:
                    input[p] = [0,0]

        multiPlayer.set_input(input)  # update the player controller map

    with Timer(text="SIM {:.8f}"):
        epochs = 10 # balance stability with performance
        dt = dt/epochs # adapt dt to #epochs
        for _ in range(epochs):
            multiPlayer.advance(dt)  # advance the simulation

    with Timer(text="GUI {:.8f}"):
        # draw death circle
        if nextDeath < current:
            # death now!
            nextDeath += deathTimer
            # multiPlayer.destruction(renderScale/2, renderScale/2, 5)
        
        alpha = (nextDeath - current) / deathTimer
        color = blend([255,0,0], alpha)

        pg.draw.circle(window, color, (500,500), 7.5*renderScale)
        # gui.circle((0.5, 0.5), color, radius = 7.5*renderScale)


        # get enables mask and use it to get enabled dots
        mask = multiPlayer.enabled.to_numpy()
        mask = list(map(lambda x: False if x > 0 else True,mask))
        allDots = multiPlayer.pos.to_numpy()
        allDots *= renderScale
        dots = np.delete(allDots, list(mask), axis=0)

        # Draw the forces
        forces = multiPlayer.f.to_numpy()
        vel = multiPlayer.vel.to_numpy()
        forces = np.delete(forces, mask, axis=0)
        vel = np.delete(vel, mask, axis=0)

        for i in range(len(forces)):
            # gui.line(begin=dots[i], end=dots[i] + forces[i]/renderScale * 0.01, radius=2, color=0xff0000)
            # gui.line(begin=dots[i], end=dots[i] + vel[i]/renderScale * 0.1, radius=2, color=0x00ff00)
            pg.draw.line(window, 0xff0000, dots[i], dots[i] + forces[i]*renderScale * 0.005, width=3)
            pg.draw.line(window, 0x00ff00, dots[i], dots[i] + vel[i]*renderScale * 0.05, width=3)

        # Get the springs
        links = multiPlayer.links.to_numpy()
        mask = list(map(lambda x: x[0] == -1,links))
        links = np.delete(links, mask, axis=0)

        # # Draw the springs
        for i in range(len(links)):
            # gui.line(begin=allDots[links[i,0]], end=allDots[links[i,1]], radius=2, color=0x444444)
            pg.draw.line(window, 0x444444, allDots[links[i,0]], allDots[links[i,1]], width=3)
        
        # Draw the dots
        # gui.circles(dots, radius=5, color=0x0097a7)
        for dot in dots:
            pg.draw.circle(window, 0x0097a7, dot, 7)

        pg.display.flip()
        clock.tick()
        fps = "{:.2f}".format(clock.get_fps())
        print("FPS: " + fps)
        pg.display.set_caption("FPS: " + fps)


pg.quit()