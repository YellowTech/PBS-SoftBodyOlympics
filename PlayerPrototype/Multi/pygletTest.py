import pyglet
import numpy as np
from codetiming import Timer

resolution = 1000
window = pyglet.window.Window(width=resolution, height=resolution)
fps_display = pyglet.window.FPSDisplay(window=window)
label = pyglet.text.Label('Hello, world',
                          font_name='Times New Roman',
                          font_size=36,
                          x=window.width//2, y=window.height//2,
                          anchor_x='center', anchor_y='center')

count = 20000 # 32 * 20

triangle = np.array([-5.0, -2.0, 0.0, 7.0, 5.0, -2.0]).reshape(3,2).transpose().swapaxes(0,1)

rand = np.random.rand(count,2).astype(dtype=np.float32) * resolution

frames = 0

def draw(dt):
    global frames
    global rand
    frames += 1

    window.clear()
    # label.draw()
    # fps_display.draw()

    if (frames % 20 == 0):
        fps = "{:.2f}".format(pyglet.clock.get_fps())
        # print(f"FPS is {fps}")
        window.set_caption(f"FPS: {fps}")

    batch = pyglet.graphics.Batch()

    # vertex_list = batch.add(2, pyglet.gl.GL_TRIANGLES, None,
    #     ('v3i', (10, 15, 30)),
    #     ('c3B', (0, 0, 255))
    # )


    with Timer(text="Creating {:.8f}"):
        
        if(True or frames%100 == 0):
            rand = np.random.rand(count,2).astype(dtype=np.float32) * resolution

        # tup = tuple((rand[:,:,None] + triangle.transpose()).swapaxes(1,2).flatten())
        tup = tuple((rand[:,None,:] + triangle).flatten())

        vertex_list = batch.add(count * 3, pyglet.gl.GL_TRIANGLES, None,
            ('v2f', tup),
            ('c3B', (255,0,0) * (count * 3))
        )
        # pyglet.graphics.draw(count * 3, pyglet.gl.GL_TRIANGLES,
        #     ('v2f', tup)
        # )

        # cs[:].x = rand[:,0]
        # for i in range(count):
        #     cs[i].x=rand[i,0]
        #     cs[i].y=rand[i,1]
            
    # vertex_list = batch.add(2, pyglet.gl.GL_POINTS, None,
    #     ('v2i', (10, 15, 30, 35)),
    #     ('c3B', (0, 0, 255, 0, 255, 0))
    # )
    # pyglet.graphics.draw(2, pyglet.gl.GL_POINTS,
    #     ('v2i', (10, 15, 30, 35))
    # )
    # pyglet.graphics.draw(2, pyglet.gl.GL_POINTS,
    #     ('v2i', (10, 15, 30, 35)),
    #     ('c3B', (0, 0, 255, 0, 255, 0))
    # )
    # for i in cs:
    #     i.draw()

    with Timer(text="Draw {:.8f}"):
        batch.draw()


pyglet.clock.schedule(draw)

pyglet.app.run()