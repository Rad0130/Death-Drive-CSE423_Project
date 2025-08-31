from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import sys
from math import cos, sin, radians, atan2, degrees
import random

camera_pos=(0,-25,15)
# Game state variables
cannon_angle = 0
car_x, car_y, car_z = 0, 0, 5 # Car position
player_speed = 5.0 # Player car speed
lane_positions = [-15, 0, 15] # x-coordinates for left, middle, right lanes

# Camera-related variables
fovY = 60
GRID_LENGTH = 600
window_width, window_height = 1000, 800

# New game state variables from the provided code
player_health = 15
player_score = 0
is_game_over = False
is_cheat_mode = False
first_person_view = False
shield_active = True
shield_health = 5

# Player car state
car_lane = 1
track_position = 0.0

# Bullet lists
player_bullets = []
enemy_bullets = []

# Enemy cars
enemies = []

# Key state variables for continuous movement
moving_forward = False
moving_backward = False

# Road and tree segments for the endless road effect
road_segments = []
tree_segments = []

# Global for the scrolling effect
scroll_speed = 0.0

# Global car dimensions for bullet spawning and drawing
car_length = 4  # Adjusted
car_width = 2  # Adjusted
car_height = 1.25  # Adjusted
wheel_radius = 0.5
cannon_length = 2.
cannon_base_height = car_height * 0.6

class Bullet:
    def __init__(self, x, y, z, angle, speed, color, is_player_bullet=True):
        self.x = x
        self.y = y
        self.z = z
        self.angle = angle
        self.speed = speed
        self.color = color
        self.is_player_bullet = is_player_bullet
        self.lifetime = 200 if is_player_bullet else 300
        
    def move(self):
        self.x += self.speed * sin(radians(self.angle))
        self.y += self.speed * cos(radians(self.angle))
        self.lifetime -= 1
        
    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glColor3f(*self.color)
        quadric = gluNewQuadric()
        gluSphere(quadric, 1, 8, 8)
        glPopMatrix()

class EnemyCar:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        # Use player car's dimensions for enemy cars
        self.car_length = 8
        self.car_width = 4
        self.car_height = 2.5
        self.color = (random.random(),random.random(),random.random())
        self.speed = random.uniform(2.0, 4.0)
        self.direction = 0
        self.shoot_cooldown = 0
        self.enemy_cannon_angle = 0
        
    def move(self):
        global car_x, car_y
        self.y -= self.speed
        
        # Orient the cannon towards the player car
        dx = car_x - self.x
        dy = car_y - self.y
        self.enemy_cannon_angle = degrees(atan2(dx, dy)) + random.uniform(-5, 5) # Slight random aim
        
        if self.y < -GRID_LENGTH:
            self.y = GRID_LENGTH + 100
            self.x = random.choice(lane_positions)
            
        self.shoot_cooldown -= 1
        if self.shoot_cooldown <= 0 and random.random() < 0.01:
            self.shoot()
            self.shoot_cooldown = random.randint(30, 60)
    
    def shoot(self):
        # Calculate cannon tip's position
        bullet_start_x = self.x + (self.car_length * 0.3 + cannon_length) * sin(radians(self.enemy_cannon_angle))
        bullet_start_y = self.y + (self.car_length * 0.3 + cannon_length) * cos(radians(self.enemy_cannon_angle))
        bullet_start_z = self.z + cannon_base_height
        
        bullet = Bullet(bullet_start_x, bullet_start_y, bullet_start_z, self.enemy_cannon_angle, 1.5, (1.0, 0.0, 0.0), False)
        enemy_bullets.append(bullet)
        
    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.direction, 0, 0, 1)

        # Main body of the car
        glColor3f(*self.color)
        glPushMatrix()
        glScalef(self.car_width, self.car_length, self.car_height)
        glutSolidCube(1)
        glPopMatrix()
        
        # Roof of the car
        glColor3f(0.8, 0.0, 0.0)
        glPushMatrix()
        glTranslatef(0, 0, self.car_height/2)
        glScalef(self.car_width * 0.8, self.car_length * 0.7, self.car_height * 0.5)
        glutSolidCube(1)
        glPopMatrix()
        
        # Add a cannon to the enemy car
        glColor3f(0.3, 0.3, 0.3)
        glPushMatrix()
        glTranslatef(0, self.car_length * 0.3, cannon_base_height)
        glRotatef(-self.enemy_cannon_angle + 180, 0, 0, 1) # Rotate to face player
        glRotatef(90, 1, 0, 0)
        glutSolidCylinder(0.4, cannon_length, 10, 10)
        glPopMatrix()

        glPopMatrix()

# Keyboard handling function
def keyboard(key, x, y):
    global cannon_angle, car_lane, is_cheat_mode, is_game_over, moving_forward, moving_backward
    
    if is_game_over and key == b'r':
        reset_game()
        return
    
    if is_game_over:
        return
    
    key = key.decode('utf-8').lower()
    
    if key == 'z':
        cannon_angle += 5 # Rotate left
    elif key == 'c':
        cannon_angle -= 5 # Rotate right
    
    # Keep the angle within 0-360 degrees
    cannon_angle %= 360
    
    if key == 'a':
        car_lane = max(0, car_lane - 1)
    elif key == 'd':
        car_lane = min(2, car_lane + 1)
    elif key == 'w':
        moving_forward = True
    elif key == 's':
        moving_backward = True
    elif key == 'v':
        is_cheat_mode = not is_cheat_mode
    
    glutPostRedisplay()

def keyboardUpListener(key, x, y):
    global moving_forward, moving_backward
    
    key = key.decode('utf-8').lower()
    
    if key == 'w':
        moving_forward = False
    elif key == 's':
        moving_backward = False

def mouseListener(button, state, x, y):
    global first_person_view
    
    if is_game_over:
        return
    
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        # Calculate cannon tip's position
        bullet_start_x = car_x + (car_length * 0.3 + cannon_length) * sin(radians(cannon_angle))
        bullet_start_y = car_y + (car_length * 0.3 + cannon_length) * cos(radians(cannon_angle))
        bullet_start_z = car_z + cannon_base_height
        
        # Invert the angle to fix the direction
        fixed_angle = -cannon_angle
        
        bullet = Bullet(bullet_start_x, bullet_start_y, bullet_start_z, fixed_angle, 10.0, (1.0, 1.0, 0.0), True)
        player_bullets.append(bullet)
    elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        first_person_view = not first_person_view

def specialKeyListener(key, x, y):
    global camera_pos
    if is_game_over:
        return
    
    x, y, z = camera_pos
    
    if key == GLUT_KEY_LEFT:
        x -= 10  # Move camera left
    elif key == GLUT_KEY_RIGHT:
        x += 10  # Move camera right
    elif key == GLUT_KEY_UP:
        z -= 10  # Move camera up
    elif key == GLUT_KEY_DOWN:
        z += 10  # Move camera down
    
    camera_pos = (x, y, z)

def setupCamera():
    global car_x, car_y, car_z, first_person_view, camera_pos
    
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect_ratio = window_width / float(window_height)
    gluPerspective(fovY, aspect_ratio, 0.1, 1500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    if first_person_view:
        # First-person view remains the same
        gluLookAt(car_x, car_y + 10, car_z + 5,
                  car_x, car_y + 50, car_z + 5,
                  0, 0, 1)
    else:
        # Calculate camera's eye position relative to the car
        cam_x = car_x + camera_pos[0]
        cam_y = car_y + camera_pos[1]
        cam_z = car_z + camera_pos[2]
        
        # The camera now looks at the car from a fixed relative position
        gluLookAt(cam_x, cam_y, cam_z,
                  car_x, car_y, car_z,
                  0, 0, 1)

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, window_width, 0, window_height)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_hud():
    health_text = f"Health: {player_health}"
    draw_text(10, window_height - 30, health_text)
    
    score_text = f"Score: {player_score}"
    draw_text(10, window_height - 60, score_text)
    
    if shield_active:
        shield_text = f"Shield: {shield_health}"
        draw_text(10, window_height - 90, shield_text)
    else:
        draw_text(10, window_height - 90, "Shield: Depleted")
    
    if is_cheat_mode:
        draw_text(10, window_height - 120, "CHEAT MODE: INVINCIBLE")
    
    if is_game_over:
        game_over_text = "GAME OVER! Press R to Restart."
        text_width = len(game_over_text) * 10
        draw_text(window_width/2 - text_width/2, window_height/2, game_over_text)

def check_collisions():
    global player_health, shield_health, shield_active, player_score, enemies, is_game_over
    
    bullets_to_remove = []
    enemies_to_remove = []
    
    for bullet in player_bullets:
        for enemy in enemies:
            dist = ((enemy.x - bullet.x) ** 2 + (enemy.y - bullet.y) ** 2) ** 0.5
            
            # Calculate a more accurate collision radius
            enemy_radius = max(enemy.car_width, enemy.car_length) / 2
            bullet_radius = 1.0 # The bullet size from your Bullet class
            
            if dist < enemy_radius + bullet_radius: 
                bullets_to_remove.append(bullet)
                enemies_to_remove.append(enemy)
                player_score += 1
                break
    
    for bullet in bullets_to_remove:
        if bullet in player_bullets:
            player_bullets.remove(bullet)
    
    for enemy in enemies_to_remove:
        if enemy in enemies:
            enemies.remove(enemy)
    
    for bullet in enemy_bullets[:]:
        dist = ((car_x - bullet.x) ** 2 + (car_y - bullet.y) ** 2) ** 0.5
        if dist < 30: # This check is for player-bullet collision and seems fine
            if shield_active and shield_health > 0:
                shield_health -= 1
                if shield_health <= 0:
                    shield_active = False
            else:
                if not is_cheat_mode:
                    player_health -= 1
                    if player_health <= 0:
                        is_game_over = True
            if bullet in enemy_bullets:
                enemy_bullets.remove(bullet)
    
    for enemy in enemies:
        dist = ((enemy.x - car_x) ** 2 + (enemy.y - car_y) ** 2) ** 0.5
        if dist < 5: # This check for enemy-player car collision seems okay for now
            if shield_active and shield_health > 0:
                shield_health -= 1
                if shield_health <= 0:
                    shield_active = False
            else:
                if not is_cheat_mode:
                    player_health -= 5
                    if player_health <= 0:
                        is_game_over = True
            enemy.x += 100 if enemy.x > car_x else -100
            enemy.y += 100 if enemy.y > car_y else -100
    
    if len(enemies) < 3:
        for _ in range(3 - len(enemies)):
            x = random.choice(lane_positions)
            y = random.uniform(GRID_LENGTH + 100, GRID_LENGTH + 200)
            z = car_z
            enemies.append(EnemyCar(x, y, z))

def idle():
    global track_position, car_x, car_y, scroll_speed
    
    if is_game_over:
        glutPostRedisplay()
        return
    
    if moving_forward:
        scroll_speed = -player_speed
    elif moving_backward:
        scroll_speed = player_speed
    else:
        scroll_speed = 0.0

    for seg in road_segments:
        seg['y'] += scroll_speed
        if seg['y'] < -GRID_LENGTH:
            seg['y'] += 2 * GRID_LENGTH
    
    for seg in tree_segments:
        seg['y'] += scroll_speed
        if seg['y'] < -GRID_LENGTH:
            seg['y'] += 2 * GRID_LENGTH

    for enemy in enemies:
        enemy.y += scroll_speed
    
    for bullet in player_bullets:
        bullet.y += scroll_speed
    
    for bullet in enemy_bullets:
        bullet.y += scroll_speed
    
    car_x = lane_positions[car_lane]
    
    for enemy in enemies:
        enemy.move()
    
    for bullet in player_bullets[:]:
        bullet.move()
        if bullet.lifetime <= 0:
            player_bullets.remove(bullet)
    
    for bullet in enemy_bullets[:]:
        bullet.move()
        if bullet.lifetime <= 0:
            enemy_bullets.remove(bullet)
    
    check_collisions()
    
    glutPostRedisplay()

def reset_game():
    global player_health, player_score, is_game_over, is_cheat_mode
    global shield_active, shield_health, car_lane, cannon_angle
    global track_position, player_bullets, enemy_bullets, enemies, car_x, car_y
    global moving_forward, moving_backward, road_segments, tree_segments
    
    player_health = 15
    player_score = 0
    is_game_over = False
    is_cheat_mode = False
    shield_active = True
    shield_health = 5
    car_lane = 1
    cannon_angle = 0
    track_position = 0
    car_x, car_y = 0, 0
    player_bullets = []
    enemy_bullets = []
    enemies = []
    moving_forward = False
    moving_backward = False
    
    for _ in range(3):
        x = random.choice(lane_positions)
        y = random.uniform(GRID_LENGTH + 100, GRID_LENGTH + 200)
        z = car_z
        enemies.append(EnemyCar(x, y, z))
    
    road_segments = [{'y': i * GRID_LENGTH} for i in range(-1, 2)]
    
    road_width = 40
    tree_positions_left = [(-road_width / 2) - 30, (-road_width / 2) - 30, (-road_width / 2) - 30]
    tree_positions_right = [(road_width / 2) + 30, (road_width / 2) + 30, (road_width / 2) + 30]
    tree_segments = []
    for y_offset in range(-1, 2):
        for pos_x in tree_positions_left + tree_positions_right:
            tree_segments.append({'x': pos_x, 'y': y_offset * GRID_LENGTH + random.uniform(-GRID_LENGTH/2, GRID_LENGTH/2), 'z': 0})

def draw_sky():
    glColor3f(0.5, 0.7, 1.0)
    glBegin(GL_QUADS)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, -100)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, -100)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, -100)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, -100)
    glEnd()

def draw_green_ground(y_offset):
    glColor3f(0.0, 0.5, 0.0)
    road_width = 40
    glBegin(GL_QUADS)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH + y_offset, 0)
    glVertex3f(-road_width / 2, -GRID_LENGTH + y_offset, 0)
    glVertex3f(-road_width / 2, GRID_LENGTH + y_offset, 0)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH + y_offset, 0)
    glEnd()
    glBegin(GL_QUADS)
    glVertex3f(road_width / 2, -GRID_LENGTH + y_offset, 0)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH + y_offset, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH + y_offset, 0)
    glVertex3f(road_width / 2, GRID_LENGTH + y_offset, 0)
    glEnd()

def draw_trees(x, y, z):
    glColor3f(0.5, 0.35, 0.05)
    glPushMatrix()
    glTranslatef(x, y, z)
    glBegin(GL_QUADS)
    glVertex3f(-2, -2, 0)
    glVertex3f(2, -2, 0)
    glVertex3f(2, 2, 20)
    glVertex3f(-2, 2, 20)
    glEnd()
    glColor3f(0.1, 0.5, 0.1)
    glTranslatef(0, 0, 20)
    glutSolidSphere(10, 10, 10)
    glPopMatrix()

def draw_road(y_offset):
    road_width = 40
    glColor3f(0.2, 0.2, 0.2)
    glBegin(GL_QUADS)
    glVertex3f(-road_width / 2, -GRID_LENGTH + y_offset, 0.1)
    glVertex3f(road_width / 2, -GRID_LENGTH + y_offset, 0.1)
    glVertex3f(road_width / 2, GRID_LENGTH + y_offset, 0.1)
    glVertex3f(-road_width / 2, GRID_LENGTH + y_offset, 0.1)
    glEnd()

    glColor3f(1.0, 1.0, 1.0)
    dash_length = 20
    gap_length = 10
    for i in range(-GRID_LENGTH, GRID_LENGTH, dash_length + gap_length):
        glBegin(GL_LINES)
        glVertex3f(0, i + y_offset, 0.2)
        glVertex3f(0, min(i + dash_length + y_offset, GRID_LENGTH + y_offset), 0.2)
        glEnd()

def draw_car():
    global car_length, car_width, car_height, wheel_radius, cannon_angle, cannon_base_height, cannon_length
    
    glPushMatrix()
    glTranslatef(car_x, car_y, car_z)
    
    glColor3f(1.0, 0.8, 0.0)
    glPushMatrix()
    glScalef(car_width, car_length, car_height)
    glutSolidCube(1)
    glPopMatrix()
    
    glColor3f(0.1, 0.1, 0.1)
    glPushMatrix()
    glTranslatef(0, 0, car_height/2)
    glScalef(car_width*0.8, car_length*0.7, car_height*0.5)
    glutSolidCube(1)
    glPopMatrix()
    
    glColor3f(0.7, 0.9, 1.0)
    glPushMatrix()
    glTranslatef(0, car_length*0.15, car_height/2 + car_height*0.2)
    glScalef(car_width*0.7, car_length*0.3, car_height*0.1)
    glutSolidCube(1)
    glPopMatrix()
    
    glColor3f(1.0, 1.0, 0.9)
    glPushMatrix()
    glTranslatef(-car_width*0.4, car_length*0.45, car_height*0.2)
    glutSolidSphere(0.4, 10, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(car_width*0.4, car_length*0.45, car_height*0.2)
    glutSolidSphere(0.4, 10, 10)
    glPopMatrix()
    
    glColor3f(1.0, 0.0, 0.0)
    glPushMatrix()
    glTranslatef(-car_width*0.4, -car_length*0.45, car_height*0.2)
    glutSolidSphere(0.4, 10, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(car_width*0.4, -car_length*0.45, car_height*0.2)
    glutSolidSphere(0.4, 10, 10)
    glPopMatrix()
    
    glColor3f(0.1, 0.1, 0.1)
    
    glPushMatrix()
    glTranslatef(-car_width*0.7, car_length*0.3, -car_height*0.5 + wheel_radius)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(wheel_radius*0.3, wheel_radius, 10, 20)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(car_width*0.7, car_length*0.3, -car_height*0.5 + wheel_radius)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(wheel_radius*0.3, wheel_radius, 10, 20)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-car_width*0.7, -car_length*0.3, -car_height*0.5 + wheel_radius)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(wheel_radius*0.3, wheel_radius, 10, 20)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(car_width*0.7, -car_length*0.3, -car_height*0.5 + wheel_radius)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(wheel_radius*0.3, wheel_radius, 10, 20)
    glPopMatrix()
    
    glColor3f(0.8, 0.8, 0.9)
    glPushMatrix()
    glTranslatef(-car_width*0.7, car_length*0.3, -car_height*0.5 + wheel_radius)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(wheel_radius*0.15, wheel_radius*0.7, 10, 20)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(car_width*0.7, car_length*0.3, -car_height*0.5 + wheel_radius)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(wheel_radius*0.15, wheel_radius*0.7, 10, 20)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-car_width*0.7, -car_length*0.3, -car_height*0.5 + wheel_radius)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(wheel_radius*0.15, wheel_radius*0.7, 10, 20)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(car_width*0.7, -car_length*0.3, -car_height*0.5 + wheel_radius)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(wheel_radius*0.15, wheel_radius*0.7, 10, 20)
    glPopMatrix()
    
    glColor3f(0.3, 0.3, 0.3)
    glPushMatrix()
    glTranslatef(0, car_length*0.3, cannon_base_height)
    glRotatef(cannon_angle, 0, 0, 1)
    glRotatef(90, 1, 0, 0)
    glutSolidCylinder(0.4, cannon_length, 10, 10)
    glPopMatrix()
    
    glPopMatrix()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, window_width, window_height)
    setupCamera()
    
    draw_sky()
    
    for seg in road_segments:
        draw_green_ground(seg['y'])
        draw_road(seg['y'])
    
    for seg in tree_segments:
        draw_trees(seg['x'], seg['y'], seg['z'])
    
    draw_car()
    
    for enemy in enemies:
        enemy.draw()
    
    for bullet in player_bullets:
        bullet.draw()
    
    for bullet in enemy_bullets:
        bullet.draw()
    
    draw_hud()
    
    glutSwapBuffers()

def reshape_window(width, height):
    global window_width, window_height
    window_width = width
    window_height = height
    glViewport(0, 0, window_width, window_height)
    setupCamera()

def idle():
    global track_position, car_x, car_y, scroll_speed
    
    if is_game_over:
        glutPostRedisplay()
        return
    
    if moving_forward:
        scroll_speed = -player_speed
    elif moving_backward:
        scroll_speed = player_speed
    else:
        scroll_speed = 0.0

    for seg in road_segments:
        seg['y'] += scroll_speed
        if seg['y'] < -GRID_LENGTH:
            seg['y'] += 2 * GRID_LENGTH
    
    for seg in tree_segments:
        seg['y'] += scroll_speed
        if seg['y'] < -GRID_LENGTH:
            seg['y'] += 2 * GRID_LENGTH

    for enemy in enemies:
        enemy.y += scroll_speed
    
    for bullet in player_bullets:
        bullet.y += scroll_speed
    
    for bullet in enemy_bullets:
        bullet.y += scroll_speed
    
    car_x = lane_positions[car_lane]
    
    for enemy in enemies:
        enemy.move()
    
    for bullet in player_bullets[:]:
        bullet.move()
        if bullet.lifetime <= 0:
            player_bullets.remove(bullet)
    
    for bullet in enemy_bullets[:]:
        bullet.move()
        if bullet.lifetime <= 0:
            enemy_bullets.remove(bullet)
    
    check_collisions()
    
    glutPostRedisplay()

def reset_game():
    global player_health, player_score, is_game_over, is_cheat_mode
    global shield_active, shield_health, car_lane, cannon_angle
    global track_position, player_bullets, enemy_bullets, enemies, car_x, car_y
    global moving_forward, moving_backward, road_segments, tree_segments
    
    player_health = 15
    player_score = 0
    is_game_over = False
    is_cheat_mode = False
    shield_active = True
    shield_health = 5
    car_lane = 1
    cannon_angle = 0
    track_position = 0
    car_x, car_y = 0, 0
    player_bullets = []
    enemy_bullets = []
    enemies = []
    moving_forward = False
    moving_backward = False
    
    for _ in range(3):
        x = random.choice(lane_positions)
        y = random.uniform(GRID_LENGTH + 100, GRID_LENGTH + 200)
        z = car_z
        enemies.append(EnemyCar(x, y, z))
    
    road_segments = [{'y': i * GRID_LENGTH} for i in range(-1, 2)]
    
    road_width = 40
    tree_positions_left = [(-road_width / 2) - 30, (-road_width / 2) - 30, (-road_width / 2) - 30]
    tree_positions_right = [(road_width / 2) + 30, (road_width / 2) + 30, (road_width / 2) + 30]
    tree_segments = []
    for y_offset in range(-1, 2):
        for pos_x in tree_positions_left + tree_positions_right:
            tree_segments.append({'x': pos_x, 'y': y_offset * GRID_LENGTH + random.uniform(-GRID_LENGTH/2, GRID_LENGTH/2), 'z': 0})

def draw_sky():
    glColor3f(0.5, 0.7, 1.0)
    glBegin(GL_QUADS)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, -100)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, -100)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, -100)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, -100)
    glEnd()

def draw_green_ground(y_offset):
    glColor3f(0.0, 0.5, 0.0)
    road_width = 40
    glBegin(GL_QUADS)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH + y_offset, 0)
    glVertex3f(-road_width / 2, -GRID_LENGTH + y_offset, 0)
    glVertex3f(-road_width / 2, GRID_LENGTH + y_offset, 0)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH + y_offset, 0)
    glEnd()
    glBegin(GL_QUADS)
    glVertex3f(road_width / 2, -GRID_LENGTH + y_offset, 0)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH + y_offset, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH + y_offset, 0)
    glVertex3f(road_width / 2, GRID_LENGTH + y_offset, 0)
    glEnd()

def draw_trees(x, y, z):
    glColor3f(0.5, 0.35, 0.05)
    glPushMatrix()
    glTranslatef(x, y, z)
    glBegin(GL_QUADS)
    glVertex3f(-2, -2, 0)
    glVertex3f(2, -2, 0)
    glVertex3f(2, 2, 20)
    glVertex3f(-2, 2, 20)
    glEnd()
    glColor3f(0.1, 0.5, 0.1)
    glTranslatef(0, 0, 20)
    glutSolidSphere(10, 10, 10)
    glPopMatrix()

def draw_road(y_offset):
    road_width = 40
    glColor3f(0.2, 0.2, 0.2)
    glBegin(GL_QUADS)
    glVertex3f(-road_width / 2, -GRID_LENGTH + y_offset, 0.1)
    glVertex3f(road_width / 2, -GRID_LENGTH + y_offset, 0.1)
    glVertex3f(road_width / 2, GRID_LENGTH + y_offset, 0.1)
    glVertex3f(-road_width / 2, GRID_LENGTH + y_offset, 0.1)
    glEnd()

    glColor3f(1.0, 1.0, 1.0)
    dash_length = 20
    gap_length = 10
    for i in range(-GRID_LENGTH, GRID_LENGTH, dash_length + gap_length):
        glBegin(GL_LINES)
        glVertex3f(0, i + y_offset, 0.2)
        glVertex3f(0, min(i + dash_length + y_offset, GRID_LENGTH + y_offset), 0.2)
        glEnd()

def draw_car():
    global car_length, car_width, car_height, wheel_radius, cannon_angle, cannon_base_height, cannon_length
    
    glPushMatrix()
    glTranslatef(car_x, car_y, car_z)
    
    glColor3f(1.0, 0.8, 0.0)
    glPushMatrix()
    glScalef(car_width, car_length, car_height)
    glutSolidCube(1)
    glPopMatrix()
    
    glColor3f(0.1, 0.1, 0.1)
    glPushMatrix()
    glTranslatef(0, 0, car_height/2)
    glScalef(car_width*0.8, car_length*0.7, car_height*0.5)
    glutSolidCube(1)
    glPopMatrix()
    
    glColor3f(0.7, 0.9, 1.0)
    glPushMatrix()
    glTranslatef(0, car_length*0.15, car_height/2 + car_height*0.2)
    glScalef(car_width*0.7, car_length*0.3, car_height*0.1)
    glutSolidCube(1)
    glPopMatrix()
    
    glColor3f(1.0, 1.0, 0.9)
    glPushMatrix()
    glTranslatef(-car_width*0.4, car_length*0.45, car_height*0.2)
    glutSolidSphere(0.4, 10, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(car_width*0.4, car_length*0.45, car_height*0.2)
    glutSolidSphere(0.4, 10, 10)
    glPopMatrix()
    
    glColor3f(1.0, 0.0, 0.0)
    glPushMatrix()
    glTranslatef(-car_width*0.4, -car_length*0.45, car_height*0.2)
    glutSolidSphere(0.4, 10, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(car_width*0.4, -car_length*0.45, car_height*0.2)
    glutSolidSphere(0.4, 10, 10)
    glPopMatrix()
    
    glColor3f(0.1, 0.1, 0.1)
    
    glPushMatrix()
    glTranslatef(-car_width*0.7, car_length*0.3, -car_height*0.5 + wheel_radius)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(wheel_radius*0.3, wheel_radius, 10, 20)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(car_width*0.7, car_length*0.3, -car_height*0.5 + wheel_radius)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(wheel_radius*0.3, wheel_radius, 10, 20)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-car_width*0.7, -car_length*0.3, -car_height*0.5 + wheel_radius)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(wheel_radius*0.3, wheel_radius, 10, 20)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(car_width*0.7, -car_length*0.3, -car_height*0.5 + wheel_radius)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(wheel_radius*0.3, wheel_radius, 10, 20)
    glPopMatrix()
    
    glColor3f(0.8, 0.8, 0.9)
    glPushMatrix()
    glTranslatef(-car_width*0.7, car_length*0.3, -car_height*0.5 + wheel_radius)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(wheel_radius*0.15, wheel_radius*0.7, 10, 20)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(car_width*0.7, car_length*0.3, -car_height*0.5 + wheel_radius)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(wheel_radius*0.15, wheel_radius*0.7, 10, 20)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-car_width*0.7, -car_length*0.3, -car_height*0.5 + wheel_radius)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(wheel_radius*0.15, wheel_radius*0.7, 10, 20)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(car_width*0.7, -car_length*0.3, -car_height*0.5 + wheel_radius)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(wheel_radius*0.15, wheel_radius*0.7, 10, 20)
    glPopMatrix()
    
    glColor3f(0.3, 0.3, 0.3)
    glPushMatrix()
    glTranslatef(0, car_length*0.3, cannon_base_height)
    glRotatef(cannon_angle, 0, 0, 1)
    glRotatef(90, 1, 0, 0)
    glutSolidCylinder(0.4, cannon_length, 10, 10)
    glPopMatrix()
    
    glPopMatrix()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, window_width, window_height)
    setupCamera()
    
    draw_sky()
    
    for seg in road_segments:
        draw_green_ground(seg['y'])
        draw_road(seg['y'])
    
    for seg in tree_segments:
        draw_trees(seg['x'], seg['y'], seg['z'])
    
    draw_car()
    
    for enemy in enemies:
        enemy.draw()
    
    for bullet in player_bullets:
        bullet.draw()
    
    for bullet in enemy_bullets:
        bullet.draw()
    
    draw_hud()
    
    glutSwapBuffers()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(window_width, window_height)
    glutCreateWindow(b"Death Drive - 3D Racing Game")
    glClearColor(0.5, 0.7, 1.0, 1.0)

    glEnable(GL_DEPTH_TEST)
    
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(keyboardUpListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glutReshapeFunc(reshape_window)
    
    reset_game()
    
    glutMainLoop()

if __name__ == "__main__":
    main()