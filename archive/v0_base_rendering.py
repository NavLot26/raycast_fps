import pygame
from sys import exit
import math
class Test:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1200, 600))
        self.clock = pygame.time.Clock()
        _ = 0
        self.map = [
            [1, 1, 1, 1, 1, 1, 1, 1],
            [1, _, 1, _, _, _, _, 1],
            [1, _, 1, _, 1, 1, _, 1],
            [1, _, 1, _, _, 1, 1, 1],
            [1, _, _, _, _, _, _, 1],
            [1, _, _, _, _, 1, 1, 1],
            [1, 1, _, 1, _, _, _, 1],
            [1, 1, 1, 1, 1, 1, 1, 1]]
        self.playerx = 330
        self.playery = 330
        # convert the map into lines on a plane
        # these should be dependent on the map size, and plane size but for the sake of the test it would be too much work 
        self.xs = [0, 75, 150, 225, 300, 375, 450, 525]
        self.ys = [0, 75, 150, 225, 300, 375, 450, 525]
        self.angle = math.pi
        self.fov = math.pi/3
        self.right, self.left, self.forward = False, False, False
        self.rays = []
        self.wall_texture = pygame.image.load('graphics/game/wall_texture1.png')
        self.sprite_image = pygame.image.load('graphics/game/ammo_pack.png')
        self.spritex = 300
        self.spritey = 375
        self.sky_texture = pygame.image.load('graphics/game/sky_texture.png')
        self.ground = pygame.Surface((600, 300))
        self.ground.fill((25, 150, 25))
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    self.right = True
                if event.key == pygame.K_LEFT:
                    self.left = True
                if event.key == pygame.K_UP:
                    self.forward = True
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_RIGHT:
                    self.right = False
                if event.key == pygame.K_LEFT:
                    self.left = False
                if event.key == pygame.K_UP:
                    self.forward = False

    def draw_map(self):
        # draw filled tiles
        for row_i in range(len(self.map)):
            for col_i in range(len((self.map[row_i]))):
                if self.map[row_i][col_i] == 1:
                    pygame.draw.rect(self.screen, (200, 200, 200), (self.xs[col_i], self.ys[row_i], 75, 75))
        # draw the lines
        for x in self.xs:
            pygame.draw.line(self.screen, (100, 100, 100), (x, 0), (x, 600), 2)
        for y in self.ys: 
            pygame.draw.line(self.screen, (100, 100, 100), (0, y), (600, y), 2)
        
        # draw the player circle
        pygame.draw.circle(self.screen, 'Red', (self.playerx, self.playery), 10)
        
        pygame.draw.circle(self.screen, 'Orange', (self.spritex, self.spritey), 8)

        # direction
        if self.right: self.angle -= 0.08
        if self.left: self.angle += 0.08
        self.angle = self.angle % (math.pi * 2)
        if self.forward: 
            self.playerx += math.sin(self.angle) * 3
            self.playery += math.cos(self.angle) * 3
    
    def cast_rays(self):
        rays = []
        angle = self.angle + self.fov/2
        for ray in range(200):
            angle -= self.fov/200
            angle %= (math.pi * 2)

            vectx, vecty = math.sin(angle), math.cos(angle)
            m = vecty/vectx
            closest_x = (10000, 10000)
            closest_y = (10000, 10000)
            # Check X
            if vectx <= 0:
                x = (self.playerx - (self.playerx % 75))
            elif vectx > 0: 
                x = (self.playerx - (self.playerx % 75)) + 75
            x_step = vectx/abs(vectx) * 75
            while True: 
                y = m * (x - self.playerx) + self.playery
                if not (0 <= x < 600) or (not 0 <= y < 600 ):
                    break
                
                row = int(y/75)
                if vectx <= 0: 
                    col = int(x/75) - 1 if int(x/75) - 1 >= 0 else 0
                elif vectx >= 0: 
                    col = int(x/75)
                
                if self.map[row][col] == 1:
                    closest_x = (x, y)
                    break
                
                x += x_step
            
            # Check Y
            if vecty <= 0:
                y = (self.playery - (self.playery % 75))
            elif vecty > 0: 
                y = (self.playery - (self.playery % 75)) + 75
            y_step = vecty/abs(vecty) * 75
            while True: 
                x = (y - self.playery)/m + self.playerx
                if not (0 <= x < 600) or (not 0 <= y < 600 ):
                    break
                
                col = int(x/75)
                if vecty <= 0: 
                    row = int(y/75) - 1 if int(y/75) - 1 >= 0 else 0
                elif vecty >= 0: 
                    row = int(y/75)
                
                if self.map[row][col] == 1:
                    closest_y = (x, y)
                    break

                y += y_step 
        
            distance_from_closest_x = ((closest_x[0] - self.playerx) ** 2 + (closest_x[1] - self.playery) ** 2) ** 0.5
            distance_from_closest_y = ((closest_y[0] - self.playerx) ** 2 + (closest_y[1] - self.playery) ** 2) ** 0.5
            
            if distance_from_closest_x < distance_from_closest_y:
                rays.append((distance_from_closest_x, closest_x[1] % 75, angle))
                pygame.draw.line(self.screen, 'Purple', (self.playerx, self.playery), (closest_x))

            else: 
                rays.append((distance_from_closest_y, closest_y[0] % 75, angle))
                pygame.draw.line(self.screen, 'Purple', (self.playerx, self.playery), (closest_y))

        self.rays = rays

    def draw_projection(self):
        x = 600
        # loop through each ray
        width = 3 # 600 pixels/300 rays
        for ray in self.rays:
            # unpack the distance and the projection point, the projection point is what x or y point on the tile the ray hits
            distance, proj_point, angle = ray
            # since the rays farther away from the center of the screen will appear to be farther away because of the 
            # math even though in real life our eyes do not see that, walls look curved when seen up close. The fish eye 
            # fix is the cosign of the difference in the angle from the center angle. The farther the ray is from the 
            # center of the screen the smaller the cosign is so if the fix is multiplied by the distance it will cancel the effect out
            fish_eye_fix = math.cos(self.angle - angle)
            distance *= fish_eye_fix
            # find the height and width of the line that should be drawn for that ray
            height = 20000/distance
            # find the tex_x, this varaible finds what x point on the texture image should corrospond to the ray
            # every tile face will show the texture so you take the proj_point and multiply it by a factor that makes it from the tile size to the texture size
            tex_x = int(proj_point * 64/75)
            # now we will split this line that is drawn for the ray into many more lines
            # find the originating height at the top of the line that is drawn for this ray
            y = 300 - height/2
            # find the length that each line should be (since each line that will be drawn corrosponds to a pixel, it shoudl be the height of the major line devided by the number of pixels in the length of the texture)
            length = height/64
            # loop through each pixel in the texture length
            for tex_y in range(64):
                # draw a rectangle that has is at x, y and has the width of the major line and the length of each minor line
                # for the color get the color for that pixel on the texture using get_at()
                color = self.wall_texture.get_at((tex_x, tex_y))
                color = (color[0] - distance/5 if color[0] - distance/5 >= 0 else 0,
                         color[1] - distance/5 if color[1] - distance/5 >= 0 else 0,
                         color[2] - distance/5 if color[2] - distance/5 >= 0 else 0)
                pygame.draw.rect(self.screen, color, (x, y, width, length + 1)) # length + 1 because the length sometimes rounds down
                # increment the length for the next minor line
                y += length
            # increment the width for the next major line
            x += width
        
    def draw_sprite(self):   
        # find the angle between the player and sprite using arc tangent and then adjust it to the way that we mesure radians     
        line_angle = math.atan2((self.spritex - self.playerx), (self.spritey - self.playery)) 
        line_angle = (line_angle)%(2*math.pi) # convert the line_angle to the way we mesure radians by moduloing it by math.pi/2
        # calculate the min and max angle on each side of the fov
        min_angle = (self.angle - self.fov/2)
        max_angle = (self.angle + self.fov/2) 
        # Since the line_angle is based on a vector it automatically stays in between 0 and 2pi with our adjustmant. 
        # This means that the line_angle may be within the range of the self.angle but it does not get detected 
        # because of the following 2 cases: 1. The line_angle is slightly above 0 and self.angle is slightly 
        # below 2pi. 2. The line_angle is slightly below 2pi and the self.angle is slighly above 0. To combat 
        # this we check these scanarios and adjust min and max angle accordingly so that they go neer self.angle 

        # if the line_angle is within fov/2 less than 2pi and the angle is within fov/2 more than 0
        if (line_angle > math.pi * 2 - self.fov/2) and (self.angle < self.fov/2):
            # add 2pi to the min and max angle
            min_angle += math.pi * 2
            max_angle += math.pi * 2

        # if the line angle is within fov/2 more than 0 and self.angle is within fov/2 less than 2pi
        if (line_angle < self.fov/2) and (self.angle > math.pi * 2 - self.fov/2):
            # subtract 2pi from the min and max angles
            min_angle -= math.pi * 2
            max_angle -= math.pi * 2

        # find the distance from the player to the sprite (this will be used now for in_fov and later for drawing the sprite)
        distance = ((self.spritex - self.playerx) ** 2 + (self.spritey - self.playery) ** 2) **0.5
        # create a varaible called in_fov that checks if the angle is within the field of view (a value slightly larger than the field of view so that if the sprite is on one side of the screen it will be partially drawn )
        in_fov = min_angle - 0.5 <= line_angle <= max_angle + 0.5
        if in_fov:
            vectx = self.spritex - self.playerx
            vecty = self.spritey - self.playery
            m = vecty/(vectx + 0.001)

            # Check X
            if vectx <= 0:
                x = (self.playerx - (self.playerx % 75))
            elif vectx > 0: 
                x = (self.playerx - (self.playerx % 75)) + 75
            x_step = vectx/abs(vectx) * 75
            while True: 
                y = m * (x - self.playerx) + self.playery
                if not (0 <= x < 600) or (not 0 <= y < 600 ):
                    break
                if not (min(self.playerx, self.spritex) <= x <= max(self.playerx, self.spritex)):
                    break
                
                row = int(y/75)
                if vectx <= 0: 
                    col = int(x/75) - 1 if int(x/75) - 1 >= 0 else 0
                elif vectx >= 0: 
                    col = int(x/75)
                
                if self.map[row][col] == 1:
                    return None
                
                x += x_step
            
            # Check Y
            if vecty <= 0:
                y = (self.playery - (self.playery % 75))
            elif vecty > 0: 
                y = (self.playery - (self.playery % 75)) + 75
            y_step = vecty/abs(vecty) * 75
            while True: 
                x = (y - self.playery)/m + self.playerx
                if not (0 <= x < 600) or (not 0 <= y < 600 ):
                    break
                if not (min(self.playery, self.spritey) <= y <= max(self.playery, self.spritey)):
                    break

                col = int(x/75)
                if vecty <= 0: 
                    row = int(y/75) - 1 if int(y/75) - 1 >= 0 else 0
                elif vecty >= 0: 
                    row = int(y/75)
                
                if self.map[row][col] == 1:
                    return None

                y += y_step 

            # if the function has not already been terminated from a collision with a filled block, draw the sprite
            # find the x that the radian coorosponds to if it were put into the ray
            # find the distance from the maximum angle, make it negative and multiply that by the pixels per radian
            x = -(line_angle - max_angle) * (600/self.fov)
            # create the sprite image (the size should be an inverse of the distance from the player)
            sprite_image = pygame.transform.scale_by(self.sprite_image, 200/distance)
            # create the rectangle using the x that was calculated fro the radian 
            # mid top for eyelevel
            rect = sprite_image.get_rect(midtop = (x + 600, 300))
            # put the sprite on the 3d projection 
            self.screen.blit(sprite_image, rect)
         
    def draw_sky(self):
        # set the current angle (first angle) to start
        angle = self.angle + self.fov/2
        # set the x to 600 and the width of each rectangle to 4
        x = 600
        width = 4
        # set the length of each rectangle to 10
        length = 10
        # go through 150 rays
        for ray in range(150):
            # increment the angle by the radains in the filed of view divided by the number of rays
            angle -= self.fov/150
            # keep the radians between 0 and 2pi
            angle %= (math.pi * 2)
            # find what what x coordintate coorosponds to the angle
            # the radians multiplied by the pixels on the texture divided by how many radians the texture should cover (all --> 2pi)
            tex_x = int(angle * 200/(math.pi * 2))
            # set y to 0
            y = 0
            # loop through each rectangle we will draw for that ray
            for rect in range(30):
                # the texture y is equal to the current y value multiplied by the ratio of texture height to half of scren height
                tex_y = int(y * 1/3)
                # get the color at texture x and texture y
                color = self.sky_texture.get_at((tex_x, tex_y))
                # draw a {color} rectangle to the screen at {x} {y} with {width} and {height}
                pygame.draw.rect(self.screen, color, (x, y, width, length))
                # increment the y by the length of the rectangle
                y += length
            # increment the x by the lenght of the ray 
            x += width

        # draw the ground
        self.screen.blit(self.ground, (600, 300))

    def run(self):
        while True:
            self.screen.fill('Black')
            self.handle_events()
            self.cast_rays()

            self.draw_sky()
            self.draw_projection()
            self.draw_sprite()
            self.draw_map()

            # update
            pygame.display.update()
            self.clock.tick(60)
            pygame.display.set_caption(f'Test (FPS: {int(self.clock.get_fps())})')

if __name__ == '__main__':
    test = Test()
    test.run()