from os import link
import taichi as ti
import numpy as np
import multiplayer as mpl
import controller as co
import time
from codetiming import Timer
from requests_futures.sessions import FuturesSession
import ujson as json
import pyglet

ti.init(arch=ti.cpu) # , excepthook=True)

players = 1 # number of players

# the big boy
multiPlayer = mpl.MultiPlayer(playerCount=players, damping=30)

with open('flubuMeshes/bigRound.npy', 'rb') as f:
    pos_loaded = np.load(f) * 10
    edges_loaded = np.load(f)
    multiPlayer.init(pos_loaded, edges_loaded)

screenRes = 1000
window = pyglet.window.Window(width=screenRes, height=screenRes)
pyglet.gl.glClearColor(255, 255, 255, 1.0)

mapSize = 40 #40
mapOffset = [-20,-20]
renderScale = screenRes / mapSize

triangle = np.array([-5.0, -2.0, 0.0, 7.0, 5.0, -2.0]).reshape(3,2).transpose().swapaxes(0,1) * 2

def draw(dt, multiPlayer, triangle):
    global mapOffset

    window.clear()
    dt = 0.001 # keep the matrix from glitching
       
    epochs = 10 # balance stability with performance
    dt = dt/epochs # adapt dt to #epochs
    for _ in range(epochs):
        multiPlayer.advance(dt)  # advance the simulation

    batch = pyglet.graphics.Batch()
    
    # get enables mask and use it to get enabled dots
    mask = multiPlayer.enabled.to_numpy()
    mask = list(map(lambda x: False if x > 0 else True,mask))
    allDots = multiPlayer.pos.to_numpy() - mapOffset
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
        ('c3B', (255,255,0) * count * 3)
    )

    # draw the batch in one call -> Superfast
    batch.draw()

    f = abs(forces).sum()
    print(f)
    if f < 1:
        print("done")
        ds = (dots / renderScale + mapOffset)
        ds = ds - np.average(ds, axis=0)

        with open('flubuMeshes/meshOut.npy', 'wb') as f:
            np.save(f, ds)
            np.save(f, links)

        pyglet.app.exit()



pyglet.clock.schedule_interval(draw, 1/60, multiPlayer, triangle)
pyglet.app.run()