import pygame

sound_effects = {"button_click": "audio/button_click.wav",}

def play_sound(sound_name: str, volume: float) -> None:
    sound_effect = pygame.mixer.Sound(sound_effects[sound_name])
    sound_effect.set_volume(volume)
    sound_effect.play()

