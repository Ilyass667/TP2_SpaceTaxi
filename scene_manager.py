import pygame
import os

from fade import Fade
from scene import Scene


class SceneManager:
    """ Singleton pour la gestion des scènes. """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SceneManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, '_initialized'):
            self._scenes = {}
            self._current_scene = None
            self._next_scene = None

            self._fade = None
            self._transitioning = False

            self._initialized = True
            self._last_print_time = pygame.time.get_ticks()


    def add_scene(self, name: str, scene: Scene) -> None:
        self._scenes[name] = scene

    def set_scene(self, name: str) -> None:
        self._current_scene = self._scenes.get(name, self._current_scene)

    def change_scene(self, name: str, fade_duration: int = 0) -> None:
        if self._current_scene and self._current_scene != self._next_scene:
            self._remove_unused_scene(self._current_scene)

        self._next_scene = self._scenes.get(name, self._current_scene)
        self._fade = Fade(self._current_scene, self._next_scene)
        self._fade.start(fade_duration)
        self._transitioning = True

    def update(self) -> None:
        if self._current_scene:
            self._current_scene.update()

        if self._next_scene:
            self._next_scene.update()

        if self._transitioning:
            self._fade.update()

            if not self._fade.is_fading():
                if self._current_scene and self._current_scene != self._next_scene:
                    self._remove_unused_scene(self._current_scene)

                self._current_scene, self._next_scene = self._next_scene, None
                self._transitioning = False

        # self.print_scenes_periodically()

    def render(self, screen: pygame.Surface) -> None:
        if self._current_scene:
            self._current_scene.render(screen)
        if self._next_scene:
            self._next_scene.render(screen)

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._current_scene:
            self._current_scene.handle_event(event)

    def _remove_unused_scene(self, scene: Scene) -> None:
        """Supprime une scène qui n'est plus utilisée sans nettoyage explicite."""
        if scene:
            # Supprime la scène du dictionnaire des scènes
            for key, value in self._scenes.items():
                if value == scene:
                    del self._scenes[key]
                    break
    
    # Pour Debug
    def print_scenes_periodically(self) -> None:
        """Print les scènes toutes les 3 secondes (3000 ms)."""
        current_time = pygame.time.get_ticks()
        if current_time - self._last_print_time >= 3000:
            self._last_print_time = current_time
            os.system("cls")
            for key, value in self._scenes.items():
                print(f"Key: {key}, Value: {value}")
