
import matplotlib.pyplot as plt
import pygame, random, time, numpy as np, pickle
from pygame.locals import *
from matplotlib import style
import os

style.use("ggplot")

SCREEN_WIDTH = 300
SCREEN_HEIGHT = 600
n = 7
SPEED = 20
GRAVITY = 10
GAME_SPEED = 15

GROUND_WIDTH = 2 * SCREEN_WIDTH
GROUND_HEIGHT = 100

PIPE_WIDTH = 80
PIPE_HEIGHT = 500

PIPE_GAP = 150

wing = 'assets/audio/wing.wav'
hit = 'assets/audio/hit.wav'

pygame.mixer.init()

class Bird(pygame.sprite.Sprite):
    def __init__(self, start_y, tint_color, index):
        pygame.sprite.Sprite.__init__(self)

        self.images = [self.tint_image(pygame.image.load('assets/sprites/bluebird-upflap.png').convert_alpha(), tint_color),
                       self.tint_image(pygame.image.load('assets/sprites/bluebird-midflap.png').convert_alpha(), tint_color),
                       self.tint_image(pygame.image.load('assets/sprites/bluebird-downflap.png').convert_alpha(), tint_color)]

        self.speed = SPEED
        self.index = index

        self.current_image = 0
        self.image = self.images[self.current_image]
        self.mask = pygame.mask.from_surface(self.image)

        self.rect = self.image.get_rect()
        self.rect[0] = SCREEN_WIDTH / 6
        self.rect[1] = start_y

    def tint_image(self, image, tint_color):
        tinted_image = image.copy()
        tinted_image.lock()
        width, height = tinted_image.get_size()

        for x in range(width):
            for y in range(height):
                r, g, b, a = tinted_image.get_at((x, y))

                if b > r and b > g:  
                    tinted_image.set_at((x, y), (tint_color[0], tint_color[1], tint_color[2], a))

        tinted_image.unlock()

        return tinted_image

    def update(self):
        self.current_image = (self.current_image + 1) % 3
        self.image = self.images[self.current_image]
        self.speed = min(min(0, self.speed) + GRAVITY, SPEED)
        self.rect[1] += self.speed

    def bump(self):
        self.speed = -2 * SPEED

    def begin(self):
        self.current_image = (self.current_image + 1) % 3
        self.image = self.images[self.current_image]


class Pipe(pygame.sprite.Sprite):
    def __init__(self, inverted, xpos, ysize):
        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.image.load('assets/sprites/pipe-green.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (PIPE_WIDTH, PIPE_HEIGHT))

        self.rect = self.image.get_rect()
        self.rect[0] = xpos

        if inverted:
            self.image = pygame.transform.flip(self.image, False, True)
            self.rect[1] = - (self.rect[3] - ysize)
        else:
            self.rect[1] = SCREEN_HEIGHT - ysize

        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.rect[0] -= GAME_SPEED


class Ground(pygame.sprite.Sprite):
    def __init__(self, xpos):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('assets/sprites/base.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (GROUND_WIDTH, GROUND_HEIGHT))

        self.mask = pygame.mask.from_surface(self.image)

        self.rect = self.image.get_rect()
        self.rect[0] = xpos
        self.rect[1] = SCREEN_HEIGHT - GROUND_HEIGHT

    def update(self):
        self.rect[0] -= GAME_SPEED


def is_off_screen(sprite):
    return sprite.rect[0] < -(sprite.rect[2])


def get_random_pipes(xpos):
    size = random.randint(25, 45) * 10
    pipe = Pipe(False, xpos, size)
    pipe_inverted = Pipe(True, xpos, SCREEN_HEIGHT - size - PIPE_GAP)
    return pipe, pipe_inverted


def disc_pos(pos):
    pos = int(pos // 5) * 5
    return pos


def imp(pos):
    pos = int(pos // 10) * 10
    return pos


def Capture(display, name, pos, size):
    image = pygame.Surface(size) 
    image.blit(display, (0, 0), (pos, size))
    pygame.image.save(image, name)


def show_leaderboard(screen, scores, cumulative_scores, font, colors):
    for _ in range(n):
        scores[_] += cumulative_scores[_]

    curr_scores = [(f"{_ + 1}", scores[_], colors[_]) for _ in range(len(scores))]
    curr_scores = sorted(curr_scores, key=lambda bird: bird[1], reverse=True)

    bird_image = pygame.image.load('assets/sprites/bluebird-midflap.png').convert_alpha()
    
    leaderboard_bg_color = (0, 0, 0)
    pygame.draw.rect(screen, leaderboard_bg_color, (SCREEN_WIDTH, 0, 300, SCREEN_HEIGHT))

    title = font.render("Leaderboard", True, (255, 255, 255))
    screen.blit(title, (SCREEN_WIDTH + 20, 20))

    padding_top = 60
    line_height = 40
    margin = 20
    image_offset_x = 45  
    
    text_colors = [
        (255, 215, 0),
        (192, 192, 192),
        (205, 127, 50), 
        (255, 255, 255) 
    ]

    for idx, bird in enumerate(curr_scores):
        color = text_colors[idx] if idx < len(text_colors) else text_colors[-1]

        leaderboard_text = font.render(
            f"Score: {bird[1]} pts", True, color
        )

        tint_color = bird[2]

        tinted_image = bird_image.copy()
        tinted_image.lock()
        width, height = tinted_image.get_size()

        for x in range(width):
            for y in range(height):
                r, g, b, a = tinted_image.get_at((x, y))

                if b > r and b > g:  
                    tinted_image.set_at((x, y), (0, 0, 0, a))
                    tinted_image.set_at((x, y), (tint_color[0], tint_color[1], tint_color[2], a))

        tinted_image.unlock()

        screen.blit(tinted_image, (SCREEN_WIDTH + margin, padding_top + idx * line_height- 3))
        del tinted_image
        screen.blit(leaderboard_text, (SCREEN_WIDTH + margin + image_offset_x, padding_top + idx * line_height))

    pygame.display.update()

num_ep = 10
score_rew = 15
flag_ = True
crash = -1000
over_flow = -1000
epsilon = 0.01
epsilon_decay = 1
alpha = 0.05
alpha_decay = 0.9998
discount = 1
show_every = 20000
peak_score = 0
scores = []
cumulative_scores = [0] * n
start_q_table = "Q_tables/qtable-1708025126.pickle"
with open(start_q_table, "rb") as f:
    q_table = pickle.load(f)

for i in range(num_ep):
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH + 300, SCREEN_HEIGHT))
    pygame.display.set_caption('Flappy Bird')

    begin = True
    while begin:

        BACKGROUND = pygame.image.load('assets/sprites/background-day.png')
        BACKGROUND = pygame.transform.scale(BACKGROUND, (SCREEN_WIDTH, SCREEN_HEIGHT))
        digits = [pygame.image.load(f'assets/sprites/{_}.png') for _ in range(10)]

        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 165, 0), (128, 0, 128), (255, 192, 203)]
        bird_group = pygame.sprite.Group()
        birds = [Bird(SCREEN_HEIGHT / 2 + _ * 10, colors[_], _) for _ in range(n)]
        bird_group.add(*birds)

        ground_group = pygame.sprite.Group()
        for j in range(2):
            ground = Ground(GROUND_WIDTH * j)
            ground_group.add(ground)

        pipe_group = pygame.sprite.Group()
        for j in range(2):
            pipes = get_random_pipes(SCREEN_WIDTH * j + 300)
            pipe_group.add(pipes[0])
            pipe_group.add(pipes[1])

        clock = pygame.time.Clock()
        score = 0

        active_birds = len(birds)
        curr_scores = [0] * n

        begin = True

        while begin:

            clock.tick(27)

            for bird in birds:
                bird.bump()

            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    quit()

                if event.type == KEYDOWN:
                    if event.key == K_SPACE:
                        begin = False
            

            screen.blit(BACKGROUND, (0, 0))

            if is_off_screen(ground_group.sprites()[0]): 
                ground_group.remove(ground_group.sprites()[0])

                new_ground = Ground(GROUND_WIDTH - 20)
                ground_group.add(new_ground)

            for bird in birds:
                bird.begin()

            ground_group.update()

            bird_group.draw(screen)
            ground_group.draw(screen)

            font = pygame.font.SysFont(None, 30)
            show_leaderboard(screen, curr_scores, cumulative_scores, font, colors)

            pygame.display.update()


    while active_birds > 0:
        clock.tick(60)
        
        for bird in birds:
            bird.bump()
            pygame.mixer.music.load(wing)
            pygame.mixer.music.play()
            begin = False

        screen.blit(BACKGROUND, (0, 0))

        if is_off_screen(ground_group.sprites()[0]):
            ground_group.remove(ground_group.sprites()[0])
            new_ground = Ground(GROUND_WIDTH - 20)
            ground_group.add(new_ground)

        for bird in birds:
            bird.begin()

        ground_group.update()
        bird_group.draw(screen)
        ground_group.draw(screen)

        font = pygame.font.SysFont(None, 30)
        text = font.render(f'Alive Birds: {active_birds} | Generation: {i + 1}', True, (255, 255, 255))
        screen.blit(text, (10, 10))

        pygame.display.update()

        total_reward = 0
        for k in range(100000):
            clock.tick(20)
            for bird in birds:
                obs = (imp(pipe_group.sprites()[1].rect[0]), imp(pipe_group.sprites()[0].rect[1] - bird.rect[1]))

                if(bird.index != n - 1):
                    if np.random.random() < epsilon:
                        action = np.random.randint(0, 2)
                    else:
                        action = np.argmax(q_table[obs][:2])

                    if action:
                        bird.bump()
                        pygame.mixer.music.load(wing)
                        pygame.mixer.music.play()

                q_table[obs][2] += 1
                
            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    if event.key == K_SPACE:
                        for bird in bird_group:
                            if bird.index == n - 1: bird.bump()
                        pygame.mixer.music.load(wing)
                        pygame.mixer.music.play()


            screen.blit(BACKGROUND, (0, 0))
            x = 130
            for num in str(score):
                screen.blit(digits[int(num)], (x, 120))
                x += 20

            if is_off_screen(ground_group.sprites()[0]):
                ground_group.remove(ground_group.sprites()[0])
                new_ground = Ground(GROUND_WIDTH - 20)
                ground_group.add(new_ground)

            if is_off_screen(pipe_group.sprites()[0]):
                pipe_group.remove(pipe_group.sprites()[0])
                pipe_group.remove(pipe_group.sprites()[0])
                pipes = get_random_pipes(SCREEN_WIDTH * 2)
                pipe_group.add(pipes[0])
                pipe_group.add(pipes[1])

            bird_group.update()
            ground_group.update()
            pipe_group.update()

            bird_group.draw(screen)
            pipe_group.draw(screen)
            ground_group.draw(screen)

            text = font.render(f'Alive Birds: {active_birds}', True, (255, 255, 255))
            screen.blit(text, (10, 10))

            leaderboard_bg_color = (0, 0, 0)
            show_leaderboard(screen, curr_scores, cumulative_scores, font, colors)

            pygame.display.update()

            crashed_birds = pygame.sprite.groupcollide(bird_group, ground_group, False, False, pygame.sprite.collide_mask) or \
                            pygame.sprite.groupcollide(bird_group, pipe_group, False, False, pygame.sprite.collide_mask)

            for bird in birds:
                if bird.rect[1] < 0:
                    reward = over_flow
                    active_birds -= 1
                    bird_group.remove(bird)
                    birds.remove(bird)

            if crashed_birds:
                reward = crash
                active_birds -= len(crashed_birds)
                for bird in crashed_birds.keys():
                    bird_group.remove(bird)

            elif any(bird.rect[1] < 0 for bird in birds):
                reward = over_flow
                active_birds -= len([bird for bird in birds if bird.rect[1] < 0])
                for bird in birds:
                    if bird.rect[1] < 0:
                        bird_group.remove(bird)

            else:
                # Check if any bird has passed through a pipe
                if pipe_group.sprites()[0].rect[0] < birds[0].rect[0] and flag_:
                    score += 1
                    flag_ = False
                    peak_score = max(peak_score, score)
                    reward = score_rew
                elif pipe_group.sprites()[0].rect[0] > birds[0].rect[0]:
                    flag_ = True
                    reward = 15
                else:
                    reward = 15

            for bird in bird_group:
                obs = (imp(pipe_group.sprites()[1].rect[0]), imp(pipe_group.sprites()[0].rect[1] - bird.rect[1]))
                try: alpha = 1 / (1 + q_table[obs][2])
                except: alpha = 0.5
                new_obs = (imp(pipe_group.sprites()[1].rect[0]), pipe_group.sprites()[0].rect[1] - disc_pos(bird.rect[1]))
                max_future_q = np.max(q_table[new_obs][:2])
                current_q = q_table[obs][action]
                new_q = (1 - alpha) * current_q + alpha * (reward + discount * max_future_q)
                q_table[obs][action] = new_q
                total_reward += reward

            if active_birds == 0:
                pygame.mixer.music.load(hit)
                pygame.mixer.music.play()
                time.sleep(2)
                break

            alive_birds = len(birds)
            
            for bird in bird_group:
                curr_scores[bird.index] = score

            show_leaderboard(screen, curr_scores, cumulative_scores, font, colors)
            
    for _ in range(n):
        cumulative_scores[_] += curr_scores[_]

    scores.append(score)
    print(f"{i + 1}th Episode: Reward = {total_reward}, Peak Score = {peak_score}, Score = {score}, Rolling Average = {round(np.mean(scores[-200:]), 4)}")
    epsilon *= epsilon_decay

