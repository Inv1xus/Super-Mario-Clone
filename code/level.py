import pygame
from support import import_csv_layout, import_cut_graphics
from settings import tile_size, screen_height
from tiles import *
from enemy import Enemy
from decoration import *
from player import  Player
from particles import PartricleEffect
from game_data import levels

class Level:
    def __init__(self,current_level, surface, create_overworld,change_coins,change_health):
        #general setup
        self.display_surface = surface
        self.world_shift = 0

        #audio
        self.coin_sound = pygame.mixer.Sound('../audio/effects/coin.wav')
        self.stomp_sound = pygame.mixer.Sound('../audio/effects/stomp.wav')

        #overworld connection
        self.create_overworld = create_overworld
        self.current_level = current_level
        level_data = levels[self.current_level]
        self.new_max_level = level_data['unlock']

        #UI
        self.change_coins = change_coins
        #player setup
        self.current_x = None
        player_layout = import_csv_layout(level_data['player'])
        self.player = pygame.sprite.GroupSingle()
        self.goal = pygame.sprite.GroupSingle()
        self.player_setup(player_layout,change_health)

        #dust
        self.dust_sprite = pygame.sprite.GroupSingle()
        self.player_on_ground = False
        #explosion
        self.explosion_sprites = pygame.sprite.Group()
        #terrain setup
        terrain_layout = import_csv_layout(level_data['terrain'])
        self.terrain_sprites =  self.create_tile_group(terrain_layout,'terrain')

        #grass setup
        grass_layout = import_csv_layout(level_data['grass'])
        self.grass_sprites = self.create_tile_group(grass_layout, 'grass')

        #crates
        crate_layout = import_csv_layout(level_data['crates'])
        self.crate_sprites = self.create_tile_group(crate_layout, 'crates')

        #coins
        coin_layout = import_csv_layout(level_data['coins'])
        self.coin_sprites = self.create_tile_group(coin_layout, 'coins')

        #FG palm trees
        fg_palm_layout = import_csv_layout(level_data['fg palms'])
        self.fg_palm_sprites = self.create_tile_group(fg_palm_layout, 'fg palms')
        # bG palm trees
        bg_palm_layout = import_csv_layout(level_data['bg palms'])
        self.bg_palm_sprites = self.create_tile_group(bg_palm_layout, 'bg palms')

        #enemy
        enemy_layout = import_csv_layout(level_data['enemies'])
        self.enemy_sprites = self.create_tile_group(enemy_layout, 'enemies')

        # constraint
        constraint_layout = import_csv_layout(level_data['constraints'])
        self.constraint_sprites = self.create_tile_group(constraint_layout, 'constraints')

        #decoration
        self.sky =Sky(8)
        level_width = len(terrain_layout[0])*tile_size
        self.water = Water(screen_height-40,level_width)
        self.clouds = Clouds(400,level_width,20)
    def check_coin_collision(self):
        collided_coins= pygame.sprite.spritecollide(self.player.sprite,self.coin_sprites,True)
        if collided_coins:
            for coin in collided_coins:
                self.change_coins(coin.value)
                self.coin_sound.play()
    def player_setup(self,layout,change_health):
        for row_index,row in enumerate(layout):
            for col_index, val in enumerate(row):
                x = col_index * tile_size
                y = row_index * tile_size
                if val == '0':
                    sprite = Player((x,y),self.display_surface,self.create_jump_particles,change_health)
                    self.player.add(sprite)
                if val == '1':
                    hat_surface = pygame.image.load('../graphics/character/hat.png').convert_alpha()
                    sprite = StaticTile(tile_size,x,y,hat_surface)
                    self.goal.add(sprite)
    def create_jump_particles(self,pos):
        if self.player.sprite.facing_right:
            pos -= pygame.math.Vector2(10,5)
        else:
            pos += pygame.math.Vector2(10, -5)
        jump_particle_sprite = PartricleEffect(pos,'jump')
        self.dust_sprite.add(jump_particle_sprite)
    def create_tile_group(self, layout,type):
        sprite_group = pygame.sprite.Group()

        for row_index,row in enumerate(layout):
            for col_index, val in enumerate(row):
                if val != '-1':
                    x = col_index * tile_size
                    y = row_index * tile_size

                    if type == 'terrain':
                        terrain_tile_list = import_cut_graphics('../graphics/terrain/terrain_tiles.png')
                        tile_surface = terrain_tile_list[int(val)]
                        sprite= StaticTile(tile_size,x,y,tile_surface)

                    if type == 'grass':
                        grass_tile_list = import_cut_graphics('../graphics/decoration/grass/grass.png')
                        tile_surface = grass_tile_list[int(val)]
                        sprite = StaticTile(tile_size, x, y, tile_surface)
                    if type == 'crates':
                        sprite = Crate(tile_size,x,y)

                    if type == 'coins':
                        if val == '0': sprite = Coin(tile_size,x,y,'../graphics/coins/gold',5)
                        if val == '1': sprite = Coin(tile_size, x, y, '../graphics/coins/silver',1)

                    if type == 'fg palms':
                        if val == '2': sprite = Palm(tile_size, x, y, '../graphics/terrain/palm_small', 38)
                        if val == '1': sprite = Palm(tile_size, x, y, '../graphics/terrain/palm_large', 64)

                    if type == 'bg palms':
                        sprite= Palm(tile_size, x, y, '../graphics/terrain/palm_bg', 64)
                    if type == 'enemies':
                        sprite = Enemy(tile_size, x, y)

                    if type == 'constraints':
                        sprite = Tile(tile_size, x, y)

                    sprite_group.add(sprite)
        return sprite_group
    def enemy_collision_reverse(self):
        for enemy in self.enemy_sprites.sprites():
            if pygame.sprite.spritecollide(enemy,self.constraint_sprites,False):
                enemy.reverse()

    def horizontal_movement_collision(self):
        player = self.player.sprite
        player.collision_rect.x += player.direction.x *player.speed
        collideable_sprites = self.terrain_sprites.sprites()+self.crate_sprites.sprites() + self.fg_palm_sprites.sprites()
        for sprite in collideable_sprites:
            if sprite.rect.colliderect(player.collision_rect):
                if player.direction.x <0:
                    player.on_left = True
                    self.current_x = player.rect.left
                    player.collision_rect.left = sprite.rect.right
                elif player.direction.x >0:
                    player.collision_rect.right = sprite.rect.left
                    player.on_right = True

    def vertical_movement_collision(self):
        player = self.player.sprite
        player.apply_gravity()
        collideable_sprites = self.terrain_sprites.sprites()+self.crate_sprites.sprites() + self.fg_palm_sprites.sprites()
        for sprite in collideable_sprites:
            if sprite.rect.colliderect(player.collision_rect):
                if player.direction.y >0:
                    player.collision_rect.bottom = sprite.rect.top
                    player.direction.y = 0
                    player.on_ground = True
                elif player.direction.y <0:
                    player.collision_rect.top = sprite.rect.bottom
                    player.direction.y = 0
                    player.on_ceiling = True
            if player.on_ground and player.direction.y<0 or player.direction.y >1:
                player.on_ground=False

    def get_player_on_ground(self):
        if self.player.sprite.on_ground:
            self.player_on_ground= True
        else:
            self.player_on_ground = False
    def create_landing_dust(self):
        if not self.player_on_ground and self.player.sprite.on_ground and not self.dust_sprite.sprites():
            if self.player.sprite.facing_right:
                offset = pygame.math.Vector2(10, 15)
            else:
                offset = pygame.math.Vector2(-10, 15)
            fall_dust_particle = PartricleEffect(self.player.sprite.rect.midbottom-offset,'land')
            self.dust_sprite.add(fall_dust_particle)
    def scroll_x(self):
        player = self.player.sprite
        player_x = player.rect.centerx
        direction_x = player.direction.x

        if player_x< (screen_width/4) and direction_x <0:
            self.world_shift = 8
            player.speed = 0
        elif player_x > screen_width-(screen_width/4) and direction_x > 0:
            self.world_shift = -8
            player.speed=0
        else:
            self.world_shift = 0
            player.speed = 8

    def check_enemy_collisions(self):
        enemy_collisions = pygame.sprite.spritecollide(self.player.sprite,self.enemy_sprites,False)
        if enemy_collisions:
            for enemy in enemy_collisions:
                enemy_center = enemy.rect.centery
                enemy_top = enemy.rect.top
                player_bottom = self.player.sprite.rect.bottom
                if enemy_top<player_bottom<enemy_center and self.player.sprite.direction.y>=0:
                    self.stomp_sound.play()
                    self.player.sprite.direction.y =-15
                    explosion_sprite = PartricleEffect(enemy.rect.center,'explosion')
                    self.explosion_sprites.add(explosion_sprite)
                    enemy.kill()
                else:
                    self.player.sprite.get_damage()

    def check_death(self):
        if self.player.sprite.rect.top > screen_height:
            self.create_overworld(self.current_level,0)
    def check_win(self):
        if pygame.sprite.spritecollide(self.player.sprite,self.goal,False):
            self.create_overworld(self.current_level, self.new_max_level)
    def run(self ):
        #run entire level

        # sky
        self.sky.draw(self.display_surface)
        self.clouds.draw(self.display_surface,self.world_shift)

        # bg Palms
        self.bg_palm_sprites.update(self.world_shift)
        self.bg_palm_sprites.draw(self.display_surface)

        # dust particles
        self.dust_sprite.update(self.world_shift)
        self.dust_sprite.draw(self.display_surface)

        #terrain
        self.terrain_sprites.draw(self.display_surface)
        self.terrain_sprites.update(self.world_shift)

        # enemy
        self.enemy_sprites.update(self.world_shift)
        self.constraint_sprites.update(self.world_shift)
        self.enemy_sprites.draw(self.display_surface)
        self.enemy_collision_reverse()
        self.explosion_sprites.update(self.world_shift)
        self.explosion_sprites.draw(self.display_surface)
        # crates
        self.crate_sprites.update(self.world_shift)
        self.crate_sprites.draw(self.display_surface)

        # grass
        self.grass_sprites.update(self.world_shift)
        self.grass_sprites.draw(self.display_surface)

        #coins
        self.coin_sprites.update(self.world_shift)
        self.coin_sprites.draw(self.display_surface)

        # fg Palms
        self.fg_palm_sprites.update(self.world_shift)
        self.fg_palm_sprites.draw(self.display_surface)

        #player sprites
        self.scroll_x()
        self.goal.update(self.world_shift)
        self.goal.draw(self.display_surface)
        self.player.update()
        self.horizontal_movement_collision()
        self.get_player_on_ground()
        self.vertical_movement_collision()
        self.create_landing_dust()
        self.player.draw(self.display_surface)

        #water
        self.water.draw(self.display_surface, self.world_shift)

        self.check_death()
        self.check_win()
        self.check_coin_collision()
        self.check_enemy_collisions()