import pygame
import random
from settings import (save_game_data, UI_SCALE,WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_CENTER, COLOR_WHITE, COLOR_BLACK,
                      COLOR_GREY, COLOR_BLUE, COLOR_DARK_BLUE, COLOR_GREEN, COLOR_DARK_GREEN,
                      COLOR_RED, COLOR_YELLOW, COLOR_GOLD)
from menus import Button, Text, confirmation_menu
from player import Player
from typing import Callable
from stats_manager import StatsManager


class Upgrade:
    """Upgrade with name, description, cost, tier, and effect function."""

    def __init__(self, name, description, cost, tier, effect_func) -> None:
        self.name: str = name
        self.description: str = description
        self.cost: int = cost
        self.tier: int = tier  # 1: common, 2: rare, 3: legendary
        self.effect_func: Callable = effect_func  # Function that applies upgrade to player

    def apply(self, player) -> None:
        """Applies this upgrade's effect to the player."""
        self.effect_func(player)

class UpgradeCard:
    """A card representing an upgrade in the shop."""

    def __init__(self, upgrade: Upgrade, position: tuple,
                 width: int, height: int) -> None:
        self.upgrade = upgrade
        self.position = position
        self.width = width
        self.height = height
        self.selected: bool = False

        # Card rect
        self.rect: pygame.Rect = pygame.Rect(0, 0, width, height)
        self.rect.center = position

        tier_colors: dict = {
            1: "#87CEEB",  # Common - Light Blue
            2: "#9932CC",  # Rare - Purple
            3: "#F43C3C"   # Legendary - Red
        }

        border_color: dict = {
            1: "#2EB0E4",  # Darker variants
            2: "#8100C1",
            3: "#FF0000"
        }

        # Tier colors
        self.color = tier_colors[upgrade.tier]
        self.border_color = border_color[upgrade.tier]

    def draw(self, screen) -> None:
        """Draws the upgrade card."""

        # Draw card background with tier color
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, self.border_color, self.rect, int(4 * UI_SCALE))

        if self.selected:
            # Highlighted border effect
            pygame.draw.rect(screen, COLOR_BLACK, self.rect.inflate(int(10 * UI_SCALE), int(10 * UI_SCALE)), int(5 * UI_SCALE))

        # Draw upgrade name at top
        name_text = Text(self.upgrade.name, (self.position[0], self.position[1] - int(140 * UI_SCALE)),
                         font_size=int(40 * UI_SCALE), colour=COLOR_BLACK)
        name_text.draw(screen)

        # Cost text
        cost_text = Text(f"${self.upgrade.cost}", (self.position[0], self.position[1] + int(150 * UI_SCALE)),
                              font_size=int(32 * UI_SCALE), colour=COLOR_BLACK)
        cost_text.draw(screen)

        # Description text
        desc_lines = self._wrap_text(self.upgrade.description, self.width - int(30 * UI_SCALE))
        desc_y = self.position[1] - int(20 * UI_SCALE)
        for line in desc_lines:
            desc_line = Text(line, (self.position[0], desc_y),
                             font_size=int(24 * UI_SCALE), colour=COLOR_BLACK)
            desc_line.draw(screen)
            desc_y += 28 * UI_SCALE  # Line spacing

    def is_clicked(self, event) -> bool:
        """Checks if the card was clicked."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.selected = not self.selected
                return True
        return False

    def is_hovered(self) -> bool:
        """Checks if mouse is hovering over the card or button."""
        return self.rect.collidepoint(pygame.mouse.get_pos())

    # noinspection PyMethodMayBeStatic
    def _wrap_text(self, text: str, max_width: int) -> list[str]:
        """Wraps text to fit within max_width, splitting on commas and spaces."""
        # First split on commas and capitalize each part
        parts = [part.strip().capitalize() for part in text.split(',')]

        lines = []
        font = pygame.font.Font(None, int(24 * UI_SCALE))

        for part in parts:
            words = part.split()
            current_line = ""

            for word in words:
                test = current_line + " " + word if current_line else word
                if font.size(test)[0] < max_width:
                    current_line = test
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word

            if current_line:
                lines.append(current_line)

        return lines[:4]  # Max 4 lines

def select_random_upgrades(all_upgrades, player: Player) -> list[Upgrade]:
    """Selects 3 random upgrades with weighted probabilities, filtering out unavailable toggles."""

    # Filter unavailable upgrades
    available = []
    for upgrade in all_upgrades:
        # Check toggle upgrades
        if upgrade.name == "Holy Trinity" and player.has_trinity:
            continue
        if upgrade.name == "Adrenaline Rush" and player.has_adrenaline:
            continue
        if upgrade.name == "Auto Clicker" and player.has_auto_shoot:
            continue
        # Check Extra Life - only show if player doesn't have 5 lives
        if upgrade.name == "Extra Life" and player.lives >= 5:
            continue

        available.append(upgrade)

    # Need at least 3 upgrades available
    if len(available) < 3:
        return available  # Return what we have

    selected = []
    for i in range(3):
        weights = [70 if u.tier == 1  # Common x75
                   else 20 if u.tier == 2  # Rare x25
                   else 10 for u in available]  # Legendary x10
        choice = random.choices(available, weights=weights, k=1)[0]
        selected.append(choice)
        available.remove(choice)

    return selected

def create_upgrade_list() -> list[Upgrade]:
    """Creates list of all possible upgrades."""

    upgrades = [
        Upgrade(
            "Health Boost",
            "Max health +50",
            200, 1,
            lambda p: setattr(p, 'max_health', p.max_health + 50)
        ),
        Upgrade(
            "Damage Boost",
            "Damage +20%",
            600, 1,
            lambda p: setattr(p.gun, 'damage', p.gun.damage * 1.2)
        ),
        Upgrade(
            "Fire Rate Boost",
            "Shoot Cooldown -20%",
            550, 1,
            lambda p: setattr(p.gun, 'fire_rate', p.gun.fire_rate * 0.8)
        ),
        Upgrade(
            "Speed Boost",
            "Movement speed +15%",
            300, 1,
            lambda p: setattr(p, 'speed', p.speed * 1.15)
        ),
        Upgrade(
            "Quick-Silver",
            "Bullet speed +25%",
            300, 1,
            lambda p: setattr(p.gun, 'bullet_speed', p.gun.bullet_speed * 1.25)
        ),
        Upgrade(
            "Toughness",
            "Damage taken -10%",
            400, 1,
            lambda p: setattr(p, 'damage_mult', p.damage_mult * 0.9)
        ),
        Upgrade(
            "Quick Reload",
            "Reload time -20%",
            450, 1,
            lambda p: setattr(p.gun, 'reload_time', p.gun.reload_time * 0.8)
        ),
        Upgrade(
            "Long Shot",
            "Bullet range +30%",
            150, 1,
            lambda p: setattr(p.gun, 'range', p.gun.range * 1.3)
        ),
        Upgrade(
            "Magazine Boost",
            "Magazine size +5",
            550, 1,
            lambda p: setattr(p.gun, 'max_ammo', p.gun.max_ammo + 5)
        ),
        Upgrade(
            "Gold Gold Gold",
            "Money earned +10%",
            1500, 2,
            lambda p: setattr(p, 'money_mult', p.money_mult * 1.1)
        ),
        Upgrade(
            "Return Policy",
            "5% chance to not consume ammo on shot",
            800, 2,
            lambda p: setattr(p.gun, 'ammo_saver_chance', p.gun.ammo_saver_chance + 0.05)
        ),
        Upgrade(
            "Tank",
            "Max health +50%, Damage -20%",
            1200, 2,
            lambda p: (setattr(p, 'max_health', p.max_health * 1.5),
                       setattr(p.gun, 'damage', p.gun.damage * 0.8))
        ),
        Upgrade(
            "Berserker",
            "Damage +50%, Max health -25%",
            1500, 2,
            lambda p: (setattr(p.gun, 'damage', p.gun.damage * 1.5),
                       setattr(p, 'max_health', p.max_health * 0.75))
        ),
        Upgrade(
            "Piercing Rounds",
            "Bullets pierce 1 additional enemy",
            1800, 2,
            lambda p: setattr(p.gun, 'piercing', p.gun.piercing + 1)
        ),
        Upgrade(
            "Vampiric Touch",
            "+10 HP on enemy kill",
            1600, 2,
            lambda p: setattr(p, 'life_steal', 10)
        ),
        Upgrade(
            "Insta-Reload",
            "+10% chance to reload instantly when running out of ammo",
            1200, 2,
            lambda p: setattr(p.gun, 'insta_reload_chance', p.gun.insta_reload_chance + 0.1)
        ),
        Upgrade(
            "Lucky Shot",
            "+5% chance to instantly kill enemies",
            2000, 3,
            lambda p: setattr(p.gun, 'insta_kill_chance', p.gun.insta_kill_chance + 0.05)
        ),
        Upgrade(
            "Shrapnel Rounds",
            "Bullets deal +20% area damage",
            4200, 3,
            lambda p: setattr(p.gun, 'area_damage', p.gun.area_damage + 0.2)
        ),
        Upgrade(
            "Extra Life",
            "Gain +1 life",
            3000, 3,
            lambda p: (setattr(p, 'lives', p.lives + 1))
        ),
        Upgrade(
            "Holy Trinity",
            "Last 3 shots in magazine are one-shot kills, -25 ammo capacity",
            3500, 3,
            lambda p: (setattr(p.gun, 'trinity', True),
                       setattr(p, 'has_trinity', True),
                       setattr(p.gun, 'max_ammo', p.gun.max_ammo - 25))
        ),
        Upgrade(
            "Adrenaline",
            "Movement speed +25% when below 30% health",
            2200, 3,
            lambda p: (setattr(p, 'adrenaline', True),
                       setattr(p, 'has_adrenaline', True))
        ),
        Upgrade(
            "Auto Clicker",
            "Automatically shoots when mouse button held down, +50% fire rate",
            10000, 3,
            lambda p: (setattr(p.gun, 'auto_shoot', True),
                       setattr(p.gun, 'fire_rate', p.gun.fire_rate * 0.5),
                       setattr(p, 'has_auto_shoot', True))
        )
        ]

    return upgrades

def upgrade_menu(screen: pygame.Surface, clock: pygame.time.Clock,
                 round_num: int, player: Player, stats_manager: StatsManager,
                 forced_upgrades: list[str] = None) -> str:
    """Displays the upgrade menu where players can purchase upgrades between rounds."""
    pygame.mouse.set_visible(True)

    upgrades = create_upgrade_list()

    # If forced_upgrades is provided, only offer those upgrades. Otherwise, select randomly.
    if forced_upgrades is None:
        offered_upgrades = select_random_upgrades(upgrades, player)
    else:
        offered_upgrades = [u for u in upgrades if u.name in forced_upgrades]


    card_spacing = 350 * UI_SCALE
    start_x = WINDOW_WIDTH // 2 - card_spacing

    upgrade_cards = []
    for i, upgrade in enumerate(offered_upgrades):
        x_pos = start_x + (i * card_spacing)
        upgrade_cards.append(UpgradeCard(upgrade, (x_pos, int(360 * UI_SCALE)),
                                         int(250 * UI_SCALE), int(350 * UI_SCALE)))

    # Buttons
    quit_button = Button("Quit Game", (int(200 * UI_SCALE), WINDOW_HEIGHT - int(100 * UI_SCALE)),
                         200, 70,
                         colour=COLOR_BLUE, font_size=32)
    buy_button = Button("Buy Selected Upgrades", (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 100),
                        300, 70, colour=COLOR_GREEN, font_size=32)
    skip_button = Button("Skip", (WINDOW_WIDTH - 200, WINDOW_HEIGHT - 100), 200, 70,
                         colour=COLOR_BLUE, font_size=32)
    buttons = [quit_button, buy_button, skip_button]

    # Buy Upgrades Text
    buy_upgrades_text = Text("Buy Upgrades", (WINDOW_WIDTH // 2, 100),
                             font_size=80, colour=COLOR_BLACK)

    # Credits
    credits_text = Text(f"Credits: ${player.money}", (30, 40), font_size=48,
                        anchor="midleft", colour=COLOR_YELLOW)

    while True:

        # Calculate total cost of selected upgrades
        selected_cards = [card for card in upgrade_cards if card.selected]
        total_cost = sum(card.upgrade.cost for card in selected_cards)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            for card in upgrade_cards:
                # Check if card is clicked. Selection toggle handled inside card class.
                card.is_clicked(event)
            if quit_button.is_clicked(event):
                confirmed = confirmation_menu(screen, clock,
                                            "Are you sure you want to quit? "
                                            "Your progress will be saved.",
                                            "Quit", "Cancel")
                if confirmed:
                    save_game_data(round_num, player, stats_manager,
                              in_upgrade_menu=True, offered_upgrades=offered_upgrades)  # Save game before quitting
                    return "MAIN_MENU"  # Go back to main menu
            if buy_button.is_clicked(event):
                if total_cost > player.money or not selected_cards:
                    continue  # Shouldn't happen due to button state, but double check

                for card in selected_cards:
                    player.update_money(-card.upgrade.cost)
                    stats_manager.update_money(card.upgrade.cost)
                    card.upgrade.apply(player)
                    stats_manager.update_upgrades()

                pygame.mouse.set_visible(False)
                return "CONTINUE"  # Proceed to next round
            if skip_button.is_clicked(event):
                pygame.mouse.set_visible(False)
                return "CONTINUE"  # Proceed to next round

        screen.fill(COLOR_WHITE)

        # Draw upgrade cards + buttons
        for item in (upgrade_cards + buttons):
            item.draw(screen)

        # Draw text
        buy_upgrades_text.draw(screen)
        credits_text.draw(screen)

        # Update cursor
        if any(item.is_hovered() for item in (upgrade_cards + buttons)):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        # Draw total cost if upgrades selected
        if selected_cards:
            total_text = Text(f"Total: ${total_cost}", (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 160),
                              font_size=36,
                              colour=COLOR_GREEN if player.money >= total_cost else COLOR_RED)
            total_text.draw(screen)

        # Disable buy button if not enough money
        if player.money < total_cost or not selected_cards:
            buy_button.is_clickable = False
        else:
            buy_button.is_clickable = True

        pygame.display.flip()
        clock.tick(60)
