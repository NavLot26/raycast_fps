import pygame
from sys import exit
import math
from random import choice, randint

from maps import maps # maps array from the maps source file 

class Game: 
    def __init__(self):
        '''Game class that runs the 3d shooter, it handles: running the game, handling events, displaying the game icons,
        spawning monsters, spawning packages, and drawing the 3d projection (player class casts the rays but game class 
        handles actually drawing the sky and walls)'''

        pygame.init()
        self.res = (1400, 800)
        self.screen = pygame.display.set_mode(self.res)

        self.clock = pygame.time.Clock()
        self.map_size = 500 # 500x500 plane

        self.brightness = 1 # brightness for taking damage screen getting darker 
        
        # directory should be set to the directory that the file is being run it
        self.directory = ''

        self.wall_quality = (200, 32) 
        self.tex_res = 64 # 64 x 64 images
        # the texture resolution modifyer is the modifyer between the quality of the textures and the number of pixels drawn per line
        self.tex_res_mod = self.tex_res/self.wall_quality[1]

        # a dictionary that maps the texture number to image
        self.wall_textures = {i:pygame.image.load(f'{self.directory}graphics/game/wall_texture{i}.png') for i in range(1, 7)}

        # sky 
        self.sky_texture = pygame.image.load(f'{self.directory}graphics/game/sky_texture.png')
        self.sky_res = (300, 100)
        self.sky_quality = (75, 30)
        # Create the level using self.create_level, but then reset mouse visible and active to true and false since they were set to false and true in create_level
        self.create_level()
        pygame.mouse.set_visible(True)
        self.active = False

        # intro screen + music 
        self.intro_screen = pygame.transform.scale(pygame.image.load(f'{self.directory}graphics/game/intro_screen.png'), self.res)
        self.music = pygame.mixer.Sound(f'{self.directory}audio/music.wav')
        self.music.set_volume(0.5)

    def create_level(self):
        '''Method that creates a new level and is run every time the game restarts or starts, it is responsible for:
        setting/resetting some attributes, spawning the monsters and packages and setting/resetting all of the UI elements'''

        # open level.txt and save the level, set mouse visible to false and active to true
        with open(f'{self.directory}level.txt') as level_file:
            self.level = int(level_file.read())
        pygame.mouse.set_visible(False)
        self.active = True
        # find the map from the imported list based on the level 
        self.map = maps[(self.level - 1)% len(maps)]

        self.map_tile_size = len(self.map) # width and height are the same 
        self.tile_size = int(self.map_size/self.map_tile_size)
        
        # mouse_x and mouse_prior x are used to calculate turning speeds, set them both to the center of the screen
        self.mouse_x = self.res[0]/2
        self.prior_x = self.res[0]/2
        pygame.mouse.set_pos((self.mouse_x, self.res[1]/2))


        # initialize the player and spawn monsters and packs 
        self.player = Player(self.tile_size, self.wall_quality, self.res, self.level, self.directory)

        self.spawn_monsters(self.level)
        self.spawn_packs(5)


        # UI 
        # define a health bar, stamina bar reload bar and ammo text surface
        self.current_health_on_bar = self.player.health * 2
        self.health_bar = pygame.surface.Surface((self.player.health * 2, 15))
        self.health_bar.fill('Green')
        self.health_rect = self.health_bar.get_rect(topleft = (10, 10))
        
        self.current_stamina_on_bar = self.player.stamina * 2
        self.sprint_bar = pygame.surface.Surface((self.player.stamina * 2, 15))
        self.sprint_bar.fill('Blue')
        self.sprint_rect = self.sprint_bar.get_rect(topleft = (220, 10))
        
        self.reload_bar = pygame.surface.Surface((self.player.arsenal[self.player.gun]['reload_speed'] * 200/self.player.arsenal[self.player.gun]['reload_speed'], 15))
        self.reload_bar.fill('Green')
        self.reload_rect = self.reload_bar.get_rect(midbottom = (self.res[0]/2, self.res[1] - 10))

        self.font = pygame.font.Font(f'{self.directory}graphics/game/font.ttf', 75)
        self.magazine_in_ammo = self.player.arsenal[self.player.gun]['magazine']
        self.capasity_in_ammo = self.player.arsenal[self.player.gun]['capasity']
        self.ammo = self.font.render(f"{self.player.arsenal[self.player.gun]['magazine']}/{self.player.arsenal[self.player.gun]['capasity']}", False, 'Red')
        self.ammo_rect = self.ammo.get_rect(topright = (self.res[0] - 10, 10))

       
        self.num_monsters_in_surf = self.num_monsters # the actual self.num_monsters is set in spawn_monsters
        self.num_monsters_surf = self.font.render(f'Killed: {self.num_monsters - len(self.monsters)}/{self.num_monsters}', False, 'Red')
        self.num_monsters_rect = self.num_monsters_surf.get_rect(midtop = (self.res[0]/2, 10))

    def run(self):
        '''Method that actually runs the class (the majority of the games methods end up being run here) 
        it is responsible for all in game functionality '''

        self.music.play(loops = -1) # infinite loop s

        while True:

            self.handle_events() # internal state handling
            # if the game is active, draw the sky cast the players rays, draw the walls, move the player, let the player shoot, draw the sprites, animatre the player, handle the end of the game
            if self.active:
                self.draw_sky()
                self.player.cast_rays(self.tile_size, self.map, self.map_size)
                self.draw_walls()
                self.player.move(self.map, self.tile_size)
                self.player.shoot(self.tile_size, self.map_size, self.map, self.res, self.screen, self.monsters)
                self.draw_sprites()
                self.player.animate(self.screen, self.res)
                self.handle_end()

            self.display_icons() # internal state handling
            
            
            # pygame update boilerplate
            pygame.display.update()
            self.clock.tick(60)
            pygame.display.set_caption(f'Maze Shooter (FPS: {int(self.clock.get_fps())})')
          
    def handle_events(self):
        '''Method that handles all of the events in the game including: exiting the game, mouse movement, WASD presses, 
        mouse clicking, e for switching guns, r for reloading, shift for sprinting, and q for quiting to the homescreen'''
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                # quit pygame, exit all of the code
                pygame.quit()
                exit()

            if self.active: 
                if event.type == pygame.MOUSEMOTION: 
                    # set the prior mouse x position the mouse position and the mouse_x to the postion of the event 
                    self.prior_x = self.mouse_x
                    self.mouse_x = pygame.mouse.get_pos()[0] # use get_pos() instead of event.pos because it is more accurate 
                    # if the mouse is outside of the set boundries
                    if not (200 < self.mouse_x < self.res[0] - 200):
                        # the prior_x should now be the middle of the screen minus the old difference between itself and the mouse_x
                        self.prior_x = self.res[0]/2 - (self.mouse_x - self.prior_x)
                        # the mouse_x should be the middle of the screen
                        self.mouse_x = self.res[0]/2
                        # set the position of the mouse to the middle of the screen
                        pygame.mouse.set_pos((self.res[0]/2, self.res[1]/2))
                    
                    # use the diff between the two mouse positions to change the players angle 
                    xchange = self.mouse_x - self.prior_x
                    self.player.angle -= xchange/500
                    self.player.angle %= (2 * math.pi)
                
                # player movmenent 
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
                

                # set state to shooting only if they are not shooting or recoiling
                if event.type == pygame.MOUSEBUTTONDOWN and self.player.arsenal[self.player.gun]['state'] == 'none': 
                    self.player.arsenal[self.player.gun]['state'] = 'shooting'
                    # if the gun they are using is automatic, set the trigger down key to have a value of true
                    if self.player.arsenal[self.player.gun]['auto']:
                        self.player.arsenal[self.player.gun]['trigger_down'] = True
                # if the player releases the mouse button and the gun is auto, set trigger down to be False
                if event.type == pygame.MOUSEBUTTONUP and self.player.arsenal[self.player.gun]['auto']:
                    self.player.arsenal[self.player.gun]['trigger_down'] = False
                
                
                # switch weapon
                if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                    self.player.gun += 1
                    self.player.gun %= len(self.player.arsenal)
                
                # reload
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r and self.player.arsenal[self.player.gun]['magazine'] < self.player.arsenal[self.player.gun]['capasity']:
                    self.player.arsenal[self.player.gun]['frame'] = 0 # frame 0 to start reloading 
                    self.player.arsenal[self.player.gun]['state'] = 'reloading'
                
                # sprint
                if event.type == pygame.KEYDOWN and event.key == pygame.K_LSHIFT: 
                    self.player.speed = 3
                elif event.type == pygame.KEYUP and event.key == pygame.K_LSHIFT: 
                    self.player.speed = 1.5


                # if the player presses q to quit the game, set the intro screen to be the plain one
                if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                    self.intro_screen = pygame.transform.scale(pygame.image.load(f'{self.directory}graphics/game/intro_screen.png'), self.res)
                    pygame.mouse.set_visible(True)
                    self.active = False


            else: # menu screen 
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    # if they press the play button 
                    if (self.res[0]/2 - 200 < x < self.res[0]/2 + 200) and (self.res[1]/2 - 75 < y < self.res[1]/2 + 75):
                        self.create_level()

    def display_icons(self):
        '''Method that displays all of the informational game icons including: the health, stamina, and reloading bars 
        and the number of bullets and capasity and monsters killed'''

        if self.active: 

            # if the current_health_on the health bar is not 2x the players health, update the health bars size and color
            if self.current_health_on_bar != self.player.health * 2: 
                self.current_health_on_bar = self.player.health * 2
                self.health_bar = pygame.surface.Surface((self.player.health * 2, 15))
                if self.player.health >= 75:
                    self.health_bar.fill('Green')
                elif self.player.health >= 50:
                    self.health_bar.fill('Yellow')
                elif self.player.health >= 25:
                    self.health_bar.fill('Orange')
                else:
                    self.health_bar.fill('Red')

            # if the current amount on the stamina bar is not the same as the players stamina * 3, update the stamina bars size
            if self.current_stamina_on_bar != self.player.stamina * 2: 
                self.current_stamina_on_bar = self.player.stamina * 2
                self.sprint_bar = pygame.surface.Surface((self.player.stamina * 2, 15))
                self.sprint_bar.fill('Blue')

            # update magazine display
            if self.magazine_in_ammo != self.player.arsenal[self.player.gun]['magazine'] or self.capasity_in_ammo != self.player.arsenal[self.player.gun]['capasity']:
                # set the magazine in ammo to the magazine and the capasity to the capasity
                self.magazine_in_ammo = self.player.arsenal[self.player.gun]['magazine']
                self.capasity_in_ammo = self.player.arsenal[self.player.gun]['capasity']
                # updaste ammo and its rectange (so that it is always centered in the corrent place)
                self.ammo = self.font.render(f"{self.player.arsenal[self.player.gun]['magazine']}/{self.player.arsenal[self.player.gun]['capasity']}", False, 'Red')
                self.ammo_rect = self.ammo.get_rect(topright = (self.res[0] - 10, 10))
            if self.num_monsters_in_surf != len(self.monsters):
                self.num_monsters_in_surf = len(self.monsters)
                self.num_monsters_surf = self.font.render(f'Killed: {self.num_monsters - len(self.monsters)}/{self.num_monsters}', False, 'Red')


            # display the icons 
            pygame.draw.rect(self.screen, 'White', self.health_rect)
            self.screen.blit(self.health_bar, self.health_rect)
            pygame.draw.rect(self.screen, 'White', self.sprint_rect)
            self.screen.blit(self.sprint_bar, self.sprint_rect)
            self.screen.blit(self.ammo, self.ammo_rect)
            self.screen.blit(self.num_monsters_surf, self.num_monsters_rect)

            # if the players state is reloading, update and display the reload bar
            if self.player.arsenal[self.player.gun]['state'] == 'reloading':
                self.reload_bar = pygame.surface.Surface((self.player.arsenal[self.player.gun]['frame'] * 200/self.player.arsenal[self.player.gun]['reload_speed'], 15))
                self.reload_bar.fill('Green')
                pygame.draw.rect(self.screen, 'White', self.reload_rect)
                self.screen.blit(self.reload_bar, self.reload_rect)

        else: # menu screen 
            self.screen.blit(self.intro_screen, (0, 0))

    def spawn_monsters(self, level):
        '''Method that is responsible for randomly spawning different kinds of monsters in random positions depending on the level'''
        monster_types = [0] # only first monster to start off with 
        # depending on what level it is add different kinds of monsters monsters
        if level >= 3:
            monster_types.append(1)
        if level >= 5:
            monster_types.append(2)
        if level >= 7:
            monster_types.append(3)
        if level >= 10:
            monster_types.append(4)

        self.num_monsters = level + 3
        
        # create a list of dictionaries where each dictionary holds the information for the monsters        
        get_move = lambda monster, num: [pygame.image.load(f'{self.directory}graphics/monster{monster}/move{i}.png') for i in range(num)]
        get_attack = lambda monster, num: [pygame.image.load(f'{self.directory}graphics/monster{monster}/attack{i}.png') for i in range(num)]
        get_die = lambda monster, num: [pygame.image.load(f'{self.directory}graphics/monster{monster}/die{i}.png') for i in range(num)]

        get_sounds = lambda monster, num: [pygame.mixer.Sound(f'{self.directory}audio/monster{monster}/sound{i}.wav') for i in range(num)]
        get_die_sound = lambda monster: pygame.mixer.Sound(f'{self.directory}audio/monster{monster}/death.mp3')
        monsters_info = [
            {'move': get_move(0, 3), 'attack': get_attack(0, 3), 'die':get_die(0, 5), 'speed': 1, 'size_factor': 1, 'animation_speed': 10, 'health': 2, 'damage': 0.5, 'sounds': get_sounds(0, 17), 'die_sound': get_die_sound(0), 'audio_speed': 10},
            {'move': get_move(1, 2), 'attack': get_attack(1, 2), 'die':get_die(1, 5), 'speed': 0.75, 'size_factor': 1.5, 'animation_speed': 15, 'health': 3, 'damage':1, 'sounds': get_sounds(1, 17), 'die_sound': get_die_sound(1), 'audio_speed': 10},
            {'move': get_move(2, 3), 'attack': get_attack(2, 2), 'die':get_die(2, 4), 'speed': 1.25, 'size_factor': 0.75, 'animation_speed': 12, 'health': 2, 'damage':0.4, 'sounds': get_sounds(2, 17), 'die_sound': get_die_sound(2), 'audio_speed': 10},
            {'move': get_move(3, 3), 'attack': get_attack(3, 2), 'die':get_die(3, 4), 'speed': 1, 'size_factor': 1, 'animation_speed': 10, 'health': 3, 'damage':0.6, 'sounds': get_sounds(3, 17), 'die_sound': get_die_sound(3), 'audio_speed': 10},
            {'move': get_move(4, 2), 'attack': get_attack(4, 2), 'die':get_die(4, 4), 'speed': 0.75, 'size_factor': 2, 'animation_speed': 20, 'health':5, 'damage':1.25, 'sounds': get_sounds(4, 17), 'die_sound': get_die_sound(4), 'audio_speed': 40}
        ]
        monsters = []
        for monster in range(self.num_monsters):
            num = choice(monster_types)
            while True:
                x, y = randint(self.tile_size, self.map_size - self.tile_size), randint(self.tile_size, self.map_size - self.tile_size)
                row = y//self.tile_size
                col = x//self.tile_size
                # if the monster is too close to the player or on a filled block try again
                if ((self.player.x - x) ** 2 + (self.player.y - y) ** 2) ** 0.5 < 200: 
                    continue
                if self.map[row][col] == 0: # they must spawn on empty space as well 
                    break

            images = {'move':monsters_info[num]['move'],'attack':monsters_info[num]['attack'], 'die':monsters_info[num]['die']} 
            monsters.append(Monster(x, y, monsters_info[num]['size_factor'], images, monsters_info[num]['speed'], monsters_info[num]['animation_speed'], monsters_info[num]['health'], monsters_info[num]['damage'], monsters_info[num]['sounds'], monsters_info[num]['die_sound'], monsters_info[num]['audio_speed']))
        self.monsters = monsters
    
    def spawn_packs(self, num_packs):
        '''Method that is responsible for randomly spawning the health and ammunition packages on the map'''
        packs = []
        for pack in range(num_packs):
            # power up types: Ammo, health
            type_ = choice(('ammo', 'health'))
            if type_ == 'ammo':
                image = pygame.image.load(f'{self.directory}graphics/game/ammo_pack.png')
            elif type_ == 'health':
                image = pygame.image.load(f'{self.directory}graphics/game/health_pack.png')
            while True:
                x, y = randint(self.tile_size, self.map_size - self.tile_size), randint(self.tile_size, self.map_size - self.tile_size)
                row = y//self.tile_size
                col = x//self.tile_size
                # if the pack is on a filled block try again, otherwise exit the loop 
                if self.map[row][col] == 0:
                    break
            # append a tuple with a sprite and the type to the packs list
            packs.append((Sprite(x, y, image, 1), type_))
        self.packs = packs

    def draw_sprites(self):
        '''Method that is responsible for drawing in the projection, moving, animating, and playing the monsters' audio, and drawing the packs in 
        the projection. (Bullet holes are drawn seperatly direcly in the player class because since they are always up against the wall they 
        can never be in front of a monster and can therfore be drawn seperatly)'''
        # sort the sprites based on their distance (sprites include packs and monsters)
        sprites = sorted([pack[0] for pack in self.packs] + self.monsters, key = lambda sprite: 1/sprite.distance)
        # loop through each sprite
        for sprite in sprites:
            if sprite in self.monsters: # we need to check visual, move, animate, draw, and play audio
                sprite.check_visual(self.player.x, self.player.y, self.player.angle, self.player.fov, self.tile_size, self.map, self.map_size)
                sprite.move(self.player.x, self.player.y, self.map, self.tile_size, self.monsters)
                sprite.animate(self.monsters, self.player)
                sprite.draw(self.res, self.player.fov, self.player.x, self.player.y, self.screen)
                sprite.play_audio()
            else: # if the sprite is a pack, just check visual and draw
                sprite.check_visual(self.player.x, self.player.y, self.player.angle, self.player.fov, self.tile_size, self.map, self.map_size)
                sprite.draw(self.res, self.player.fov, self.player.x, self.player.y, self.screen)

        # handle packs 
        for pack in self.packs:
            sprite, type_ = pack
            if sprite.distance < 10: # player picks up the pack if they are closer than 10 units 
                if type_ == 'ammo': 
                    self.player.arsenal[self.player.gun]['magazine'] = self.player.arsenal[self.player.gun]['capasity']
                    self.player.arsenal[self.player.gun]['state'] = 'none'
                    self.player.arsenal[self.player.gun]['reload_sound'].play()
                elif type_ == 'health': # add 20 to the players heath
                    self.player.health += 20
                    if self.player.health > 100:
                        self.player.health = 100
                    self.player.heal_sound.play()
                # remove the pack from the packs list if it was used 
                self.packs.remove(pack)  
        
    def draw_walls(self):
        '''Method that is responsible for drawing the textured walls in the 3d projection using the rays that are casted in the player class. 
        Algorithm was developed by me with the exception of some references from the internet'''

        # x coordinate for drawin on screen and width of each line
        x = 0
        width = self.res[0]/self.player.num_rays

        for ray in self.player.rays: 
            distance, tex_point, angle, tex_i = ray # a ray is returned as the distance, where on the texture it lands, the angle, and which texture it lands on 
            
            # fix the fishe eye effect by multiplyin each distance by is cosine, shrinking distances on the edge of the screen 
            fish_eye_fix = math.cos(self.player.angle - angle) 
            distance *= fish_eye_fix

            height = 20000/distance # height is based on inverse distance 
            texture = self.wall_textures[tex_i]
            tex_x = int((tex_point * self.tex_res/self.tile_size)) # x point on texture based on texture point 

            # draw each y rectangle, making up the line, starting at the top 
            y = self.res[1]/2 - height/2
            length = height/self.wall_quality[1]
            color_mod = distance/(self.brightness * 4) # color mod depending on brightness as well as the distance, making farther areas darker

            for pixel in range(self.wall_quality[1]):
                tex_y = int(pixel * self.tex_res_mod) # get the y coordinate on the texture, so we can sample from there 
                color = texture.get_at((tex_x, tex_y))
                # color mod is used to darken the color 
                color = (color[0] - color_mod if color[0] - color_mod >= 0 else 0,
                         color[1] - color_mod if color[1] - color_mod >= 0 else 0,
                         color[2] - color_mod if color[2] - color_mod >= 0 else 0)
                # draw a rectangle for that pixel 
                pygame.draw.rect(self.screen, color, (x, y, width + 1, length + 1)) # +1 for round down case

                # move to the next place to draw 
                y += length
            x += width

    def draw_sky(self):
        '''Method that is responsible for drawing the textured sky in the 3d projection. 
        this algorithm was also almost entirly developed by me other than some minor internet references '''

        color_mod = 20/self.brightness # the color mod only depends on the brightness here, since there is no "distance" to the sky 


        # start angle and start x coordinate for drawing 
        angle = self.player.angle + self.player.fov/2
        x = 0

        width = self.res[0]/self.sky_quality[0]
        height = self.res[1]/2/self.sky_quality[1]

        for ray in range(self.sky_quality[0]): 
            # decrement the angle and keep it in between 0 and 2pi
            angle -= self.player.fov/self.sky_quality[0]
            angle %= (math.pi * 2)

            tex_x = int(angle * self.sky_res[0]/(math.pi * 2)) # sample x is found using the angle scaled to cover the whole sky 
            
            # each y coordinate in that line 
            y = 0
            for rect in range(self.sky_quality[1]):
                tex_y = int(rect * self.sky_res[1]/self.sky_quality[1])
                
                color = self.sky_texture.get_at((tex_x, tex_y))
                color = (color[0] - color_mod if color[0] - color_mod >= 0 else 0,
                         color[1] - color_mod if color[1] - color_mod >= 0 else 0,
                         color[2] - color_mod if color[2] - color_mod >= 0 else 0)

                pygame.draw.rect(self.screen, color, (x, y, width + 1, height + 1)) # +1 for round down case

                y += height
            x += width

        # draw the ground here as well, just as a solid rectangle 
        pygame.draw.rect(self.screen, (self.brightness * 75, self.brightness * 75, self.brightness * 75), (0, self.res[1]/2, self.res[0], self.res[1]/2))
        
        
        # handle brightness based on monster attacks 
        attacking = [monster.state == 'attack' for monster in self.monsters]
        if True in attacking and self.brightness > 0.5:
            self.brightness -= 0.05
        elif not (True in attacking) and self.brightness < 1:
            self.brightness += 0.1

    def handle_end(self):
        '''Method that is responsible for ending the game if the player wins or looses and returning the player to the home screen'''
        
        # death (health hits 0 )
        if self.player.health <= 0: 
            self.intro_screen = pygame.transform.scale(pygame.image.load(f'{self.directory}graphics/game/loose_screen.png'), self.res)
            pygame.mouse.set_visible(True)
            self.active = False

        # win (no more monsters)
        elif len(self.monsters) == 0:
            self.intro_screen = pygame.transform.scale(pygame.image.load(f'{self.directory}graphics/game/win_screen.png'), self.res)
            pygame.mouse.set_visible(True)
            self.active = False

            # increment level in save file 
            self.level += 1
            with open(f'{self.directory}level.txt', 'w') as level_file:
                level_file.write(str(self.level))

class Player:
    def __init__(self, tile_size, wall_quality, res, level, directory):
        # player always starts in the middle of the top left tile 
        self.x = tile_size/2 + tile_size
        self.y = tile_size/2 + tile_size

        self.angle = 0
        self.fov = math.pi/3
        self.rays = []

        self.forward, self.back, self.left, self.right = False, False, False, False
        self.num_rays = wall_quality[0] # number of rays is based on the number of lines the game wants to draw 
        
        # size modifactions for the gun rendering 
        size_mod1 = res[0]/280
        size_mod2 = res[0]/233
        # use lambda functions to easily get the textures and sounds 
        get_gun = lambda num: pygame.transform.scale_by(pygame.image.load(f'{directory}graphics/player/gun{num}.png'), size_mod1)
        get_shoot = lambda num: pygame.transform.scale_by(pygame.image.load(f'{directory}graphics/player/gun{num}_shoot.png'), size_mod1)
        get_recoil = lambda num: pygame.transform.scale_by(pygame.image.load(f'{directory}graphics/player/gun{num}_recoil.png'), size_mod1)
        get_reload = lambda num: pygame.transform.scale_by(pygame.image.load(f'{directory}graphics/player/gun{num}_relode.png'), size_mod2)
        
        get_shoot_sound = lambda num: pygame.mixer.Sound(f'{directory}audio/player/gun{num}_shoot.wav')
        get_reload_sound = lambda num: pygame.mixer.Sound(f'{directory}audio/player/gun{num}_reload.wav')



        # guns are represented by data in a dictionary 
        # the arsenal gets new guns based on the level 
        self.arsenal = []
        self.arsenal.append({'none': get_gun(0), 'shoot':get_shoot(0), 'recoil':get_recoil(0), 'recoil_speed': 15, 'capasity': 8, 'magazine': 8, 'frame': 0, 'state': 'none', 'reload':get_reload(0), 'reload_speed': 50, 'auto': False, 'trigger_down': None, 'damage': 1, 'shoot_sound':get_shoot_sound(0), 'reload_sound':get_reload_sound(0)})
        if level >= 5: 
            self.arsenal.append({'none': get_gun(1), 'shoot':get_shoot(1), 'recoil':get_recoil(1), 'recoil_speed': 20, 'capasity': 18, 'magazine': 18, 'frame': 0, 'state': 'none', 'reload':get_reload(1), 'reload_speed': 75, 'auto': False, 'trigger_down': None, 'damage': 2, 'shoot_sound':get_shoot_sound(1), 'reload_sound':get_reload_sound(1)})
        if level >= 8: 
            self.arsenal.append({'none': get_gun(2), 'shoot':get_shoot(2), 'recoil':get_recoil(2), 'recoil_speed': 5, 'capasity': 30, 'magazine': 30, 'frame': 0, 'state': 'none', 'reload':get_reload(2), 'reload_speed': 150, 'auto': True, 'trigger_down': False, 'damage': 1, 'shoot_sound':get_shoot_sound(2), 'reload_sound':get_reload_sound(2)})

        self.gun = 0 # index from arsenal 
        self.gun_height = res[1] 
        self.gun_height_inc = 1
        self.shake = False # when walking, the gun shakes 

        self.bullet_holes = []
        self.bullet_hole_image = pygame.image.load(f'{directory}graphics/player/bullet_hole.png')

        # some other data 
        self.speed = 1.5
        self.health = 100
        self.stamina = 100

        # sound the player gets when they heal 
        self.heal_sound = pygame.mixer.Sound(f'{directory}audio/player/heal.mp3')

    def cast_rays(self, tile_size, map, map_size):
        '''Since I do not know enough about triganometry to implement this algoirhtm as it usually is done, I created my own custom implementation that just used point slope formula and other algebraic techniques '''
        rays = []
        angle = self.angle + self.fov/2 # start on the left of fov 

        for ray in range(self.num_rays):
            angle = (angle - self.fov/self.num_rays) % (math.pi * 2)
            vectx, vecty = math.sin(angle), math.cos(angle)

            m = vecty/vectx # slope 

            # very far, so always overriden 
            closest_x = (10000, 10000)
            closest_y = (10000, 10000)

            # Check X intersections 

            # first x line and the step to continue 
            if vectx <= 0:
                x = (self.x - (self.x % tile_size))
            elif vectx > 0: 
                x = (self.x - (self.x % tile_size)) + tile_size
            
            x_step = vectx/abs(vectx) * tile_size

            while True: # breaks when we hit a filled tile 
                # use point slope formula to get y point of the collision 
                y = m * (x - self.x) + self.y

                # if the point of intersection is outside of the map (break out of the loop since there is nothing important past there )
                if (not 0 <= y < map_size):
                    break
                
                row = int(y/tile_size)
                col = int(x/tile_size) - 1 if vectx <= 0 else int(x/tile_size) # incormperate the direction of the ray into collumn to be correct 
                
                if map[row][col] > 0: # if it is filled 
                    closest_x = (x, y)
                    x_texture_i = map[row][col]
                    break

                x += x_step
            
            # Check Y intersections (basically the same as checking x, just switching some of the logic)
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
                row = int(y/tile_size) - 1 if vecty <= 0 else int(y/tile_size)
                
                if map[row][col] > 0:
                    closest_y = (x, y)
                    y_texture_i = map[row][col]
                    break

                y += y_step 
        
            distance_from_closest_x = ((closest_x[0] - self.x) ** 2 + (closest_x[1] - self.y) ** 2) ** 0.5
            distance_from_closest_y = ((closest_y[0] - self.x) ** 2 + (closest_y[1] - self.y) ** 2) ** 0.5
            
            # whcih ever one is closer, use that as the ray distance 
            if distance_from_closest_x < distance_from_closest_y:
                rays.append((distance_from_closest_x, closest_x[1] % tile_size, angle, x_texture_i))
            else: 
                rays.append((distance_from_closest_y, closest_y[0] % tile_size, angle, y_texture_i))

        self.rays = rays

    def move(self, map, tile_size):
        # depending on the direction they want to go, change the x and y coordinates while not allowing them to go through solid tiles
        if self.forward and \
        map[int((math.cos(self.angle) * 10 + self.y)/tile_size)][int((math.sin(self.angle) * 10 + self.x)/tile_size)] == 0: # ensure it is not solid 
            self.x += math.sin(self.angle) * self.speed
            self.y += math.cos(self.angle) * self.speed
        elif self.back and \
        map[int((math.cos(self.angle - math.pi) * 10 + self.y)/tile_size)][int((math.sin(self.angle - math.pi) * 10 + self.x)/tile_size)] == 0: 
            self.x += math.sin(self.angle - math.pi) * self.speed
            self.y += math.cos(self.angle - math.pi) * self.speed
        if self.right and \
        map[int((math.cos(self.angle - math.pi/2) * 10 + self.y)/tile_size)][int((math.sin(self.angle - math.pi/2) * 10 + self.x)/tile_size)] == 0: 
            self.x += math.sin(self.angle - math.pi/2) * self.speed
            self.y += math.cos(self.angle - math.pi/2) * self.speed
        elif self.left and \
        map[int((math.cos(self.angle + math.pi/2) * 10 + self.y)/tile_size)][int((math.sin(self.angle + math.pi/2) * 10 + self.x)/tile_size)] == 0:
            self.x += math.sin(self.angle + math.pi/2) * self.speed
            self.y += math.cos(self.angle + math.pi/2) * self.speed
        
        # handle sprinting 
        if self.speed == 3:
            if self.stamina <= 2: 
                self.speed = 1.5
            self.stamina -= 1 # constant stamina decrement if sprinting 
        elif self.stamina < 100: 
            self.stamina += 0.25 # constant increment if not sprinting 

    def animate(self, screen, res):
        # shooting 
        if self.arsenal[self.gun]['state'] == 'shooting':
            if self.arsenal[self.gun]['frame'] <= 6: # six frame animation
                if self.arsenal[self.gun]['frame'] == 1:
                    self.arsenal[self.gun]['shoot_sound'].play()
                image = self.arsenal[self.gun]['shoot']
                self.arsenal[self.gun]['frame']+= 1
            else: # recoil 
                self.arsenal[self.gun]['state'] = 'recoiling'
                self.arsenal[self.gun]['magazine'] -= 1
                self.arsenal[self.gun]['frame'] = 0
        # handle recoiling 
        if self.arsenal[self.gun]['state'] == 'recoiling':
            if self.arsenal[self.gun]['frame'] <= self.arsenal[self.gun]['recoil_speed']: # the larger the recoil speed the less time it takes for the animation frame to reach its max
                image = self.arsenal[self.gun]['recoil']
                self.arsenal[self.gun]['frame'] += 1
            else: 
                # move onto the next animation of the gun (dependent on auto)
                if self.arsenal[self.gun]['auto'] and self.arsenal[self.gun]['trigger_down']:
                    self.arsenal[self.gun]['state'] = 'shooting'
                    image = self.arsenal[self.gun]['shoot']
                # not auto 
                else:
                    self.arsenal[self.gun]['state'] = 'none'
                # set the frame of the gun to be 0, since recoiling is over
                self.arsenal[self.gun]['frame'] = 0
                
        # if the gun ran out of bullets (from the last shot), set the guns state to be reloading
        if self.arsenal[self.gun]['magazine'] <= 0: 
            self.arsenal[self.gun]['state'] = 'reloading'

        # handle reloading 
        if self.arsenal[self.gun]['state'] == 'reloading':
            if self.arsenal[self.gun]['frame'] <= self.arsenal[self.gun]['reload_speed']:
                if self.arsenal[self.gun]['frame'] == 1:
                    self.arsenal[self.gun]['reload_sound'].play()
                image = self.arsenal[self.gun]['reload']
                self.arsenal[self.gun]['frame'] += 1
            else: 
                # done recoiling 
                self.arsenal[self.gun]['state'] = 'none'
                self.arsenal[self.gun]['frame'] = 0
                self.arsenal[self.gun]['magazine'] = self.arsenal[self.gun]['capasity']

        if self.arsenal[self.gun]['state'] == 'none':
            image = self.arsenal[self.gun]['none']

        # shake gun 
        if self.shake: 
            if self.gun_height >= res[1] + 20: 
                self.gun_height_inc = -self.speed//1.5
            if self.gun_height <= res[1]:
                self.gun_height_inc = self.speed//1.5
            self.gun_height += self.gun_height_inc
            # we should only check if we should stop shaking when it reaches the bottom of the screen that way if the player stops moving it will always end up at the bottom of the screen 
            # if the gun reached the bottom of the screen the player is not moving, set self.shake to be false
            if self.gun_height <= res[1] and not (self.forward or self.back or self.left or self.right):
                self.shake = False
        # otherwise, if the player is not shaking and it is moveing, set self.shake to True
        elif self.forward or self.back or self.left or self.right: 
            self.shake = True

        rect = image.get_rect(midbottom = (res[0]/2, self.gun_height))

        screen.blit(image, rect) # draw gun 

    def shoot(self, tile_size, map_size, map, res, screen, monsters):
        ### NEW SHOTS, CAST A RAY 
        if self.arsenal[self.gun]['state'] == 'shooting' and self.arsenal[self.gun]['frame'] == 1:
            # set hit to false for now
            hit = False
            # sort the monsters from closest to farthest away that way if the bullet can hit them both it only hits the closest because of the break and filter them so that only the ones that are visual can be shot
            monsters = [monster for monster in sorted(monsters, key = lambda monster: monster.distance) if monster.visual]
            # loop through each monser in the new sorted and purely visual list
            for monster in monsters: 
                # if the monster is colliding with the midpoint of the screen (like and invisible cross-hair)
                if monster.state != 'die' and monster.rect.collidepoint((res[0]/2, res[1]/2)): # collide with middle of the screen 
                    # decrement the monsters health by the damage of the current gun, set hit to True and break out of the loop 
                    monster.health -= self.arsenal[self.gun]['damage']
                    hit = True
                    break
            ### add bullet holes
            # if no monsters were hit after looping through all of the visual ones 
            if not hit:
                # create a bullet hole 
                # find the vector and slope of the the angle that the player is facing
                vectx, vecty = math.sin(self.angle), math.cos(self.angle)
                m = vecty/(vectx + 0.001)
                # set the closest x and closest y to be 
                closest_x = (10000, 10000)
                closest_y = (10000, 10000)
                # Check X
                # get the first x line in the direction that the player is looking by subtracting x % tile_size from the current x (and adding the tile_size if the vector x is posotive)
                if vectx <= 0:
                    x = (self.x - (self.x % tile_size))
                elif vectx > 0: 
                    x = (self.x - (self.x % tile_size)) + tile_size
                # get the x step by multiplyng the sign (- or +) of the vectx by the tile_size
                # vectx will never be 0 so /vectx is not a problem
                x_step = vectx/abs(vectx) * tile_size
                # untill broken (brakes when the vector hits a line with a filled tile)
                while True: 
                    # get the y of the intersection of the point where the vector intersects with the current x by using a rearanged version of the point slope formula with the players coordinates as the point
                    y = m * (x - self.x) + self.y
                    # if the point of intersection is outside of the map (break out of the loop since)
                    # if the y is outside of the map (this can happen because we are not checking y intersecitons yet), break the loop
                    if not (0 <= x < map_size) or (not 0 <= y < map_size ):
                        break
                    # we use int(x/tile_size) instead of x//tile_size, becuase x is a float so x// will return a float and we need an int
                    # get the row and column that the x and y corrospond to
                    row = int(y/tile_size)
                    # the column is more complicated because the x is in between 2 columns and we need to check the one behind the x coordinate from the players point of view
                    # if the the vector is negative subtract 1 from the column but otherwise just keep it the same
                    col = int(x/tile_size) - 1 if vectx <= 0 else int(x/tile_size)
                    # if the map at theat roe and column is a filled tile, assign the closest x intersection to the point and break the loop
                    if map[row][col] > 0:
                        closest_x = (x, y)
                        break
                    # increment x by the x_step
                    x += x_step
                # checking for y intersections is the basically the same process as checking for x intersections (only a few changes ex: the point slope formula is rearanged)
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
                    row = int(y/tile_size) - 1 if vecty <= 0 else int(y/tile_size)
                    
                    if map[row][col] > 0:
                        closest_y = (x, y)
                        break

                    y += y_step 

                # find
                # get the distance from the closest x and y intersections using the distance formula 
                distance_from_closest_x = ((closest_x[0] - self.x) ** 2 + (closest_x[1] - self.y) ** 2) ** 0.5
                distance_from_closest_y = ((closest_y[0] - self.x) ** 2 + (closest_y[1] - self.y) ** 2) ** 0.5
                # if the closest x is closer, use its coordinate as the x and y otherwise use the y coordinates
                if distance_from_closest_x < distance_from_closest_y:
                    # put the coordinate one point off of the wall so that nothing goes wrong in Sprite.check_visual
                    x = closest_x[0] - vectx/abs(vectx)
                    y = closest_x[1]
                else: 
                    # put the coordinate one point off of the wall so that nothing goes wrong in Sprite.check_visual
                    x = closest_y[0]
                    y = closest_y[1] - vecty/abs(vecty)
                # create a bullet_hole object using the defined sprite class and append the object with a timer int to the bullet_holes attribute
                bullet_hole = Sprite(x, y, self.bullet_hole_image, 1)
                self.bullet_holes.append([bullet_hole, 0]) # 0: lifetime counter

        ### show bullet holes
        # loop through each bullet hole and unpack the hole into the sprite and the lifetime_counter
        for hole in self.bullet_holes:
            sprite, lifetime_counter = hole
            # draw the sprite
            # run sprite.check_visual to make edit sprite.visual and make sure the sprite can be seen
            sprite.check_visual(self.x, self.y, self.angle, self.fov, tile_size, map, map_size)
            # draw the sprite to the screen using sprite.draw
            sprite.draw(res, self.fov, self.x, self.y, screen)
            # if the hole's life_time_counter becomes larger than 150, remove the hole from bullet_holes
            if lifetime_counter > 150:
                self.bullet_holes.remove(hole)
            # increment the sprites lifetime_counter by one 
            hole[1] += 1

class Sprite:
    def __init__(self, x, y, image, size_factor):
        self.x, self.y = x, y
        self.image = image
        self.size_factor = size_factor
        # the side_error value corosponds to how far away the sprite can be from the fov so that it can still be drawn (this way parts of the sprite can be drawn on the side of the screen )
        # it is directly preportional to the size_factor because the larger the size of the sprite the more distance should be allowed 
        self.side_error = size_factor/2 
        self.distance = 1
        # this boolean controlls whether the sprite is drawn to the screen, depending on if there are walls in the way and if the sprite is within the players field of view
        # it is recalculated on every call of check_visual() - this is the whole entire purpouse of set visual
        self.visual = False 

    def check_visual(self, playerx, playery, player_angle, fov, tile_size, map, map_size):
        # ray cast to check if the sprite is visual 
        self.line_angle = math.atan2((self.x - playerx), (self.y - playery)) % (2 * math.pi)
        min_angle = player_angle - fov/2
        # max angle needs to be accessed by the draw function without calling check_visual so it must be an attribute
        self.max_angle = player_angle + fov/2
        # if the line angle is in between (2pi - fov/2) and (2pi) and the player angle is in between 0 and fov/2 then the line angle 
        # will not be recorded as inbetween the angles because the min_angle in negative and the max_angle is low, but the line_angle is high, so to adjust we must add 2pi to both the min and max angles
        if (self.line_angle > math.pi * 2 - fov/2) and (player_angle < fov/2):
            min_angle += math.pi * 2
            self.max_angle += math.pi * 2
        # if the line angle is in between 0 and 2pi and the player_angle is in between 2pi - fov and 2pi the line angle will not be recorded as in between 
        # the min and max angles because the max_angle > 2pi and the min_angle is very high but the line_angle is very low, so to adjust we must subtract 2pi from both the min and max angles
        elif (self.line_angle < fov/2) and (player_angle > math.pi * 2 - fov/2): ## elif??
            # subtract 2pi from the min and max angles
            min_angle -= math.pi * 2
            self.max_angle -= math.pi * 2
        # after these adjustmants we can check if the sprite is in the field of view by checking if the line_angle is in between the min and max_angles with the side errors 
        in_fov = (min_angle - self.side_error) <= self.line_angle <= (self.max_angle + self.side_error)
        # if the sprite is in fov, we must check if it is behind a wall by casting a ray towards it and checking if the ray hits a wall
        if in_fov:
            # get the vector x, y and the slope of the line going from the player to the sprite
            vectx = self.x - playerx
            vecty = self.y - playery
            m = vecty/(vectx+ 0.001) # add a small value in case vectx is 0

            # CHECK X
            # get the first x line in the direction that the player is looking by subtracting x % tile_size from the current x (and adding the tile_size if the vector x is posotive)
            x = (playerx - (playerx % tile_size)) if vectx <= 0 else (playerx - (playerx % tile_size)) + tile_size
            # get the x step by multiplyng the sign (- or +) of the vectx by the tile_size
            # if the vectx is 0, the monster is on the same x as the player so set x_step to none
            x_step = vectx/abs(vectx) * tile_size if abs(vectx) != 0 else None
            # untill broken (brakes when the vector hits a line with a filled tile)
            while True: 
                # get the y of the intersection of the point where the vector intersects with the current x by using a rearanged version of the point slope formula with the players coordinates as the point
                y = m * (x - playerx) + playery
                # outside fo map 
                # if the monster is on the same x as the player, break the loop because no x walls need to be checked for intersections
                if x_step == None:
                    break
                # if the y is outside of the map, break the loop because all ys after will also be outside
                elif (not 0 <= y < map_size):
                    break
                # if the y is not in between the player and the sprite no walls need to be checked becuase they are behind the sprite from the players pov
                elif not (min(playerx, self.x) <= x <= max(playerx, self.x)):
                    break
                # we use int(x/tile_size) instead of x//tile_size, becuase x is a float so x// will return a float and we need an int
                # get the row and column that the x and y corrospond to
                row = int(y/tile_size)
                # the column is more complicated because the x is in between 2 columns and we need to check the one behind the x coordinate from the players point of view
                # if the the vector is negative subtract 1 from the column but otherwise just keep it the same
                col = int(x/tile_size) - 1 if vectx <= 0 else int(x/tile_size)
                # if the map at the row and column is a filled tile, set self.visual to false because since the wall is filled the sprite cannot be seen 
                if map[row][col] > 0:
                    self.visual = False
                    return None
                # increment x by the x_step
                x += x_step
            
            # CHECK Y
            # checking for y intersections is the basically the same process as checking for x intersections (only a few changes ex: the point slope formula is rearanged)
            if vecty <= 0:
                y = (playery - (playery % tile_size))
            elif vecty > 0: 
                y = (playery - (playery % tile_size)) + tile_size
            y_step = vecty/abs(vecty) * tile_size if abs(vecty) != 0 else None
            while True: 
                x = (y - playery)/m + playerx
                if y_step == None:
                    break
                elif not (0 <= x < map_size):
                    break
                elif not (min(playery, self.y) <= y <= max(playery, self.y)):
                    break

                col = int(x/tile_size)
                row = int(y/tile_size) - 1 if vecty <= 0 else int(y/tile_size)

                # if hit filled square
                if map[row][col] > 0:
                    self.visual = False
                    return None # terminate

                y += y_step 
            # if the sprite has passed all of the tests, it is within the fov, and when a ray is casted the ray does not intersect with any x or y filled walls,
            # then we can draw it so set self.visual to True and terminate the function
            self.visual = True
            return None 
        # otherwise if the sprite is outside of the fov, set self.visual to false and terminate the function
        else: 
            self.visual = False
            return None # terminate
            
    def draw(self, res, fov, playerx, playery, screen):
        # self.distance should be updated regardless of visual 
        # calculate the sprites distance from the player
        self.distance = ((self.x - playerx) ** 2 + (self.y - playery) ** 2) ** 0.5 # attribute because it needs to be accessed outside of the class
        # drawing should only take place if the monster is visual, (this attribute is updated in sprite.check_visual)
        if self.visual:
            # the x on the screen that the sprite should be drawn on is calculated by multiplying the difference in radians from the angle 
            # to the max_angle by the pixels per radian so that the radians cancel out and we are just left with pixels
            # the differece from the angle to the max_angle is calculated like this becuase since radians go counter clockwise but our fov goes clockwise we need to get the
            # difference from the max_angle but since that would be negative we multiply it by negative 1 to make it posotive 
            x = -(self.line_angle - self.max_angle) * (res[0]/fov)
            # the image is the sprites image scaled by an inverse of the distance * the scale factor 
            image = pygame.transform.scale_by(self.image, 200/self.distance * self.size_factor)
            # the rectangle is at the x calculated above and the center y of the screen
            self.rect = image.get_rect(center = (x, res[1]/2)) # needs to be accesed outside of the class by player.shoot() so we make it an attribute
            # put the image on the screen !!
            screen.blit(image, self.rect)

class Monster(Sprite):
    def __init__(self, x, y, size_factor, images, speed, animation_speed, health, damage, sounds, die_sound, audio_speed):
        # inherit from the sprite class which will control all drawing to the 3d projection
        super().__init__(x, y, images['move'][0], size_factor)
        # still: the monster has not been seen yet and is just a point on the hypothetical map plain
        # move: the monster is moving towards the player but is not close enough to attack
        # attack: the monster is close enough to the player to give the player damage and it cannot move
        # the monster is in a die state and it will be removed from the monsters list after it animated death
        self.state = 'still'
        # get the speed, and images dictionary from the arguments
        self.speed = speed
        self.images = images
        # the frame controlls what frame of animation the monster is on and the animation speed controlls how many frames it takes to switch images
        self.frame = 0
        self.animation_speed = animation_speed # smaller number is faster 
        self.health = health
        self.damage = damage
        # the sound_num is equivilent to self.frames except it handles sound rather than images
        self.sound_num = 0
        self.sounds = sounds
        self.die_sound = die_sound
        self.audio_speed = audio_speed

    def move(self, playerx, playery, map, tile_size, monsters):
        # if the monster is moving: (attacking, death, and still are all stationary states)
        if self.state == 'move':
            vectx, vecty = playerx - self.x, playery - self.y
            magnitude = (vectx ** 2 + vecty ** 2) ** 0.5
            # normalize 
            vectx /= magnitude
            vecty /= magnitude 
            # find move x and move y which are where the monster will move if nothing is in its way ( just the current position plus the vector times the speed)
            move_x, move_y = self.x + vectx * self.speed , self.y + vecty * self.speed 
            ### check if the monster will move is into a wall
            move_row, move_col = int(move_y/tile_size), int(move_x/tile_size)
            # find the row and column that the monster is currently in by deviding the current position by the tile_size
            row, col = int(self.y/tile_size), int(self.x/tile_size)
            # if where the monster will move is filled
            if map[move_row][move_col] > 0:
                # if where the monster will move is filled because of the row where they will move 
                if map[move_row][col] > 0: 
                    # make the monster only not move on the y axis
                    # the vecty becomes 0 but the vectx needs to increase to become 1 or -1 to make up for the lost vecty
                    vectx = vectx/(abs(vectx) + 0.001) # magnitude (but magnitude is 1 because of normilization
                    vecty = 0
                # if where the monster will move is filled becuase of the col where they will move (both can trigger so no elif)
                if map[row][move_col] > 0: 
                    # make the monster not move on the x axis
                    # the vecty should be reset to 1 or -1 to make up for the lost vectx but if vecty is already 0 from the prior if statment keep it as 0
                    vecty = vecty/(abs(vecty) + 0.001) if vecty != 0 else 0
                    vectx = 0

            ### check if the where the monster will move is too close to another monster
            # loop through each monster
            for monster in monsters:
                # if the monster is not the self object and the monster is either moving or attacking (not still or dying)
                if monster != self and monster.state in ('move', 'attack'):
                    distance = ((move_x - monster.x) ** 2 + (move_y - monster.y) ** 2) ** 0.5
                    # if the distnace is less than 10 and our monster object is farther from the player (only the monster farther from the player should stop move breifly)
                    if distance < 10 and monster.distance < self.distance:
                        vectx, vecty = 0, 0
            

            xchange = vectx * self.speed
            ychange = vecty * self.speed 
            self.x += xchange
            self.y += ychange       

    def animate(self, monsters, player):
        # Change state can happen without visual but in actual animation visual is necasary 
        ### Change state
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
        # if the monster is dieing but the player looked away, kill the monster
        elif self.state == 'die' and not self.visual:
            monsters.remove(self)
        # if the monster is dieing and the image (self.frame/self.animation_speed) it is on is the last image, remove it from monsters
        elif self.state == 'die' and self.frame/self.animation_speed == len(self.images['die']) - 1: 
            monsters.remove(self)
        # if the monster is attacking decrement the players health by the monsters damage
        if self.state == 'attack':
            player.health -= self.damage
        # actuall animation should only take place if the monster is visual, (this attribute is updated in sprite.check_visual)
        if self.visual: 
            # since the monster can be seen (from the if statement above), if the state is still, set the state to move because as soon as the monster is seen by the player it should immedielty start moving towards the player
            if self.state == 'still':
                self.state = 'move'
            # Handle animation
            # if the frame is divisble by the animation speed (this will trigger every {animation_speed} frames)
            if self.frame % self.animation_speed == 0:
                # if the frame / animation speed is is larger than the number of indexes in self.images[self.state], set the frame back to 0
                if self.frame/self.animation_speed > len(self.images[self.state]) - 1:
                    self.frame = 0
                # the image should be the images of the state of the frame // the animation speed (// just gets rid of the .0 because the frame will always be divisble by the animation speed becuas of the if statment above)
                self.image = self.images[self.state][self.frame//self.animation_speed]
            # increment the frame
            self.frame += 1

    def play_audio(self):
        if self.state in ('move', 'attack'):
            # if the sound_num is devisible by the audio speed (this will trigger every {audio_speed} frames)
            if self.sound_num % self.audio_speed == 0:
                # play the sounds of the sound_num // the audio speed (// just gets rid of the .0)
                self.sounds[self.sound_num//self.audio_speed].play()
                # if the sound_num over the audio_speed corrosponds to the last sound in the self.sounds list, reset the sound_num to 1
                if self.sound_num/self.audio_speed == len(self.sounds) - 1:
                    self.sound_num = 0
            self.sound_num += 1
            
        # otherwise, if the monsters state is die and the monster is on the first death frame, play the monsters death sound
        elif self.state == 'die' and self.frame == 1:
            self.die_sound.play()    

# if the code is being run on the current file, create a game object and run it
if __name__ == '__main__':
    game = Game()
    game.run()
