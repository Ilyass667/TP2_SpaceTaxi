import pygame
import random
import math

from scene import Scene
from scene_manager import SceneManager
from taxi import Taxi
from game_settings import GameSettings



class LevelLoadingScene(Scene): # M12
    """ Scène de chargement d'un niveau avec nom et animations. """

    _ZIGZAG_OFFSET = 50  # Distance horizontale de zigzag
    _ZIGZAG_COUNT = 5  # Nombre total de zigzags
    _CIRCLE_INTERVAL = 250  # Intervalle entre les boules de neige (ms)
    _FADE_OUT_DURATION = 500  # Durée de la transition audio (ms)

    def __init__(self, level: int, level_name: str) -> None:
        super().__init__()
        self._level = level
        self._level_name = level_name
        self._bg_color = (0, 0, 0) 

        # Position initiale du taxi : centre bas de l'écran
        self._taxi = Taxi((GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT - 100))
        self._zigzag_direction = 1  # 1 pour droite, -1 pour gauche
        self._zigzag_progress = 0
        self._transitioning = False
        self._taxi_stopped = False

        # Texte
        self._font = pygame.font.Font(None, 36)
        self._level_text = self._font.render(f"Niveau {self._level}: {self._level_name}", True, (255, 255, 255))
        self._text_pos = (
            GameSettings.SCREEN_WIDTH // 2 - self._level_text.get_width() // 2,
            GameSettings.SCREEN_HEIGHT // 2 - self._level_text.get_height() // 2,
        )

        # Effet boules de neige
        self._particles = []
        self._last_particle_time = pygame.time.get_ticks()

        # Musique
        self._music = pygame.mixer.Sound("snd/390539__burghrecords__dystopian-future-fx-sounds-8.wav")
        self._music_started = False
        self._fade_out_start_time = None

        # Surface pour l'affichage
        self._surface = pygame.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

    def update(self) -> None:
        if not self._music_started:
            self._music.play()
            self._music_started = True

        if self._fade_out_start_time:
            elapsed_time = pygame.time.get_ticks() - self._fade_out_start_time
            volume = max(0.0, 1.0 - (elapsed_time / LevelLoadingScene._FADE_OUT_DURATION))
            self._music.set_volume(volume)
            if volume == 0:
                self._fade_out_start_time = None

        # Effet boules de neige
        current_time = pygame.time.get_ticks()
        if current_time - self._last_particle_time > LevelLoadingScene._CIRCLE_INTERVAL:
            angle = random.uniform(0, 2 * 3.14159)
            speed = random.uniform(2, 4)
            self._particles.append({"pos": [GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2],
                                    "vel": [speed * math.cos(angle), speed * math.sin(angle)]})
            self._last_particle_time = current_time
        for particle in self._particles:
            particle["pos"][0] += particle["vel"][0]
            particle["pos"][1] += particle["vel"][1]
        self._particles = [p for p in self._particles if 0 <= p["pos"][0] <= GameSettings.SCREEN_WIDTH and
                           0 <= p["pos"][1] <= GameSettings.SCREEN_HEIGHT]

        # Déplacement du taxi
        if not self._transitioning and not self._taxi_stopped:
            self._taxi.rect.x += self._zigzag_direction * 2
            if abs(self._taxi.rect.x - GameSettings.SCREEN_WIDTH // 2) >= LevelLoadingScene._ZIGZAG_OFFSET:
                self._zigzag_direction *= -1
                self._zigzag_progress += 1
            self._taxi.rect.y -= 1

            # Si le taxi touche le texte
            if self._taxi.rect.colliderect(
                pygame.Rect(self._text_pos[0], self._text_pos[1], self._level_text.get_width(), self._level_text.get_height())
            ):
                self._fade_out_start_time = pygame.time.get_ticks()
                self._transitioning = True
                self._taxi_stopped = True  # Arrêter le taxi
                SceneManager().change_scene(f"level{self._level}", LevelLoadingScene._FADE_OUT_DURATION)

    def render(self, screen: pygame.Surface) -> None:
        screen.fill(self._bg_color)

        # Effet boules de neige
        for particle in self._particles:
            pygame.draw.circle(screen, (255, 255, 255), (int(particle["pos"][0]), int(particle["pos"][1])), 3)

        # Texte
        screen.blit(self._level_text, self._text_pos)

        # Taxi
        screen.blit(self._taxi.image, self._taxi.rect.topleft)

    def surface(self) -> pygame.Surface:
        """ Retourne la surface de la scène. """
        return self._surface
