import taichi as ti

ti.init(arch=ti.gpu)


class Controller:
    def __init__(self, up: chr, down: chr, left: chr, right: chr):
        self.up = up
        self.down = down
        self.left = left
        self.right = right
        self.x = 0
        self. y = 0

    def eventiter(self, e):
        if e.key == self.up:
            self.y += 1
        elif e.key == self.left:
            self.x -= 1
        elif e.key == self.down:
            self.y -= 1
        elif e.key == self.right:
            self.x += 1

    def getinput(self):
        x_input, y_input = self.x, self.y
        self.x, self.y = 0, 0
        return x_input, y_input


