import pygame
import random
import sys

from . import settings
from .data import (
    FINAL_QUESTIONS,
    BRONZE_TIME_SECONDS,
    GOLD_TIME_SECONDS,
    LEVELS,
    adjusted_run_time,
    discounted_shop_price,
    medal_for_time,
    pizza_outcome_from_roll,
    SILVER_TIME_SECONDS,
    SKINS,
)
from .graphics import *
from .settings import *
from .world import (
    COIN_SPOTS_BY_LEVEL, CRYSTAL_SPOTS, LEVEL_PLATFORMS, RED_CRYSTAL_SPOT, SPIKES_BY_LEVEL, collect_items,
    logical_mouse_position, move_player, present_frame, reset_current_level_coins,
    reset_player_position, toggle_fullscreen, get_level_birds, update_bombs,
)

def main():
    fullscreen = False
    screen = "menu"
    level_index = 0
    unlocked = 1
    solved = set()
    fragments = set()
    coins_collected = [set() for _ in LEVELS]
    coin_balance = 0
    xp = 0
    exploration = False
    final_completed = False
    final_index = 0
    quiz_feedback = ""
    music_enabled = True
    sounds_enabled = True
    owned_skins = {0}
    selected_skin = 0
    secret_skin_found = False
    shop_message = ""
    quiz_flash_until = 0
    shop_buttons = []
    speed_boost_button = pygame.Rect(0, 0, 0, 0)
    jetpack_button = pygame.Rect(0, 0, 0, 0)
    pizza_button = pygame.Rect(0, 0, 0, 0)
    speed_boost_owned = False
    speed_boost_used_levels = set()
    speed_boost_until = 0
    jetpack_equipped = False
    jetpack_fuel = 0.0
    jetpack_active = False
    player_width_scale = 1.0
    player_height_scale = 1.0
    pizza_outcome = "negative"
    pizza_wheel_started_at = 0
    pizza_result_until = 0
    bombs = []
    explosions = []
    next_bomb_drop_at = 0

    player = pygame.Rect(45, GROUND_Y - 54, 40, 54)
    guide = pygame.Rect(WORLD_WIDTH - 100, GROUND_Y - 62, 42, 62)
    velocity_y = 0
    on_ground = True
    question_buttons = []
    final_quiz = False
    level_questions = []
    level_question_index = 0
    quiz_lives = 3
    running = True
    reward_message_until = 0
    collect_message = ""
    collect_message_until = 0
    death_reason = "Spadłeś w przepaść"
    death_coins_lost = 0
    jump_buffer = 0
    coyote_time = 0
    player_start_x = 45
    run_started_at = None
    run_elapsed_seconds = 0
    run_adjusted_seconds = 0
    run_medal = ""
    run_coins_collected = 0
    run_deaths = 0
    secret_message_until = 0

    def purchase_speed_boost():
        nonlocal coin_balance, speed_boost_owned, shop_message
        if speed_boost_owned:
            shop_message = "Speed boost jest już kupiony — aktywuj go klawiszem F podczas poziomu."
        elif coin_balance >= discounted_shop_price(20):
            coin_balance -= discounted_shop_price(20)
            speed_boost_owned = True
            shop_message = "Kupiono speed boost za 10 monet! Raz na poziom aktywujesz go klawiszem F."
        else:
            shop_message = "Brakuje monet. Speed boost kosztuje teraz 10 monet."

    def purchase_jetpack():
        nonlocal coin_balance, jetpack_equipped, jetpack_fuel, shop_message
        if jetpack_equipped:
            shop_message = "Jetpack jest już założony."
        elif coin_balance >= discounted_shop_price(50):
            coin_balance -= discounted_shop_price(50)
            jetpack_equipped = True
            jetpack_fuel = 100
            shop_message = "Kupiono jetpack za 24 monety! Przytrzymaj SPACJĘ podczas poziomu, aby wzlecieć."
        else:
            shop_message = "Brakuje monet. Jetpack kosztuje teraz 24 monety."

    def purchase_pizza():
        nonlocal coin_balance, pizza_outcome, pizza_wheel_started_at, screen, shop_message
        if coin_balance < 15:
            shop_message = "Brakuje monet. Pizza Książula kosztuje 15 monet."
            return
        coin_balance -= 15
        pizza_outcome = pizza_outcome_from_roll(random.randrange(100))
        pizza_wheel_started_at = pygame.time.get_ticks()
        shop_message = ""
        screen = "pizza_wheel"

    def apply_pizza_effect():
        nonlocal player_width_scale, player_height_scale, pizza_result_until, screen
        if pizza_outcome == "positive":
            player_width_scale *= 0.5
            player_height_scale *= 0.5
        elif pizza_outcome == "negative":
            player_width_scale *= 1.5
        player.size = (
            max(1, round(40 * player_width_scale)),
            max(1, round(54 * player_height_scale)),
        )
        player.centerx = max(0, player.centerx)
        player.bottom = min(player.bottom, GROUND_Y)
        pizza_result_until = pygame.time.get_ticks() + 4500
        screen = "pizza_result"

    def current_run_time(now):
        if run_started_at is None:
            return 0
        return (now - run_started_at) / 1000

    def reset_player_state():
        nonlocal velocity_y, on_ground, jump_buffer, coyote_time
        player.size = (
            max(1, round(40 * player_width_scale)),
            max(1, round(54 * player_height_scale)),
        )
        velocity_y, on_ground, jump_buffer, coyote_time = reset_player_position(
            player,
            player_start_x,
            GROUND_Y,
        )

    def die(reason):
        nonlocal xp, coin_balance, screen, death_reason, death_coins_lost, run_deaths
        death_reason = reason
        xp, death_coins_lost = reset_current_level_coins(coins_collected, level_index, xp)
        coin_balance = max(0, coin_balance - death_coins_lost)
        run_deaths += 1
        screen = "dead"

    def enter_level(selected):
        nonlocal level_index, screen, run_started_at, next_bomb_drop_at
        level_index = selected
        if selected == 0 and run_started_at is None:
            run_started_at = pygame.time.get_ticks()
        reset_player_state()
        guide.x = WORLD_WIDTH - 100
        bombs.clear()
        explosions.clear()
        next_bomb_drop_at = pygame.time.get_ticks() + random.randint(1800, 3500)
        screen = "play"

    def restart_level():
        nonlocal screen, collect_message_until, next_bomb_drop_at
        reset_player_state()
        collect_message_until = 0
        bombs.clear()
        explosions.clear()
        next_bomb_drop_at = pygame.time.get_ticks() + random.randint(1800, 3500)
        screen = "play"

    def start_level_quiz():
        nonlocal level_questions, level_question_index, quiz_feedback, screen, quiz_lives, final_quiz
        final_quiz = False
        level_questions = []
        for source in random.sample(LEVELS[level_index]["questions"], 5):
            question = dict(source)
            options = list(question["options"])
            correct_answer = options[question["answer"]]
            random.shuffle(options)
            question["options"] = options
            question["answer"] = options.index(correct_answer)
            level_questions.append(question)
        level_question_index = 0
        quiz_lives = 3
        quiz_feedback = ""
        screen = "quiz"

    def answer_question(selected):
        nonlocal xp, unlocked, final_index, final_completed, screen
        nonlocal quiz_feedback, level_question_index, reward_message_until, quiz_lives, quiz_flash_until
        nonlocal run_elapsed_seconds, run_adjusted_seconds, run_medal
        if final_quiz:
            question = FINAL_QUESTIONS[final_index]
            if selected == question["answer"]:
                final_index += 1
                quiz_feedback = ""
                if final_index == len(FINAL_QUESTIONS):
                    xp += 1000
                    final_completed = True
                    run_elapsed_seconds = current_run_time(pygame.time.get_ticks())
                    run_adjusted_seconds = adjusted_run_time(
                        run_elapsed_seconds,
                        run_coins_collected,
                        run_deaths,
                    )
                    run_medal = medal_for_time(run_adjusted_seconds)
                    screen = "complete"
            else:
                quiz_lives -= 1
                quiz_flash_until = pygame.time.get_ticks() + 180
                if quiz_lives == 0:
                    final_index = 0
                    quiz_lives = 3
                quiz_feedback = ""
            return

        question = level_questions[level_question_index]
        if selected != question["answer"]:
            quiz_lives -= 1
            quiz_flash_until = pygame.time.get_ticks() + 180
            if quiz_lives == 0:
                level_question_index = 0
                quiz_lives = 3
            quiz_feedback = ""
            return

        level_question_index += 1
        quiz_feedback = ""
        if level_question_index == len(level_questions):
            level = LEVELS[level_index]
            solved.add(level_index)
            xp += level["xp"]
            unlocked = max(unlocked, min(len(LEVELS), level_index + 2))
            reward_message_until = pygame.time.get_ticks() + 7000
            screen = "play"

    while running:
        dt = min(CLOCK.tick(FPS) / 1000, 0.04)
        jump_pressed = False
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    fullscreen = toggle_fullscreen(fullscreen)
                elif event.key == pygame.K_ESCAPE:
                    if screen == "settings":
                        screen = "menu"
                    elif screen == "shop":
                        screen = "map"
                    elif screen in ("quiz", "final_quiz", "map", "complete"):
                        screen = "map" if screen == "complete" else "play"
                        quiz_feedback = ""
                    elif screen == "play":
                        screen = "map"
                elif screen == "menu" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    screen = "map"
                elif screen == "menu" and event.key == pygame.K_o:
                    screen = "settings"
                elif screen == "settings":
                    if event.key == pygame.K_m:
                        music_enabled = not music_enabled
                    elif event.key == pygame.K_d:
                        sounds_enabled = not sounds_enabled
                    elif event.key == pygame.K_ESCAPE:
                        screen = "menu"
                elif screen == "complete" and event.key == pygame.K_RETURN:
                    exploration = True
                    unlocked = len(LEVELS)
                    screen = "map"
                elif screen == "dead":
                    if event.key in (pygame.K_r, pygame.K_RETURN):
                        restart_level()
                    elif event.key in (pygame.K_m, pygame.K_ESCAPE):
                        screen = "map"
                elif screen == "map":
                    if event.key == pygame.K_m:
                        screen = "play"
                    elif event.key == pygame.K_s:
                        shop_message = ""
                        screen = "shop"
                    elif pygame.K_1 <= event.key <= pygame.K_5:
                        selected = event.key - pygame.K_1
                        if selected < unlocked or exploration:
                            enter_level(selected)
                    elif event.key == pygame.K_f and len(solved) == len(LEVELS) and len(fragments) == len(LEVELS) and not final_completed:
                        final_index = 0
                        final_quiz = True
                        quiz_lives = 3
                        quiz_feedback = ""
                        quiz_flash_until = 0
                        screen = "final_quiz"
                elif screen == "play":
                    if event.key == pygame.K_m:
                        screen = "map"
                    elif event.key == pygame.K_f:
                        if not speed_boost_owned:
                            collect_message = "Speed boost kupisz w sklepie za 20 monet."
                            collect_message_until = pygame.time.get_ticks() + 2200
                        elif level_index in speed_boost_used_levels:
                            collect_message = "Speed boost został już użyty na tej mapie."
                            collect_message_until = pygame.time.get_ticks() + 2200
                        else:
                            speed_boost_used_levels.add(level_index)
                            speed_boost_until = pygame.time.get_ticks() + 10000
                            collect_message = "Speed boost aktywny przez 10 sekund!"
                            collect_message_until = pygame.time.get_ticks() + 2200
                    elif event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                        jump_pressed = True
                    elif event.key == pygame.K_e and player.colliderect(guide.inflate(90, 50)) and level_index not in solved:
                        start_level_quiz()
                elif screen == "shop":
                    if event.key in (pygame.K_ESCAPE, pygame.K_m):
                        screen = "map"
                    elif pygame.K_1 <= event.key <= pygame.K_5:
                        skin_index = event.key - pygame.K_1
                        price = discounted_shop_price(SKINS[skin_index]["cost"])
                        if SKINS[skin_index].get("secret", False) and not secret_skin_found:
                            shop_message = "Najpierw znajdź czerwony kryształ na poziomie 3."
                        elif skin_index in owned_skins:
                            selected_skin = skin_index
                            shop_message = f"Wybrano skórkę: {SKINS[skin_index]['name']}."
                        elif coin_balance >= price:
                            coin_balance -= price
                            owned_skins.add(skin_index)
                            selected_skin = skin_index
                            shop_message = f"Kupiono skórkę: {SKINS[skin_index]['name']}!"
                        else:
                            shop_message = f"Brakuje monet. Potrzeba: {price}."
                    elif event.key == pygame.K_6:
                        purchase_speed_boost()
                    elif event.key == pygame.K_7:
                        purchase_jetpack()
                    elif event.key == pygame.K_8:
                        purchase_pizza()
                elif screen in ("quiz", "final_quiz") and event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    selected = event.key - pygame.K_1
                    options = FINAL_QUESTIONS[final_index]["options"] if final_quiz else level_questions[level_question_index]["options"]
                    if selected < len(options):
                        answer_question(selected)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_position = logical_mouse_position(event.pos)
                if screen == "menu":
                    if pygame.Rect(325, 405, 310, 60).collidepoint(mouse_position):
                        screen = "map"
                    elif pygame.Rect(370, 475, 220, 42).collidepoint(mouse_position):
                        screen = "settings"
                elif screen == "settings":
                    if pygame.Rect(270, 245, 420, 62).collidepoint(mouse_position):
                        music_enabled = not music_enabled
                    elif pygame.Rect(270, 330, 420, 62).collidepoint(mouse_position):
                        sounds_enabled = not sounds_enabled
                    elif pygame.Rect(325, 440, 310, 56).collidepoint(mouse_position):
                        screen = "menu"
                elif screen == "map":
                    if pygame.Rect(775, 95, 150, 42).collidepoint(mouse_position):
                        shop_message = ""
                        screen = "shop"
                    else:
                        points = [(155, 285), (315, 210), (480, 310), (645, 210), (810, 285)]
                        for index, point in enumerate(points):
                            if math.dist(mouse_position, point) <= 40 and (index < unlocked or exploration):
                                enter_level(index)
                                break
                        if (
                            pygame.Rect(340, 465, 280, 54).collidepoint(mouse_position)
                            and len(solved) == len(LEVELS)
                            and len(fragments) == len(LEVELS)
                            and not final_completed
                        ):
                            final_index = 0
                            final_quiz = True
                            quiz_lives = 3
                            quiz_feedback = ""
                            quiz_flash_until = 0
                            screen = "final_quiz"
                elif screen == "shop":
                    if speed_boost_button.collidepoint(mouse_position):
                        purchase_speed_boost()
                    elif jetpack_button.collidepoint(mouse_position):
                        purchase_jetpack()
                    elif pizza_button.collidepoint(mouse_position):
                        purchase_pizza()
                    else:
                        for skin_index, rect in enumerate(shop_buttons):
                            if rect.collidepoint(mouse_position):
                                price = discounted_shop_price(SKINS[skin_index]["cost"])
                                if SKINS[skin_index].get("secret", False) and not secret_skin_found:
                                    shop_message = "Najpierw znajdź czerwony kryształ na poziomie 3."
                                elif skin_index in owned_skins:
                                    selected_skin = skin_index
                                    shop_message = f"Wybrano skórkę: {SKINS[skin_index]['name']}."
                                elif coin_balance >= price:
                                    coin_balance -= price
                                    owned_skins.add(skin_index)
                                    selected_skin = skin_index
                                    shop_message = f"Kupiono skórkę: {SKINS[skin_index]['name']}!"
                                else:
                                    shop_message = f"Brakuje monet. Potrzeba: {price}."
                                break
                elif screen == "dead":
                    if pygame.Rect(305, 345, 350, 55).collidepoint(mouse_position):
                        restart_level()
                    elif pygame.Rect(305, 420, 350, 55).collidepoint(mouse_position):
                        screen = "map"
                elif screen in ("quiz", "final_quiz"):
                    for index, rect in enumerate(question_buttons):
                        if rect.collidepoint(mouse_position):
                            answer_question(index)
                            break

        if screen == "pizza_wheel":
            if pygame.time.get_ticks() - pizza_wheel_started_at >= 3500:
                apply_pizza_effect()
        elif screen == "pizza_result" and pygame.time.get_ticks() >= pizza_result_until:
            screen = "shop"

        if screen == "play":
            jump_buffer = 0.14 if jump_pressed else max(0, jump_buffer - dt)
            coyote_time = 0.12 if on_ground else max(0, coyote_time - dt)
            can_jump = jump_buffer > 0 and coyote_time > 0
            keys = pygame.key.get_pressed()
            speed_boost_active = pygame.time.get_ticks() < speed_boost_until
            jetpack_active = jetpack_equipped and jetpack_fuel > 0 and keys[pygame.K_SPACE]
            if jetpack_active:
                jetpack_fuel = max(0, jetpack_fuel - dt * 30)
                if jetpack_fuel == 0:
                    jetpack_equipped = False
                    jetpack_active = False
            velocity_y, on_ground, fell_into_pit = move_player(
                player,
                velocity_y,
                dt,
                keys[pygame.K_LEFT] or keys[pygame.K_a],
                keys[pygame.K_RIGHT] or keys[pygame.K_d],
                can_jump and not jetpack_active,
                on_ground or coyote_time > 0,
                LEVEL_PLATFORMS[level_index],
                speed_multiplier=1.25 if speed_boost_active else 1.0,
                jetpack_active=jetpack_active,
            )
            if can_jump and velocity_y < 0:
                jump_buffer = 0
                coyote_time = 0

            time_ms = pygame.time.get_ticks()
            birds = get_level_birds(time_ms, level_index)
            if time_ms >= next_bomb_drop_at:
                bird = random.choice(birds)
                bombs.append(
                    (
                        pygame.Rect(bird.centerx - 6, bird.bottom, 12, 14),
                        random.randint(260, 320),
                    )
                )
                next_bomb_drop_at = time_ms + random.randint(2500, 4500)
            bombs, new_explosions, bomb_hit_player = update_bombs(
                bombs,
                dt,
                LEVEL_PLATFORMS[level_index],
                player,
            )
            explosions.extend((blast, time_ms + 320) for blast in new_explosions)
            explosions = [
                (blast, expires_at)
                for blast, expires_at in explosions
                if time_ms < expires_at
            ]
            player_hit_bird = any(player.colliderect(bird) for bird in birds)
            player_hit_spikes = any(player.colliderect(spike) for spike in SPIKES_BY_LEVEL[level_index])
            secret_crystal_rect = pygame.Rect(RED_CRYSTAL_SPOT[0], RED_CRYSTAL_SPOT[1], 30, 40)
            if level_index == 2 and not secret_skin_found and player.colliderect(secret_crystal_rect):
                secret_skin_found = True
                secret_message_until = time_ms + 5000
            if fell_into_pit:
                die("Spadłeś w przepaść")
            elif player_hit_bird:
                die("Uderzył Cię ptak")
            elif bomb_hit_player:
                die("Trafiła Cię bomba")
            elif player_hit_spikes:
                die("Nadziałeś się na kolce")
            else:
                coins_before = len(coins_collected[level_index])
                xp_gained, messages = collect_items(player, level_index, coins_collected[level_index], fragments)
                coins_gained = len(coins_collected[level_index]) - coins_before
                coin_balance += coins_gained
                run_coins_collected += coins_gained
                if xp_gained:
                    xp += xp_gained
                    collect_message = "  ".join(messages)
                    collect_message_until = pygame.time.get_ticks() + 2600

                camera_x = max(0, min(WORLD_WIDTH - WIDTH, player.centerx - WIDTH // 2))
                camera_y = min(0, player.centery - round(HEIGHT * 0.62))
                near_guide = player.colliderect(guide.inflate(90, 50))
                draw_play(
                    SCREEN,
                    level_index,
                    player,
                    guide,
                    near_guide,
                    solved,
                    fragments,
                    coins_collected[level_index],
                    coin_balance,
                    xp,
                    final_completed,
                    exploration,
                    camera_x,
                    SPIKES_BY_LEVEL[level_index],
                    SKINS[selected_skin]["color"],
                    bool(keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_RIGHT] or keys[pygame.K_d]),
                    time_ms / 100,
                    time_ms,
                    camera_y,
                    secret_skin_found,
                    current_run_time(time_ms) if run_started_at is not None else None,
                    run_deaths,
                    jetpack_equipped,
                    jetpack_fuel,
                    jetpack_active,
                    speed_boost_active,
                )
                draw_bombs(SCREEN, bombs, camera_x, camera_y)
                draw_explosions(SCREEN, explosions, camera_x, camera_y, time_ms)
                if level_index in solved and pygame.time.get_ticks() < reward_message_until:
                    draw_reward(SCREEN, LEVELS[level_index])
                if pygame.time.get_ticks() < collect_message_until:
                    pygame.draw.rect(SCREEN, (29, 43, 61), (180, 75, 600, 46), border_radius=12)
                    draw_text(SCREEN, collect_message, SMALL_FONT, GOLD, (WIDTH // 2, 98), center=True)
                if time_ms < secret_message_until:
                    draw_outlined_text(
                        SCREEN,
                        "ZNALAZŁEŚ SEKRET!",
                        TITLE_FONT,
                        (238, 47, 61),
                        (12, 12, 12),
                        (WIDTH // 2, HEIGHT // 2),
                        center=True,
                    )
        elif screen == "menu":
            draw_menu(SCREEN)
        elif screen == "map":
            draw_map(
                SCREEN, unlocked, solved, fragments, xp, exploration, final_completed,
                coin_balance,
            )
        elif screen == "settings":
            draw_settings(SCREEN, music_enabled, sounds_enabled)
        elif screen == "shop":
            shop_buttons, speed_boost_button, jetpack_button, pizza_button = draw_shop(
                SCREEN,
                coin_balance,
                owned_skins,
                selected_skin,
                secret_skin_found,
                shop_message,
                speed_boost_owned,
                jetpack_equipped,
            )
        elif screen == "pizza_wheel":
            draw_pizza_wheel(
                SCREEN,
                pygame.time.get_ticks() - pizza_wheel_started_at,
                pizza_outcome,
            )
        elif screen == "pizza_result":
            draw_pizza_result(SCREEN, pizza_outcome)
        elif screen in ("quiz", "final_quiz"):
            if final_quiz:
                question = FINAL_QUESTIONS[final_index]
                question_buttons = draw_question(
                    SCREEN,
                    {"name": "Finał przy Radiostacji", "color": (149, 119, 69)},
                    question["question"],
                    question["options"],
                    final_index,
                    len(FINAL_QUESTIONS),
                    quiz_feedback,
                    quiz_lives,
                    coin_balance,
                    final_map=True,
                    error_flash=pygame.time.get_ticks() < quiz_flash_until,
                )
            else:
                question = level_questions[level_question_index]
                question_buttons = draw_question(
                    SCREEN,
                    LEVELS[level_index],
                    question["question"],
                    question["options"],
                    level_question_index,
                    len(level_questions),
                    quiz_feedback,
                    quiz_lives,
                    coin_balance,
                    error_flash=pygame.time.get_ticks() < quiz_flash_until,
                )
        elif screen == "complete":
            draw_completion(
                SCREEN,
                xp,
                run_elapsed_seconds,
                run_adjusted_seconds,
                run_medal,
                (GOLD_TIME_SECONDS, SILVER_TIME_SECONDS, BRONZE_TIME_SECONDS),
                run_deaths,
                run_coins_collected,
            )
        elif screen == "dead":
            draw_death(SCREEN, LEVELS[level_index]["name"], death_reason, death_coins_lost)

        if run_started_at is not None and screen not in ("menu", "settings", "complete", "pizza_wheel", "pizza_result"):
            elapsed = current_run_time(pygame.time.get_ticks())
            timer_panel = pygame.Rect(WIDTH - 190, HEIGHT - 38, 176, 28)
            pygame.draw.rect(SCREEN, (28, 39, 55), timer_panel, border_radius=8)
            draw_text(SCREEN, f"CZAS GRY: {format_time(elapsed)}", FONT, WHITE, timer_panel.center, center=True)

        present_frame()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
12