import taichi as ti
import numpy as np
import multiplayer as mpl
import controller as co
import time
from codetiming import Timer
from requests_futures.sessions import FuturesSession
import ujson as json
import pyglet

def blend(color, alpha, base=[255,255,255]):
    '''
    color should be a 3-element iterable,  elements in [0,255]
    alpha should be a float in [0,1]
    base should be a 3-element iterable, elements in [0,255] (defaults to white)
    '''
    out = [int(round((alpha * color[i]) + ((1 - alpha) * base[i]))) for i in range(3)]

    return out[0] * 16**4 + out[1] * 255 * 16**2 + out[2]

ti.init(arch=ti.cpu) # , excepthook=True)

players = 20 # number of players
playerColors = [[0,0,255] for i in range(players)]

# the big boy
multiPlayer = mpl.MultiPlayer(playerCount=players)

requestsSession = FuturesSession(max_workers=4)

# array to store all inputs in
input = np.zeros((players, 2), dtype=np.float32)

multiPlayer.init()


screenRes = 1000
window = pyglet.window.Window(width=screenRes, height=screenRes)
pyglet.gl.glClearColor(255, 255, 255, 1.0)

renderScale = screenRes / 1000 * 30


# frame timer to find dt
lastFrame = time.time() - (1000/60)
deathTimer = 5.0
nextDeath = time.time() + deathTimer
frames = 0
inputRequest = requestsSession.get('https://input.yellowtech.ch/input')

# wait for request to finish to get count and colors
responseJSON = json.loads(inputRequest.result().content)

triangle = np.array([-5.0, -2.0, 0.0, 7.0, 5.0, -2.0]).reshape(3,2).transpose().swapaxes(0,1) * 2


for p in range(players):
    h = responseJSON[p]["color"].lstrip('#')
    playerColors[p] = list(int(h[i:i+2], 16) for i in (0, 2, 4))

playerColorsRepeated = np.array(playerColors).repeat(multiPlayer.vertPerPlayer, axis=0)

def draw(dt, multiPlayer, triangle):
    global lastFrame
    global deathTimer
    global nextDeath
    global inputRequest
    global frames
    global playerColorsRepeated

    frames += 1
    
    window.clear()

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
                        input[p] = [inp[0],-inp[1]]
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

        # pg.draw.circle(window, color, (500,500), 7.5*renderScale)
        # gui.circle((0.5, 0.5), color, radius = 7.5*renderScale)

        batch = pyglet.graphics.Batch()
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
        count = dots.shape[0]

        # Draw Forces and Velocities
        buf = np.zeros((count*2,2), dtype=np.float32)
        buf[0::2] = dots
        buf[1::2] = dots + (forces*renderScale * 0.004)
        linkList = batch.add(count * 2, pyglet.gl.GL_LINES, None,
            ('v2f', buf.flatten()),
            ('c3B', (200,0,0) * (count * 2))
        )

        buf[1::2] = dots + (vel*renderScale * 0.05)
        linkList = batch.add(count * 2, pyglet.gl.GL_LINES, None,
            ('v2f', buf.flatten()),
            ('c3B', (0,200,0) * (count * 2))
        )

        # Get the springs
        links = multiPlayer.links.to_numpy()
        maskList = list(map(lambda x: x[0] == -1,links))
        links = np.delete(links, maskList, axis=0)

        # Draw the springs
        linkCount = links.shape[0]
        buf = np.zeros((linkCount * 2,2), dtype=np.float32)
        buf[0::2] = allDots[links[:,0]]
        buf[1::2] = allDots[links[:,1]]
        linkList = batch.add(linkCount * 2, pyglet.gl.GL_LINES, None,
            ('v2f', buf.flatten()),
            ('c3B', (20,20,20) * (linkCount * 2))
        )

        # Draw the dots        
        dotList = batch.add(count * 3, pyglet.gl.GL_TRIANGLES, None,
            ('v2f', (dots[:,None,:] + triangle).flatten()),
            ('c3B', playerColorsRepeated[~ np.array(mask)].repeat(3,axis=0).flatten())
        )

        # draw the batch in one call -> Superfast
        batch.draw()

        # set title to current fps
        if (frames % 20 == 0):
            fps = "{:.2f}".format(pyglet.clock.get_fps())
            window.set_caption(f"FPS: {fps}")


pyglet.clock.schedule(draw, multiPlayer, triangle)
pyglet.app.run()