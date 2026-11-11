import random
import pygame

SFX_DIR = "assets/audio/sfx/"
MUSIC_DIR = "assets/audio/music/"

# name: (list of files (one is picked at random), volume, minimum seconds between plays)
SOUNDS: dict[str, tuple[list[str], float, float]] = {
    # Player
    "shoot":        (["shoot.ogg"], 0.35, 0.03),
    "reload":       (["reload.ogg"], 0.6, 0.1),
    "reload_done":  (["reload_done.ogg"], 0.6, 0.1),
    "step":         ([f"step{i}.ogg" for i in range(4)], 0.12, 0.1),
    "hurt":         (["hurt.ogg"], 0.6, 0.12),
    # Enemies
    "enemy_hit":    (["enemy_hit1.ogg", "enemy_hit2.ogg"], 0.35, 0.04),
    "enemy_die":    (["enemy_die.ogg"], 0.5, 0.05),
    "enemy_shoot":  (["enemy_shoot.ogg"], 0.25, 0.08),
    "brute_slam":   (["brute_slam.ogg"], 0.7, 0.15),
    "alert":        (["alert.ogg"], 0.25, 0.3),
    "explosion":    (["explosion.ogg"], 0.5, 0.08),
    "coin":         (["coin.ogg"], 0.35, 0.06),
    # Flag & rounds
    "tick":         (["tick.ogg"], 0.5, 0.2),
    "flag_planted": (["flag_planted.ogg"], 0.7, 0.5),
    "flag_hit":     (["flag_hit.ogg"], 0.3, 0.25),
    "round_won":    (["round_won.ogg"], 0.7, 0.5),
    "round_lost":   (["round_lost.ogg"], 0.7, 0.5),
    # UI
    "click":        (["click.ogg"], 0.6, 0.05),
    "hover":        (["hover.ogg"], 0.3, 0.05),
    "select":       (["select.ogg"], 0.5, 0.05),
    "buy":          (["buy.ogg"], 0.7, 0.2),
}

MUSIC: dict[str, tuple[str, float]] = {
    "menu":   ("menu.mp3", 0.35),
    "battle": ("battle.mp3", 0.25),
}

HEARING_DISTANCE = 1100  # World pixels at which positional sounds fade out completely


class Audio:
    """
    Plays sound effects and music. If no audio device is available the game
    simply runs silently. Press M in game or in the menus to mute / unmute.
    """
    enabled: bool = False
    muted: bool = False
    listener: pygame.Vector2 | None = None  # Usually the player's position
    _sounds: dict[str, list[pygame.mixer.Sound]] = {}
    _last_played: dict[str, int] = {}
    _current_music: str | None = None

    @classmethod
    def init(cls) -> None:
        """Initialises the mixer and loads every sound effect."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(44100, -16, 2, 512)
            pygame.mixer.set_num_channels(32)
            for name, (files, volume, _) in SOUNDS.items():
                cls._sounds[name] = []
                for file in files:
                    sound = pygame.mixer.Sound(SFX_DIR + file)
                    sound.set_volume(volume)
                    cls._sounds[name].append(sound)
            cls.enabled = True
        except (pygame.error, FileNotFoundError) as error:
            print(f"Audio disabled: {error}")
            cls.enabled = False

    @classmethod
    def play(cls, name: str, position=None, volume: float = 1.0) -> None:
        """
        Plays a sound effect.

        :param name: Name of the sound (key of SOUNDS).
        :param position: Optional world position; the sound gets quieter further from the listener.
        :param volume: Extra volume multiplier (0-1).
        """
        if not cls.enabled or cls.muted or name not in cls._sounds:
            return

        # Don't play the same sound many times in the same instant
        now = pygame.time.get_ticks()
        if now - cls._last_played.get(name, -100000) < SOUNDS[name][2] * 1000:
            return

        if position is not None and cls.listener is not None:
            distance = cls.listener.distance_to(position)
            volume *= max(0.0, 1 - distance / HEARING_DISTANCE)
            if volume <= 0.02:
                return

        channel = random.choice(cls._sounds[name]).play()
        if channel is not None:
            channel.set_volume(volume)
            cls._last_played[name] = now

    @classmethod
    def music(cls, track: str) -> None:
        """Starts looping a music track (does nothing if it is already playing)."""
        if not cls.enabled or track == cls._current_music:
            return
        file, volume = MUSIC[track]
        try:
            pygame.mixer.music.load(MUSIC_DIR + file)
            pygame.mixer.music.set_volume(0 if cls.muted else volume)
            pygame.mixer.music.play(-1, fade_ms=1000)
            cls._current_music = track
        except pygame.error as error:
            print(f"Could not play music: {error}")

    @classmethod
    def toggle_mute(cls) -> None:
        """Mutes or unmutes all sound and music."""
        cls.muted = not cls.muted
        if cls.enabled:
            volume = MUSIC[cls._current_music][1] if cls._current_music else 0
            pygame.mixer.music.set_volume(0 if cls.muted else volume)
            if cls.muted:
                pygame.mixer.stop()
