import random
from kivy.graphics import Rectangle, Ellipse
from kivy.core.window import Window

# tank class declaration - the player controled object
class Tank:
    def __init__(self,game,tile_size):
        self.game = game
        self.tile_size = tile_size
        self.pos = [Window.width / 2 - self.tile_size / 2, self.tile_size]
        self.textures = ["resources/tank.png", "resources/tank2.png", "resources/tank3.png"]
        self.shield_texture = "resources/shield.png"
        self.shield_status = False
        self.shield_on_canvas = False
        self.shield_time = 0
        self.curr_frame = 0
        self.blink_dt = 0.2
        self.draw = Rectangle(source=self.textures[self.curr_frame], pos=self.pos, size=(self.tile_size, self.tile_size))
        self.shield = Rectangle(source=self.shield_texture, pos=self.pos, size=(self.tile_size * 2, self.tile_size * 2))
        self.exp_rec = [Rectangle(source="resources/tank_des.png", tex_coords=[0, 1 / 15, 1, 1 / 15, 1, 0, 0, 0],
                                  size=(self.tile_size * 3, self.tile_size * 2)), 1]

    def check_shield(self, dt):
        if self.shield_time > 0:
            self.shield_time -= dt
            if self.shield_time < 2.5:
                self.shield_blink(dt)
        if self.shield_time < 0:
            self.shield_status = False
            self.shield_on_canvas = False
            self.game.canvas.remove(self.shield)
            self.shield_time = 0

    def shield_on(self):
        if not self.shield_status:
            self.shield_status = True
            self.shield_on_canvas = True
            self.game.canvas.add(self.shield)
        self.shield_time = 12

    def shield_blink(self, dt):
        self.blink_dt -= dt
        if self.blink_dt < 0:
            if self.shield_on_canvas:
                self.game.canvas.remove(self.shield)
                self.shield_on_canvas = False
            elif not self.shield_on_canvas:
                self.game.canvas.add(self.shield)
                self.shield_on_canvas = True
            self.blink_dt = 0.2

    def hit(self):
        for i in self.game.balls.container:
            if self.game.collision(i[0], self.draw, 0.15):
                self.game.gameover()

    def firing(self):
        if self.game.firing:
            self.draw.source = self.textures[self.curr_frame]
            self.curr_frame -= 1
        if self.curr_frame == -1:
            self.curr_frame = 2
        if not self.game.firing:
            self.curr_frame = 0
            self.draw.source = self.textures[self.curr_frame]

    def explosion(self, i, pos):
        self.exp_rec[0].pos = (pos[0] - self.tile_size, pos[1])
        self.exp_rec[0].tex_coords = [0, i / 15 + 1 / 15 + 1 / 3000, 1, i / 15 + 1 / 15 + 1 / 3000, 1,
                                      i / 15 + 1 / 3000, 0, i / 15 + 1 / 3000]
        self.exp_rec[1] += 1
        if self.exp_rec[1] == 15:
            self.exp_rec[1] = 14


# bullets shot by the player
class Bullets:
    def __init__(self, game, tile_size):
        self.game = game
        self.tile_size = tile_size
        self.pos = [100, 100]
        self.container = []

    def fire(self, pos):
        self.container.append(Rectangle(source="resources/bullet.png", pos=pos, size=(self.tile_size / 8, self.tile_size / 8)))

    def move_up(self, dt):
        i = 0
        while i < len(self.container):
            x = self.container[i].pos[0]
            y = self.container[i].pos[1] + self.tile_size * dt * 8
            self.container[i].pos = (x, y)
            if y > Window.height:
                self.container.pop(i)
            i += 1

    def destroy(self, i):
        self.game.canvas.remove(self.container[i])
        self.container.pop(i)


# class that generates balls
class Balls:
    def __init__(self, game, tile_size):
        self.game = game
        self.tile_size = tile_size
        self.pos = [100, 100]
        self.container = []

    def spawn(self):
        l_r = random.choice([-1, 1])
        pos = ()
        if l_r == 1:
            ran = random.randint(round(self.tile_size / 2), round(self.tile_size))
            pos = (ran * -1, Window.height / 2)
        if l_r == -1:
            pos = (
            random.randint(round(Window.width + self.tile_size / 2), round(Window.width + self.tile_size)), Window.height / 2)
        self.container.append(
            [Ellipse(source="resources/ball.png", pos=pos, size=(self.tile_size / 2, self.tile_size / 2)), 0,
             self.tile_size * 0.02 * l_r, self.tile_size * 0.01 * -random.randint(8, 10),
             3, 1])

    def movement(self, dt):
        for i in range(len(self.container)):
            if self.tile_size / 4 < self.container[i][0].pos[0] < Window.width - 1.25 * self.tile_size:
                self.container[i][5] = 0
            if self.container[i][5] == 0:
                if self.container[i][0].pos[0] > Window.width - self.tile_size / 2:
                    self.container[i][2] *= -1
                if self.container[i][0].pos[0] < 0:
                    self.container[i][2] *= -1
                if self.container[i][0].pos[1] < self.tile_size:
                    self.container[i][1] = 0

            dvy = self.container[i][3] + 10 * self.container[i][1]
            vy = self.container[i][0].pos[1] - dvy
            vx = self.container[i][0].pos[0] + self.container[i][2] * dt * self.tile_size * 0.7

            self.container[i][1] += dt
            self.container[i][0].pos = (vx, vy)

        self.check_bullet_hit()

        if self.game.tank.shield_status:
            self.check_shield_hit()

        if self.game.laser.laser_status:
            self.check_laser_hit()

    def check_bullet_hit(self):
        i = 0
        while i < len(self.container):
            for j in self.game.bullets.container:
                if self.game.collision(j, self.container[i][0]):
                    self.container[i][4] -= 1
                    if self.container[i][4] == 0:
                        self.destroy(i)
                    self.game.bullets.destroy(self.game.bullets.container.index(j))
                    break
            i += 1

    def check_shield_hit(self):
        i = 0
        while i < len(self.container):
            if self.game.collision(self.container[i][0], self.game.tank.shield, 0.2):
                self.destroy(i)
                break
            i += 1

    def check_laser_hit(self):
        i = 0
        while i < len(self.container):
            if (self.game.laser.laser.pos[0] + self.game.laser.laser.size[0] > self.container[i][0].pos[0] > self.game.laser.laser.pos[
                0]) or (
                    self.game.laser.laser.pos[0] < self.container[i][0].pos[0] + self.container[i][0].size[0] <
                    self.game.laser.laser.pos[0] + self.game.laser.laser.size[0]):
                self.destroy(i)
                break
            i += 1

    def destroy(self, i):
        self.game.explosion.add_exp([self.container[i][0].pos[0] + self.container[i][0].size[0] / 2,
                                self.container[i][0].pos[1] + self.container[i][0].size[1] / 2], 1)
        self.game.bonus.spawn([self.container[i][0].pos[0] + self.container[i][0].size[0] / 2,
                          self.container[i][0].pos[1] + self.container[i][0].size[1] / 2])
        self.game.canvas.remove(self.container[i][0])
        self.container.pop(i)
        self.game.score += 1
        self.game.pop_sound.play()
        self.game.canvas.remove(self.game.score_text)
        self.game.score_text = self.game.add_text(f"Score: {self.game.score}", self.tile_size / 2, 0.25 * self.tile_size,
                                        Window.height - 0.75 * self.tile_size, (self.tile_size * 2, self.tile_size))
        self.game.canvas.add(self.game.score_text)


# class that adds animations whenever the ball is destroyed
class Explosion:
    def __init__(self, game, tile_size):
        self.game = game
        self.tile_size = tile_size
        self.container = []
        self.pos = [100, 100]
        self.texture = "resources/destroy.png"

    def add_exp(self, pos, frame):
        self.container.append([Rectangle(source=self.texture, tex_coords=[0, 1 / 14, 1, 1 / 14, 1, 0, 0, 0],
                                         pos=(pos[0] - self.tile_size / 2, pos[1] - self.tile_size / 2),
                                         size=(self.tile_size, self.tile_size)), frame])
        self.game.canvas.add(self.container[-1][0])

    def animation(self):
        i = 0
        while i < len(self.container):
            self.container[i][1] += 1
            self.container[i][0].tex_coords = [0, self.container[i][1] / 14 + 1 / 14, 1,
                                               self.container[i][1] / 14 + 1 / 14, 1, self.container[i][1] / 14, 0,
                                               self.container[i][1] / 14]
            if self.container[i][1] == 14:
                self.container.pop(i)
            i += 1

# class that generates bonuses
class Bonus:
    def __init__(self, game, tile_size):
        self.game = game
        self.tile_size = tile_size
        self.container = []
        self.texture = "resources/crate.png"
        self.texture_l = "resources/crateL.png"

    def events(self, dt):
        self.fall(dt)
        self.collection()

    def spawn(self, pos):
        if random.randint(0, 5) == 1:
            if random.randint(0, 2) == 1:
                self.container.append([Rectangle(source=self.texture, pos=pos, size=(self.tile_size / 2, self.tile_size / 2)), 0])
                self.game.canvas.add(self.container[-1][0])
            else:
                self.container.append(
                    [Rectangle(source=self.texture_l, pos=pos, size=(self.tile_size / 2, self.tile_size / 2)), 1])
                self.game.canvas.add(self.container[-1][0])

    def fall(self, dt):
        for i in self.container:
            y = i[0].pos[1]
            if y > self.tile_size:
                y -= dt * self.tile_size * 5
                i[0].pos = (i[0].pos[0], y)
            else:
                i[0].pos = (i[0].pos[0], self.tile_size)

    def collection(self):
        i = 0
        while i < len(self.container):
            if self.game.collision(self.container[i][0], self.game.tank.draw):
                self.game.canvas.remove(self.container[i][0])
                if self.container[i][1] == 0:
                    self.game.tank.shield_on()
                if self.container[i][1] == 1:
                    self.game.lasers_left += 1
                    self.game.canvas.remove(self.game.laser_text)
                    self.game.laser_text = self.game.add_text(f": {self.game.lasers_left}", self.tile_size / 2, self.tile_size,
                                                    Window.height - 1.5 * self.tile_size, (self.tile_size * 2, self.tile_size))
                    self.game.canvas.add(self.game.laser_text)
                self.container.pop(i)
            i += 1


# class that animates Laser bonus
class Laser:
    def __init__(self, game, tile_size):
        self.game = game
        self.tile_size = tile_size
        self.container = []
        self.texture = "resources/mine.png"
        self.texture_l = "resources/laser.png"
        self.laser_status = False
        self.time = 0
        self.laser = Rectangle(source=self.texture, size=(self.tile_size * 0.75, self.tile_size * 0.75))

    def spawn(self, pos):
        if self.laser_status:
            self.remove_animation()
            self.game.canvas.remove(self.laser)
        self.laser_status = True
        self.time = 10
        self.laser.pos = pos
        self.add_animation(pos, -1)
        self.game.canvas.add(self.laser)

    def check_time(self, dt):
        if self.time > 0:
            self.animation()
            self.time -= dt
        if self.time < 0:
            self.laser_status = False
            self.game.canvas.remove(self.laser)
            self.remove_animation()
            self.time = 0

    def add_animation(self, pos, frame):
        for i in range(round((Window.height - self.tile_size) / (self.tile_size * 0.75))):
            self.container.append([Rectangle(source=self.texture_l, tex_coords=[0, 1 / 15, 1, 1 / 15, 1, 0, 0, 0],
                                             pos=(pos[0], pos[1] + self.tile_size * 0.75 * i),
                                             size=(self.tile_size * 0.75, self.tile_size * 0.75)), frame])
            self.game.canvas.add(self.container[-1][0])

    def remove_animation(self):
        for i in self.container:
            self.game.canvas.remove(i[0])
        self.container = []

    def animation(self):
        i = 0
        while i < len(self.container):
            self.container[i][1] += 1
            self.container[i][0].tex_coords = [0, self.container[i][1] / 15 + 1 / 15, 1,
                                               self.container[i][1] / 15 + 1 / 15, 1, self.container[i][1] / 15, 0,
                                               self.container[i][1] / 15]
            if self.container[i][1] == 14:
                self.container[i][1] = 0
            i += 1