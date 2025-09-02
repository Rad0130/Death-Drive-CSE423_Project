from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import sys
from math import cos, sin, radians, atan2, degrees
import random

# Initialize korchi global variables
camera_pos = (0, -25, 15)  # Camera position (x, y, z)
cannon_angle = 0  # player's cannon er angle
car_x, car_y, car_z = 0, 0, 5  # Player car er position
player_speed = 5.0  # player car er speed
lane_positions = [-30, -15, 0, 15, 30]  # Predefined lane x-positions
fovY = 60  # perspective projection er jonno field of view
GRID_LENGTH = 600  #game world grid er length
window_width, window_height = 1000, 800  # Window dimensions
player_health = 15  # Player er health points
player_score = 0  # Player er jei score
is_game_over = False  # Game over er flag
is_cheat_mode = False  # Cheat mode er flag (invincibility)
first_person_view = False  # Toggle kora 1st and 3rd person er view er jonno
shield_active = True  # Shield status
shield_health = 5  # Shield health points
car_lane = 2  # lane index (0 to 4) er 2nd index ta default position
track_position = 0.0  # Track scrolling position
player_bullets = []  # player-fired bullets er list
enemy_bullets = []  #enemy-fired bullets er list
enemies = []  # List of enemy cars
moving_forward = False  # Forward movement flag
moving_backward = False  # Backward movement flag
road_segments = []  # List of road segment positions
tree_segments = []  # List of tree positions
scroll_speed = 0.0  # Speed of world scrolling
car_length = 4  # Player car dimensions
car_width = 2
car_height = 1.25
wheel_radius = 0.5  # Wheel size
cannon_length = 2.0  # Cannon length
cannon_base_height = car_height * 0.6  # Cannon height offset
road_width = 70  # Width of the road

# Bullet class to represent player and enemy projectiles
class Bullet:
    def __init__(self, x, y, z, angle, speed, color, is_player_bullet=True):
        self.x = x  # X position
        self.y = y  # Y position
        self.z = z  # Z position
        self.angle = angle  # Movement angle
        self.speed = speed  # Bullet speed
        self.color = color  # Bullet color (RGB)
        self.is_player_bullet = is_player_bullet  # True for player, False for enemy
        self.lifetime = 200 if is_player_bullet else 300  # Bullet er duration

    def move(self):
        # Update korchi bullet position based on angle and speed
        self.x += self.speed * sin(radians(self.angle))
        self.y += self.speed * cos(radians(self.angle))
        self.lifetime -= 1  # Decrease korbo lifetime

    def draw(self):
        # bullet draw kora hoyeche using sphere
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glColor3f(*self.color)
        quadric = gluNewQuadric()
        gluSphere(quadric, 0.5, 8, 8)  # Draw sphere with radius 0.5
        glPopMatrix()

#enemy vehicles represent korte
class EnemyCar:
    def __init__(self, x, y, z):
        # Initialize enemy car properties
        self.x = x  # X position
        self.y = y  # Y position
        self.z = z  # Z position
        self.car_length = 8  # Enemy car dimensions
        self.car_width = 4
        self.car_height = 2.5
        self.color = (random.random(), random.random(), random.random())  # Random color
        self.speed = random.uniform(2.0, 4.0)  # Random speed
        self.direction = 0  # Facing direction
        self.shoot_cooldown = 0  # Cooldown for shooting
        self.enemy_cannon_angle = 0  # Enemy cannon angle

    def move(self):
        # Update korbo enemy car position and behavior
        global car_x, car_y
        self.y -= self.speed  # Move towards player, picher dike ashche enemy cars
        dx = car_x - self.x
        dy = car_y - self.y
        self.enemy_cannon_angle = degrees(atan2(dx, dy)) + random.uniform(-5, 5)  # enemy er cannon aims slightly off from the exact direction of the player
        #atan2 radians return kore,degrees converts this angle to degrees
        if self.y < -GRID_LENGTH:  # Respawn korbo at top if off-screen
            self.y = GRID_LENGTH + 100
            self.x = random.choice(lane_positions)
        self.shoot_cooldown -= 1
        if self.shoot_cooldown <= 0 and random.random() < 0.01:  # Randomly shoot
            self.shoot()
            self.shoot_cooldown = random.randint(30, 60)  # Reset korbo cooldown

    def shoot(self):
        # Create a new enemy bullet
        bullet_start_x = self.x + (self.car_length * 0.3 + cannon_length) * sin(radians(self.enemy_cannon_angle)) #jate cannon point er shamne theke ber hoy bullet
        bullet_start_y = self.y + (self.car_length * 0.3 + cannon_length) * cos(radians(self.enemy_cannon_angle))
        bullet_start_z = self.z + cannon_base_height
        bullet = Bullet(bullet_start_x, bullet_start_y, bullet_start_z, self.enemy_cannon_angle, 1.5, (1.0, 0.0, 0.0), False)
#1.5 hoche speed of bullet,(1.0, 0.0, 0.0):RGB color of the bullet (red), False: bujhay je eta enemy bullet (not a player bullet)
        enemy_bullets.append(bullet)

    def draw(self):
        # Render korrchi enemy car
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.direction, 0, 0, 1)
        glColor3f(*self.color)
        glPushMatrix()
        glScalef(self.car_width, self.car_length, self.car_height)
        glutSolidCube(1)  # main body
        glPopMatrix()
        glColor3f(0.8, 0.0, 0.0)
        glPushMatrix()
        glTranslatef(0, 0, self.car_height/2)
        glScalef(self.car_width * 0.8, self.car_length * 0.7, self.car_height * 0.5)
        glutSolidCube(1)  # upper body
        glPopMatrix()
        glColor3f(0.3, 0.3, 0.3)
        glPushMatrix()
        glTranslatef(0, self.car_length * 0.3, cannon_base_height)
        glRotatef(-self.enemy_cannon_angle + 180, 0, 0, 1)
        glRotatef(90, 1, 0, 0)
        quadric = gluNewQuadric()
        gluCylinder(quadric, 0.4, 0.4, cannon_length, 10, 10)  # Draw cannon
        glPopMatrix()
        glPopMatrix()

# Handle keyboard input for controls
def keyboard(key, x, y):
    global cannon_angle, car_lane, is_cheat_mode, is_game_over, moving_forward, moving_backward
    if is_game_over and key == b'r':  # Restart game on 'r' if game over
        reset_game()
        return
    if is_game_over:
        return
    key = key.decode('utf-8').lower()
    if key == 'z':
        cannon_angle += 5  # Rotate cannon left
    elif key == 'c':
        cannon_angle -= 5  # Rotate cannon right
    elif key == 'a':
        car_lane = max(0, car_lane - 1)  # Move left
    elif key == 'd':
        car_lane = min(4, car_lane + 1)  # Move right
    elif key == 'w':
        moving_forward = not moving_forward  # Toggle forward movement
        if moving_forward:
            moving_backward = False
    elif key == 's':
        moving_backward = not moving_backward  # Toggle backward movement
        if moving_backward:
            moving_forward = False
    elif key == 'v':
        is_cheat_mode = not is_cheat_mode  # Toggle cheat mode
    cannon_angle %= 360  #angle rakhlam in 0-360 range
    glutPostRedisplay()  # Request redraw


def mouseListener(button, state, x, y):
    global first_person_view
    if is_game_over:
        return
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:  # Shoot on left click
        bullet_start_x = car_x + (car_length * 0.3 + cannon_length) * sin(radians(cannon_angle))
        bullet_start_y = car_y + (car_length * 0.3 + cannon_length) * cos(radians(cannon_angle))
        bullet_start_z = car_z + cannon_base_height
        fixed_angle = -cannon_angle
        bullet = Bullet(bullet_start_x, bullet_start_y, bullet_start_z, fixed_angle, 10.0, (1.0, 1.0, 0.0), True)
        player_bullets.append(bullet)
    elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:  # Toggle view on right click
        first_person_view = not first_person_view

# Handle special keys for camera movement
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

# camera perspective and view set kora
def setupCamera():
    global car_x, car_y, car_z, first_person_view, camera_pos, window_width, window_height
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    if window_height == 0:
        window_height = 1
    aspect_ratio = window_width / float(window_height)
    gluPerspective(fovY, aspect_ratio, 0.1, 1500)  # Set perspective projection
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    if first_person_view:  # First-person view
        gluLookAt(car_x, car_y + 10, car_z + 5,
                  car_x, car_y + 50, car_z + 5,
                  0, 0, 1)
    else:  # Third-person view
        cam_x = car_x + camera_pos[0]
        cam_y = car_y + camera_pos[1]
        cam_z = car_z + camera_pos[2]
        gluLookAt(cam_x, cam_y, cam_z,
                  car_x, car_y, car_z,
                  0, 0, 1)

# Draw 2D text for HUD
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)  # White text
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, window_width, 0, window_height)  # Set 2D orthographic projection
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)  # Set text position
    for ch in text:
        glutBitmapCharacter(font, ord(ch))  # Draw each character
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# Draw heads-up display (HUD)
def draw_hud():
    global window_width, window_height
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

# Check korbo for collisions between bullets, enemies, and player
def check_collisions():
    global player_health, shield_health, shield_active, player_score, enemies, is_game_over
    bullets_to_remove = []
    enemies_to_remove = []
    # Check player bullets hitting enemies
    for bullet in player_bullets:
        for enemy in enemies:
            dist = ((enemy.x - bullet.x) ** 2 + (enemy.y - bullet.y) ** 2) ** 0.5
            enemy_radius = max(enemy.car_width, enemy.car_length) / 2
            bullet_radius = 0.5
            if dist < enemy_radius + bullet_radius:  # Collision detected
                bullets_to_remove.append(bullet)
                enemies_to_remove.append(enemy)
                player_score += 1
                break
    # Remove korbo collided player er bullets
    for bullet in bullets_to_remove:
        if bullet in player_bullets:
            player_bullets.remove(bullet)
    # destroyed enemies remove kore dibo
    for enemy in enemies_to_remove:
        if enemy in enemies:
            enemies.remove(enemy)
    # Check korchi enemy bullets player hit korche kina
    for bullet in enemy_bullets[:]:
        dist = ((car_x - bullet.x) ** 2 + (car_y - bullet.y) ** 2) ** 0.5
        if dist < 15:  # Collision with player
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
    # enemy cars player er shathe colliding korche kina 
    for enemy in enemies:
        dist = ((enemy.x - car_x) ** 2 + (enemy.y - car_y) ** 2) ** 0.5
        if dist < 5:  # Collision with player
            if shield_active and shield_health > 0:
                shield_health -= 1
                if shield_health <= 0:
                    shield_active = False
            else:
                if not is_cheat_mode:
                    player_health -= 5
                if player_health <= 0:
                    is_game_over = True
            # enemy ke push away kore dibo if collision
            enemy.x += 100 if enemy.x > car_x else -100
            enemy.y += 100 if enemy.y > car_y else -100
    # Spawn korbo new enemies if needed
    if len(enemies) < 3:
        for i in range(3 - len(enemies)):
            x = random.choice(lane_positions)
            y = random.uniform(GRID_LENGTH + 100, GRID_LENGTH + 200)
            z = car_z
            enemies.append(EnemyCar(x, y, z))

# game state update korchi in idle loop
def idle():
    global track_position, car_x, car_y, scroll_speed
    if is_game_over:
        glutPostRedisplay()
        return
    # based on player movement, scroll speed set korchi
    if moving_forward:
        scroll_speed = -player_speed  #world moves down, simulating kore je player moving up
    elif moving_backward:
        scroll_speed = player_speed
    else:
        scroll_speed = 0.0
    # Update road and tree segments
    for seg in road_segments:
        seg['y'] += scroll_speed
        if seg['y'] < -GRID_LENGTH:
            seg['y'] += 2 * GRID_LENGTH
    for seg in tree_segments:
        seg['y'] += scroll_speed
        if seg['y'] < -GRID_LENGTH:
            seg['y'] += 2 * GRID_LENGTH
    # Update enemy and bullet positions
    for enemy in enemies:
        enemy.y += scroll_speed
    for bullet in player_bullets:
        bullet.y += scroll_speed
    for bullet in enemy_bullets:
        bullet.y += scroll_speed
    car_x = lane_positions[car_lane]  # Update player position
    # Move enemies and bullets
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
    check_collisions()  # Check collisions
    glutPostRedisplay()  # Request redraw

# Reset game state
def reset_game():
    global player_health, player_score, is_game_over, is_cheat_mode
    global shield_active, shield_health, car_lane, cannon_angle
    global track_position, player_bullets, enemy_bullets, enemies, car_x, car_y
    global moving_forward, moving_backward, road_segments, tree_segments
    # Reset all game variables
    player_health = 15
    player_score = 0
    is_game_over = False
    is_cheat_mode = False
    shield_active = True
    shield_health = 5
    car_lane = 2
    cannon_angle = 0
    track_position = 0
    car_x, car_y = 0, 0
    player_bullets = []
    enemy_bullets = []
    enemies = []
    moving_forward = False
    moving_backward = False

    road_segments = [{'y': i * GRID_LENGTH} for i in range(-1, 2)]
    #3 ta segment e road draw korlam
    # Initialize tree positions
    tree_positions_left = [(-road_width / 2) - 30, (-road_width / 2) - 30, (-road_width / 2) - 30]
    tree_positions_right = [(road_width / 2) + 30, (road_width / 2) + 30, (road_width / 2) + 30]
    #3 ta kore tree place
    tree_segments = []
    for y_offset in range(-1, 2):
        for pos_x in tree_positions_left + tree_positions_right:  #combines six x-positions (three left, three right) for trees in each segment
            tree_segments.append({'x': pos_x, 'y': y_offset * GRID_LENGTH + random.uniform(-GRID_LENGTH/2, GRID_LENGTH/2), 'z': 0})
    #jemon, 18 trees, with 6 in each segment
# Draw sky background
def draw_sky():
    glColor3f(0.5, 0.7, 1.0)  # Light blue color
    glBegin(GL_QUADS)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, -100)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, -100)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, -100)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, -100)
    glEnd()

# Draw green ground on both sides of the road
def draw_green_ground(y_offset):
    glColor3f(0.0, 0.5, 0.0)  # Green color
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

# Draw trees on dui sides of the road
def draw_trees(x, y, z):
    glColor3f(0.5, 0.35, 0.05)  # Brown trunk
    glPushMatrix()
    glTranslatef(x, y, z)
    glBegin(GL_QUADS)
    glVertex3f(-2, -2, 0)
    glVertex3f(2, -2, 0)
    glVertex3f(2, 2, 20)
    glVertex3f(-2, 2, 20)
    glEnd()
    glColor3f(0.1, 0.5, 0.1)  # Green foliage
    glTranslatef(0, 0, 20)
    quadric = gluNewQuadric()
    gluSphere(quadric, 10, 10, 10)  # Draw spherical foliage
    glPopMatrix()

# lane markings kora in draw road
def draw_road(y_offset):
    glColor3f(0.2, 0.2, 0.2)  # Gray road
    glBegin(GL_QUADS)
    glVertex3f(-road_width / 2, -GRID_LENGTH + y_offset, 0.1)
    glVertex3f(road_width / 2, -GRID_LENGTH + y_offset, 0.1)
    glVertex3f(road_width / 2, GRID_LENGTH + y_offset, 0.1)
    glVertex3f(-road_width / 2, GRID_LENGTH + y_offset, 0.1)
    glEnd()
    glColor3f(1.0, 1.0, 1.0)  # White lane markings
    dash_length = 20
    gap_length = 10
    for i in range(-GRID_LENGTH, GRID_LENGTH, dash_length + gap_length):
        glBegin(GL_LINES)
        glVertex3f(-road_width/2 + 15, i + y_offset, 0.2)
        glVertex3f(-road_width/2 + 15, min(i + dash_length + y_offset, GRID_LENGTH + y_offset), 0.2)
        glEnd()
        glBegin(GL_LINES)
        glVertex3f(-road_width/2 + 30, i + y_offset, 0.2)
        glVertex3f(-road_width/2 + 30, min(i + dash_length + y_offset, GRID_LENGTH + y_offset), 0.2)
        glEnd()
        glBegin(GL_LINES)
        glVertex3f(0, i + y_offset, 0.2)
        glVertex3f(0, min(i + dash_length + y_offset, GRID_LENGTH + y_offset), 0.2)
        glEnd()
        glBegin(GL_LINES)
        glVertex3f(road_width/2 - 30, i + y_offset, 0.2)
        glVertex3f(road_width/2 - 30, min(i + dash_length + y_offset, GRID_LENGTH + y_offset), 0.2)
        glEnd()
        glBegin(GL_LINES)
        glVertex3f(road_width/2 - 15, i + y_offset, 0.2)
        glVertex3f(road_width/2 - 15, min(i + dash_length + y_offset, GRID_LENGTH + y_offset), 0.2)
        glEnd()

# Draw player car
def draw_car():
    global car_length, car_width, car_height, wheel_radius, cannon_angle, cannon_base_height, cannon_length, shield_active
    glPushMatrix()
    glTranslatef(car_x, car_y, car_z)
    glColor3f(1.0, 0.8, 0.0)  # Yellow body
    glPushMatrix()
    glScalef(car_width, car_length, car_height)
    glutSolidCube(1)  # Main body
    glPopMatrix()
    glColor3f(0.1, 0.1, 0.1)  # Dark gray upper body
    glPushMatrix()
    glTranslatef(0, 0, car_height/2)
    glScalef(car_width*0.8, car_length*0.7, car_height*0.5)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.7, 0.9, 1.0)  # Light blue windshield
    glPushMatrix()
    glTranslatef(0, car_length*0.15, car_height/2 + car_height*0.2)
    glScalef(car_width*0.7, car_length*0.3, car_height*0.1)
    glutSolidCube(1)
    glPopMatrix()
    # Draw headlights
    glColor3f(1.0, 1.0, 0.9)
    glPushMatrix()
    glTranslatef(-car_width*0.4, car_length*0.45, car_height*0.2)
    quadric = gluNewQuadric()
    gluSphere(quadric, 0.4, 10, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(car_width*0.4, car_length*0.45, car_height*0.2)
    quadric = gluNewQuadric()
    gluSphere(quadric, 0.4, 10, 10)
    glPopMatrix()
    # Draw taillights
    glColor3f(1.0, 0.0, 0.0)
    glPushMatrix()
    glTranslatef(-car_width*0.4, -car_length*0.45, car_height*0.2)
    quadric = gluNewQuadric()
    gluSphere(quadric, 0.4, 10, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(car_width*0.4, -car_length*0.45, car_height*0.2)
    quadric = gluNewQuadric()
    gluSphere(quadric, 0.4, 10, 10)
    glPopMatrix()
    # Draw wheels
    glColor3f(0.1, 0.1, 0.1)
    glPushMatrix()
    glTranslatef(-car_width*0.7, car_length*0.3, -car_height*0.5 + wheel_radius)
    glRotatef(90, 0, 1, 0)
    quadric = gluNewQuadric()
    gluSphere(quadric, wheel_radius, 10, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(car_width*0.7, car_length*0.3, -car_height*0.5 + wheel_radius)
    glRotatef(90, 0, 1, 0)
    quadric = gluNewQuadric()
    gluSphere(quadric, wheel_radius, 10, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(-car_width*0.7, -car_length*0.3, -car_height*0.5 + wheel_radius)
    glRotatef(90, 0, 1, 0)
    quadric = gluNewQuadric()
    gluSphere(quadric, wheel_radius, 10, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(car_width*0.7, -car_length*0.3, -car_height*0.5 + wheel_radius)
    glRotatef(90, 0, 1, 0)
    quadric = gluNewQuadric()
    gluSphere(quadric, wheel_radius, 10, 10)
    glPopMatrix()
    # Draw wheel hubs
    glColor3f(0.8, 0.8, 0.9)
    glPushMatrix()
    glTranslatef(-car_width*0.7, car_length*0.3, -car_height*0.5 + wheel_radius)
    glRotatef(90, 0, 1, 0)
    quadric = gluNewQuadric()
    gluSphere(quadric, wheel_radius*0.7, 10, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(car_width*0.7, car_length*0.3, -car_height*0.5 + wheel_radius)
    glRotatef(90, 0, 1, 0)
    quadric = gluNewQuadric()
    gluSphere(quadric, wheel_radius*0.7, 10, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(-car_width*0.7, -car_length*0.3, -car_height*0.5 + wheel_radius)
    glRotatef(90, 0, 1, 0)
    quadric = gluNewQuadric()
    gluSphere(quadric, wheel_radius*0.7, 10, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(car_width*0.7, -car_length*0.3, -car_height*0.5 + wheel_radius)
    glRotatef(90, 0, 1, 0)
    quadric = gluNewQuadric()
    gluSphere(quadric, wheel_radius*0.7, 10, 10)
    glPopMatrix()
    # Draw cannon
    glColor3f(0.3, 0.3, 0.3)
    glPushMatrix()
    glTranslatef(0, car_length*0.3, cannon_base_height)
    glRotatef(cannon_angle, 0, 0, 1)
    glRotatef(90, 1, 0, 0)
    quadric = gluNewQuadric()
    gluCylinder(quadric, 0.4, 0.4, cannon_length, 10, 10)
    glPopMatrix()
    # Draw shield if active
    if shield_active:
        glColor3f(0.9, 0.95, 1.0)
        glPushMatrix()
        glTranslatef(0, 0, car_height/2)
        glPointSize(2.0)
        glBegin(GL_POINTS)
        for i in range(20):
            angle1 = 3.14159 * i / 10
            for j in range(20):
                angle2 = 2 * 3.14159 * j / 20
                x = 2.5 * sin(angle1) * cos(angle2)
                y = 2.5 * sin(angle1) * sin(angle2)
                z = 2.5 * cos(angle1)
                glVertex3f(x, y, z)
        glEnd()
        glPopMatrix()
    glPopMatrix()

# Main rendering function
def showScreen():
    global window_width, window_height
    window_width = glutGet(GLUT_WINDOW_WIDTH)
    window_height = glutGet(GLUT_WINDOW_HEIGHT)
    
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # Clear buffers
    glLoadIdentity()
    
    glViewport(0, 0, window_width, window_height) 
    
    setupCamera()  # Configure camera
    
    # Draw shob game elements
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
        
    draw_hud()  # Draw HUD
    
    glutSwapBuffers()  # Swap buffers jate double buffering hoy

# Main function to initialize and run the game
def main():
    glutInit()  # Initialize GLUT
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)  # Set display mode
    glutInitWindowSize(window_width, window_height)  # Set window size
    glutCreateWindow(b"Death Drive - 3D Racing Game")  # Create window
    glClearColor(0.5, 0.7, 1.0, 1.0)  # Set clear color (sky blue)
    glEnable(GL_DEPTH_TEST)  # Enable korlam depth testing
    glutDisplayFunc(showScreen)  
    glutKeyboardFunc(keyboard)  
    glutSpecialFunc(specialKeyListener)  
    glutMouseFunc(mouseListener)  
    glutIdleFunc(idle)  
    reset_game()  # Initialize game state
    glutMainLoop()  

if __name__ == "__main__":
    main()