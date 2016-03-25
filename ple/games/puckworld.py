import pygame
import sys
import math

import base

from pygame.constants import K_w, K_a, K_s, K_d
from primitives import Player, Creep
from utils.vec2d import vec2d
from random import uniform

class PuckCreep(pygame.sprite.Sprite):

    def __init__(self, pos_init, attr, SCREEN_WIDTH, SCREEN_HEIGHT):
        pygame.sprite.Sprite.__init__(self)        

        self.pos = vec2d(pos_init)
        self.attr = attr
        self.SCREEN_WIDTH = SCREEN_WIDTH
        self.SCREEN_HEIGHT = SCREEN_HEIGHT

        image = pygame.Surface((self.attr["radius_outer"]*2, self.attr["radius_outer"]*2))
        image.fill((0, 0, 0, 0))
        image.set_colorkey((0,0,0))       
        pygame.draw.circle(
                image,
                self.attr["color_outer"],
                (self.attr["radius_outer"], self.attr["radius_outer"]),
                self.attr["radius_outer"],
                0
        )

        image.set_alpha(int(255*0.75))

        pygame.draw.circle(
                image,
                self.attr["color_center"],
                (self.attr["radius_outer"],self.attr["radius_outer"]),
                self.attr["radius_center"],
                0
        )

        self.image = image
        self.rect = self.image.get_rect()
        self.rect.center = pos_init

    def update(self, ndx, ndy, dt):
        self.pos.x += ndx * self.attr['speed'] * dt
        self.pos.y += ndy * self.attr['speed'] * dt

        self.rect.center = (self.pos.x, self.pos.y)    


class PuckWorld(base.Game):

    def __init__(self, 
        creep_speed=0.003, 
        agent_speed=0.009):

        actions = {
            "up": K_w,
            "left": K_a,
            "right": K_d,
            "down": K_s
        }

        width = 64
        height = 64

        base.Game.__init__(self, width, height, actions=actions)

        self.CREEP_BAD = {
            "radius_center": 3,
            "radius_outer": 17,
            "color_center": (110, 45, 45),
            "color_outer": (150, 95, 95),
            "speed": creep_speed
        }

        self.CREEP_GOOD = {
            "radius": 3,
            "color": (40, 140, 40)
        }

        self.AGENT_COLOR = (60, 60, 140)
        self.AGENT_SPEED = agent_speed 
        self.AGENT_RADIUS = 3
        self.AGENT_INIT_POS = (0,0)

        self.BG_COLOR = (255, 255, 255)
        self.dx = 0
        self.dy = 0
        self.ticks = 0

    def _handle_player_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                key = event.key
                
                self.dx *= 0.9
                self.dy *= 0.9

                if key == self.actions["left"]:
                    self.dx -= self.AGENT_SPEED

                if key == self.actions["right"]:
                    self.dx += self.AGENT_SPEED

                if key == self.actions["up"]:
                    self.dy -= self.AGENT_SPEED

                if key == self.actions["down"]:
                    self.dy += self.AGENT_SPEED

    def getScore(self):
        return self.score

    def game_over(self):
        """
            Return bool if the game has 'finished'
        """
        return False

    def _rngCreepPos(self):
        return ( int(uniform(self.CREEP_GOOD['radius']*3, self.screen_dim[0]-self.CREEP_GOOD['radius']*2.5)), int(uniform(self.CREEP_GOOD['radius']*3, self.screen_dim[1]-self.CREEP_GOOD['radius']*2.5)) )

    def init(self):
        """
            Starts/Resets the game to its inital state
        """

        self.player = Player(self.AGENT_RADIUS, self.AGENT_COLOR, self.AGENT_SPEED, self.AGENT_INIT_POS, self.screen_dim[0], self.screen_dim[1]) 
        self.player_group = pygame.sprite.Group()
        self.player_group.add( self.player )

        self.good_creep = Creep(
            self.CREEP_GOOD['color'], 
            self.CREEP_GOOD['radius'], 
            self._rngCreepPos(),
            (1,1), 
            0.0,
            1.0,
            "GOOD", 
            self.screen_dim[0], 
            self.screen_dim[1],
            0
        )

        self.bad_creep = PuckCreep((self.screen_dim[0], self.screen_dim[1]), self.CREEP_BAD, self.screen_dim[0]*0.75, self.screen_dim[1]*0.75)

        self.creeps = pygame.sprite.Group()
        self.creeps.add(self.good_creep)
        self.creeps.add(self.bad_creep)
        

        self.score = 0
        self.ticks = 0
        self.lives = -1

    def step(self, dt):
        """
            Perform one step of game emulation.
        """

        self.ticks += 1
        self.screen.fill(self.BG_COLOR)

        self._handle_player_events()
        self.player_group.update(self.dx, self.dy, dt)
        
        dx = self.player.pos.x-self.good_creep.pos.x
        dy = self.player.pos.y-self.good_creep.pos.y
        dist_to_good = math.sqrt(dx*dx + dy*dy)

        dx = self.player.pos.x-self.bad_creep.pos.x
        dy = self.player.pos.y-self.bad_creep.pos.y
        dist_to_bad = math.sqrt(dx*dx + dy*dy)

        reward = -dist_to_good
        if dist_to_bad < self.CREEP_BAD['radius_outer']:
            reward += 2.0*(dist_to_bad - self.CREEP_BAD['radius_outer']) / float(self.CREEP_BAD['radius_outer'])

        self.score += reward

        if self.ticks % 500 == 0:
            x,y = self._rngCreepPos()
            self.good_creep.pos.x = x
            self.good_creep.pos.y = y

        ndx = 0.0 if dist_to_bad == 0.0 else dx/dist_to_bad
        ndy = 0.0 if dist_to_bad == 0.0 else dy/dist_to_bad

        self.bad_creep.update(ndx, ndy, dt)
        self.good_creep.update(dt)

        self.player_group.draw(self.screen)
        self.creeps.draw(self.screen)


if __name__ == "__main__":
        pygame.init()
        game = PuckWorld()
        game.screen = pygame.display.set_mode( game.getScreenDims(), 0, 32)
        game.clock = pygame.time.Clock()
        game.init()

        while True:
            dt = game.clock.tick_busy_loop(60)
            game.step(dt)
            pygame.display.update()