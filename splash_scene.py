# Modification A2 demander : la trame sonore s'exécuter dejà dans l'écran noir et durant la fondu car
# le constructeur démarre déjà la musique dès que la scène est initialisée (self._music.play(loops=-1, fade_ms=1000)
# ducoup est-ce que je fait des modification quand même pour montrer que c'est fait ?





import pygame

from scene import Scene
from scene_manager import SceneManager
from file_error import FileError # C3



class SplashScene(Scene):
    """ Scène titre (splash). """

    # Modif A1 Début : Ajout de la durée pour le fondu d'entrée
    _FADE_IN_DURATION: int = 1500  # Durée du fondu (en millisecondes)
    # Modif A1 Fin

    _FADE_OUT_DURATION: int = 1500  # ms

    def __init__(self) -> None:
        try:
            super().__init__()
            self._surface = pygame.image.load("img/splash.png").convert_alpha()

            # Modif A2 Début : Initialisation de la musique pour qu'elle démarre dès l'écran noir
            self._music = pygame.mixer.Sound("snd/371516__mrthenoronha__space-game-theme-loop.wav")
            self._fade_in_start_time = pygame.time.get_ticks()  # Début du fondu
            self._music_started = False  # Indicateur pour savoir si la musique a démarré
            # Modif A2 Fin

            self._fade_out_start_time = None
            self._transitioning = False  # C1


            # Modif A1 Début : Création de la surface noire pour couvrir toute la fenêtre
            screen_size = pygame.display.get_surface().get_size()  # Récupération dynamique des dimensions
            self._black_surface = pygame.Surface(screen_size)  # Création de la surface noire
            self._black_surface.fill((0, 0, 0))  # Remplissage avec du noir
            # Modif A1 Fin

            # Modif A3 Début : Initialisation pour le texte animé
            self._font = pygame.font.Font("fonts/BoomBox2.ttf", 16)  # Taille de la police réduite
            self._text_opacity = 255  # Opacité du texte
            self._text_fading_out = True  # Indicateur de l'état du fading
            # Modif A3 Fin
        except FileNotFoundError as e: # C3
            error_message = str(e)
            filename = error_message.split("No file '")[1].split("'")[0]
            error = FileError(f"FATAL ERROR loading {filename}")
            error.run()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and not self._transitioning: # C1
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._fade_out_start_time = pygame.time.get_ticks()
                self._transitioning = True # C1
                SceneManager().change_scene("level1_load", SplashScene._FADE_OUT_DURATION)

    def update(self) -> None:
        # Modif A2 Début : Démarrer la musique dès le début du fondu
        if not self._music_started:
            self._music.play(loops=-1, fade_ms=1000)  # La musique démarre avec un fondu
            self._music_started = True  # Met à jour l'indicateur pour éviter de rejouer la musique
        # Modif A2 Fin

        # Modif A1 Début : Gestion du fondu d'entrée
        elapsed_time = pygame.time.get_ticks() - self._fade_in_start_time
        if elapsed_time < SplashScene._FADE_IN_DURATION:
            # Calcul de l'opacité (diminue de 255 à 0)
            opacity = max(0, 255 - int((elapsed_time / SplashScene._FADE_IN_DURATION) * 255))
            self._black_surface.set_alpha(opacity)
        # Modif A1 Fin

        # Modif A3 Début : Animation de l'opacité du texte
        if self._text_fading_out:
            self._text_opacity -= 2  # Réduction plus lente pour un clignotement fluide
            if self._text_opacity <= 50:  # Limite inférieure
                self._text_fading_out = False
        else:
            self._text_opacity += 2  # Augmentation plus lente
            if self._text_opacity >= 255:  # Limite supérieure
                self._text_fading_out = True
        # Modif A3 Fin

        if self._fade_out_start_time:
            elapsed_time = pygame.time.get_ticks() - self._fade_out_start_time
            volume = max(0.0, 1.0 - (elapsed_time / SplashScene._FADE_OUT_DURATION))
            self._music.set_volume(volume)
            if volume == 0:
                self._fade_out_start_time = None

    def render(self, screen: pygame.Surface) -> None:
        # Affichage de l'écran splash
        screen.blit(self._surface, (0, 0))

        # Modif A1 Début : Affichage de la surface noire pour l'effet de fondu
        elapsed_time = pygame.time.get_ticks() - self._fade_in_start_time
        if elapsed_time < SplashScene._FADE_IN_DURATION:
            screen.blit(self._black_surface, (0, 0))
        # Modif A1 Fin

        # Modif A3 Début : Affichage du texte animé avec position dynamique
        full_text = "PRESS SPACE OR RETURN TO PLAY"
        words = full_text.split()

        # Calculer la largeur totale du texte
        total_width = sum(self._font.size(word)[0] for word in words) + (len(words) - 1) * 10  # Espaces entre les mots
        screen_width, screen_height = screen.get_size()  # Dimensions réelles de l'écran
        x_offset = (screen_width - total_width) // 2  # Calcul du décalage horizontal pour centrer
        y_position = screen_height - 110  # Position 110 pixels au-dessus du bas de l'écran

        for word in words:
            if word == "SPACE" or word == "RETURN":
                color = (255, 255, 0)  # Jaune
            else:
                color = (255, 255, 255)  # Blanc

            # Contour bleu foncé
            outline_surface = self._font.render(word, True, (0, 0, 139))
            screen.blit(outline_surface, (x_offset - 2, y_position - 2))

            # Texte principal
            word_surface = self._font.render(word, True, color)
            word_surface.set_alpha(self._text_opacity)
            screen.blit(word_surface, (x_offset, y_position))

            x_offset += word_surface.get_width() + 10  # Espace entre les mots
        # Modif A3 Fin

    def surface(self) -> pygame.Surface:
        return self._surface
    