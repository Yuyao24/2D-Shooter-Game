import pygame
from settings import (AssetManager, save_game, WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_WHITE, COLOR_BLACK, COLOR_GREY,
                      COLOR_BLUE, COLOR_DARK_BLUE, COLOR_YELLOW, COLOR_RED, COLOR_GREEN,
                      COLOR_DARK_GREEN, WINDOW_CENTER)
from player import Player
from flag import Flag

class Button:
    """Button for menus."""
    def __init__(self, text: str, position: tuple[int, int], width: int, height: int,
                 colour: str = COLOR_BLUE, font_size: int = 50) -> None:
        self.text_content: str = text
        self.position: tuple[int, int] = position
        self.width: int = width
        self.height: int = height
        self.colour: str = colour
        self.font_size: int = font_size

        # Button rectangle
        self.rect: pygame.Rect = pygame.Rect(position, (width, height))
        self.rect.center = position

        # Text object
        self.text_obj: Text = Text(text, position, font_size, "#000000")

        # Clickable
        self.is_clickable: bool = True

    def draw(self, screen: pygame.Surface) -> None: 
        """Renders the button on the given surface."""
        if self.is_clickable:
            if self.is_hovered():
                pygame.draw.rect(screen, COLOR_WHITE, self.rect)
                pygame.draw.rect(screen, self.colour, self.rect, 3) # Border
                self.text_obj.draw(screen)
            else:
                pygame.draw.rect(screen, self.colour, self.rect)
                pygame.draw.rect(screen, COLOR_BLACK, self.rect, 3) # Border
                self.text_obj.draw(screen)
        else:
            pygame.draw.rect(screen, COLOR_GREY, self.rect)
            pygame.draw.rect(screen, COLOR_BLACK, self.rect, 3)  # Border
            self.text_obj.draw(screen)

    def is_clicked(self, event: pygame.event.Event) -> bool: 
        """Checks if the button was clicked in the given event."""
        if self.is_clickable:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Button 1 is left click
                if self.is_hovered():
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
        self.position: tuple[int, int] = position
        self.font_size: int = font_size
        self.colour: str | tuple[int, int, int] = colour
        self.font: pygame.font.Font = pygame.font.Font(None, font_size)

        # Text surface and rect
        self.text_surf: pygame.Surface = self.font.render(text, True, colour)
        self.text_rect: pygame.Rect = self.text_surf.get_rect(center=position)

        # Adjust text position based on anchor
        if anchor == "center":
            self.text_rect.center = position
        elif anchor == "topleft":
            self.text_rect.topleft = position
        elif anchor == "midleft":
            self.text_rect.midleft = position
        elif anchor == "topright":
            self.text_rect.topright = position
        elif anchor == "midright":
            self.text_rect.midright = position
        elif anchor == "bottomleft":
            self.text_rect.bottomleft = position
        elif anchor == "bottomright":
            self.text_rect.bottomright = position

    def draw(self, screen: pygame.Surface) -> None:
        """Renders the text on the given surface."""
        screen.blit(self.text_surf, self.text_rect)

class HUD:
    """HUD (Heads-Up Display) for displaying player health, credits, ammo, etc."""
    def __init__(self, player: Player, flag: Flag) -> None:
        # Player and flag references
        self.player: Player = player
        self.flag: Flag = flag

        self.ammo_icon: pygame.Surface = AssetManager.get_image("assets/images/ammo_icon.png")
        self.ammo_icon = pygame.transform.scale(self.ammo_icon, (12, 30))

        self.heart_icon: pygame.Surface = AssetManager.get_image("assets/images/heart_icon.png")
        self.heart_icon = pygame.transform.scale(self.heart_icon, (30, 30))

        self.compass_icon: pygame.Surface = AssetManager.get_image("assets/images/compass_arrow.png")
        self.compass_icon = pygame.transform.scale(self.compass_icon, (30, 30))

        self.round = 1

    def draw(self, screen: pygame.Surface) -> None:
        """Draws the HUD on the given surface."""
        self.health_bar(screen)
        self.ammo_counter(screen)
        self.credit_counter(screen)
        self.lives_counter(screen)
        self.reload_progress(screen)
        self.flag_compass(screen)
        self.round_counter(screen)

    def health_bar(self, screen: pygame.Surface) -> None:
        """Draws the health bar on the given surface."""

        # Calculate health bar width based on current health
        health_ratio = self.player.health / self.player.max_health
        health_bar_width = int(health_ratio * 200)

        # Red for missing health, green for current health
        max_health_bar = pygame.Rect(10, 10, 200, 20)
        current_health_bar = pygame.Rect(10, 10, health_bar_width, 20)

        # Draw health bar
        pygame.draw.rect(screen, COLOR_RED, max_health_bar)
        pygame.draw.rect(screen, COLOR_GREEN, current_health_bar)

        # Black border around health bar
        border_thickness = 3
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

        ammo_text = Text(text, (55, 678),
                         font_size=48, colour=COLOR_BLUE, anchor="midleft")

        screen.blit(self.ammo_icon, (30, 660))
        ammo_text.draw(screen)

    def credit_counter(self, screen: pygame.Surface) -> None:
        """Draws the credit counter on the given surface."""
        current_credits = self.player.money

        credit_text = Text(f"$ {current_credits}", (29, 630),
                           font_size=48, colour=COLOR_BLUE, anchor="midleft")
        credit_text.draw(screen)

    def lives_counter(self, screen: pygame.Surface) -> None:
        """Draws the lives counter on the given surface."""
        current_lives = self.player.lives
        for i in range(current_lives):
            screen.blit(self.heart_icon, (10 + i * 35, 40))

    def reload_progress(self, screen: pygame.Surface) -> None:
        """Draws the reload progress bar on the given surface."""
        if not self.player.gun.is_reloading:
            return

        now = pygame.time.get_ticks()
        progress = now - self.player.gun.reload_start_time

        # Calculate progress bar width based on reload time
        reload_progress = progress / self.player.gun.reload_time
        progress_bar_width = int(reload_progress * 100)

        bg_rect = pygame.Rect(0, 0, 100, 10)
        bg_rect.center = (WINDOW_WIDTH // 2, 430)
        progress_rect = pygame.Rect(bg_rect.left, bg_rect.top, progress_bar_width, 10)

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

        arrow_pos = pygame.math.Vector2(WINDOW_CENTER) + direction * 100

        # Rotate arrow to face flag
        rotation = direction.angle_to(pygame.math.Vector2(0, -1))
        rotated_image = pygame.transform.rotate(self.compass_icon, rotation)
        rotated_rect = rotated_image.get_rect(center=arrow_pos)

        screen.blit(rotated_image, rotated_rect)

    def round_counter(self, screen: pygame.Surface) -> None:
        """Draws the round counter on the given surface."""
        round_text = Text(f"Round: {self.round}", (WINDOW_WIDTH - 25, 35),
                         font_size=48, colour=COLOR_BLUE, anchor="midright")
        round_text.draw(screen)

def main_menu(screen: pygame.Surface, clock: pygame.time.Clock) -> str:
    """
    Displays the main menu and handles user interaction.
    
    :return: The next game state (e.g., "PLAYING", "QUIT").
    """

    pygame.mouse.set_visible(True)

    # Load high score
    try:
        with open("game_save/highscore.txt", "r") as score_file:
            high_score = score_file.read()
    except FileNotFoundError:
        high_score = "0"

    # Create high-score text
    high_score_text = Text(f"High Score: {high_score}",
                           (WINDOW_WIDTH // 2, 120), font_size=100, colour=COLOR_DARK_BLUE)

    # Load save file
    try:
        with open("game_save/save_data.txt", "r") as save_file:
            save_data = save_file.read()
    except FileNotFoundError:
        save_data = None

    # Create buttons
    resume_game_button = Button("Resume Game", (WINDOW_WIDTH // 2, 300), 300, 120)
    new_game_button = Button("New Game", (WINDOW_WIDTH // 2, 450), 300, 120)
    quit_button = Button("Quit", (WINDOW_WIDTH // 2, 600), 300, 120)
    buttons = [resume_game_button, new_game_button, quit_button]

    while True:
        for event in pygame.event.get(): # Event loop
            if quit_button.is_clicked(event) or event.type == pygame.QUIT:
                confirmed = confirmation_menu(screen, clock,
                                            "Are you sure you want to quit?")
                if confirmed:
                    return "QUIT"  # Change game state to QUIT
            if resume_game_button.is_clicked(event):
                return "PLAYING"  # Change game state to PLAYING
            if new_game_button.is_clicked(event):
                return "PLAYING"  # Change game state to PLAYING

        # Update cursor
        if any(button.is_hovered() for button in buttons):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        if not save_data:  # Disable resume button if no save data
            resume_game_button.is_clickable = False
        else:
            resume_game_button.is_clickable = True

        screen.fill(COLOR_WHITE)  # Clear screen with a white background

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
    paused_text = Text("Game Paused", (WINDOW_WIDTH // 2, 150), font_size=100, colour=COLOR_DARK_BLUE)

    # Create buttons
    resume_button = Button("Resume", (WINDOW_WIDTH // 2, 325), 300, 120)
    quit_button = Button("Save and Quit", (WINDOW_WIDTH // 2, 470), 300, 120)
    buttons = [resume_button, quit_button]

    # Create a transparent overlay
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    overlay.set_alpha(128)  # 0 : transparent, 255 : opaque
    overlay.fill((0, 0, 0))  # Black tint

    while True:
        for event in pygame.event.get(): # Event loop
            if event.type == pygame.QUIT:
                return "QUIT"
            if quit_button.is_clicked(event):
                confirmed = confirmation_menu(screen, clock, 
                                                "Are you sure you want to quit? " \
                                                "Your progress will be saved.")
                if confirmed:
                    save_game(round_num, player, stats_manager)  # Save game before quitting
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
    main_menu_button = Button("Main Menu", (WINDOW_WIDTH // 2, 600), 300, 120)
    buttons = [main_menu_button]

    while True:
        for event in pygame.event.get(): # Event loop
            if event.type == pygame.QUIT:
                return "QUIT"
            if main_menu_button.is_clicked(event):
                return "MAIN_MENU"  # Change game state to MAIN MENU

        # Update cursor
        if any(button.is_hovered() for button in buttons):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        screen.fill(COLOR_WHITE)  # Clear screen with a white background

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

def confirmation_menu(screen: pygame.Surface, clock: pygame.time.Clock, message: str) -> bool:
    """
    Displays a confirmation dialog with the given message and Yes/No buttons.

    :return: True if the user clicks Yes, False if the user clicks No or closes the dialog.
    """

    pygame.mouse.set_visible(True)
    # Dialog box
    dialog_rect = pygame.Rect(0, 0, 500, 360)
    dialog_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
    
    # Create dialog text
    wrapped_message = wrap_text(message, 400)
    text_objects = []
    for i, line in enumerate(wrapped_message):
        text_objects.append(Text(line, (WINDOW_WIDTH // 2, 240 + i * 60), font_size=48, colour=COLOR_BLACK))

    # Create buttons
    yes_button = Button("Yes", (WINDOW_WIDTH // 2 - 100, 440), 150, 80)
    no_button = Button("No", (WINDOW_WIDTH // 2 + 100, 440), 150, 80)
    buttons = [yes_button, no_button]

    while True:
        for event in pygame.event.get(): # Event loop
            if event.type == pygame.QUIT:
                return False
            if yes_button.is_clicked(event):
                return True
            if no_button.is_clicked(event):
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False

        # Update cursor
        if any(button.is_hovered() for button in buttons):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        # Draw box
        pygame.draw.rect(screen, COLOR_WHITE, dialog_rect)
        pygame.draw.rect(screen, COLOR_BLACK, dialog_rect, 3)  # Border

        # Render dialog text
        for text_obj in text_objects:
            text_obj.draw(screen)

        # Render buttons
        for button in buttons:
            button.draw(screen)

        pygame.display.flip() # Update display
        clock.tick(60)

def wrap_text(text: str, max_width: int) -> list[str]:
    """
    Wraps the given text into multiple lines so that it fits within the specified width.

    :param text: The text to wrap.
    :param font: The font used to measure text width.
    :param max_width: The maximum width in pixels for each line.
    :return: A list of strings, where each string is a line of wrapped text.
    """
    font = pygame.font.Font(None, 50)  # Use a default font and size for measurement
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