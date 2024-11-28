import pygame


class GameSettings:
    """ Singleton pour les paramètres de jeu. """

    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720
    FPS = 90

    NB_PLAYER_LIVES = 5

    # Modif M14 Début : Déplacer tous les noms de fichiers vers GameSettings.
    # Chemins pour les polices
    FONT_BOOMBOX2 = "fonts/boombox2.ttf"

    # Chemins pour les images
    IMG_HUD_LIVES = "img/hud_lives.png"
    IMG_ASTRONAUT = "img/astronaut.png"
    IMG_EAST = "img/east01.png"
    IMG_FUEL_GAUGE_EMPTY = "img/fuel_gauge_empty.png"
    IMG_FUEL_GAUGE_FULL = "img/fuel_gauge_full.png"
    IMG_GATE = "img/gate.png"
    IMG_LOADING = "img/loading.png"
    IMG_OBSTACLE1 = "img/obstacle01.png"
    IMG_OBSTACLE2 = "img/obstacle02.png"
    IMG_PAD1 = "img/pad01.png"
    IMG_PAD2 = "img/pad02.png"
    IMG_PAD3 = "img/pad03.png"
    IMG_PAD4 = "img/pad04.png"
    IMG_PAD5 = "img/pad05.png"
    IMG_PUMP = "img/pump.png"
    IMG_SOUTH = "img/south01.png"
    IMG_SPACE = "img/space01.png"
    IMG_SPLASH = "img/splash.png"
    IMG_TAXI = "img/taxis.png"
    IMG_WEST = "img/west01.png"

    # Chemins pour les sons
    SND_GARY_HEY = "voices/gary_hey_01.mp3"
    SND_GARY_HEY_TAXI1 = "voices/gary_hey_taxi_01.mp3"
    SND_GARY_HEY_TAXI2 = "voices/gary_hey_taxi_02.mp3"
    SND_GARY_HEY_TAXI3 = "voices/gary_hey_taxi_03.mp3"
    SND_GARY_PAD1 = "voices/gary_pad_1_please_01.mp3"
    SND_GARY_PAD2 = "voices/gary_pad_2_please_01.mp3"
    SND_GARY_PAD3 = "voices/gary_pad_3_please_01.mp3"
    SND_GARY_PAD4 = "voices/gary_pad_4_please_01.mp3"
    SND_GARY_PAD5 = "voices/gary_pad_5_please_01.mp3"
    SND_GARY_UP = "voices/gary_up_please_01.mp3"

    #Modif M14 Fin

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(GameSettings, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, '_initialized'):
            self.screen = None
            self.pad_font = pygame.font.Font("fonts/boombox2.ttf", 11)

            self._initialized = True
