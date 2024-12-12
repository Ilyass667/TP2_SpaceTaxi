import sys

import pygame
from scene import Scene


class GameOverScene(Scene):
    """ Scène affichée lorsque le jeu est terminé. """

    def __init__(self, message: str) -> None:
        """
        Initialise une instance de la scène GAME OVER.
        :param message: Message à afficher dans la scène.
        """
        super().__init__()
        self._message = message
        self._font = pygame.font.Font(None, 72)  # Police par défaut, taille 72
        self._text_surface = self._font.render(self._message, True, (255, 0, 0))  # Texte rouge
        self._text_rect = self._text_surface.get_rect(center=(640, 360))  # Centré à l'écran
        self._background_color = (0, 0, 0)  # Fond noir

    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Gère les événements PyGame.
        Permet de quitter le jeu ou de réinitialiser via la touche Entrée.
        """
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            pygame.quit()
            sys.exit(0)  # Quitte le jeu si Enter est pressé

    def render(self, screen: pygame.Surface) -> None:
        """
        Effectue le rendu de la scène GAME OVER.
        :param screen: Surface PyGame.
        """
        screen.fill(self._background_color)
        screen.blit(self._text_surface, self._text_rect)

    def update(self) -> None:
        """
        Méthode vide, car aucun élément ne doit être mis à jour.
        """
        pass

    def surface(self) -> pygame.Surface:
        """
        Retourne une surface vide, car cette méthode est abstraite dans la classe de base.
        """
        return pygame.Surface((0, 0))
