import pygame
from sys import exit
import math
class Game: 
    def __init__(self):
        pygame.init()
        self.full_res = (1000, 800)
        self.res = (1000, 800) # to be changed 
        self.screen = pygame.display.set_mode(self.full_res)
        self.clock = pygame.time.Clock()
        pygame.mouse.set_visible(False)
        # game independents
        _ = 0
        self.map = [
            [3, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [3, _, _, _, 6, _, _, _, 4, 1],
            [3, _, _, 1, _, 2, 1, _, _, 1],
            [3, _, 5, _, _, _, _, 4, _, 1],
            [3, _, 1, _, _, 3, _, 4, _, 1],
            [3, _, _, _, _, _, _, _, _, 1],
            [3, _, 1, 4, _, 5, _, 2, _, 1],
            [3, _, _, 6, 1, 1, 1, 6, _, 1],
            [3, 3, _, _, _, _, _, _, _, 1],
            [3, 3, 3, 3, 3, 3, 3, 3, 1, 1]
        ]
       
        self.map_size = 500 # 500x500 plane
        self.fps = int(self.clock.get_fps())
        

        # game dependents 
        self.map_tile_size = len(self.map) # width and height are the same for simplicity
        self.tile_size = int(self.map_size/self.map_tile_size) # current: 50
        self.xs = [self.tile_size * factor for factor in range(len(self.map))]
        self.ys = [self.tile_size * factor for factor in range(len(self.map))]
        self.mouse_x = self.res[0]/2
        self.prior_x = self.res[0]/2
        pygame.mouse.set_pos((self.mouse_x, self.res[1]/2))


        # textures
        self.wall_quality = (200, 64) # 150 columns (rays), 64 rectangles per column 
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

    def run(self):
        while True:
            self.screen.fill('Black')
            self.handle_events()
            self.draw_map()
            self.player.cast_rays(self.tile_size, self.map, self.map_size, self.screen)
            self.draw_sky()
            self.draw_walls()
            self.player.move(self.fps, self.map, self.tile_size)
            self.player.shoot(self.tile_size, self.map_size, self.map, self.res, self.screen)
            self.player.animate(self.screen, self.res, self.fps)
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

            if event.type == pygame.MOUSEBUTTONDOWN and self.player.arsenal[self.player.gun]['state'] == 'none': 
                self.player.arsenal[self.player.gun]['state'] = 'shooting'
                if self.player.arsenal[self.player.gun]['auto']:
                    self.player.arsenal[self.player.gun]['trigger_down'] = True

            if event.type == pygame.MOUSEBUTTONUP and self.player.arsenal[self.player.gun]['auto']:
                self.player.arsenal[self.player.gun]['trigger_down'] = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                self.player.gun += 1
                self.player.gun %= 3
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.player.arsenal[self.player.gun]['frame'] = 0
                self.player.arsenal[self.player.gun]['state'] = 'reloading'

    def draw_map(self):
        for row_i in range(self.map_tile_size):
            for col_i in range(self.map_tile_size):
                if self.map[row_i][col_i] > 0:
                    pygame.draw.rect(self.screen, (200, 200, 200), (self.xs[col_i] + self.res[0], self.ys[row_i], self.tile_size, self.tile_size))

        for x in self.xs:
            pygame.draw.line(self.screen, (100, 100, 100), (x + self.res[0], 0), (x + self.res[0], self.map_size))
        for y in self.ys:
            pygame.draw.line(self.screen, (100, 100, 100), (self.res[0], y), (self.res[0] + self.map_size, y))

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
            for pixel in range(self.wall_quality[1]):
                # texture y is equal to the integer of the pixel * the texture resolution modifyer
                tex_y = int(pixel * self.tex_res_mod)
                color = texture.get_at((tex_x, tex_y))
                pygame.draw.rect(self.screen, color, (x, y, width + 1, length + 1)) # +1 for round down case
                y += length
            x += width

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
        self.angle = math.pi
        self.fov = math.pi/3
        self.rays = []
        self.forward, self.back, self.left, self.right = False, False, False, False
        self.num_rays = wall_quality[0]
        self.speed = 100

        # weapons
        get_gun = lambda num: pygame.transform.scale_by(pygame.image.load(f'graphics/player/gun{num}.png'), 4)
        get_fire = lambda num: pygame.transform.scale_by(pygame.image.load(f'graphics/player/gun{num}_shoot.png'), 4)
        get_recoil = lambda num: pygame.transform.scale_by(pygame.image.load(f'graphics/player/gun{num}_recoil.png'), 4)
        get_reload = lambda num: pygame.transform.scale_by(pygame.image.load(f'graphics/player/gun{num}_relode.png'), 6)
        self.arsenal = [{'none': get_gun(0), 'shoot': get_fire(0), 'recoil':get_recoil(0), 'recoil_speed': 5, 'capasity': 8, 'magazine': 8, 'frame': 0, 'state': 'none', 'reload':get_reload(0), 'reload_speed': 1, 'auto': False, 'trigger_down': None},
                        {'none': get_gun(1), 'shoot': get_fire(1), 'recoil':get_recoil(1), 'recoil_speed': 3, 'capasity': 18, 'magazine': 18, 'frame': 0, 'state': 'none', 'reload':get_reload(1), 'reload_speed': 0.7, 'auto': False, 'trigger_down': None},
                        {'none': get_gun(2), 'shoot': get_fire(2), 'recoil':get_recoil(2), 'recoil_speed': 15, 'capasity': 30, 'magazine': 30, 'frame': 0, 'state': 'none', 'reload':get_reload(2), 'reload_speed': 0.3, 'auto': True, 'trigger_down': False}]
        
        self.gun = 0
        self.gun_height = res[1]
        self.gun_height_inc = 1
        self.shake = False
        self.bullet_holes = []
        self.bullet_hole_image = pygame.image.load('graphics/player/bullet_hole.png')

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
                pygame.draw.line(screen, 'Purple', (self.x + 1000, self.y), (closest_x[0] + 1000, closest_x[1]))
            else: 
                rays.append((distance_from_closest_y, closest_y[0] % tile_size, angle, y_texture_i))
                pygame.draw.line(screen, 'Purple', (self.x + 1000, self.y), (closest_y[0] + 1000, closest_y[1]))
            self.rays = rays

        # self.rays = rays
        return rays

    def move(self, fps, map, tile_size):
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
                self.gun_height_inc = -1
            if self.gun_height <= res[1]:
                self.gun_height_inc = 1
            self.gun_height += self.gun_height_inc

            if self.gun_height == res[1] and not (self.forward or self.back or self.left or self.right):
                self.shake = False
        if self.forward or self.back or self.left or self.right: 
            self.shake = True


        

        rect = image.get_rect(midbottom = (res[0]/2, self.gun_height))
        screen.blit(image, rect)

    def shoot(self, tile_size, map_size, map, res, screen):
        # handle new shots 
        # if the player is shooting
        if self.arsenal[self.gun]['state'] == 'shooting' and self.arsenal[self.gun]['frame'] == 1:
            hit_monster = False # come back to
            if hit_monster:
                pass # come back to 
            else:
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

            if sprite.check_visual(self.x, self.y, self.angle, self.fov, tile_size, map, map_size):
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
                    return False
                
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
                    return False

                y += y_step 

            return True

        else: 
            return False
            
    def draw(self, res, fov, playerx, playery, screen):
        #         radian                        * pixel per radain
        x = -(self.line_angle - self.max_angle) * (res[0]/fov)
        distance = ((self.x - playerx) ** 2 + (self.y - playery) ** 2) ** 0.5
        image = pygame.transform.scale_by(self.image, 200/distance * self.size_factor)
        rect = image.get_rect(midtop = (x, res[1]/2))
        screen.blit(image, rect)

      
if __name__ == '__main__':
    game = Game()
    game.run()