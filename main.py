import random

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Ellipse
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.text import Label as CoreLabel
from kivy.core.audio import SoundLoader

Config.set('kivy', 'window_icon', "resources/tank.png")

#window size declaration
Window.size = (540,960)

#declaration of tile size which is later used in order to properly place objects on screen
tile_size = Window.width / 6


#main game class
class GameWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_again_text = None
        self.laser = Laser()
        self.bonus = Bonus()
        self.balls = Balls()
        self.explosion = Explosion()
        self.bullets = Bullets()
        self.pause = True
        self.tank = Tank()
        self.touch_x = 100
        self.touch_y = 100
        self.firing = False
        self.dead = False
        self.time_since_dead = 5
        self.score = 0
        self.lasers_left = 0
        self.clouds = [Rectangle(source="resources/cloud1.png", image_ratio=0.5,
                                 pos=(0.5 * tile_size, Window.height - tile_size * 3),
                                 size=(tile_size * 3, tile_size * 1.5)),
                       Rectangle(source="resources/cloud2.png", pos=(tile_size * 3, Window.height - tile_size * 3),
                                 size=(tile_size * 3, tile_size * 1.5)),
                       Rectangle(source="resources/cloud2.png", pos=(-2 * tile_size, Window.height - tile_size * 3),
                                 size=(tile_size * 2, tile_size * 1))]

        with self.canvas:
            Rectangle(source="resources/bbg.png", pos=(0, 0), size=(Window.width, Window.height))
            Rectangle(source="resources/bg.png", pos=(0, 0), size=(Window.width, Window.height / 2))
            for i in range(8):
                Rectangle(source="resources/grass1.png", pos=(0 + i * tile_size, 0), size=(tile_size, tile_size))
            Rectangle(source=self.laser.texture, pos=(tile_size/4, Window.height - tile_size* 1.5), size=(0.75 * tile_size, 0.75 * tile_size))

        self.add_clouds()
        self.start_text = self.add_text("Click to play", tile_size / 2, Window.width / 2 - tile_size * 1.5,
                                        Window.height / 2, (tile_size * 2, tile_size))
        self.canvas.add(self.start_text)
        self.score_text = self.add_text(f"Score: {self.score}", tile_size / 2, 0.25 * tile_size,
                                        Window.height - 0.75 * tile_size, (tile_size * 2, tile_size))
        self.canvas.add(self.score_text)
        self.laser_text = self.add_text(f": {self.lasers_left}", tile_size / 2, tile_size,
                                        Window.height - 1.5 * tile_size, (tile_size * 2, tile_size))
        self.canvas.add(self.laser_text)

        self.shot_sound = SoundLoader.load("resources/pop.wav")
        self.pop_sound = SoundLoader.load("resources/crack.wav")

        Clock.schedule_interval(self.every_frame, 0)
        Clock.schedule_interval(self.fire, 0.15)

    def on_touch_down(self, touch):
        self.firing = True
        self.touch_x = touch.x
        self.touch_y = touch.y
        if self.pause and self.time_since_dead >= 5:
            self.pause = False
            self.game_reset()
        if tile_size/4 < touch.x < tile_size and Window.height - tile_size * 1.5 < touch.y < Window.height - tile_size * 0.75 and self.lasers_left > 0:
            self.laser.spawn(self.tank.draw.pos)
            self.lasers_left -= 1
            self.canvas.remove(self.laser_text)
            self.laser_text = self.add_text(f": {self.lasers_left}", tile_size / 2, tile_size,
                                            Window.height - 1.5 * tile_size, (tile_size * 2, tile_size))
            self.canvas.add(self.laser_text)

    def on_touch_up(self, touch):
        self.firing = False

    def on_touch_move(self, touch):
        self.touch_x = touch.x
        self.touch_y = touch.y

    def add_bullet(self):
        self.shot_sound.play()
        self.bullets.fire((self.tank.draw.pos[0] + tile_size / 2 - tile_size / 16, self.tank.draw.pos[1] + tile_size))
        self.canvas.add(self.bullets.container[-1])

    def add_ball(self, dt):
        if random.randint(0, int(1.2 / dt)) == 1:
            self.balls.spawn()
            self.canvas.add(self.balls.container[-1][0])

    def every_frame(self, dt):
        if not self.pause:
            self.player_move(dt)
            self.add_ball(dt)
            self.tank.hit()
            self.tank.firing()
            self.tank.check_shield(dt)
        self.laser.check_time(dt)
        self.explosion.animation()
        self.bullets.move_up(dt)
        self.balls.movement(dt)
        self.move_clouds(dt)
        self.bonus.events(dt)
        if self.dead:
            self.time_since_dead += dt
            self.tank.explosion(self.tank.exp_rec[1], self.tank.draw.pos)
        if self.time_since_dead > 5 and self.pause == True:
            self.start_again_text = self.add_text("Click to play again", tile_size / 3, Window.width / 2 - tile_size*1.5,
                                            Window.height / 2, (tile_size * 2, tile_size))
            self.canvas.add(self.start_again_text)

    def collision(self, e1, e2, reduction=0.0):
        r1x = e1.pos[0]
        r1y = e1.pos[1]
        r2x = e2.pos[0] + reduction * tile_size
        r2y = e2.pos[1] + reduction * tile_size
        r1w = e1.size[0]
        r1h = e1.size[1]
        r2w = e2.size[0] - 2 * reduction * tile_size
        r2h = e2.size[1] - 2 * reduction * tile_size

        if r1x < r2x + r2w and r1x + r1w > r2x and r1y < r2y + r2h and r1y + r1h > r2y:
            return True
        else:
            return False

    def player_move(self, dt):

        x = self.tank.draw.pos[0]

        size = tile_size * 6 * dt

        if self.firing == True and self.touch_x > x + tile_size / 2 and x < Window.width - tile_size and self.touch_y < Window.height - 2*tile_size:
            x += size
        if self.firing == True and self.touch_x < x + tile_size / 2 and x > 0 and self.touch_y < Window.height - 2*tile_size:
            x -= size

        self.tank.draw.pos = (x, self.tank.draw.pos[1])
        self.tank.shield.pos = (self.tank.draw.pos[0] - tile_size / 2, self.tank.draw.pos[1])

    def fire(self, dt):
        if self.firing == True and self.pause == False:
            self.add_bullet()

    def move_clouds(self, dt):
        for i in range(0, len(self.clouds)):
            if self.clouds[i].pos[0] < Window.width:
                self.clouds[i].pos = (self.clouds[i].pos[0] + dt * 20, self.clouds[i].pos[1])
            else:
                self.clouds[i].pos = (-3 * tile_size, self.clouds[i].pos[1])

    def add_clouds(self):
        for i in self.clouds:
            self.canvas.add(i)

    def add_text(self, text, size, x, y, recsize):
        self.rect = Rectangle(pos=(x, y), size=recsize)
        label = CoreLabel(text=text, font_name="resources/Font1.ttf", font_size=size)
        label.refresh()
        text = label.texture
        pos = (x, y)
        return Rectangle(size=text.size, pos=pos, texture=text)

    def gameover(self):
        self.pause = True
        self.dead = True
        self.time_since_dead = 0
        self.canvas.remove(self.tank.draw)
        self.canvas.add(self.tank.exp_rec[0])

    def game_reset(self):
        self.idle_screen()
        self.score = 0
        self.lasers_left = 0
        self.tank = Tank()
        self.bullets = Bullets()
        self.balls = Balls()
        self.explosion = Explosion()
        self.bonus = Bonus()
        self.laser = Laser()
        self.idle_screen()
        self.canvas.add(self.tank.draw)
        self.dead = False

    def idle_screen(self):
        self.canvas.clear()
        with self.canvas:
            Rectangle(source="resources/bbg.png", pos=(0, 0), size=(Window.width, Window.height))
            Rectangle(source="resources/bg.png", pos=(0, 0), size=(Window.width, Window.height / 2))
            for i in range(8):
                Rectangle(source="resources/grass1.png", pos=(0 + i * tile_size, 0), size=(tile_size, tile_size))
            Rectangle(source=self.laser.texture, pos=(tile_size / 4, Window.height - tile_size * 1.5),
                      size=(0.75 * tile_size, 0.75 * tile_size))
        self.score_text = self.add_text(f"Score: {self.score}", tile_size / 2, 0.25 * tile_size,
                                        Window.height - 0.75 * tile_size, (tile_size * 2, tile_size))
        self.canvas.add(self.score_text)
        self.laser_text = self.add_text(f": {self.lasers_left}", tile_size / 2, tile_size,
                                        Window.height - 1.5 * tile_size, (tile_size * 2, tile_size))
        self.canvas.add(self.laser_text)
        self.add_clouds()

#tank class declaration - the player controled object
class Tank:
    def __init__(self):
        self.pos = [Window.width / 2 - tile_size / 2, tile_size]
        self.textures = ["resources/tank.png", "resources/tank2.png", "resources/tank3.png"]
        self.shield_texture = "resources/shield.png"
        self.shield_status = False
        self.shield_on_canvas = False
        self.shield_time = 0
        self.curr_frame = 0
        self.blink_dt = 0.2
        self.draw = Rectangle(source=self.textures[self.curr_frame], pos=self.pos, size=(tile_size, tile_size))
        self.shield = Rectangle(source=self.shield_texture, pos=self.pos, size=(tile_size * 2, tile_size * 2))
        self.exp_rec = [Rectangle(source="resources/tank_des.png", tex_coords=[0, 1 / 15, 1, 1 / 15, 1, 0, 0, 0],
                                  size=(tile_size * 3, tile_size * 2)), 1]

    def check_shield(self, dt):
        if self.shield_time > 0:
            self.shield_time -= dt
            if self.shield_time < 2.5:
                self.shield_blink(dt)
        if self.shield_time < 0:
            self.shield_status = False
            self.shield_on_canvas = False
            game.canvas.remove(self.shield)
            self.shield_time = 0

    def shield_on(self):
        if not self.shield_status:
            self.shield_status = True
            self.shield_on_canvas = True
            game.canvas.add(self.shield)
        self.shield_time = 12

    def shield_blink(self, dt):
        self.blink_dt -= dt
        if self.blink_dt < 0:
            if self.shield_on_canvas:
                game.canvas.remove(self.shield)
                self.shield_on_canvas = False
            elif not self.shield_on_canvas:
                game.canvas.add(self.shield)
                self.shield_on_canvas = True
            self.blink_dt = 0.2

    def hit(self):
        for i in game.balls.container:
            if game.collision(i[0], self.draw, 0.15):
                game.gameover()

    def firing(self):
        if game.firing:
            self.draw.source = self.textures[self.curr_frame]
            self.curr_frame -= 1
        if self.curr_frame == -1:
            self.curr_frame = 2
        if not game.firing:
            self.curr_frame = 0
            self.draw.source = self.textures[self.curr_frame]

    def explosion(self, i, pos):
        self.exp_rec[0].pos = (pos[0] - tile_size, pos[1])
        self.exp_rec[0].tex_coords = [0, i/15 + 1/15 + 1/3000, 1, i/15 + 1/15 + 1/3000, 1, i/15 + 1/3000, 0, i/15 + 1/3000]
        self.exp_rec[1] += 1
        if self.exp_rec[1] == 15:
            self.exp_rec[1] = 14

#bullets shot by the player
class Bullets:
    def __init__(self):
        self.pos = [100, 100]
        self.container = []

    def fire(self, pos):
        self.container.append(Rectangle(source="resources/bullet.png", pos=pos, size=(tile_size / 8, tile_size / 8)))

    def move_up(self, dt):
        i = 0
        while i < len(self.container):
            x = self.container[i].pos[0]
            y = self.container[i].pos[1] + tile_size * dt * 8
            self.container[i].pos = (x, y)
            if y > Window.height:
                self.container.pop(i)
            i += 1

    def destroy(self, i):
        game.canvas.remove(self.container[i])
        self.container.pop(i)


class Balls:
    def __init__(self):
        self.pos = [100, 100]
        self.container = []

    def spawn(self):
        l_r = random.choice([-1, 1])
        if l_r == 1:
            ran = random.randint(round(tile_size/2), round(tile_size))
            pos = (ran*-1, Window.height/2)
        if l_r == -1:
            pos = (random.randint(round(Window.width + tile_size/2), round(Window.width + tile_size)), Window.height / 2)
        self.container.append(
            [Ellipse(source="resources/ball.png", pos=pos, size=(tile_size / 2, tile_size / 2)), 0,
             tile_size * 0.02 * l_r, tile_size * 0.01 * -random.randint(8, 10),
             3, 1])

    def movement(self, dt):
        for i in range(len(self.container)):
            if tile_size/4 < self.container[i][0].pos[0] < Window.width - 1.25*tile_size:
                self.container[i][5] = 0
            if self.container[i][5] == 0:
                if self.container[i][0].pos[0] > Window.width - tile_size / 2:
                    self.container[i][2] *= -1
                if self.container[i][0].pos[0] < 0:
                    self.container[i][2] *= -1
                if self.container[i][0].pos[1] < tile_size:
                    self.container[i][1] = 0

            dvy = self.container[i][3] + 10 * self.container[i][1]
            vy = self.container[i][0].pos[1] - dvy
            vx = self.container[i][0].pos[0] + self.container[i][2] * dt * tile_size * 0.7

            self.container[i][1] += dt
            self.container[i][0].pos = (vx, vy)

        self.check_bullet_hit()

        if game.tank.shield_status:
            self.check_shield_hit()

        if game.laser.laser_status:
            self.check_laser_hit()

    def check_bullet_hit(self):
        i = 0
        while i < len(self.container):
            for j in game.bullets.container:
                if game.collision(j, self.container[i][0]):
                    self.container[i][4] -= 1
                    if self.container[i][4] == 0:
                        self.destroy(i)
                    game.bullets.destroy(game.bullets.container.index(j))
                    break
            i += 1

    def check_shield_hit(self):
        i = 0
        while i < len(self.container):
            if game.collision(self.container[i][0], game.tank.shield, 0.2):
                self.destroy(i)
                break
            i += 1

    def check_laser_hit(self):
        i = 0
        while i < len(self.container):
            if (game.laser.laser.pos[0] + game.laser.laser.size[0] > self.container[i][0].pos[0] > game.laser.laser.pos[
                0]) or (
                    game.laser.laser.pos[0] < self.container[i][0].pos[0] + self.container[i][0].size[0] <
                    game.laser.laser.pos[0] + game.laser.laser.size[0]):
                self.destroy(i)
                break
            i += 1

    def destroy(self, i):
        game.explosion.add_exp([self.container[i][0].pos[0] + self.container[i][0].size[0] / 2,
                                self.container[i][0].pos[1] + self.container[i][0].size[1] / 2], 1)
        game.bonus.spawn([self.container[i][0].pos[0] + self.container[i][0].size[0] / 2,
                          self.container[i][0].pos[1] + self.container[i][0].size[1] / 2])
        game.canvas.remove(self.container[i][0])
        self.container.pop(i)
        game.score += 1
        game.pop_sound.play()
        game.canvas.remove(game.score_text)
        game.score_text = game.add_text(f"Score: {game.score}", tile_size / 2, 0.25 * tile_size,
                                        Window.height - 0.75 * tile_size, (tile_size * 2, tile_size))
        game.canvas.add(game.score_text)


class Explosion:
    def __init__(self):
        self.container = []
        self.pos = [100, 100]
        self.texture = "resources/destroy.png"

    def add_exp(self, pos, frame):
        self.container.append([Rectangle(source=self.texture, tex_coords=[0, 1 / 14, 1, 1 / 14, 1, 0, 0, 0],
                                         pos=(pos[0] - tile_size / 2, pos[1] - tile_size / 2),
                                         size=(tile_size, tile_size)), frame])
        game.canvas.add(self.container[-1][0])

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


class Bonus:
    def __init__(self):
        self.container = []
        self.texture = "resources/crate.png"
        self.texture_l = "resources/crateL.png"

    def events(self, dt):
        self.fall(dt)
        self.collection()

    def spawn(self, pos):
        if random.randint(0, 5) == 1:
            if random.randint(0, 2) == 1:
                self.container.append([Rectangle(source=self.texture, pos=pos, size=(tile_size / 2, tile_size / 2)), 0])
                game.canvas.add(self.container[-1][0])
            else:
                self.container.append(
                    [Rectangle(source=self.texture_l, pos=pos, size=(tile_size / 2, tile_size / 2)), 1])
                game.canvas.add(self.container[-1][0])

    def fall(self, dt):
        for i in self.container:
            y = i[0].pos[1]
            if y > tile_size:
                y -= dt * tile_size * 5
                i[0].pos = (i[0].pos[0], y)
            else:
                i[0].pos = (i[0].pos[0], tile_size)

    def collection(self):
        i = 0
        while i < len(self.container):
            if game.collision(self.container[i][0], game.tank.draw):
                game.canvas.remove(self.container[i][0])
                if self.container[i][1] == 0:
                    game.tank.shield_on()
                if self.container[i][1] == 1:
                    game.lasers_left += 1
                    game.canvas.remove(game.laser_text)
                    game.laser_text = game.add_text(f": {game.lasers_left}", tile_size / 2, tile_size,
                                                    Window.height - 1.5 * tile_size, (tile_size * 2, tile_size))
                    game.canvas.add(game.laser_text)
                self.container.pop(i)
            i += 1


class Laser:
    def __init__(self):
        self.container = []
        self.texture = "resources/mine.png"
        self.texture_l = "resources/laser.png"
        self.laser_status = False
        self.time = 0
        self.laser = Rectangle(source=self.texture, size=(tile_size * 0.75, tile_size * 0.75))

    def spawn(self, pos):
        if self.laser_status:
            self.remove_animation()
            game.canvas.remove(self.laser)
        self.laser_status = True
        self.time = 10
        self.laser.pos = pos
        self.add_animation(pos, -1)
        game.canvas.add(self.laser)

    def check_time(self, dt):
        if self.time > 0:
            self.animation()
            self.time -= dt
        if self.time < 0:
            self.laser_status = False
            game.canvas.remove(self.laser)
            self.remove_animation()
            self.time = 0

    def add_animation(self, pos, frame):
        for i in range(round((Window.height-tile_size)/(tile_size*0.75))):
            self.container.append([Rectangle(source=self.texture_l, tex_coords=[0, 1 / 15, 1, 1 / 15, 1, 0, 0, 0],
                                             pos=(pos[0], pos[1] + tile_size * 0.75 * i),
                                             size=(tile_size * 0.75, tile_size * 0.75)), frame])
            game.canvas.add(self.container[-1][0])

    def remove_animation(self):
        for i in self.container:
            game.canvas.remove(i[0])
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

game = GameWidget()


class MyApp(App):
    icon = "resources/tank.png"

    def build(self):
        return game


if __name__ == "__main__":
    app = MyApp()
    app.run()
