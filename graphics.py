import math
from pathlib import Path

import pygame

from . import settings
from .data import LEVELS, SKINS, discounted_shop_price
from .settings import *
from .world import (
    COIN_SPOTS_BY_LEVEL,
    CRYSTAL_SPOTS,
    LEVEL_PLATFORMS,
    RED_CRYSTAL_SPOT,
    SPIKES_BY_LEVEL,
    get_level_birds,
)


def _load_backgrounds():
    filenames = (
        "palmhouse.jpg",
        "radio_tower.jpg",
        "market_square.jpg",
        "polytechnic.jpg",
        "computer_lab.jpg",
    )
    backgrounds = []
    background_dir = Path(__file__).resolve().parent.parent / "assets" / "backgrounds"
    for filename in filenames:
        path = background_dir / filename
        image = pygame.image.load(path).convert()
        scale = max(WIDTH / image.get_width(), HEIGHT / image.get_height())
        size = (round(image.get_width() * scale), round(image.get_height() * scale))
        image = pygame.transform.smoothscale(image, size)
        crop = pygame.Rect(0, 0, WIDTH, HEIGHT)
        crop.center = image.get_rect().center
        background = image.subsurface(crop).copy()
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((13, 23, 36, 95))
        background.blit(shade, (0, 0))
        backgrounds.append(background)
    return backgrounds


PHOTO_BACKGROUNDS = _load_backgrounds()

def draw_text(surface, text, font, color, position, center=False):
    image = font.render(text, True, color)
    rect = image.get_rect()
    if center:
        rect.center = position
    else:
        rect.topleft = position
    surface.blit(image, rect)
    return rect


def draw_outlined_text(surface, text, font, color, outline_color, position, center=False):
    image = font.render(text, True, color)
    rect = image.get_rect()
    if center:
        rect.center = position
    else:
        rect.topleft = position
    outline = font.render(text, True, outline_color)
    for offset_x, offset_y in (
        (-2, -2), (0, -2), (2, -2),
        (-2, 0),             (2, 0),
        (-2, 2),  (0, 2),  (2, 2),
    ):
        surface.blit(outline, rect.move(offset_x, offset_y))
    surface.blit(image, rect)
    return rect


def wrap_text(text, font, max_width):
    lines = []
    line = ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if font.size(candidate)[0] <= max_width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def draw_wrapped(surface, text, font, color, x, y, max_width, line_height=None):
    line_height = line_height or font.get_linesize()
    for line in wrap_text(text, font, max_width):
        draw_text(surface, line, font, color, (x, y))
        y += line_height
    return y


def draw_panel(surface, rect, color=(255, 255, 255), border=GOLD):
    pygame.draw.rect(surface, (0, 0, 0, 70), rect.move(0, 5), border_radius=18)
    pygame.draw.rect(surface, color, rect, border_radius=18)
    pygame.draw.rect(surface, border, rect, 3, border_radius=18)


def draw_button(surface, rect, label, active=True, selected=False):
    color = (68, 111, 150) if active else (84, 91, 102)
    if selected:
        color = (75, 143, 112)
    pygame.draw.rect(surface, color, rect, border_radius=12)
    pygame.draw.rect(surface, (220, 229, 235), rect, 2, border_radius=12)
    draw_text(surface, label, SMALL_FONT, WHITE, rect.center, center=True)


def draw_player(surface, rect, golden=False, skin_color=None, walking=False, walk_phase=0, jetpack=False, jetpack_active=False):
    body_color = GOLD if golden else (skin_color or BLUE)
    bob = round(math.sin(walk_phase * 2) * 2) if walking else 0
    sprite = pygame.Surface((40, 54), pygame.SRCALPHA)
    if jetpack:
        backpack = pygame.Rect(0, 22 + bob, 13, 20)
        pygame.draw.rect(sprite, (115, 127, 139), backpack, border_radius=4)
        pygame.draw.rect(sprite, (206, 216, 224), backpack, 2, border_radius=4)
        pygame.draw.rect(sprite, (85, 96, 107), (backpack.x - 2, backpack.bottom - 3, 5, 7), border_radius=2)
        if jetpack_active:
            pygame.draw.polygon(
                sprite,
                (255, 166, 55),
                [(backpack.x, backpack.bottom + 2), (backpack.x + 2, backpack.bottom + 13), (backpack.x + 5, backpack.bottom + 2)],
            )
    body = pygame.Rect(5, 17 + bob, 30, 33)
    pygame.draw.rect(sprite, body_color, body, border_radius=8)
    pygame.draw.circle(sprite, (255, 218, 184), (20, 11 + bob), 12)
    leg_swing = round(math.sin(walk_phase * 2) * 5) if walking else 0
    pygame.draw.line(sprite, (50, 71, 101), (14, 45 + bob), (13 - leg_swing, 53), 6)
    pygame.draw.line(sprite, (50, 71, 101), (27, 45 + bob), (28 + leg_swing, 53), 6)
    pygame.draw.circle(sprite, INK, (24, 10 + bob), 2)
    if rect.size != sprite.get_size():
        sprite = pygame.transform.smoothscale(sprite, rect.size)
    surface.blit(sprite, rect.topleft)


def draw_background(surface, level_index):
    level = LEVELS[level_index]
    surface.blit(PHOTO_BACKGROUNDS[level_index], (0, 0))
    draw_text(surface, level["name"].upper(), SMALL_FONT, WHITE, (24, 25))

def draw_guide(surface, level, rect, solved):
    color = level["color"]
    pygame.draw.ellipse(surface, (0, 0, 0, 60), (rect.x - 8, rect.bottom - 3, rect.width + 16, 12))
    pygame.draw.rect(surface, color, rect, border_radius=9)
    pygame.draw.circle(surface, (255, 220, 185), (rect.centerx, rect.y + 11), 11)
    pygame.draw.circle(surface, INK, (rect.centerx + 4, rect.y + 10), 2)
    pygame.draw.rect(surface, GOLD if solved else WHITE, (rect.x + 8, rect.y + 31, 24, 7), border_radius=3)
    pygame.draw.rect(surface, GOLD, (rect.x + 9, rect.y + 43, 22, 14), border_radius=4)
    if solved:
        draw_text(surface, "✓", BIG_FONT, GOLD, (rect.right + 3, rect.y - 6))
    else:
        draw_text(surface, "?", BIG_FONT, WHITE, (rect.right + 3, rect.y - 6))


def draw_menu(surface):
    surface.fill(NAVY)
    for radius, alpha in [(250, 20), (175, 28), (100, 38)]:
        glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (90, 158, 224, alpha), (radius, radius), radius)
        surface.blit(glow, (WIDTH // 2 - radius, 150 - radius))
    draw_text(surface, "MISJA GLIWICE", TITLE_FONT, WHITE, (WIDTH // 2, 100), center=True)
    draw_text(surface, "STRAŻNICY WIEDZY", BIG_FONT, GOLD, (WIDTH // 2, 148), center=True)
    pygame.draw.polygon(surface, (111, 192, 242), [(480, 205), (510, 235), (480, 268), (450, 235)])
    pygame.draw.polygon(surface, (217, 243, 255), [(480, 216), (499, 235), (480, 256), (461, 235)])
    draw_text(surface, "Kryształ Wiedzy rozpadł się na pięć fragmentów.", FONT, WHITE, (WIDTH // 2, 325), center=True)
    draw_text(surface, "Odwiedź gliwickie miejsca, rozwiązuj quizy i odzyskaj wszystkie.", SMALL_FONT, (210, 220, 233), (WIDTH // 2, 359), center=True)
    draw_button(surface, pygame.Rect(325, 405, 310, 60), "ENTER — rozpocznij przygodę")
    draw_button(surface, pygame.Rect(370, 475, 220, 42), "O — ustawienia")
    draw_text(surface, "← → / A D — ruch   •   SPACJA — skok   •   E — rozmowa   •   F11 — fullscreen", SMALL_FONT, (210, 220, 233), (WIDTH // 2, 550), center=True)
    draw_text(surface, "M — mapa   •   ESC — powrót", SMALL_FONT, (210, 220, 233), (WIDTH // 2, 578), center=True)


def draw_map(surface, unlocked, solved, fragments, xp, exploration, final_completed, coin_balance):
    surface.fill((31, 47, 69))
    draw_text(surface, "MAPA GLIWIC", TITLE_FONT, WHITE, (WIDTH // 2, 54), center=True)
    draw_text(surface, f"XP: {xp}     Fragmenty kryształu: {len(fragments)}/5", FONT, GOLD, (WIDTH // 2, 104), center=True)
    draw_text(surface, f"Monety: {coin_balance}", SMALL_FONT, GOLD, (WIDTH - 110, 125), center=True)
    draw_text(surface, "Moneta: −0,5 s • Śmierć: +5 s", FONT, (235, 241, 247), (WIDTH // 2, 178), center=True)
    draw_button(surface, pygame.Rect(775, 95, 150, 42), "S — sklep", True, True)
    if exploration:
        draw_text(surface, "TRYB EKSPLORACJI — wszystkie lokacje są dostępne", SMALL_FONT, (182, 220, 191), (WIDTH // 2, 135), center=True)
    earned_badges = [LEVELS[index]["badge"] for index in sorted(solved)]
    if earned_badges:
        draw_text(surface, "Odznaki: " + "  •  ".join(earned_badges), SMALL_FONT, (221, 226, 233), (WIDTH // 2, 153), center=True)
    points = [(155, 285), (315, 210), (480, 310), (645, 210), (810, 285)]
    for first, second in zip(points, points[1:]):
        pygame.draw.line(surface, (129, 151, 174), first, second, 7)
    for index, (point, level) in enumerate(zip(points, LEVELS)):
        active = index < unlocked or exploration
        color = level["color"] if active else (82, 91, 103)
        pygame.draw.circle(surface, color, point, 38)
        pygame.draw.circle(surface, GOLD if index in fragments else WHITE, point, 38, 3)
        draw_text(surface, str(index + 1), BIG_FONT, WHITE, point, center=True)
        label_y = point[1] + 54
        for line_index, line in enumerate(wrap_text(level["name"], SMALL_FONT, 145)):
            draw_text(surface, line, SMALL_FONT, WHITE if active else (158, 162, 168), (point[0], label_y + line_index * 18), center=True)
        if index in solved:
            draw_text(surface, "UKOŃCZONE", SMALL_FONT, GOLD, (point[0], label_y + 38), center=True)
        elif not active:
            draw_text(surface, "ZABLOKOWANE", SMALL_FONT, (180, 184, 190), (point[0], label_y + 38), center=True)
    if len(solved) == len(LEVELS) and len(fragments) == len(LEVELS) and not final_completed:
        draw_button(surface, pygame.Rect(340, 465, 280, 54), "F — finał przy Radiostacji", True, True)
    elif len(solved) == len(LEVELS) and len(fragments) < len(LEVELS):
        draw_text(surface, "Zbierz fragment kryształu w każdej lokacji, aby odblokować finał.", SMALL_FONT, GOLD, (WIDTH // 2, 490), center=True)
    elif final_completed:
        draw_text(surface, "FINAŁ UKOŃCZONY — Ambasador Gliwic", SMALL_FONT, GOLD, (WIDTH // 2, 490), center=True)
    draw_text(surface, "Wybierz lokację 1–5 • S — sklep skórek • F — finał po zebraniu kryształów", SMALL_FONT, (210, 220, 233), (WIDTH // 2, 572), center=True)


def draw_settings(surface, music_enabled, sounds_enabled):
    surface.fill((31, 47, 69))
    draw_text(surface, "USTAWIENIA", TITLE_FONT, WHITE, (WIDTH // 2, 115), center=True)
    draw_text(surface, "Przełączniki są gotowe — dźwięki dodamy później.", SMALL_FONT, (210, 220, 233), (WIDTH // 2, 165), center=True)
    draw_button(surface, pygame.Rect(270, 245, 420, 62), f"M — muzyka: {'WŁ.' if music_enabled else 'WYŁ.'}")
    draw_button(surface, pygame.Rect(270, 330, 420, 62), f"D — dźwięki: {'WŁ.' if sounds_enabled else 'WYŁ.'}")
    draw_button(surface, pygame.Rect(325, 440, 310, 56), "ESC — powrót do menu")


def draw_shop(
    surface,
    coins,
    owned_skins,
    selected_skin,
    secret_skin_found,
    shop_message="",
    speed_boost_owned=False,
    jetpack_equipped=False,
):
    surface.fill((31, 47, 69))
    draw_text(surface, "SKLEP SKÓREK I ULEPSZEŃ", TITLE_FONT, WHITE, (WIDTH // 2, 65), center=True)
    draw_text(surface, f"Twój portfel: {coins} monet", FONT, GOLD, (WIDTH // 2, 115), center=True)
    cards = []
    for index, skin in enumerate(SKINS):
        x = 28 + index * 184
        rect = pygame.Rect(x, 190, 168, 235)
        cards.append(rect)
        draw_panel(surface, rect, (246, 245, 236), GOLD if index == selected_skin else skin["color"])
        preview = pygame.Rect(x + 64, 225, 40, 54)
        draw_player(surface, preview, skin_color=skin["color"])
        draw_text(surface, skin["name"], SMALL_FONT, INK, (rect.centerx, 310), center=True)
        is_secret = skin.get("secret", False)
        if is_secret and index not in owned_skins and not secret_skin_found:
            label = "SEKRET: POZIOM 3"
            available = False
        else:
            price = discounted_shop_price(skin["cost"])
            label = "WYBRANA" if selected_skin == index else ("POSIADANA" if index in owned_skins else f"{price} monet")
            available = index in owned_skins or coins >= price
        draw_button(surface, pygame.Rect(x + 8, 350, 152, 46), label, available)
    speed_rect = pygame.Rect(115, 445, 335, 58)
    jetpack_rect = pygame.Rect(510, 445, 335, 58)
    draw_button(
        surface,
        speed_rect,
        "SPEED BOOST — POSIADANY" if speed_boost_owned else "SPEED BOOST — 10 MONET",
        speed_boost_owned or coins >= discounted_shop_price(20),
        speed_boost_owned,
    )
    draw_button(
        surface,
        jetpack_rect,
        "JETPACK — ZAŁOŻONY" if jetpack_equipped else "JETPACK — 24 MONETY",
        jetpack_equipped or coins >= discounted_shop_price(50),
        jetpack_equipped,
    )
    pizza_rect = pygame.Rect(310, 510, 340, 48)
    draw_button(surface, pizza_rect, "PIZZA KSIĄŻULA — 15 MONET", coins >= 15)
    if shop_message:
        draw_text(surface, shop_message, SMALL_FONT, GOLD, (WIDTH // 2, 572), center=True)
    draw_text(surface, "6/7/8: zakupy • F: boost • SPACJA: jetpack • ESC/M: mapa", SMALL_FONT, (210, 220, 233), (WIDTH // 2, 608), center=True)
    return cards, speed_rect, jetpack_rect, pizza_rect


def _draw_wheel_segment(surface, center, radius, start_angle, end_angle, color):
    points = [center]
    steps = 32
    points.extend(
        (
            round(center[0] + math.cos(math.radians(start_angle + (end_angle - start_angle) * i / steps)) * radius),
            round(center[1] + math.sin(math.radians(start_angle + (end_angle - start_angle) * i / steps)) * radius),
        )
        for i in range(steps + 1)
    )
    pygame.draw.polygon(surface, color, points)


def draw_pizza_wheel(surface, elapsed_ms, outcome):
    surface.fill((25, 36, 54))
    draw_text(surface, "PIZZA KSIĄŻULA — KOŁO FORTUNY", TITLE_FONT, WHITE, (WIDTH // 2, 72), center=True)
    center = (WIDTH // 2, HEIGHT // 2 + 15)
    radius = 175
    progress = min(1, max(0, elapsed_ms / 3500))
    eased_progress = 1 - (1 - progress) ** 4
    segment_centers = {
        "positive": 88.2,
        "negative": 264.6,
        "win": 356.4,
    }
    final_angle = 8 * 360 + ((-90 - segment_centers[outcome]) % 360)
    angle = final_angle * eased_progress
    positive_end = 176.4
    negative_end = 352.8
    _draw_wheel_segment(surface, center, radius, angle, angle + positive_end, (59, 174, 104))
    _draw_wheel_segment(surface, center, radius, angle + positive_end, angle + negative_end, (213, 66, 66))
    _draw_wheel_segment(surface, center, radius, angle + negative_end, angle + 360, (255, 211, 63))
    pygame.draw.circle(surface, (245, 235, 201), center, radius, 5)
    for label, degrees in (
        ("EFEKT POZYTYWNY — 49%", angle + segment_centers["positive"]),
        ("EFEKT NEGATYWNY — 49%", angle + segment_centers["negative"]),
    ):
        label_center = (
            round(center[0] + math.cos(math.radians(degrees)) * radius * 0.57),
            round(center[1] + math.sin(math.radians(degrees)) * radius * 0.57),
        )
        draw_text(surface, label, SMALL_FONT, WHITE, label_center, center=True)
    draw_text(surface, "WYGRANA 2%", SMALL_FONT, (255, 225, 119), (WIDTH - 105, center[1] - 5), center=True)
    pygame.draw.circle(surface, (255, 215, 94), center, 17)
    pygame.draw.polygon(
        surface,
        (255, 215, 94),
        [(center[0], center[1] - radius - 26), (center[0] - 17, center[1] - radius - 2), (center[0] + 17, center[1] - radius - 2)],
    )
    draw_text(surface, "Losowanie trwa...", FONT, WHITE, (WIDTH // 2, HEIGHT - 55), center=True)


def draw_pizza_result(surface, outcome):
    surface.fill((25, 36, 54))
    panel = pygame.Rect(50, 235, WIDTH - 100, 170)
    pygame.draw.rect(surface, (12, 18, 28), panel, border_radius=18)
    pygame.draw.rect(surface, (76, 88, 106), panel, 2, border_radius=18)
    if outcome == "win":
        draw_outlined_text(
            surface,
            "WYGRAŁEŚ!",
            BIG_FONT,
            (255, 220, 54),
            (0, 0, 0),
            (WIDTH // 2, panel.centery),
            center=True,
        )
        return
    lines = (
        ("OTRZYMAŁEŚ EFEKT POZYTYWNY,", "ODDAŁEŚ PIZZE SWOJEJ BABCI I ZOSTAŁEŚ POMNIEJSZONY")
        if outcome == "positive"
        else ("OTRZYMAŁEŚ EFEKT NEGATYWNY,", "ZJADŁEŚ PIZZE I ZOSTAŁEŚ POSZERZONY")
    )
    color = (74, 226, 113) if outcome == "positive" else (242, 65, 65)
    draw_outlined_text(surface, lines[0], FONT, color, (0, 0, 0), (WIDTH // 2, 290), center=True)
    draw_outlined_text(surface, lines[1], FONT, color, (0, 0, 0), (WIDTH // 2, 342), center=True)


def draw_coin(surface, rect, time_ms, camera_x, camera_y=0):
    screen_rect = rect.move(-camera_x, -camera_y)
    if not screen_rect.colliderect(pygame.Rect(0, 0, WIDTH, HEIGHT)):
        return
    width = max(5, round(12 * abs(math.sin(time_ms / 180))))
    pygame.draw.ellipse(surface, (169, 113, 34), screen_rect.move(2, 3).inflate(-4, -2))
    pygame.draw.ellipse(surface, (255, 208, 64), (screen_rect.centerx - width // 2, screen_rect.y, width, screen_rect.height))
    if width > 7:
        pygame.draw.ellipse(surface, (255, 239, 147), (screen_rect.centerx - 2, screen_rect.y + 4, 4, screen_rect.height - 8))


def draw_crystal(surface, rect, camera_x, camera_y=0, color=(73, 216, 244)):
    screen_rect = rect.move(-camera_x, -camera_y)
    if not screen_rect.colliderect(pygame.Rect(0, 0, WIDTH, HEIGHT)):
        return
    points = [
        (screen_rect.centerx, screen_rect.top),
        (screen_rect.right, screen_rect.y + 11),
        (screen_rect.centerx + 5, screen_rect.bottom),
        (screen_rect.left, screen_rect.y + 17),
    ]
    pygame.draw.polygon(surface, color, points)
    pygame.draw.polygon(surface, (222, 252, 255), points, 2)
    pygame.draw.line(surface, (194, 248, 255), (screen_rect.centerx, screen_rect.y + 4), (screen_rect.centerx, screen_rect.bottom - 4), 2)


def draw_radio_tower(surface, camera_x, camera_y=0):
    left = 1220 - camera_x
    right = 1330 - camera_x
    top = 52 - camera_y
    bottom = GROUND_Y - camera_y
    pygame.draw.line(surface, (114, 74, 48), (left, bottom), (left + 5, top + 12), 12)
    pygame.draw.line(surface, (114, 74, 48), (right, bottom), (right - 5, top + 12), 12)
    pygame.draw.line(surface, (187, 133, 83), (left + 13, bottom), (left + 18, top + 12), 5)
    pygame.draw.line(surface, (187, 133, 83), (right - 13, bottom), (right - 18, top + 12), 5)
    for y in range(top + 25, bottom, 32):
        span = (right - left) * (y - top) / (bottom - top)
        left_edge = left + (right - left - span) / 2
        right_edge = right - (right - left - span) / 2
        pygame.draw.line(surface, (180, 126, 77), (left_edge, y), (right_edge, y), 5)
        if y + 32 < bottom:
            pygame.draw.line(surface, (145, 93, 59), (left_edge, y), (right_edge, y + 32), 3)
            pygame.draw.line(surface, (145, 93, 59), (right_edge, y), (left_edge, y + 32), 3)
    pygame.draw.line(surface, (93, 73, 61), (left + 55, top + 10), (left + 55, 18), 4)
    draw_text(surface, "WIEŻA", SMALL_FONT, WHITE, (left + 25, bottom + 17), center=True)


def draw_bird(surface, rect, camera_x, camera_y=0, direction=1):
    bird_surface = pygame.Surface((34, 24), pygame.SRCALPHA)
    wing_lift = round(math.sin(pygame.time.get_ticks() / 75 + rect.x) * 6)
    pygame.draw.ellipse(bird_surface, WHITE, (3, 8, 20, 10))
    pygame.draw.circle(bird_surface, WHITE, (24, 10), 5)
    pygame.draw.polygon(bird_surface, WHITE, [(27, 9), (33, 11), (27, 13)])
    pygame.draw.polygon(bird_surface, (223, 229, 237), [(10, 11), (2, 4 - wing_lift), (17, 8)])
    pygame.draw.circle(bird_surface, INK, (25, 9), 1)
    if direction < 0:
        bird_surface = pygame.transform.flip(bird_surface, True, False)
    surface.blit(
        bird_surface,
        (rect.centerx - camera_x - 17, rect.centery - camera_y - 12),
    )


def draw_spikes(surface, spikes, camera_x, camera_y=0):
    for spike in spikes:
        visible = spike.move(-camera_x, -camera_y)
        if visible.right < 0 or visible.left > WIDTH:
            continue
        points = [
            (visible.left, visible.bottom),
            (visible.left + visible.width // 2, visible.top),
            (visible.right, visible.bottom),
        ]
        pygame.draw.polygon(surface, (190, 207, 218), points)
        pygame.draw.polygon(surface, (49, 60, 73), points, 2)


def draw_bombs(surface, bombs, camera_x, camera_y=0):
    for bomb, _speed in bombs:
        visible = bomb.move(-camera_x, -camera_y)
        if not visible.colliderect(pygame.Rect(0, 0, WIDTH, HEIGHT)):
            continue
        pygame.draw.ellipse(surface, (42, 37, 41), visible)
        pygame.draw.ellipse(surface, (161, 53, 47), (visible.x + 3, visible.y + 2, visible.width - 6, 6))
        pygame.draw.line(
            surface,
            (235, 191, 93),
            (visible.centerx, visible.y),
            (visible.centerx + 3, visible.y - 5),
            2,
        )


def draw_explosions(surface, explosions, camera_x, camera_y, time_ms):
    for blast, expires_at in explosions:
        remaining = max(0, min(1, (expires_at - time_ms) / 320))
        center = (blast.centerx - camera_x, blast.centery - camera_y)
        radius = round(max(blast.width, blast.height) * (0.16 + 0.34 * remaining))
        pygame.draw.circle(surface, (205, 54, 35), center, radius)
        pygame.draw.circle(surface, (255, 166, 57), center, max(1, round(radius * 0.68)))
        pygame.draw.circle(surface, (255, 225, 132), center, max(1, round(radius * 0.34)))


def draw_final_map(surface, final_index, time_ms):
    surface.fill((28, 45, 64))
    map_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)
    pygame.draw.rect(surface, (50, 77, 81), map_rect)
    pygame.draw.rect(surface, (60, 89, 91), (0, 430, WIDTH, 210))
    route = [(80, 440), (220, 370), (360, 400), (500, 310), (660, 350), (830, 235)]
    pygame.draw.lines(surface, (226, 195, 117), False, route, 16)
    pygame.draw.lines(surface, (247, 226, 168), False, route, 3)
    landmarks = [
        ("PALMIARNIA", (125, 270), (65, 153, 111)),
        ("RYNEK", (340, 210), (192, 131, 87)),
        ("POLITECHNIKA", (575, 190), (102, 146, 190)),
        ("RADIOSTACJA", (815, 120), (175, 136, 89)),
    ]
    for label, center, color in landmarks:
        rect = pygame.Rect(center[0] - 58, center[1] - 32, 116, 64)
        pygame.draw.rect(surface, color, rect, border_radius=12)
        pygame.draw.rect(surface, (238, 233, 210), rect, 2, border_radius=12)
        draw_text(surface, label, SMALL_FONT, WHITE, (center[0], center[1] + 44), center=True)
    active_index = min(final_index, len(route) - 1)
    marker = route[active_index]
    pulse = 17 + round(4 * math.sin(time_ms / 160))
    pygame.draw.circle(surface, (247, 229, 164), marker, pulse + 7, 2)
    pygame.draw.circle(surface, (255, 211, 80), marker, pulse)
    pygame.draw.circle(surface, (255, 250, 224), marker, 6)
    birds = [
        pygame.Rect((time_ms // 9) % (WIDTH + 50) - 25, 165 + round(22 * math.sin(time_ms / 190)), 30, 18),
        pygame.Rect(WIDTH - (time_ms // 13) % (WIDTH + 50), 285 + round(18 * math.sin(time_ms / 230)), 30, 18),
    ]
    for index, bird in enumerate(birds):
        draw_bird(surface, bird, 0, direction=1 if index == 0 else -1)
    draw_text(surface, "WIELKI FINAŁ — TRASA OSTATNIEGO KRYSZTAŁU", SMALL_FONT, WHITE, (WIDTH // 2, 22), center=True)


def draw_play(surface, level_index, player, guide, near_guide, solved, fragments, coins_collected, coin_count, xp, golden, exploration, camera_x, spikes, skin_color, walking, walk_phase, time_ms, camera_y=0, secret_crystal=False, elapsed_seconds=None, death_count=0, jetpack_equipped=False, jetpack_fuel=0, jetpack_active=False, speed_boost_active=False):
    level = LEVELS[level_index]
    draw_background(surface, level_index)
    if level_index == 1:
        draw_radio_tower(surface, camera_x, camera_y)
    for platform in LEVEL_PLATFORMS[level_index]:
        screen_platform = platform.move(-camera_x, -camera_y)
        if screen_platform.colliderect(pygame.Rect(0, 0, WIDTH, HEIGHT)):
            pygame.draw.rect(surface, (77, 129, 86), screen_platform, border_radius=5)
            pygame.draw.rect(surface, (137, 190, 126), (screen_platform.x, screen_platform.y, screen_platform.width, 6), border_radius=4)
            if screen_platform.height > 20:
                pygame.draw.rect(surface, (105, 81, 61), (screen_platform.x, screen_platform.y + 6, screen_platform.width, screen_platform.height - 6))
    for coin_index, spot in enumerate(COIN_SPOTS_BY_LEVEL[level_index]):
        if coin_index not in coins_collected:
            draw_coin(surface, pygame.Rect(spot[0], spot[1], 24, 24), pygame.time.get_ticks(), camera_x, camera_y)
    if level_index not in fragments:
        crystal = CRYSTAL_SPOTS[level_index]
        draw_crystal(surface, pygame.Rect(crystal[0], crystal[1], 30, 40), camera_x, camera_y)
    if level_index == 2 and not secret_crystal:
        draw_crystal(
            surface,
            pygame.Rect(RED_CRYSTAL_SPOT[0], RED_CRYSTAL_SPOT[1], 30, 40),
            camera_x,
            camera_y,
            (232, 54, 70),
        )
    draw_spikes(surface, spikes, camera_x, camera_y)
    birds = get_level_birds(time_ms, level_index)
    for index, bird in enumerate(birds):
        draw_bird(surface, bird, camera_x, camera_y, direction=1 if index in (0, 2) else -1)
    draw_guide(surface, level, guide.move(-camera_x, -camera_y), level_index in solved)
    player_screen = player.move(-camera_x, -camera_y)
    draw_player(
        surface,
        player_screen,
        golden,
        skin_color,
        walking,
        walk_phase,
        jetpack_equipped,
        jetpack_active,
    )
    pygame.draw.rect(surface, (28, 39, 55), (0, 0, WIDTH, 54))
    draw_text(surface, f"Śmierci: {death_count}", FONT, WHITE, (20, 15))
    draw_text(surface, level["name"], FONT, WHITE, (145, 15))
    draw_text(surface, f"Monety {coin_count}   Kryształ {len(fragments)}/5   XP {xp}", SMALL_FONT, GOLD, (WIDTH - 360, 17))
    if elapsed_seconds is not None:
        draw_text(surface, f"CZAS {format_time(elapsed_seconds)}", FONT, WHITE, (WIDTH // 2, 35), center=True)
    if speed_boost_active:
        draw_text(surface, "SPEED BOOST!", SMALL_FONT, (255, 225, 120), (WIDTH - 155, 48), center=True)
    if jetpack_equipped:
        fuel_box = pygame.Rect(player_screen.centerx - 44, player_screen.top - 44, 88, 40)
        pygame.draw.rect(surface, (25, 35, 50), fuel_box, border_radius=7)
        pygame.draw.rect(surface, WHITE, fuel_box, 1, border_radius=7)
        draw_text(surface, f"PALIWO {max(0, round(jetpack_fuel))}", SMALL_FONT, WHITE, (fuel_box.centerx, fuel_box.y + 11), center=True)
        fuel_bar = pygame.Rect(fuel_box.x + 7, fuel_box.bottom - 9, fuel_box.width - 14, 5)
        pygame.draw.rect(surface, (75, 87, 100), fuel_bar, border_radius=3)
        fuel_bar.width = round(fuel_bar.width * max(0, min(100, jetpack_fuel)) / 100)
        pygame.draw.rect(surface, (92, 218, 152), fuel_bar, border_radius=3)
    if exploration:
        draw_text(surface, "EKSPLORACJA", SMALL_FONT, (183, 224, 195), (WIDTH - 405, 18))
    hint = "Uważaj na latające ptaki i kolce!"
    if level_index == 1:
        hint += " Kryształ czeka na szczycie wieży."
    elif level_index == 2 and not secret_crystal:
        hint += " Wzleć jetpackiem na platformę na początku i zbierz czerwony kryształ."
    draw_text(surface, hint, SMALL_FONT, INK, (WIDTH // 2, 65), center=True)
    if near_guide:
        hint = "Zadanie ukończone — M: mapa" if level_index in solved else "E — porozmawiaj i rozwiąż quiz"
        pygame.draw.rect(surface, (29, 43, 61), (230, 565, 500, 42), border_radius=12)
        draw_text(surface, hint, SMALL_FONT, GOLD, (WIDTH // 2, 586), center=True)
    else:
        draw_text(surface, "← → / A D: ruch     SPACJA: skok     M: mapa", SMALL_FONT, (177, 245, 184), (WIDTH // 2, 585), center=True)


def draw_question(surface, level, question, options, question_index=None, total=None, feedback="", lives=3, coin_count=0, final_map=False, error_flash=False):
    if final_map:
        draw_final_map(surface, question_index or 0, pygame.time.get_ticks())
        header = pygame.Surface((800, 150), pygame.SRCALPHA)
        pygame.draw.rect(header, (246, 245, 236, 225), header.get_rect(), border_radius=18)
        pygame.draw.rect(header, level["color"], header.get_rect(), 3, border_radius=18)
        surface.blit(header, (80, 55))
        draw_text(surface, level["name"], BIG_FONT, INK, (WIDTH // 2, 82), center=True)
        draw_text(surface, f"Monety: {coin_count}", SMALL_FONT, INK, (105, 107))
        draw_quiz_lives(surface, lives)
        if question_index is not None:
            draw_text(surface, f"Finał — pytanie {question_index + 1}/{total}", SMALL_FONT, level["color"], (WIDTH // 2, 108), center=True)
        draw_wrapped(surface, question, FONT, INK, 125, 132, 710, 25)
        buttons = []
        for index, option in enumerate(options):
            rect = pygame.Rect(35 + index * 310, 510, 270, 86)
            pygame.draw.rect(surface, (55, 92, 126), rect, border_radius=12)
            pygame.draw.rect(surface, (220, 229, 235), rect, 2, border_radius=12)
            draw_wrapped(surface, f"{index + 1}. {option}", SMALL_FONT, WHITE, rect.x + 12, rect.y + 15, rect.width - 24, 20)
            buttons.append(rect)
        draw_text(surface, "Wybierz odpowiedź 1–3 lub kliknij punkt na trasie.", SMALL_FONT, WHITE, (WIDTH // 2, 620), center=True)
        if feedback:
            draw_text(surface, feedback, SMALL_FONT, (255, 236, 197), (WIDTH // 2, 462), center=True)
        if error_flash:
            flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash.fill((235, 24, 34, 92))
            surface.blit(flash, (0, 0))
        return buttons
    else:
        surface.fill((27, 40, 59))
    card = pygame.Rect(100, 70, 760, 500)
    draw_panel(surface, card, (246, 245, 236), level["color"])
    draw_text(surface, level["name"], BIG_FONT, INK, (WIDTH // 2, 108), center=True)
    draw_text(surface, f"Monety: {coin_count}", SMALL_FONT, INK, (155, 112))
    draw_quiz_lives(surface, lives)
    if question_index is not None:
        draw_text(surface, f"Wielki quiz — pytanie {question_index + 1}/{total}", SMALL_FONT, level["color"], (WIDTH // 2, 150), center=True)
    y = draw_wrapped(surface, question, FONT, INK, 155, 190, 650, 28)
    buttons = []
    y = max(270, y + 20)
    for index, option in enumerate(options):
        rect = pygame.Rect(155, y + index * 66, 650, 54)
        draw_button(surface, rect, f"{index + 1}. {option}")
        buttons.append(rect)
    if feedback:
        draw_wrapped(surface, feedback, SMALL_FONT, (39, 110, 78), 160, 493, 645, 20)
    draw_text(surface, "Wybierz odpowiedź klawiszem 1–3 lub kliknij przycisk. ESC — mapa.", SMALL_FONT, (95, 105, 113), (WIDTH // 2, 547), center=True)
    if error_flash:
        flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        flash.fill((235, 24, 34, 92))
        surface.blit(flash, (0, 0))
    return buttons


def draw_quiz_lives(surface, lives):
    draw_text(surface, "ŻYCIA:", SMALL_FONT, INK, (725, 112))
    for index in range(3):
        color = RED if index < lives else (194, 194, 188)
        pygame.draw.circle(surface, color, (790 + index * 22, 120), 7)


def draw_death(surface, level_name, reason, coins_lost):
    surface.fill((32, 24, 31))
    draw_text(surface, "UMARŁEŚ!", TITLE_FONT, (239, 93, 83), (WIDTH // 2, 165), center=True)
    draw_text(surface, f"{reason} w lokacji: {level_name}", FONT, WHITE, (WIDTH // 2, 220), center=True)
    draw_text(surface, "Nie trać ducha — możesz próbować bez limitu!", SMALL_FONT, (211, 204, 204), (WIDTH // 2, 265), center=True)
    draw_button(surface, pygame.Rect(305, 345, 350, 55), "R / ENTER — spróbuj ponownie")
    draw_button(surface, pygame.Rect(305, 420, 350, 55), "M — wróć na mapę")
    draw_text(surface, f"Utracono {coins_lost} monet z tej lokacji. Monety z poprzednich poziomów zostają.", SMALL_FONT, GOLD, (WIDTH // 2, 515), center=True)


def draw_reward(surface, level):
    rect = pygame.Rect(175, 68, 610, 126)
    draw_panel(surface, rect, (246, 245, 236), level["color"])
    draw_text(surface, f"+{level['xp']} XP   •   Odznaka: {level['badge']}", SMALL_FONT, INK, (rect.centerx, 95), center=True)
    draw_wrapped(surface, level["fact"], SMALL_FONT, INK, 200, 122, 560, 19)


def draw_completion(surface, xp, elapsed_seconds, adjusted_seconds, medal, thresholds, death_count, coin_count):
    surface.fill((35, 55, 76))
    certificate = pygame.Rect(115, 55, 730, 490)
    draw_panel(surface, certificate, (246, 245, 236), GOLD)
    draw_text(surface, "CERTYFIKAT UKOŃCZENIA", TITLE_FONT, (38, 58, 83), (WIDTH // 2, 100), center=True)
    pygame.draw.line(surface, (193, 160, 84), (250, 145), (710, 145), 2)
    draw_text(surface, "KRYSZTAŁ ODNOWIONY!", TITLE_FONT, (151, 101, 26), (WIDTH // 2, 175), center=True)
    draw_text(surface, "Ambasador Gliwic", BIG_FONT, (32, 49, 68), (WIDTH // 2, 213), center=True)
    draw_text(surface, f"Czas gry: {format_time(elapsed_seconds)}   •   Wynik po bonusach: {format_time(adjusted_seconds)}", FONT, (32, 49, 68), (WIDTH // 2, 258), center=True)
    draw_text(surface, f"Medal: {medal}   •   Złoty ≤ {format_time(thresholds[0])}   |   Srebrny ≤ {format_time(thresholds[1])}   |   Brązowy ≤ {format_time(thresholds[2])}", SMALL_FONT, (36, 54, 74), (WIDTH // 2, 293), center=True)
    draw_text(surface, f"Ilość śmierci: {death_count}   •   Dodany czas: +{death_count * 5} s", FONT, (32, 49, 68), (WIDTH // 2, 340), center=True)
    draw_text(surface, f"Liczba zebranych monet: {coin_count}   •   Skrócony czas: −{coin_count * 0.5:g} s", FONT, (32, 49, 68), (WIDTH // 2, 378), center=True)
    draw_text(surface, f"Nagroda: 1 000 XP   •   Łącznie XP: {xp}", FONT, (32, 49, 68), (WIDTH // 2, 430), center=True)
    if medal == "BRAK":
        draw_text(surface, "Wynik po bonusach powyżej 5:00 — tym razem bez medalu.", SMALL_FONT, (118, 53, 48), (WIDTH // 2, 466), center=True)
    draw_text(surface, "ENTER — rozpocznij tryb eksploracji", FONT, (240, 245, 250), (WIDTH // 2, 580), center=True)


def format_time(total_seconds):
    total_seconds = max(0, int(total_seconds))
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes:02}:{seconds:02}"
