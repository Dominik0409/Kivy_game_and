import random

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Rectangle
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.text import Label as CoreLabel
from kivy.core.audio import SoundLoader
import objects

Config.set('kivy', 'window_icon', "resources/tank.png")

# window size declaration
Window.size = (540, 960)

# declaration of tile size which is later used in order to properly place objects on screen
tile_size = Window.width / 6


# main game class inherits from a Kivy Widget class
class GameWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_again_text = None
        self.laser = objects.Laser(self, tile_size)
        self.bonus = objects.Bonus(self, tile_size)
        self.balls = objects.Balls(self, tile_size)
        self.explosion = objects.Explosion(self, tile_size)
        self.bullets = objects.Bullets(self, tile_size)
        self.pause = True
        self.tank = objects.Tank(self, tile_size)
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
            Rectangle(source=self.laser.texture, pos=(tile_size / 4, Window.height - tile_size * 1.5),
                      size=(0.75 * tile_size, 0.75 * tile_size))

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
        if tile_size / 4 < touch.x < tile_size and Window.height - tile_size * 1.5 < touch.y < Window.height - tile_size * 0.75 and self.lasers_left > 0:
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
            self.start_again_text = self.add_text("Click to play again", tile_size / 3,
                                                  Window.width / 2 - tile_size * 1.5,
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

        if self.firing == True and self.touch_x > x + tile_size / 2 and x < Window.width - tile_size and self.touch_y < Window.height - 2 * tile_size:
            x += size
        if self.firing == True and self.touch_x < x + tile_size / 2 and x > 0 and self.touch_y < Window.height - 2 * tile_size:
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
        self.tank = objects.Tank(self, tile_size)
        self.bullets = objects.Bullets(self, tile_size)
        self.balls = objects.Balls(self, tile_size)
        self.explosion = objects.Explosion(self, tile_size)
        self.bonus = objects.Bonus(self, tile_size)
        self.laser = objects.Laser(self, tile_size)
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


game = GameWidget()


class MyApp(App):
    icon = "resources/tank.png"

    def build(self):
        return game


if __name__ == "__main__":
    app = MyApp()
    app.run()
