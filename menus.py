import math
import pygame
from settings import (AssetManager, save_game_data, save_data_exists, clear_save_data, UI_SCALE, WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_WHITE, COLOR_BLACK, COLOR_GREY,
                      COLOR_BLUE, COLOR_DARK_BLUE, COLOR_YELLOW, COLOR_RED, COLOR_GREEN,
                      COLOR_DARK_GREEN, WINDOW_CENTER, save_game_data, get_font, nine_slice)
from player import Player
from flag import Flag
from sound import Audio

# UI pack images used for buttons, per button colour
BUTTON_IMAGES = {
    COLOR_BLUE: "assets/images/ui/button_blue.png",
    COLOR_GREEN: "assets/images/ui/button_green.png",
    COLOR_RED: "assets/images/ui/button_red.png",
    COLOR_YELLOW: "assets/images/ui/button_yellow.png",
}
DISABLED_BUTTON_IMAGE = "assets/images/ui/button_grey.png"
PANEL_IMAGE = "assets/images/ui/panel.png"


def draw_panel(screen: pygame.Surface, rect: pygame.Rect, alpha: int = 240) -> None:
    """Draws a rounded UI panel (scaled from the UI pack) filling the given rect."""
    panel = nine_slice(PANEL_IMAGE, rect.size, 12)
    panel.set_alpha(alpha)
    screen.blit(panel, rect)


def handle_mute_key(event: pygame.event.Event) -> None:
    """Toggles sound when M is pressed."""
    if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
        Audio.toggle_mute()

class Button:
    """Button for menus."""
    def __init__(self, text: str, position: tuple[int, int], width: int, height: int,
                 colour: str = COLOR_BLUE, font_size: int = 50) -> None:
        self.text_content: str = text
        self.position: tuple[int, int] = (int(position[0] * UI_SCALE), int(position[1] * UI_SCALE))
        self.width: int = int(width * UI_SCALE)
        self.height: int = int(height * UI_SCALE)
        self.colour: str = colour
        self.font_size: int = int(font_size * UI_SCALE)

        # Button rectangle
        self.rect: pygame.Rect = pygame.Rect(self.position, (self.width, self.height))
        self.rect.center = self.position

        # Text object
        self.text_obj: Text = Text(text, position, font_size, "#000000")

        # Clickable
        self.is_clickable: bool = True

        # Hover state (to play a sound when the mouse moves onto the button)
        self.was_hovered: bool = False

    def draw(self, screen: pygame.Surface) -> None:
        """Renders the button on the given surface."""
        hovered = self.is_clickable and self.is_hovered()
        if hovered and not self.was_hovered:
            Audio.play("hover")
        self.was_hovered = hovered

        if self.is_clickable:
            image_path = BUTTON_IMAGES.get(self.colour, BUTTON_IMAGES[COLOR_BLUE])
            pressed = hovered and pygame.mouse.get_pressed()[0]
            image = nine_slice(image_path, self.rect.size, 14, brighten=30 if hovered else 0)
            lift = 0 if pressed else (-int(3 * UI_SCALE) if hovered else 0)
            text_colour = COLOR_WHITE
        else:
            image = nine_slice(DISABLED_BUTTON_IMAGE, self.rect.size, 14)
            lift = 0
            text_colour = "#8A8A99"

        screen.blit(image, self.rect.move(0, lift))

        # Text with a soft shadow, centred on the button's face (above its 3D edge)
        face_center = (self.rect.centerx, self.rect.centery + lift - int(2 * UI_SCALE))
        label = get_font(self.font_size).render(self.text_content, True, text_colour)
        if self.is_clickable:
            shadow = get_font(self.font_size).render(self.text_content, True, (0, 0, 0))
            shadow.set_alpha(90)
            screen.blit(shadow, shadow.get_rect(center=(face_center[0] + 2, face_center[1] + 2)))
        screen.blit(label, label.get_rect(center=face_center))

    def is_clicked(self, event: pygame.event.Event) -> bool:
        """Checks if the button was clicked in the given event."""
        if self.is_clickable:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Button 1 is left click
                if self.is_hovered():
                    Audio.play("click")
                    return True
        return False

    def is_hovered(self) -> bool:
        """Checks if the mouse is currently hovering over the button."""
        mouse_pos = pygame.mouse.get_pos()
        return self.rect.collidepoint(mouse_pos)

class Text:
    """Text label."""
    def __init__(self, text: str, position: tuple[int, int], font_size: int = 50,
                 colour: str | tuple[int, int, int] = "#000000", anchor: str = "center") -> None:
        self.text: str = text
        self.position: tuple[int, int] = (int(position[0] * UI_SCALE), int(position[1] * UI_SCALE))
        self.font_size: int = int(font_size * UI_SCALE)
        self.colour: str | tuple[int, int, int] = colour
        self.font: pygame.font.Font = get_font(self.font_size)

        # Text surface and rect
        self.text_surf: pygame.Surface = self.font.render(text, True, colour)
        self.text_rect: pygame.Rect = self.text_surf.get_rect(center=self.position)

        # Adjust text position based on anchor
        if anchor == "center":
            self.text_rect.center = self.position
        elif anchor == "topleft":
            self.text_rect.topleft = self.position
        elif anchor == "midleft":
            self.text_rect.midleft = self.position
        elif anchor == "topright":
            self.text_rect.topright = self.position
        elif anchor == "midright":
            self.text_rect.midright = self.position
        elif anchor == "bottomleft":
            self.text_rect.bottomleft = self.position
        elif anchor == "bottomright":
            self.text_rect.bottomright = self.position

    def draw(self, screen: pygame.Surface) -> None:
        """Renders the text on the given surface."""
        screen.blit(self.text_surf, self.text_rect)

def draw_shadowed_text(screen: pygame.Surface, text: str, position: tuple[float, float],
                       font_size: int, colour, anchor: str = "center") -> None:
    """Draws text with a dark outline so it stays readable on any background."""
    for dx, dy in ((-1.5, 0), (1.5, 0), (0, -1.5), (0, 1.5), (1.5, 1.5)):
        Text(text, (position[0] + dx, position[1] + dy), font_size, COLOR_BLACK, anchor).draw(screen)
    Text(text, position, font_size, colour, anchor).draw(screen)


class HUD:
    """HUD (Heads-Up Display) for displaying player health, credits, ammo, etc."""
    def __init__(self, player: Player, flag: Flag) -> None:
        # Player and flag references
        self.player: Player = player
        self.flag: Flag = flag

        self.ammo_icon: pygame.Surface = AssetManager.get_image("assets/images/ammo_icon.png")
        self.ammo_icon = pygame.transform.scale(self.ammo_icon, (12 * UI_SCALE, 30 * UI_SCALE))

        self.heart_icon: pygame.Surface = AssetManager.get_image("assets/images/heart_icon.png")
        self.heart_icon = pygame.transform.scale(self.heart_icon, (30 * UI_SCALE, 30 * UI_SCALE))

        self.compass_icon: pygame.Surface = AssetManager.get_image("assets/images/compass_arrow.png")
        self.compass_icon = pygame.transform.scale(self.compass_icon, (30 * UI_SCALE, 30 * UI_SCALE))

        self.round = 1

        # Health shown by the bar "drains" smoothly towards the real value
        self.display_health: float = player.health
        self.last_tick: int = pygame.time.get_ticks()

        # Red vignette shown when the player is hurt or at low health
        self.vignette: pygame.Surface = AssetManager.cached(("vignette",), make_vignette)

    def draw(self, screen: pygame.Surface) -> None:
        """Draws the HUD on the given surface."""
        self.damage_vignette(screen)
        self.objective(screen)
        self.health_bar(screen)
        self.ammo_counter(screen)
        self.credit_counter(screen)
        self.lives_counter(screen)
        self.reload_progress(screen)
        self.flag_compass(screen)
        self.round_counter(screen)

    def health_bar(self, screen: pygame.Surface) -> None:
        """Draws the health bar on the given surface."""

        # Smoothly move the displayed health towards the real health
        now = pygame.time.get_ticks()
        dt = (now - self.last_tick) / 1000
        self.last_tick = now
        if self.display_health > self.player.health:
            self.display_health = max(self.player.health,
                                      self.display_health - self.player.max_health * 0.8 * dt)
        else:
            self.display_health = self.player.health

        # Calculate health bar width based on current health
        health_ratio = max(0.0, self.player.health / self.player.max_health)
        health_bar_width = int(health_ratio * 200 * UI_SCALE)
        trail_ratio = max(0.0, self.display_health / self.player.max_health)

        # Red for missing health, yellow for recently lost health, green for current health
        max_health_bar = pygame.Rect(10 * UI_SCALE, 10 * UI_SCALE, 200 * UI_SCALE, 20 * UI_SCALE)
        trail_bar = pygame.Rect(10 * UI_SCALE, 10 * UI_SCALE, int(trail_ratio * 200 * UI_SCALE), 20 * UI_SCALE)
        current_health_bar = pygame.Rect(10 * UI_SCALE, 10 * UI_SCALE, health_bar_width, 20 * UI_SCALE)

        # Draw health bar
        pygame.draw.rect(screen, COLOR_RED, max_health_bar)
        pygame.draw.rect(screen, COLOR_YELLOW, trail_bar)
        pygame.draw.rect(screen, COLOR_GREEN, current_health_bar)

        # Health number
        Text(f"{max(0, int(math.ceil(self.player.health)))} / {int(self.player.max_health)}",
             (110, 20), font_size=22, colour=COLOR_BLACK).draw(screen)

        # Black border around health bar
        border_thickness = int(3 * UI_SCALE)
        border_rect = max_health_bar.inflate(border_thickness * 2, border_thickness * 2)
        pygame.draw.rect(screen, COLOR_BLACK, border_rect, border_thickness)

    def ammo_counter(self, screen: pygame.Surface) -> None:
        """Draws the ammo counter on the given surface."""
        current_ammo = self.player.gun.ammo
        max_ammo = self.player.gun.max_ammo

        if self.player.gun.is_reloading:
            text = "RELOADING..."
        else:
            text = f"{current_ammo} / {max_ammo}"

        screen.blit(self.ammo_icon, (30 * UI_SCALE, 660 * UI_SCALE))
        draw_shadowed_text(screen, text, (55, 678), 48, COLOR_BLUE, "midleft")

    def credit_counter(self, screen: pygame.Surface) -> None:
        """Draws the credit counter on the given surface."""
        current_credits = self.player.money

        draw_shadowed_text(screen, f"$ {current_credits}", (29, 630), 48, COLOR_BLUE, "midleft")

    def lives_counter(self, screen: pygame.Surface) -> None:
        """Draws the lives counter on the given surface."""
        current_lives = self.player.lives
        for i in range(current_lives):
            screen.blit(self.heart_icon, (int(10 + i * 35) * UI_SCALE, int(40 * UI_SCALE)))

    def reload_progress(self, screen: pygame.Surface) -> None:
        """Draws the reload progress bar on the given surface."""
        if not self.player.gun.is_reloading:
            return

        now = pygame.time.get_ticks()
        progress = now - self.player.gun.reload_start_time

        # Calculate progress bar width based on reload time
        reload_progress = progress / self.player.gun.reload_time
        progress_bar_width = int(reload_progress * 100 * UI_SCALE)

        bg_rect = pygame.Rect(0, 0, 100 * UI_SCALE, 10 * UI_SCALE)
        bg_rect.center = (WINDOW_WIDTH * UI_SCALE // 2, 645)
        progress_rect = pygame.Rect(bg_rect.left, bg_rect.top, progress_bar_width, 10 * UI_SCALE)

        pygame.draw.rect(screen, COLOR_GREY, bg_rect)
        pygame.draw.rect(screen, COLOR_BLUE, progress_rect)

    def flag_compass(self, screen: pygame.Surface) -> None:
        """Draws the flag pointer on the given surface."""
        if self.flag.is_planted or self.flag.plant_progress > 0:
            return # Don't draw if flag is already or being planted

        player_pos = pygame.math.Vector2(self.player.rect.center)
        flag_pos = pygame.math.Vector2(self.flag.rect.center)

        # Calculate direction vector
        direction = flag_pos - player_pos
        if direction.length() == 0:
            direction = pygame.math.Vector2(0, 1) # Default to up if on top of flag
        direction = direction.normalize()

        arrow_pos = (pygame.math.Vector2(WINDOW_WIDTH * UI_SCALE // 2, WINDOW_HEIGHT * UI_SCALE // 2)
                     + direction * 100)

        # Rotate arrow to face flag
        rotation = direction.angle_to(pygame.math.Vector2(0, -1))
        rotated_image = pygame.transform.rotate(self.compass_icon, rotation)
        rotated_rect = rotated_image.get_rect(center=arrow_pos)

        screen.blit(rotated_image, rotated_rect)

    def damage_vignette(self, screen: pygame.Surface) -> None:
        """Tints the screen edges red when the player is hurt or low on health."""
        low_health = max(0.0, 1 - self.player.health / (self.player.max_health * 0.35))
        hurt = max(0.0, self.player.hurt_timer / 0.15) * 0.6
        strength = min(1.0, max(low_health * (0.75 + 0.25 * math.sin(pygame.time.get_ticks() / 150)), hurt))
        if strength > 0.01:
            self.vignette.set_alpha(int(255 * strength))
            screen.blit(self.vignette, (0, 0))

    def objective(self, screen: pygame.Surface) -> None:
        """Shows the current objective: plant the flag, or the flag defense timer."""
        center_x = WINDOW_WIDTH // 2
        if not self.flag.is_planted:
            distance = pygame.math.Vector2(self.player.rect.midbottom).distance_to(self.flag.position)
            if self.flag.plant_progress > 0:
                text = f"PLANTING... {int(100 * self.flag.plant_progress / self.flag.plant_time_required)}%"
            else:
                text = f"FIND AND PLANT THE FLAG  ({int(distance / 64)}m)"
            draw_shadowed_text(screen, text, (center_x, 20), 36, COLOR_WHITE)
            return

        if self.flag.outcome:
            return

        # Defense timer bar: empties as the flag is defended, grows when enemies hit the flag
        ratio = max(0.0, min(1.0, self.flag.timer / self.flag.max_timer))
        width, height = int(300 * UI_SCALE), int(18 * UI_SCALE)
        bar = pygame.Rect(0, 0, width, height)
        bar.center = (int(center_x * UI_SCALE), int(48 * UI_SCALE))
        danger = self.flag.timer > self.flag.max_timer / 2
        pygame.draw.rect(screen, (40, 40, 40), bar)
        pygame.draw.rect(screen, COLOR_RED if danger else COLOR_BLUE,
                         (bar.left, bar.top, int(width * ratio), height))
        pygame.draw.rect(screen, COLOR_BLACK, bar, int(3 * UI_SCALE))

        label = f"DEFEND THE FLAG: {int(math.ceil(self.flag.timer))}s"
        draw_shadowed_text(screen, label, (center_x, 20), 36, COLOR_RED if danger else COLOR_WHITE)

    def round_counter(self, screen: pygame.Surface) -> None:
        """Draws the round counter on the given surface."""
        draw_shadowed_text(screen, f"Round: {self.round}", (WINDOW_WIDTH - 38, 52.5), 48, COLOR_BLUE, "midright")

def make_vignette() -> pygame.Surface:
    """Creates a full-screen red vignette (transparent centre, red edges)."""
    size = (int(WINDOW_WIDTH * UI_SCALE), int(WINDOW_HEIGHT * UI_SCALE))
    small = pygame.Surface((160, 90), pygame.SRCALPHA)
    for y in range(90):
        for x in range(160):
            dx, dy = (x - 80) / 80, (y - 45) / 45
            d = max(0.0, min(1.0, (math.hypot(dx, dy) - 0.55) / 0.6))
            small.set_at((x, y), (200, 0, 0, int(200 * d * d)))
    return pygame.transform.smoothscale(small, size)


class MenuBackground:
    """Animated menu background: scrolling sea with characters from the game."""
    def __init__(self) -> None:
        coast = AssetManager.get_image("assets/map/coast.png")
        # The open-water tile has 4 animation frames, 3 tiles apart vertically
        self.water = [coast.subsurface((64, 64 + 192 * i, 64, 64)) for i in range(4)]
        self.player_frames = AssetManager.get_sheet("assets/images/player_sheet.png", 128, 128)[2]
        monster = AssetManager.get_sheet("assets/images/monsters/Charmadillo.png", 192, 192)[0]
        self.monster_frames = monster  # Monsters face left, towards the player
        self.title_font = get_font(int(130 * UI_SCALE))

    def draw(self, screen: pygame.Surface, title: str | None = None, panel_rect: tuple | None = None) -> None:
        ticks = pygame.time.get_ticks()
        frame = self.water[(ticks // 300) % 4]
        scroll = (ticks / 40) % 64
        width, height = screen.get_size()
        for y in range(-1, height // 64 + 2):
            for x in range(-1, width // 64 + 2):
                screen.blit(frame, (x * 64 - scroll, y * 64 - scroll / 2))

        if panel_rect:
            rect = pygame.Rect([int(v * UI_SCALE) for v in panel_rect])
            draw_panel(screen, rect)

            # Player and a monster standing on either side of the panel
            bob = math.sin(ticks / 250) * 4
            player = pygame.transform.scale_by(self.player_frames[(ticks // 150) % 4], 1.5)
            screen.blit(player, player.get_rect(midright=(rect.left - 20, rect.centery + bob)))
            monster = self.monster_frames[(ticks // 170) % 4]
            screen.blit(monster, monster.get_rect(midleft=(rect.right + 10, rect.centery - bob)))

        if title:
            for offset, colour in (((6, 6), COLOR_BLACK), ((0, 0), COLOR_WHITE)):
                label = self.title_font.render(title, True, colour)
                screen.blit(label, label.get_rect(center=(width // 2 + offset[0], int(75 * UI_SCALE) + offset[1])))


def main_menu(screen: pygame.Surface, clock: pygame.time.Clock) -> str:
    """
    Displays the main menu and handles user interaction.
    
    :return: A tuple of (next game state, resume flag).
    """

    pygame.mouse.set_visible(True)
    Audio.music("menu")

    # Load high score
    try:
        with open("game_save/highscore.txt", "r") as score_file:
            high_score = score_file.read()
    except FileNotFoundError:
        high_score = "0"

    # Create high-score text
    high_score_text = Text(f"High Score: {high_score}",
                           (WINDOW_WIDTH // 2, 190), font_size=70, colour=COLOR_DARK_BLUE)
    background = MenuBackground()

    # Create buttons
    resume_game_button = Button("Resume Game", (WINDOW_WIDTH // 2, 300),
                                300, 120)
    new_game_button = Button("New Game", (WINDOW_WIDTH // 2, 450),
                             300, 120)
    quit_button = Button("Quit", (WINDOW_WIDTH // 2, 600),
                         300, 120)
    buttons = [resume_game_button, new_game_button, quit_button]

    while True:

        # Only allow resuming if there is a save
        resume_game_button.is_clickable = save_data_exists()

        for event in pygame.event.get(): # Event loop
            handle_mute_key(event)
            if quit_button.is_clicked(event) or event.type == pygame.QUIT:
                return "QUIT", False  # Change game state to QUIT, (False irrelevant for quitting)
            if resume_game_button.is_clicked(event):
                return "PLAYING", True  # Change game state to PLAYING, flag to indicate resuming from save

            if new_game_button.is_clicked(event):
                if save_data_exists():
                    confirmed = confirmation_menu(screen, clock,
                                                  "Are you sure you want to start a new game? "
                                                  "Your previous progress will be lost.",
                                                  "Yes", "Cancel")
                    if confirmed:
                        clear_save_data()
                        return "PLAYING", False  # Change game state to PLAYING, flag to indicate not resuming from save

                else:
                    # If no save data, just start new game without confirmation
                    return "PLAYING", False  # Change game state to PLAYING, flag to indicate not resuming from save

        # Update cursor
        if any(button.is_hovered() for button in buttons):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        # Animated background with title
        background.draw(screen, "SHOOTER GAME", (WINDOW_WIDTH // 2 - 230, 145, 460, 545))

        # Render buttons
        for button in buttons:
            button.draw(screen)

        # Render high score
        high_score_text.draw(screen)

        pygame.display.flip() # Update display
        clock.tick(60)

def pause_menu(screen: pygame.Surface, clock: pygame.time.Clock,
               round_num: int, player, stats_manager) -> str:
    """
    Displays the pause menu as a transparent overlay and handles user interaction.
    
    :return: The next game state (e.g., "PLAYING", "MAIN_MENU", "QUIT").
    """

    pygame.mouse.set_visible(True)

    background = screen.copy()# Take screenshot of background

    # Game paused text
    paused_text = Text("Game Paused", (WINDOW_WIDTH // 2, 150),
                       font_size=100, colour=COLOR_WHITE)

    # Create buttons
    resume_button = Button("Resume", (WINDOW_WIDTH // 2, 325),
                           300 , 120)
    quit_button = Button("Save and Quit", (WINDOW_WIDTH // 2, 470),
                         300, 120)
    buttons = [resume_button, quit_button]

    mute_hint = Text("Press M to mute / unmute sound", (WINDOW_WIDTH // 2, 580),
                     font_size=32, colour=COLOR_WHITE)

    # Create a transparent overlay
    overlay = pygame.Surface((WINDOW_WIDTH * UI_SCALE, WINDOW_HEIGHT * UI_SCALE))
    overlay.set_alpha(128)  # 0 : transparent, 255 : opaque
    overlay.fill((0, 0, 0))  # Black tint

    while True:
        for event in pygame.event.get(): # Event loop
            if event.type == pygame.QUIT:
                return "QUIT"
            handle_mute_key(event)
            if quit_button.is_clicked(event):
                confirmed = confirmation_menu(screen, clock, 
                                                "Are you sure you want to quit? "
                                                "Your progress will be saved.",
                                                "Quit", "Cancel")
                if confirmed:
                    save_game_data(round_num, player, stats_manager)  # Save game before quitting
                    return "MAIN_MENU"  # Change game state to MAIN MENU
            if resume_button.is_clicked(event) or event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "PLAYING"  # Change game state to PLAYING

        # Update cursor
        if any(button.is_hovered() for button in buttons):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        # Draw the captured screenshot
        screen.blit(background, (0, 0))
        # Draw the transparent overlay
        screen.blit(overlay, (0, 0))

        # Render paused text
        paused_text.draw(screen)
        mute_hint.draw(screen)

        # Render buttons
        for button in buttons:
            button.draw(screen)

        pygame.display.flip() # Update display
        clock.tick(60)

def game_over_menu(screen: pygame.Surface, clock: pygame.time.Clock, game_over_stats: dict) -> str:
    """
    Displays the game over menu and handles user interaction.

    :return: The next game state ("MAIN_MENU").
    """

    pygame.mouse.set_visible(True)

    Audio.music("menu")

    # Game over text
    game_over_text = Text("Game Over", (WINDOW_WIDTH // 2, 100),
                          font_size=100, colour=COLOR_RED)

    # Game over stats
    score_text = Text(f"Score: {game_over_stats['Score']}", (WINDOW_WIDTH // 2, 185),
                      font_size=85, colour=COLOR_DARK_BLUE)
    round_text = Text(f"Rounds Completed: {game_over_stats['Rounds']}", (WINDOW_WIDTH // 2, 270),
                      font_size=48, colour=COLOR_DARK_BLUE)
    kills_text = Text(f"Enemies Killed: {game_over_stats['Kills']}", (WINDOW_WIDTH // 2, 320),
                      font_size=48, colour=COLOR_DARK_BLUE)
    flag_text = Text(f"Flags Planted: {game_over_stats['Flags']}", (WINDOW_WIDTH // 2, 370),
                     font_size=48, colour=COLOR_DARK_BLUE)
    upgrades_text = Text(f"Upgrades Purchased: {game_over_stats['Upgrades']}", (WINDOW_WIDTH // 2, 420),
                         font_size=48, colour=COLOR_DARK_BLUE)
    money_text = Text(f"Money Spent: ${game_over_stats['Money']}", (WINDOW_WIDTH // 2, 470),
                        font_size=48, colour=COLOR_DARK_BLUE)

    # Update high score if needed
    score = game_over_stats['Score']
    with open("game_save/highscore.txt", "r") as score_file:
        high_score = int(score_file.read())
    if score > high_score:
        with open("game_save/highscore.txt", "w") as score_file:
            score_file.write(str(score))

    # Create buttons
    main_menu_button = Button("Main Menu", (WINDOW_WIDTH // 2, 600),
                              300, 120)
    buttons = [main_menu_button]
    background = MenuBackground()

    while True:
        for event in pygame.event.get(): # Event loop
            if event.type == pygame.QUIT:
                return "QUIT"
            handle_mute_key(event)
            if main_menu_button.is_clicked(event):
                return "MAIN_MENU"  # Change game state to MAIN MENU

        # Update cursor
        if any(button.is_hovered() for button in buttons):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        # Animated background with a panel behind the stats
        background.draw(screen, None, (WINDOW_WIDTH // 2 - 300, 40, 600, 640))

        # Render game over text
        game_over_text.draw(screen)
        score_text.draw(screen)
        round_text.draw(screen)
        kills_text.draw(screen)
        flag_text.draw(screen)
        upgrades_text.draw(screen)
        money_text.draw(screen)

        # Render buttons
        for button in buttons:
            button.draw(screen)

        pygame.display.flip() # Update display
        clock.tick(60)

def confirmation_menu(screen: pygame.Surface, clock: pygame.time.Clock,
                      message: str, confirm_message: str, decline_message: str) -> bool:
    """
    Displays a confirmation dialog with the given message and appropriate buttons.

    :param screen: The screen where the menu is drawn.
    :param clock: The clock to be used (redundant in this menu).
    :param message: The message to display in the confirmation dialog.
    :param confirm_message: The text to display on the confirm button (e.g., "Yes").
    :param decline_message: The text to display on the decline button (e.g., "No").
    :return: True if the user clicks Yes, False if the user clicks No or closes the dialog.
    """

    pygame.mouse.set_visible(True)
    # Dialog box
    dialog_rect = pygame.Rect(0, 0, int(640 * UI_SCALE), (360 * UI_SCALE))
    dialog_rect.center = (int(WINDOW_WIDTH // 2 * UI_SCALE), int(WINDOW_HEIGHT // 2 * UI_SCALE))
    
    # Create dialog text
    wrapped_message = wrap_text(message, int(580 * UI_SCALE), int(48 * UI_SCALE))
    text_objects = []
    for i, line in enumerate(wrapped_message):
        text_objects.append(Text(line, (WINDOW_WIDTH // 2, 240 + i * 60),
                                 font_size=48, colour=COLOR_BLACK))

    # Create buttons
    confirm_button = Button(confirm_message, (WINDOW_WIDTH // 2 + 125, 440),
                            150, 80)
    cancel_button = Button(decline_message, (WINDOW_WIDTH // 2 - 125, 440),
                           150, 80)
    buttons = [confirm_button, cancel_button]

    while True:
        for event in pygame.event.get(): # Event loop
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()  # Shouldn't happen during fullscreen gameplay, but just in case
            if confirm_button.is_clicked(event):
                return True
            if cancel_button.is_clicked(event):
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False

        # Update cursor
        if any(button.is_hovered() for button in buttons):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        # Render all elements
        draw_panel(screen, dialog_rect, 255)
        for text_obj in text_objects:
            text_obj.draw(screen)
        for button in buttons:
            button.draw(screen)

        pygame.display.flip() # Update display
        clock.tick(60)

def wrap_text(text: str, max_width: int, font_size: int) -> list[str]:
    """
    Wraps the given text into multiple lines so that it fits within the specified width.

    :param text: The text to wrap.
    :param max_width: The maximum width in pixels for each line.
    :param font_size: The font size to use for measuring text width.
    :return: A list of strings, where each string is a line of wrapped text.
    """
    font = get_font(font_size)
    words = text.split(' ')
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + word + " "
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line.strip())
            current_line = word + " "

    if current_line:
        lines.append(current_line.strip())

    return lines