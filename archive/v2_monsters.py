import pygame
from sys import exit
import math
from random import choice, randint
class Game: 
    def __init__(self):
        pygame.init()
        self.full_res = (1400, 800)
        self.res = (900, 800) # to be changed 
        self.screen = pygame.display.set_mode(self.full_res)
        self.clock = pygame.time.Clock()
        pygame.mouse.set_visible(False)
        # game independents
        _ = 0
        self.map = [
            [3, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [3, _, _, 1, 6, 4, _, _, _, 1],
            [3, _, _, 1, _, 2, 1, 6, _, 1],
            [3, _, _, _, _, _, _, 4, _, 1],
            [3, _, 3, 3, _, 3, _, 4, _, 1],
            [3, _, _, _, _, _, _, _, _, 1],
            [3, _, 1, 4, _, 5, _, 2, _, 1],
            [3, _, _, 6, 1, 1, 1, 6, _, 1],
            [3, 3, _, _, _, _, _, _, _, 1],
            [3, 3, 3, 3, 3, 3, 3, 3, 1, 1]
        ]
       
        self.map_size = 500 # 500x500 plane
        self.fps = int(self.clock.get_fps())
        self.brightness = 4
        

        # game dependents 
        self.map_tile_size = len(self.map) # width and height are the same for simplicity
        self.tile_size = int(self.map_size/self.map_tile_size) # current: 50
        # set the position of the mouse to the center of the screen
        self.mouse_x = self.res[0]/2
        self.prior_x = self.res[0]/2
        pygame.mouse.set_pos((self.mouse_x, self.res[1]/2))


        # textures
        self.wall_quality = (200, 32) # 150 columns (rays), 64 rectangles per column 
        self.tex_res = 64 # 64 x 64 images
        # the texture resolution modifyer is the modifyer between the quality of the textures and the number of pixels drawn per line
        self.tex_res_mod = self.tex_res/self.wall_quality[1]
        self.wall_textures = {i:pygame.image.load(f'graphics/game/wall_texture{i}.png') for i in range(1, 7)}
        # sky
        self.sky_texture = pygame.image.load('graphics/game/sky_texture.png')
        self.sky_res = (300, 100)
        self.sky_quality = (75, 30)

        # player
        self.player = Player(self.map_size, self.wall_quality, self.res)

        # monsters
        
        self.spawn_monsters(10, (0, 1, 2, 3, 4))

    def run(self):
        while True:
            self.screen.fill('Black')
            self.handle_events()
            self.draw_map()
            self.draw_sky()
            self.player.cast_rays(self.tile_size, self.map, self.map_size, self.screen)
            self.draw_walls()
            self.draw_monsters()
            self.player.move(self.fps, self.map, self.tile_size)
            self.player.shoot(self.tile_size, self.map_size, self.map, self.res, self.screen, self.monsters)
            self.player.animate(self.screen, self.res, self.fps)
            self.handle_end()
            pygame.display.update()
            self.clock.tick(60)
            self.fps = int(self.clock.get_fps())
            pygame.display.set_caption(f'First Person Shooter (FPS: {self.fps})')
          
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                exit()
            # if there is mouse motion
            if event.type == pygame.MOUSEMOTION: 
                # set the prior mouse x position the mouse positiona nd the mouse_x to the postion of the event 
                self.prior_x = self.mouse_x
                self.mouse_x = pygame.mouse.get_pos()[0] # use get_pos() instead of event.pos because it is more accurate 
                # if the mouse is outside of the set boundrys
                if not (200 < self.mouse_x < self.res[0] - 200):
                    # the prior_x should now be the middle of the screen - the old difference between itself and the mouse_x
                    self.prior_x = self.res[0]/2 - (self.mouse_x - self.prior_x)
                    # the mouse_x should be the middle of the screen
                    self.mouse_x = self.res[0]/2
                    # set the position of the mouse to the middle of the screen
                    pygame.mouse.set_pos((self.res[0]/2, self.res[1]/2))
                
                # create xchange and use it to change the players angle
                xchange = self.mouse_x - self.prior_x
                self.player.angle -= xchange/500
                self.player.angle %= (2 * math.pi)
            # move
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    self.player.forward = True
                elif event.key == pygame.K_s:
                    self.player.back = True
                elif event.key == pygame.K_a:
                    self.player.left = True
                elif event.key == pygame.K_d:
                    self.player.right = True
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_w:
                    self.player.forward = False
                elif event.key == pygame.K_s:
                    self.player.back = False
                elif event.key == pygame.K_a:
                    self.player.left = False
                elif event.key == pygame.K_d:
                    self.player.right = False
            # shoot
            if event.type == pygame.MOUSEBUTTONDOWN and self.player.arsenal[self.player.gun]['state'] == 'none': 
                self.player.arsenal[self.player.gun]['state'] = 'shooting'
                if self.player.arsenal[self.player.gun]['auto']:
                    self.player.arsenal[self.player.gun]['trigger_down'] = True
            if event.type == pygame.MOUSEBUTTONUP and self.player.arsenal[self.player.gun]['auto']:
                self.player.arsenal[self.player.gun]['trigger_down'] = False
            # switch wepon 
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                self.player.gun += 1
                self.player.gun %= 3
            # reload
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.player.arsenal[self.player.gun]['frame'] = 0
                self.player.arsenal[self.player.gun]['state'] = 'reloading'
            # sprint
            if event.type == pygame.KEYDOWN and event.key == pygame.K_LSHIFT: 
                self.player.speed = 200
            elif event.type == pygame.KEYUP and event.key == pygame.K_LSHIFT: 
                self.player.speed = 100

    def spawn_monsters(self, num_monsters, monster_types):
        # get a big dictionary that holds all the info for each kind of monster
        get_move = lambda monster, num: [pygame.image.load(f'graphics/monster{monster}/move{i}.png') for i in range(num)]
        get_attack = lambda monster, num: [pygame.image.load(f'graphics/monster{monster}/attack{i}.png') for i in range(num)]
        get_die = lambda monster, num: [pygame.image.load(f'graphics/monster{monster}/die{i}.png') for i in range(num)]
        monsters_info = [
            {'move': get_move(0, 3), 'attack': get_attack(0, 3), 'die':get_die(0, 5), 'speed': 1, 'size_factor': 1, 'animation_speed': 10, 'health': 3, 'damage': 0.5},
            {'move': get_move(1, 2), 'attack': get_attack(1, 2), 'die':get_die(1, 5), 'speed': 0.75, 'size_factor': 1.5, 'animation_speed': 15, 'health': 5, 'damage':1},
            {'move': get_move(2, 3), 'attack': get_attack(2, 2), 'die':get_die(2, 4), 'speed': 1.25, 'size_factor': 1.75, 'animation_speed': 12, 'health': 2, 'damage':0.4},
            {'move': get_move(3, 3), 'attack': get_attack(3, 2), 'die':get_die(3, 4), 'speed': 1, 'size_factor': 0.5, 'animation_speed': 10, 'health': 3, 'damage':0.6},
            {'move': get_move(4, 2), 'attack': get_attack(4, 2), 'die':get_die(4, 4), 'speed': 0.75, 'size_factor': 1.5, 'animation_speed': 20, 'health': 6, 'damage':1.25}
        ]
        monsters = []
        for monster in range(num_monsters):
            # choose a kind of monster and find a place for it 
            num = choice(monster_types)
            while True:
                x, y = randint(self.tile_size, self.map_size - self.tile_size), randint(self.tile_size, self.map_size - self.tile_size)
                row = y//self.tile_size
                col = x//self.tile_size
                # if the monster is too close to the player or on a filled block try again, otherwise exit the loop 
                if ((self.player.x - x) ** 2 + (self.player.y - y) ** 2) ** 0.5 < 200: 
                    continue
                if self.map[row][col] == 0:
                    break
            images = {'move':monsters_info[num]['move'],'attack':monsters_info[num]['attack'], 'die':monsters_info[num]['die']} 
            monsters.append(Monster(x, y, 1.25, images, monsters_info[num]['speed'], monsters_info[num]['animation_speed'], monsters_info[num]['health'], monsters_info[num]['damage']))
            
        self.monsters = monsters
    
    def draw_monsters(self):
        # sort monsters from farthest to closest so that closest ones are drawn last
        self.monsters = sorted(self.monsters, key = lambda monster: 1/monster.distance)
        # for each monster
        for monster in self.monsters: 
            # update monster.visual using monster.check_visual() and then move, animate, draw, the monster and let itattack
            monster.check_visual(self.player.x, self.player.y, self.player.angle, self.player.fov, self.tile_size, self.map, self.map_size)
            monster.move(self.player.x, self.player.y, self.map, self.tile_size, self.monsters)
            monster.animate(self.monsters)
            monster.draw(self.res, self.player.fov, self.player.x, self.player.y, self.screen)
            monster.attack(self.player)
            
    def draw_map(self):
        xs = [self.tile_size * factor for factor in range(len(self.map))]
        ys = [self.tile_size * factor for factor in range(len(self.map))]
        for row_i in range(self.map_tile_size):
            for col_i in range(self.map_tile_size):
                if self.map[row_i][col_i] > 0:
                    pygame.draw.rect(self.screen, (200, 200, 200), (xs[col_i] + self.res[0], ys[row_i], self.tile_size, self.tile_size))

        for x in xs:
            pygame.draw.line(self.screen, (100, 100, 100), (x + self.res[0], 0), (x + self.res[0], self.map_size))
        for y in ys:
            pygame.draw.line(self.screen, (100, 100, 100), (self.res[0], y), (self.res[0] + self.map_size, y))

        for monster in self.monsters:
            pygame.draw.circle(self.screen, 'Green', (monster.x + self.res[0], monster.y), 8)
        pygame.draw.circle(self.screen, 'Red', (self.player.x + self.res[0], self.player.y), 10)
        
    def draw_walls(self):
        x = 0
        width = self.res[0]/self.player.num_rays
        for ray in self.player.rays: 
            distance, tex_point, angle, tex_i = ray
            fish_eye_fix = math.cos(self.player.angle - angle)
            distance *= fish_eye_fix
            height = 20000/distance
            texture = self.wall_textures[tex_i]
            tex_x = int((tex_point * self.tex_res/self.tile_size))
            y = self.res[1]/2 - height/2
            length = height/self.wall_quality[1]
            color_mod = distance/self.brightness
            for pixel in range(self.wall_quality[1]):
                # texture y is equal to the integer of the pixel * the texture resolution modifyer
                tex_y = int(pixel * self.tex_res_mod)
                color = texture.get_at((tex_x, tex_y))
                color = (color[0] - color_mod if color[0] - color_mod >= 0 else 0,
                         color[1] - color_mod if color[1] - color_mod >= 0 else 0,
                         color[2] - color_mod if color[2] - color_mod >= 0 else 0)
                pygame.draw.rect(self.screen, color, (x, y, width + 1, length + 1)) # +1 for round down case
                y += length
            x += width

    def handle_end(self):
        if self.player.health <= 0: 
            # come back when gamestates are created
            print('Player died. ')
            exit()
        if len(self.monsters) == 0:
            print('Player won')
            exit()

    def draw_sky(self):
        angle = self.player.angle + self.player.fov/2
        x = 0
        width = self.res[0]/self.sky_quality[0]
        height = self.res[1]/2/self.sky_quality[1]
        for ray in range(self.sky_quality[0]):
            angle -= self.player.fov/self.sky_quality[0]
            angle %= (math.pi * 2)
            # the angle times the ratio of the width of the sky which needs to cover the whole screen to the number of radians it needs to cover
            tex_x = int(angle * self.sky_res[0]/(math.pi * 2))
            y = 0
            for rect in range(self.sky_quality[1]):
                # the rectangle multiplied the ratio of the sky resolution to the quality
                tex_y = int(rect * self.sky_res[1]/self.sky_quality[1])
                color = self.sky_texture.get_at((tex_x, tex_y))
                pygame.draw.rect(self.screen, color, (x, y, width + 1, height + 1)) # +1 for round down case
                y += height
            x += width

        pygame.draw.rect(self.screen, (75, 75, 75), (0, self.res[1]/2, self.res[0], self.res[1]/2))


class Player:
    def __init__(self, map_size, wall_quality, res):
        # projection
        self.x = 75
        self.y = 75
        self.angle = 0
        self.fov = math.pi/3
        self.rays = []
        self.forward, self.back, self.left, self.right = False, False, False, False
        self.num_rays = wall_quality[0]

        # weapons
        get_gun = lambda num: pygame.transform.scale_by(pygame.image.load(f'graphics/player/gun{num}.png'), 4)
        get_shoot = lambda num: pygame.transform.scale_by(pygame.image.load(f'graphics/player/gun{num}_shoot.png'), 4)
        get_recoil = lambda num: pygame.transform.scale_by(pygame.image.load(f'graphics/player/gun{num}_recoil.png'), 4)
        get_reload = lambda num: pygame.transform.scale_by(pygame.image.load(f'graphics/player/gun{num}_relode.png'), 6)
        self.arsenal = [{'none': get_gun(0), 'shoot':get_shoot(0), 'recoil':get_recoil(0), 'recoil_speed': 5, 'capasity': 8, 'magazine': 8, 'frame': 0, 'state': 'none', 'reload':get_reload(0), 'reload_speed': 1, 'auto': False, 'trigger_down': None, 'damage': 1},
                        {'none': get_gun(1), 'shoot':get_shoot(1), 'recoil':get_recoil(1), 'recoil_speed': 3, 'capasity': 18, 'magazine': 18, 'frame': 0, 'state': 'none', 'reload':get_reload(1), 'reload_speed': 0.7, 'auto': False, 'trigger_down': None, 'damage': 2},
                        {'none': get_gun(2), 'shoot':get_shoot(2), 'recoil':get_recoil(2), 'recoil_speed': 15, 'capasity': 30, 'magazine': 30, 'frame': 0, 'state': 'none', 'reload':get_reload(2), 'reload_speed': 0.3, 'auto': True, 'trigger_down': False, 'damage': 1}]
        
        self.gun = 0
        self.gun_height = res[1]
        self.gun_height_inc = 1
        self.shake = False
        self.bullet_holes = []
        self.bullet_hole_image = pygame.image.load('graphics/player/bullet_hole.png')

        # other
        self.speed = 100
        self.health = 100
        self.stamina = 100

    def cast_rays(self, tile_size, map, map_size, screen):
        rays = []
        angle = self.angle + self.fov/2
        for ray in range(self.num_rays):
            angle -= self.fov/self.num_rays
            angle %= (math.pi * 2)
            vectx, vecty = math.sin(angle), math.cos(angle)
            m = vecty/vectx

            closest_x = (10000, 10000)
            closest_y = (10000, 10000)
            # Check X
            if vectx <= 0:
                x = (self.x - (self.x % tile_size))
            elif vectx > 0: 
                x = (self.x - (self.x % tile_size)) + tile_size
            x_step = vectx/abs(vectx) * tile_size
            while True: 
                y = m * (x - self.x) + self.y
                if not (0 <= x < map_size) or (not 0 <= y < map_size ):
                    break
                
                row = int(y/tile_size)
                if vectx <= 0: 
                    col = int(x/tile_size) - 1 if int(x/tile_size) - 1 >= 0 else 0
                elif vectx >= 0: 
                    col = int(x/tile_size)
                
                if map[row][col] > 0:
                    closest_x = (x, y)
                    x_texture_i = map[row][col]
                    break
                
                x += x_step
            
            # Check Y
            if vecty <= 0:
                y = (self.y - (self.y % tile_size))
            elif vecty > 0: 
                y = (self.y - (self.y % tile_size)) + tile_size
            y_step = vecty/abs(vecty) * tile_size
            while True: 
                x = (y - self.y)/m + self.x
                if not (0 <= x < map_size) or (not 0 <= y < map_size):
                    break
                
                col = int(x/tile_size)
                if vecty <= 0: 
                    row = int(y/tile_size) - 1 if int(y/tile_size) - 1 >= 0 else 0
                elif vecty >= 0: 
                    row = int(y/tile_size)
                
                if map[row][col] > 0:
                    closest_y = (x, y)
                    y_texture_i = map[row][col]
                    break

                y += y_step 
        
            # find
            distance_from_closest_x = ((closest_x[0] - self.x) ** 2 + (closest_x[1] - self.y) ** 2) ** 0.5
            distance_from_closest_y = ((closest_y[0] - self.x) ** 2 + (closest_y[1] - self.y) ** 2) ** 0.5
            # if the closest x is closer, cast the ray untill that point, otherwise cast it to the closesty
            if distance_from_closest_x < distance_from_closest_y:
                rays.append((distance_from_closest_x, closest_x[1] % tile_size, angle, x_texture_i))
                # pygame.draw.line(screen, 'Purple', (self.x + 500, self.y), (closest_x[0] + 500, closest_x[1]))
            else: 
                rays.append((distance_from_closest_y, closest_y[0] % tile_size, angle, y_texture_i))
                # pygame.draw.line(screen, 'Purple', (self.x + 500, self.y), (closest_y[0] + 500, closest_y[1]))
        
        self.rays = rays

    def move(self, fps, map, tile_size):
        # no normilization needed because since we are calculating the vector from an angle, sin and cos, already have the hipotinuse equal to 1
        if self.forward and \
        map[int((math.cos(self.angle) * 10 + self.y)/tile_size)][int((math.sin(self.angle) * 10 + self.x)/tile_size)] == 0:
            self.x += math.sin(self.angle) * self.speed/fps
            self.y += math.cos(self.angle) * self.speed/fps
        elif self.back and \
        map[int((math.cos(self.angle - math.pi) * 10 + self.y)/tile_size)][int((math.sin(self.angle - math.pi) * 10 + self.x)/tile_size)] == 0: 
            self.x -= math.sin(self.angle) * self.speed/fps
            self.y -= math.cos(self.angle) * self.speed/fps
        if self.right and \
        map[int((math.cos(self.angle - math.pi/2) * 10 + self.y)/tile_size)][int((math.sin(self.angle - math.pi/2) * 10 + self.x)/tile_size)] == 0: 
            self.x += math.sin(self.angle - math.pi/2) * self.speed/fps
            self.y += math.cos(self.angle - math.pi/2) * self.speed/fps
        elif self.left and \
        map[int((math.cos(self.angle + math.pi/2) * 10 + self.y)/tile_size)][int((math.sin(self.angle + math.pi/2) * 10 + self.x)/tile_size)] == 0:
            self.x += math.sin(self.angle + math.pi/2) * self.speed/fps
            self.y += math.cos(self.angle + math.pi/2) * self.speed/fps

        # handle sprinting 
        # if the player is sprinting
        if self.speed == 200:
            # of their stamina reaches 0, set the speed back to normal
            if self.stamina <= 0: 
                self.speed = 100
            # decrement the stamina
            self.stamina -= 1
        # otherwise, if the player is not sprinting and their stamina is not full, increment their stamina
        elif self.stamina < 100: 
            self.stamina += 0.25

    def animate(self, screen, res, fps):
        if self.arsenal[self.gun]['state'] == 'shooting':
            if self.arsenal[self.gun]['frame'] <= fps/10:
                image = self.arsenal[self.gun]['shoot']
                self.arsenal[self.gun]['frame']+= 1
            else: 
                # move onto recoil
                self.arsenal[self.gun]['state'] = 'recoiling'
                self.arsenal[self.gun]['frame'] = 0
        
        if self.arsenal[self.gun]['state'] == 'recoiling':
            if self.arsenal[self.gun]['frame'] <= fps/self.arsenal[self.gun]['recoil_speed']: # the larger the recoil speed the less time it takes for the animation frame to reach its max
                image = self.arsenal[self.gun]['recoil']
                self.arsenal[self.gun]['frame'] += 1
            else: 
                # if the gun is automatic
                if self.arsenal[self.gun]['auto']:
                    # if the trigger is not heald down
                    if not self.arsenal[self.gun]['trigger_down']:
                        # set the state to none and set the release to False again
                        self.arsenal[self.gun]['state'] = 'none'
                    # otherwise, if the trigger is still being heald down 
                    else:
                        # set the state back to shooting to shoot the next bullet
                        self.arsenal[self.gun]['state'] = 'shooting'
                        # because we check for shooting before we check for recoiling after shooting we have to create the image 
                        image = self.arsenal[self.gun]['shoot']
                        
                else:
                    self.arsenal[self.gun]['state'] = 'none'
                
                self.arsenal[self.gun]['frame'] = 0
                self.arsenal[self.gun]['magazine'] -= 1

        if self.arsenal[self.gun]['magazine'] <= 0: 
            self.arsenal[self.gun]['state'] = 'reloading'
        
        if self.arsenal[self.gun]['state'] == 'reloading':
            if self.arsenal[self.gun]['frame'] <= fps/self.arsenal[self.gun]['reload_speed']:
                image = self.arsenal[self.gun]['reload']
                self.arsenal[self.gun]['frame'] += 1
            else: 
                self.arsenal[self.gun]['state'] = 'none'
                self.arsenal[self.gun]['frame'] = 0
                self.arsenal[self.gun]['magazine'] = self.arsenal[self.gun]['capasity']

        if self.arsenal[self.gun]['state'] == 'none':
            image = self.arsenal[self.gun]['none']


        if self.shake: 
            if self.gun_height >= res[1] + 20: 
                self.gun_height_inc = -self.speed/100
            if self.gun_height <= res[1]:
                self.gun_height_inc = self.speed/100
            self.gun_height += self.gun_height_inc

            if self.gun_height == res[1] and not (self.forward or self.back or self.left or self.right):
                self.shake = False
        if self.forward or self.back or self.left or self.right: 
            self.shake = True


        

        rect = image.get_rect(midbottom = (res[0]/2, self.gun_height))
        screen.blit(image, rect)

    def shoot(self, tile_size, map_size, map, res, screen, monsters):
        # handle new shots 
        # if the player is shooting
        if self.arsenal[self.gun]['state'] == 'shooting' and self.arsenal[self.gun]['frame'] == 1:
            hit = False
            # sort the monsters from closest to farthest away that way if the bullet can hit them both it only hits the closest because of the break and filter them so that only the ones that are visual can be shot
            monsters = [monster for monster in sorted(monsters, key = lambda monster: monster.distance) if monster.visual]
            for monster in monsters: 
                if monster.rect.collidepoint((res[0]/2, res[1]/2)): # collide with middle of the screen 
                    monster.health -= self.arsenal[self.gun]['damage']
                    hit = True
                    break
            if not hit:
                # find first intersection with the wall 
                vectx, vecty = math.sin(self.angle), math.cos(self.angle)
                m = vecty/vectx
                closest_x = (10000, 10000)
                closest_y = (10000, 10000)
                # Check X
                if vectx <= 0:
                    x = (self.x - (self.x % tile_size))
                elif vectx > 0: 
                    x = (self.x - (self.x % tile_size)) + tile_size
                x_step = vectx/abs(vectx) * tile_size
                while True: 
                    y = m * (x - self.x) + self.y
                    if not (0 <= x < map_size) or (not 0 <= y < map_size ):
                        break
                    
                    row = int(y/tile_size)
                    if vectx <= 0: 
                        col = int(x/tile_size) - 1 if int(x/tile_size) - 1 >= 0 else 0
                    elif vectx >= 0: 
                        col = int(x/tile_size)
                    
                    if map[row][col] > 0:
                        closest_x = (x, y)
                        break
                    
                    x += x_step
                
                # Check Y
                if vecty <= 0:
                    y = (self.y - (self.y % tile_size))
                elif vecty > 0: 
                    y = (self.y - (self.y % tile_size)) + tile_size
                y_step = vecty/abs(vecty) * tile_size
                while True: 
                    x = (y - self.y)/m + self.x
                    if not (0 <= x < map_size) or (not 0 <= y < map_size):
                        break
                    
                    col = int(x/tile_size)
                    if vecty <= 0: 
                        row = int(y/tile_size) - 1 if int(y/tile_size) - 1 >= 0 else 0
                    elif vecty >= 0: 
                        row = int(y/tile_size)
                    
                    if map[row][col] > 0:
                        closest_y = (x, y)
                        break

                    y += y_step 

                # find
                distance_from_closest_x = ((closest_x[0] - self.x) ** 2 + (closest_x[1] - self.y) ** 2) ** 0.5
                distance_from_closest_y = ((closest_y[0] - self.x) ** 2 + (closest_y[1] - self.y) ** 2) ** 0.5
                # if the closest x is closer, cast the ray untill that point, otherwise cast it to the closesty
                if distance_from_closest_x < distance_from_closest_y:
                    # put the coordinate one point off of the wall so that nothing goes wrong in Sprite.check_visual
                    x = closest_x[0] - vectx/abs(vectx)
                    y = closest_x[1]
                else: 
                    x = closest_y[0]
                    y = closest_y[1] - vecty/abs(vecty)

                bullet_hole = Sprite(x, y, self.bullet_hole_image, 1)
                self.bullet_holes.append([bullet_hole, 0]) # 0: lifetime counter

        # show bullet holes
        for hole in self.bullet_holes:
            sprite, lifetime_counter = hole
            # draw the sprite
            sprite.check_visual(self.x, self.y, self.angle, self.fov, tile_size, map, map_size)
            sprite.draw(res, self.fov, self.x, self.y, screen)
            if lifetime_counter > 150:
                self.bullet_holes.remove(hole)
            hole[1] += 1


class Sprite:
    def __init__(self, x, y, image, size_factor):
        self.x, self.y = x, y
        self.image = image
        self.size_factor = size_factor
        self.side_error = 0.5 # make dependent on size factor when size_factor is figured out
        self.distance = 100
        self.visual = False 

    def check_visual(self, playerx, playery, player_angle, fov, tile_size, map, map_size):
        # min, max, and line angles 
        self.line_angle = math.atan2((self.x - playerx), (self.y - playery))
        self.line_angle %= (2 * math.pi)
        min_angle = player_angle - fov/2
        # max angle needs to be accessed by the draw function without calling check_visual so it must be an attribute
        self.max_angle = player_angle + fov/2
        # handle wrap around
        if (self.line_angle > math.pi * 2 - fov/2) and (player_angle < fov/2):
            min_angle += math.pi * 2
            self.max_angle += math.pi * 2
        if (self.line_angle < fov/2) and (player_angle > math.pi * 2 - fov/2): ## elif??
            # subtract 2pi from the min and max angles
            min_angle -= math.pi * 2
            self.max_angle -= math.pi * 2

        in_fov = (min_angle - self.side_error) <= self.line_angle <= (self.max_angle + self.side_error)
        if in_fov:
            vectx = self.x - playerx
            vecty = self.y - playery
            m = vecty/vectx

            # CHECK X
            if vectx <= 0:
                x = (playerx - (playerx % tile_size))
            elif vectx > 0: 
                x = (playerx - (playerx % tile_size)) + tile_size
            x_step = vectx/abs(vectx) * tile_size # vectx sign (- or +) * tile_size

            while True: 
                y = m * (x - playerx) + playery
                # outside fo map 
                if not (0 <= x < map_size) or (not 0 <= y < map_size):
                    break
                # y not in between player and sprite
                if not (min(playerx, self.x) <= x <= max(playerx, self.x)):
                    break
                
                row = int(y/tile_size)
                if vectx <= 0: 
                    col = int(x/tile_size) - 1 if int(x/tile_size) - 1 >= 0 else 0
                elif vectx >= 0: 
                    col = int(x/tile_size)
                if map[row][col] > 0:
                    self.visual = False
                    return None
                
                x += x_step
            

            # CHECK Y
            if vecty <= 0:
                y = (playery - (playery % tile_size))
            elif vecty > 0: 
                y = (playery - (playery % tile_size)) + tile_size
            y_step = vecty/abs(vecty) * tile_size
            while True: 
                # calculate x for each y
                x = (y - playery)/m + playerx
                # outside of map
                if not (0 <= x < map_size) or (not 0 <= y < map_size):
                    break
                # y not in between player and sprite
                if not (min(playery, self.y) <= y <= max(playery, self.y)):
                    break

                col = int(x/tile_size)
                if vecty <= 0: 
                    row = int(y/tile_size) - 1 if int(y/tile_size) - 1 >= 0 else 0
                elif vecty >= 0: 
                    row = int(y/tile_size)

                # if hit filled square
                if map[row][col] > 0:
                    self.visual = False
                    return None # terminate

                y += y_step 

            self.visual = True
            return None # terminate

        else: 
            self.visual = False
            return None # terminate
            
    def draw(self, res, fov, playerx, playery, screen):
        self.distance = ((self.x - playerx) ** 2 + (self.y - playery) ** 2) ** 0.5 # attribute because it needs to be accessed outside of the class
        # drawing should only take place if the monster is visual, (this attribute is updated in sprite.check_visual)
        if self.visual:
        #         radian                        * pixel per radain
            x = -(self.line_angle - self.max_angle) * (res[0]/fov)
            image = pygame.transform.scale_by(self.image, 200/self.distance * self.size_factor)
            self.rect = image.get_rect(center= (x, res[1]/2)) # needs to be accesed outside of the class by player.shoot()
            screen.blit(image, self.rect)


class Monster(Sprite):
    def __init__(self, x, y, size_factor, images, speed, animation_speed, health, damage):
        super().__init__(x, y, images['move'][0], size_factor)
        # state_possiblities = (none, move, attack, die)
        self.state = 'still'
        self.speed = speed
        self.images = images
        self.frame = 0
        self.animation_speed = animation_speed # smaller number is faster 
        self.health = health
        self.damage = damage

    def move(self, playerx, playery, map, tile_size, monsters):
        # if the monster is moving: (attacking and death are stationary states)
        if self.state == 'move':
            vectx, vecty = playerx - self.x, playery - self.y
            magnitude = (vectx ** 2 + vecty ** 2) ** 0.5
            # normalize the vectors 
            vectx /= magnitude
            vecty /= magnitude 
            # find move x and move y which are where the monster will move if nothing is in its way
            move_x, move_y = self.x + vectx * self.speed * 2, self.y + vecty * self.speed * 2 # exaterate (*2) the change slightly so that monsters dont get too close to walls 
            # find the move row and the move column that the move x and y corrospond to 
            move_row, move_col = int(move_y/tile_size), int(move_x/tile_size)
            # find the row and column that the monster is currently in 
            row, col = int(self.y/tile_size), int(self.x/tile_size)
            # if where the monster will move is filled
            if map[move_row][move_col] > 0:
                # if it is filled because of the row
                if map[move_row][col] > 0: 
                    # make the monste only move on the x (make the x make up for the y and make the x the y 0)
                    vectx = vectx/(abs(vectx) + 0.001) # magnitude (but magnitude is 1 because of normilization
                    vecty = 0
                # if it is filled because of the column (both can trigger (no elif))
                if map[row][move_col] > 0:  
                    # make the monster only move on the y (make the y make up for the x and make the x 0)
                    vecty = vecty/(abs(vecty) + 0.001) if vecty != 0 else 0
                    vectx = 0

            for monster in monsters:
                if monster != self and monster.state != 'die':
                    distance = ((self.x - monster.x) ** 2 + (self.y - monster.y) ** 2) ** 0.5
                    if distance < 10:
                        # if the monster is farther from the player
                        if monster.distance < self.distance:
                            vectx, vecty = 0, 0


            # find the xchange by multiplying the vector by the speed and move the monster by its xchange
            xchange = vectx * self.speed
            ychange = vecty * self.speed 
            self.x += xchange
            self.y += ychange       

    def animate(self, monsters):
        # Change state
        # if the monster is close to the player but is still moving, set the state to attack (monsters do not move while attacking)
        if self.distance < 30 and self.state == 'move':
            self.state = 'attack'
            self.frame = 0
        # if the monster is attacking but the distance from the player is greater than 30, change its state to move so that it can move towards the player
        elif self.distance > 30 and self.state == 'attack':
            self.state = 'move'
            self.frame = 0
        # if the monsters health hits 0 but it is not dieing,  set its state to die
        elif self.health <= 0 and self.state != 'die': 
            self.state = 'die'
            self.frame = 0
        # if the monster is dieing and the image (self.frame/self.animation_speed) it is on is the last image, remove it from monsters
        if self.state == 'die' and self.frame/self.animation_speed == len(self.images['die']) - 1: 
            monsters.remove(self)
        
        # animation should only take place if the monster is visual, (this attribute is updated in sprite.check_visual)
        if self.visual: 
            # since the player can be seen, and the state is still, set the state to move
            if self.state == 'still':
                self.state = 'move'
            # Handle animation
            # if the frame modulo the animation speed is 0 (this will trigger every {animation_speed} frames)
            if self.frame % self.animation_speed == 0:
                # if the frame / animation speed is is larger than the number of indexes in self.images[self.state], set the frame back to 0
                if self.frame/self.animation_speed > len(self.images[self.state]) - 1:
                    self.frame = 0
                # set the image to be the images of the state of the frame integer divided by the animation speed
                self.image = self.images[self.state][self.frame//self.animation_speed]
            # increment the frame
            self.frame += 1

    def attack(self, player):
        # if the monster is attacking decrement the health 
            if self.state == 'attack':
                player.health -= self.damage
        

if __name__ == '__main__':
    game = Game()
    game.run()