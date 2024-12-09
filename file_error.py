import pygame
import threading
from game_settings import GameSettings

class FileError: # C3
    def __init__(self, error_message):
        self._error_message = error_message
        self._countdown_step = 1  # Pas du décompte (en secondes)

        self._width = GameSettings.SCREEN_WIDTH
        self._height = GameSettings.SCREEN_HEIGHT
        self._screen = pygame.display.set_mode((self._width, self._height))
        pygame.display.set_caption("Erreur")
        self._clock = pygame.time.Clock()
        self._running = True
        self._countdown = 10

        self._stop_event = threading.Event()

        # Lancement du thread de décompte
        self._countdown_thread = threading.Thread(target=self._countdown_timer)
        self._countdown_thread.daemon = True
        self._countdown_thread.start()

    def _countdown_timer(self):
        """ Fil d'exécution pour gérer le décompte. """
        while self._countdown > 0 and self._running:
            self._stop_event.wait(self._countdown_step) 
            if not self._running:  # Arrête si le programme est terminé
                break
            self._countdown -= self._countdown_step
        self._running = False  # Termine le programme si le décompte atteint zéro

    def run(self):
        """ Lance le décompte. 
        !!! IL FAUT PARFOIS PATIENTER POUR LA FIN DE L'ÉXECUTION DU THREAD !!! """
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    self._running = False
                    pygame.quit()
                    return
            self._update_display()
            self._clock.tick(GameSettings.FPS) / 1000


    def _update_display(self):
        """ Met à jour l'affichage """
        self._screen.fill((0, 0, 0))

        self._draw_text(self._error_message, (255, 0, 0), (self._width // 2, self._height // 3))

        countdown_message = f"Program will be terminated in {self._countdown} seconds (or Press ESCAPE to terminate now)."
        self._draw_text(countdown_message, (255, 204, 204), (self._width // 2, self._height - 30))

        pygame.display.flip()

    def _draw_text(self, text, color, position):
        """ Dessine le texte """
        font = pygame.font.Font(None, 36)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=position)
        self._screen.blit(text_surface, text_rect)
