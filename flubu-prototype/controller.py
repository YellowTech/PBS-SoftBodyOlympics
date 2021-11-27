import taichi as ti

# ti.init(arch=ti.gpu)


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
            self.y = 2 - e.type.value # type value: 1 for press, 2 for release
        elif e.key == self.left:
            self.x = -2 + e.type.value
        elif e.key == self.down:
            self.y = -2 + e.type.value
        elif e.key == self.right:
            self.x = 2 - e.type.value

    def getinput(self):
        x_input, y_input = self.x, self.y
        return x_input, y_input


