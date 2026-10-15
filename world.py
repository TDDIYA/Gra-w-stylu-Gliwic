import math
import random

import pygame

from . import settings
from .data import LEVELS
from .settings import GROUND_Y, HEIGHT, WIDTH, WORLD_WIDTH


def _generate_level(rng, level_index):
    platforms = []
    x = 0
    while x < WORLD_WIDTH:
        floor_width = rng.randint(245, 340)
        floor_width = min(floor_width, WORLD_WIDTH - x)
        floor = pygame.Rect(x, GROUND_Y, floor_width, HEIGHT - GROUND_Y + 20)
        platforms.append(floor)
        x += floor_width
        if x >= WORLD_WIDTH:
            break

        remaining = WORLD_WIDTH - x
        if remaining <= 360:
            floor.width += remaining
            break

        gap_width = min(rng.randint(145, 180), remaining - 220)
        first_x = x + rng.randint(5, 18)
        first_y = rng.choice((470, 480, 485))
        first_width = rng.randint(68, 84)
        second_x = first_x + rng.randint(76, 91)
        second_y = first_y - rng.randint(42, 58)
        second_width = rng.randint(64, 82)
        platforms.append(pygame.Rect(first_x, first_y, first_width, 18))
        platforms.append(pygame.Rect(second_x, second_y, second_width, 18))
        x += gap_width

    if level_index == 1:
        tower_area = pygame.Rect(1120, 35, 240, 470)
        platforms = [
            platform
            for platform in platforms
            if platform.height > 20 or not platform.colliderect(tower_area)
        ]
        tower_steps = [
            (1150, 475), (1240, 415), (1150, 355), (1240, 295),
            (1150, 235), (1240, 175), (1150, 115), (1240, 55),
        ]
        platforms.extend(pygame.Rect(step_x, y, 90, 18) for step_x, y in tower_steps)

    floors = [platform for platform in platforms if platform.height > 20]
    spike_floors = [floor for floor in floors if floor.left >= 300 and floor.right <= WORLD_WIDTH - 220]
    spike_floors = rng.sample(spike_floors, min(3, len(spike_floors)))
    spikes = []
    for floor in spike_floors:
        spike_x = rng.randint(floor.left + 70, floor.right - 54)
        spikes.append(pygame.Rect(spike_x, floor.top - 24, 42, 24))

    if level_index in _small_spike_levels:
        small_spike_platforms = [
            platform for platform in platforms
            if platform.height <= 20
            and platform.width >= 66
            and 300 <= platform.left <= WORLD_WIDTH - 300
            and not (level_index == 1 and pygame.Rect(1120, 35, 240, 470).colliderect(platform))
        ]
        for platform in rng.sample(small_spike_platforms, min(2, len(small_spike_platforms))):
            spikes.append(
                pygame.Rect(platform.centerx - 13, platform.top - 15, 26, 15)
            )

    coins = []
    for platform in platforms:
        if platform.left < 0:
            continue
        if platform.height > 20:
            count = 2 if platform.width > 290 else 1
            for coin_index in range(count):
                if count == 2 and coin_index == 0:
                    coin_x = rng.randint(platform.left + 30, platform.left + 65)
                elif count == 2:
                    coin_x = rng.randint(platform.right - 80, platform.right - 48)
                else:
                    coin_x = rng.randint(platform.left + 30, platform.right - 48)
                coins.append((coin_x, platform.top - 34))
        elif rng.random() < 0.72:
            coins.append((platform.centerx - 12, platform.top - 34))

    crystal_platforms = [
        platform for platform in platforms
        if platform.height <= 20 and 500 <= platform.centerx <= WORLD_WIDTH - 500
        and platform.top >= 350
    ]
    crystal_platform = rng.choice(crystal_platforms)
    crystal = (crystal_platform.centerx - 15, crystal_platform.top - 37)
    if level_index == 1:
        crystal = (1270, 14)

    return platforms, coins, crystal, spikes


_world_rng = random.Random()
_small_spike_levels = set(_world_rng.sample(range(len(LEVELS)), 2))
_generated_worlds = [_generate_level(_world_rng, index) for index in range(len(LEVELS))]
LEVEL_PLATFORMS = [world[0] for world in _generated_worlds]
COIN_SPOTS_BY_LEVEL = [world[1] for world in _generated_worlds]
CRYSTAL_SPOTS = [world[2] for world in _generated_worlds]
SPIKES_BY_LEVEL = [world[3] for world in _generated_worlds]
RED_CRYSTAL_PLATFORM = pygame.Rect(115, 205, 190, 18)
LEVEL_PLATFORMS[2].append(RED_CRYSTAL_PLATFORM)
RED_CRYSTAL_SPOT = (RED_CRYSTAL_PLATFORM.centerx - 15, RED_CRYSTAL_PLATFORM.top - 40)


def move_player(
    player,
    velocity_y,
    dt,
    moving_left,
    moving_right,
    jump_pressed,
    on_ground,
    platforms,
    min_x=0,
    speed_multiplier=1.0,
    jetpack_active=False,
):
    speed = 270 * speed_multiplier
    if moving_left:
        player.x -= round(speed * dt)
    if moving_right:
        player.x += round(speed * dt)
    player.x = max(min_x, min(WORLD_WIDTH - player.width, player.x))

    if jump_pressed and on_ground:
        velocity_y = -520
        on_ground = False

    if jetpack_active:
        velocity_y = -360
        on_ground = False

    velocity_y += 1250 * dt
    previous_bottom = player.bottom
    player.y += round(velocity_y * dt)
    on_ground = False
    for platform in platforms:
        inset = min(12, platform.width // 5)
        hitbox = pygame.Rect(platform.x + inset, platform.y, platform.width - inset * 2, platform.height)
        crossed_top = previous_bottom <= hitbox.top and player.bottom >= hitbox.top
        overlaps_horizontally = player.right > hitbox.left and player.left < hitbox.right
        if overlaps_horizontally and crossed_top and velocity_y >= 0:
            player.bottom = platform.top
            velocity_y = 0
            on_ground = True
    if player.top > HEIGHT:
        return velocity_y, on_ground, True
    return velocity_y, on_ground, False


def reset_player_position(player, start_x, ground_y):
    player.x = start_x
    player.bottom = ground_y
    return 0, True, 0, 0


def collect_items(player, level_index, collected_coins, fragments):
    xp_gained = 0
    messages = []
    for coin_index, spot in enumerate(COIN_SPOTS_BY_LEVEL[level_index]):
        coin_rect = pygame.Rect(spot[0], spot[1], 24, 24)
        if coin_index not in collected_coins and player.colliderect(coin_rect):
            collected_coins.add(coin_index)
            xp_gained += 10
            messages.append("+10 XP, -0,5 s — zebrano monetę!")

    crystal_spot = CRYSTAL_SPOTS[level_index]
    crystal_rect = pygame.Rect(crystal_spot[0], crystal_spot[1], 30, 40)
    if level_index not in fragments and player.colliderect(crystal_rect):
        fragments.add(level_index)
        xp_gained += 50
        messages.append("+50 XP — zdobyto fragment Kryształu Wiedzy!")
    return xp_gained, messages


def reset_current_level_coins(coins_collected, level_index, xp):
    coins_lost = len(coins_collected[level_index])
    coins_collected[level_index].clear()
    return max(0, xp - coins_lost * 10), coins_lost


def get_level_birds(time_ms, level_index):
    t = time_ms / 1000
    offset = level_index * 173
    return [
        pygame.Rect(round(180 + ((t * 135 + offset) % (WORLD_WIDTH - 220))), round(230 + math.sin(t * 1.5 + level_index) * 105), 30, 18),
        pygame.Rect(round(WORLD_WIDTH - 200 - ((t * 105 + offset * 2) % (WORLD_WIDTH - 220))), round(345 + math.sin(t * 1.2 + 1.5) * 95), 30, 18),
        pygame.Rect(round(220 + ((t * 90 + offset * 3) % (WORLD_WIDTH - 260))), round(150 + math.sin(t * 1.7 + 3 + level_index) * 65), 30, 18),
    ]


def update_bombs(bombs, dt, platforms, player):
    remaining = []
    explosions = []
    player_hit = False
    for bomb, speed in bombs:
        previous_bottom = bomb.bottom
        bomb.y += round(speed * dt)
        impact_y = None
        for platform in platforms:
            crossed_platform = previous_bottom <= platform.top <= bomb.bottom
            if crossed_platform and bomb.right > platform.left and bomb.left < platform.right:
                impact_y = platform.top
                break
        if impact_y is None and bomb.top > HEIGHT:
            continue
        if impact_y is not None or bomb.colliderect(player):
            center_y = impact_y if impact_y is not None else bomb.centery
            blast = pygame.Rect(bomb.centerx - 40, center_y - 40, 80, 80)
            explosions.append(blast)
            if blast.colliderect(player):
                player_hit = True
        else:
            remaining.append((bomb, speed))
    return remaining, explosions, player_hit


def toggle_fullscreen(fullscreen):
    if fullscreen:
        settings.WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
    else:
        desktop_width, desktop_height = pygame.display.get_desktop_sizes()[0]
        settings.WINDOW = pygame.display.set_mode(
            (desktop_width, desktop_height),
            pygame.FULLSCREEN,
        )
    settings.SCALED_FRAME = pygame.Surface((WIDTH, HEIGHT))
    return not fullscreen


def logical_mouse_position(position):
    window_width, window_height = settings.WINDOW.get_size()
    scale = min(window_width / WIDTH, window_height / HEIGHT)
    rendered_width = round(WIDTH * scale)
    rendered_height = round(HEIGHT * scale)
    offset_x = (window_width - rendered_width) // 2
    offset_y = (window_height - rendered_height) // 2
    x = round((position[0] - offset_x) / scale)
    y = round((position[1] - offset_y) / scale)
    return max(0, min(WIDTH - 1, x)), max(0, min(HEIGHT - 1, y))


def present_frame():
    window_width, window_height = settings.WINDOW.get_size()
    scale = min(window_width / WIDTH, window_height / HEIGHT)
    rendered_size = (round(WIDTH * scale), round(HEIGHT * scale))
    if settings.SCALED_FRAME.get_size() != rendered_size:
        settings.SCALED_FRAME = pygame.Surface(rendered_size)
    pygame.transform.smoothscale(settings.SCREEN, rendered_size, settings.SCALED_FRAME)
    settings.WINDOW.fill((0, 0, 0))
    settings.WINDOW.blit(
        settings.SCALED_FRAME,
        ((window_width - rendered_size[0]) // 2, (window_height - rendered_size[1]) // 2),
    )
    pygame.display.flip()
