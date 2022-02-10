import random

from kivy.app import App
from kivy.uix.widget import  Widget
from kivy.graphics import Rectangle,Ellipse
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.text import Label as CoreLabel
Config.set('kivy','window_icon',"resources/tank.png")

Window.size = (540,960)
tile_size = Window.width/6

class GameWidget(Widget):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.pause = True
        self.tank = Tank(self)
        self.touch_x = 100
        self.touch_y = 100
        self.firing = False
        self.dead = False
        self.score = 0
        self.clouds = [Rectangle(source="resources/cloud1.png",image_ratio=0.5, pos=(0.5*tile_size, Window.height-tile_size*3), size=(tile_size*3, tile_size*1.5)),Rectangle(source="resources/cloud2.png", pos=(tile_size*3, Window.height-tile_size*3), size=(tile_size*3, tile_size*1.5)),Rectangle(source="resources/cloud2.png", pos=(-2*tile_size, Window.height-tile_size*3), size=(tile_size*2, tile_size*1))]

        with self.canvas:
            Rectangle(source="resources/bbg.png", pos = (0,0), size = (Window.width,Window.height))
            Rectangle(source="resources/bg.png", pos = (0,0), size = (Window.width,Window.height/2))
#            Label(text="Click to play", font_name="resources/Font1.ttf", font_size=tile_size/2, pos = (Window.width/2-tile_size,Window.height/2), size=(tile_size*2,tile_size))
            for i in range(8):
                Rectangle(source="resources/grass1.png", pos = (0+i*tile_size,0), size = (tile_size,tile_size))
        self.add_clouds()

        self.start_text = self.add_text("Click to play", tile_size/2, Window.width / 2 - tile_size*1.5, Window.height / 2, (tile_size*2,tile_size))
        self.canvas.add(self.start_text)
        self.score_text = self.add_text(f"Score: {self.score}", tile_size/2, 0.25 * tile_size, Window.height - 0.75 * tile_size, (tile_size*2,tile_size))
        self.canvas.add(self.score_text)



        Clock.schedule_interval(self.every_frame, 0)
        Clock.schedule_interval(self.fire, 0.15)

    def on_touch_down(self, touch):
        self.firing = True
        self.touch_x = touch.x
        self.touch_y = touch.y
        if self.pause == True:
            self.pause = False
            self.game_reset()

    def on_touch_up(self, touch):
        self.firing = False
        self.tank.curr_frame = 0

    def on_touch_move(self, touch):
        self.touch_x = touch.x
        self.touch_y = touch.y

    def add_bullet(self):
        self.bullets.fire((self.tank.draw.pos[0]+tile_size/2-tile_size/16,self.tank.draw.pos[1]+tile_size))
        self.canvas.add(self.bullets.container[-1])

    def add_ball(self, dt):
        if random.randint(0, 100) == 1:
            self.balls.spawn((random.randint(round(tile_size),round(Window.width-tile_size)), Window.height/2))
            self.canvas.add(self.balls.container[-1][0])
            self.tank.curr_frame = 2

    def every_frame(self,dt):
        if self.pause == False:
            self.player_move(dt)
            self.bullets.move_up(dt)
            self.balls.movement(dt)
            self.add_ball(dt)
            self.tank.hit(dt)
            self.tank.firing(dt)
            self.explosion.animation(dt)
        self.move_clouds(dt)
        if self.dead == True:
            self.tank.explosion(dt,self.tank.exp_rec[1],self.tank.draw.pos)

    def collision(self, e1, e2, reduction=0):
        r1x = e1.pos[0]
        r1y = e1.pos[1]
        r2x = e2.pos[0] + reduction * tile_size
        r2y = e2.pos[1] + reduction * tile_size
        r1w = e1.size[0]
        r1h = e1.size[1]
        r2w = e2.size[0]  - reduction * tile_size
        r2h = e2.size[1]  - reduction * tile_size

        if (r1x < r2x + r2w and r1x + r1w > r2x and r1y < r2y + r2h and r1y + r1h > r2y):
            return True
        else:
            return False

    def player_move(self,dt):

        x = self.tank.draw.pos[0]

        size = tile_size * 6 * dt

        if self.firing == True and self.touch_x > x+tile_size/2 and x < Window.width - tile_size:
            x += size
        if self.firing == True and self.touch_x < x+tile_size/2 and x > 0:
            x -= size

        self.tank.draw.pos = (x, self.tank.draw.pos[1])

    def fire(self, dt):
        if self.firing == True and self.pause == False:
            self.add_bullet()

    def move_clouds(self,dt):
        for i in range(0,len(self.clouds)):
            if self.clouds[i].pos[0] < Window.width:
                self.clouds[i].pos = (self.clouds[i].pos[0]+dt*20, self.clouds[i].pos[1])
            else: self.clouds[i].pos = (-3*tile_size, self.clouds[i].pos[1])

    def add_clouds(self):
        for i in self.clouds:
            self.canvas.add(i)

    def add_text(self,text,size,x,y,recsize):
        self.rect = Rectangle(pos = (x,y), size=recsize)
        label = CoreLabel(text=text,font_name="resources/Font1.ttf", font_size=size)
        label.refresh()
        text = label.texture
        pos = (x,y)
        return  Rectangle(size=text.size, pos=pos, texture=text)

    def gameover(self):
        self.pause = True
        self.idle_screen()
        self.dead = True
        self.canvas.add(self.tank.exp_rec[0])

    def game_reset(self):
        self.score = 0
        self.tank = Tank(self)
        self.bullets = Bullets(self)
        self.balls = Balls(self)
        self.explosion = Explosion(self)
        self.idle_screen()
        self.canvas.add(self.tank.draw)
        self.dead = False

    def idle_screen(self):
        self.canvas.clear()
        with self.canvas:
            Rectangle(source="resources/bbg.png", pos = (0,0), size = (Window.width,Window.height))
            Rectangle(source="resources/bg.png", pos = (0,0), size = (Window.width,Window.height/2))
            for i in range(8):
                Rectangle(source="resources/grass1.png", pos = (0+i*tile_size,0), size = (tile_size,tile_size))
        self.score_text = self.add_text(f"Score: {self.score}", tile_size / 2, 0.25 * tile_size, Window.height - 0.75 * tile_size,(tile_size * 2, tile_size))
        self.canvas.add(self.score_text)
        self.add_clouds()

class Tank():
    def __init__(self,game):
        super().__init__()
        self.game = game
        self.pos = [Window.width/2 - tile_size/2, tile_size]
        self.textures = ["resources/tank.png","resources/tank2.png","resources/tank3.png"]
        self.curr_frame = 0
        self.draw = Rectangle(source=self.textures[self.curr_frame], pos=self.pos, size=(tile_size, tile_size))
        self.exp_rec=[Rectangle(source="resources/tank_des.png",tex_coords=[0,1/15,1,1/15,1,0,0,0], size=(tile_size*3, tile_size*2)),1]

    def hit(self,dt):
        for i in self.game.balls.container:
            if self.game.collision(i[0],self.draw,0.5):
                self.game.gameover()

    def firing(self,dt):
        if self.game.firing == True and self.curr_frame != 0:
            self.draw.source = self.textures[self.curr_frame]
            self.curr_frame -= 1
        if self.game.firing == True: self.curr_frame == 0


    def explosion(self,dt,i,pos):
        self.exp_rec[0].pos = (pos[0]-tile_size,pos[1])
        self.exp_rec[0].tex_coords = [0,i/15+1/15,1,i/15+1/15,1,i/15,0,i/15]
        self.exp_rec[1] += 1
        if self.exp_rec[1] == 15: self.exp_rec[1] = 14


class Bullets():
    def __init__(self,game):
        super().__init__()
        self.game = game
        self.pos = [100, 100]
        self.container = []

    def fire(self,pos):
        self.container.append(Rectangle(source="resources/bullet.png", pos=pos, size=(tile_size/8, tile_size/8)))

    def move_up(self,dt):
        i = 0
        while i < len(self.container):
            x = self.container[i].pos[0]
            y = self.container[i].pos[1] + tile_size * dt * 8
            self.container[i].pos = (x, y)
            if y > Window.height: self.container.pop(i)
            i += 1

    def destroy(self,i):
        self.game.canvas.remove(self.container[i])
        self.container.pop(i)

class Balls():
    def __init__(self,game):
        super().__init__()
        self.game = game
        self.pos = [100, 100]
        self.container = []

    def spawn(self,pos):
        self.container.append([Ellipse(source="resources/ball.png",color= (0,0,50),pos=pos, size=(tile_size/2, tile_size/2)),0,tile_size * 0.02 * random.choice([-1,1]),tile_size * 0.01 * -random.randint(8,10),random.randint(2,4)])

    def movement(self,dt):
        for i in range(len(self.container)):
            if self.container[i][0].pos[0] > Window.width-tile_size/2: self.container[i][2] *= -1
            if self.container[i][0].pos[0] < 0: self.container[i][2] *= -1
            if self.container[i][0].pos[1] < tile_size: self.container[i][1] = 0
            dvy = self.container[i][3] + 10 * self.container[i][1]
            vy = self.container[i][0].pos[1] - dvy
            vx = self.container[i][0].pos[0] + self.container[i][2]
            self.container[i][1] += dt
            self.container[i][0].pos = (vx,vy)
        i = 0
        while i < len(self.container):
            for j in self.game.bullets.container:
                if self.game.collision(j,self.container[i][0]) == True:
                    self.container[i][4] -= 1
                    if self.container[i][4] == 0:
                        self.destroy(i)
                    self.game.bullets.destroy(self.game.bullets.container.index(j))
                    break
            i += 1

    def destroy(self,i):
        self.game.explosion.add_exp([self.container[i][0].pos[0]+self.container[i][0].size[0]/2,self.container[i][0].pos[1]+self.container[i][0].size[1]/2],1)
        self.game.canvas.remove(self.container[i][0])
        self.container.pop(i)
        self.game.score += 1
        self.game.canvas.remove(self.game.score_text)
        self.game.score_text = self.game.add_text(f"Score: {self.game.score}", tile_size / 2, 0.25 * tile_size,
                                        Window.height - 0.75 * tile_size, (tile_size * 2, tile_size))
        self.game.canvas.add(self.game.score_text)

class Explosion():
    def __init__(self,game):
        super().__init__()
        self.game = game
        self.container = []
        self.pos = [100,100]
        self.texture = "resources/destroy.png"

    def add_exp(self,pos,frame):
        self.container.append([Rectangle(source=self.texture,tex_coords=[0,1/14,1,1/14,1,0,0,0],pos=(pos[0]-tile_size/2,pos[1]-tile_size/2), size=(tile_size, tile_size)),frame])
        self.game.canvas.add(self.container[-1][0])

    def animation(self,dt):
        i = 0
        while i < len(self.container):
            self.container[i][1] += 1
            self.container[i][0].tex_coords=[0,self.container[i][1]/14+1/14,1,self.container[i][1]/14+1/14,1,self.container[i][1]/14,0,self.container[i][1]/14]
            if self.container[i][1] == 14:
                self.container.pop(i)
            i += 1

game = GameWidget()

class MyApp(App):
    icon = "resources/tank.png"
    def build(self):
        return game

if __name__ == "__main__":
    app = MyApp()
    app.run()
