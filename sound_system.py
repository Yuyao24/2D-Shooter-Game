import pygame

sounds = {"button_click": "audio/button_click.wav",}

def play_sound(sound: str, volume: float) -> None:
    sound_effect = pygame.mixer.Sound(sounds[sound])
    sound_effect.set_volume(volume)
    sound_effect.play()

