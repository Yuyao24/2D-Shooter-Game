import pygame

pygame.mixer.init() # Initialize Pygame mixer

# Preload sound effects
sound_effects: dict = {
    "button_click": pygame.mixer.Sound("audio/button_click.wav"),
    }

def play_sound(sound_name: str, volume: float) -> None:
    sound_effects[sound_name].set_volume(volume)
    sound_effects[sound_name].play()

