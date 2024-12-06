import pygame
import time
import configparser  # Modif M5 Début : Import pour lire le fichier de configuration
# Modif M5 Fin
import threading  # Modif A8 Début import pour le fil d'exécution
#Modif A8 Fin
from astronaut import Astronaut
from game_settings import GameSettings
from gate import Gate
from hud import HUD
from obstacle import Obstacle
from pad import Pad
from pump import Pump
from scene import Scene
from scene_manager import SceneManager
from taxi import Taxi


class LevelScene(Scene):
    """ Un niveau de jeu. """

    _FADE_OUT_DURATION: int = 500  # ms
    _TIME_BETWEEN_ASTRONAUTS: int = 5  # s

    def __init__(self, level: int) -> None:
        """
        Initialise une instance de niveau de jeu.
        :param level: le numéro de niveau
        """
        super().__init__()
        self._level = level

        self._processed_pads = set()        # Modif A8 Début:
        # Variables pour gérer l'affichage du texte avec effets
        self._text_to_display = None
        self._text_alpha = 0
        self._text_rect = None
        self._text_visible = False
        # Modif A8 Fin:


        self._settings = GameSettings()
        self._hud = HUD()

        self._taxi = Taxi((self._settings.SCREEN_WIDTH / 2, self._settings.SCREEN_HEIGHT / 2))

        # Modif M5 Début : Initialiser _music_started par défaut
        self._music_started = False
        self._fade_out_start_time = None
        # Modif M5 Fin

        # Modif M5 Début : Charger la configuration depuis un fichier
        level_file = f"levels/level{self._level}.cfg"  # Dossier
        self._load_level_config(level_file)
        # Modif M5 Fin

        self._reinitialize()
        self._hud.visible = True

    def _evaluate_position(self, expr: str) -> int:

        return eval(expr, {"SCREEN_WIDTH": self._settings.SCREEN_WIDTH,
                           "SCREEN_HEIGHT": self._settings.SCREEN_HEIGHT})

    # Modif M5 Début : Nouvelle méthode pour charger les données du fichier de configuration
    def _load_level_config(self, file_name: str) -> None:
        """
        Charge les données du niveau à partir d'un fichier de configuration.
        :param file_name: nom du fichier de configuration.
        """
        config = configparser.ConfigParser()
        config.read(file_name)

        # Charger le fond et la musique
        self._surface = pygame.image.load(config['Level']['background']).convert_alpha()
        self._music = pygame.mixer.Sound(config['Level']['music'])

        # Charger la gate
        gate_data = config['Gate']
        gate_position = tuple(self._evaluate_position(pos) for pos in gate_data['position'].split(','))
        self._gate = Gate(gate_data['image'], gate_position)

        # Charger les obstacles
        self._obstacles = []
        for key, value in config['Obstacles'].items():
            image, x, y = value.split(',')
            position = (self._evaluate_position(x), self._evaluate_position(y))
            self._obstacles.append(Obstacle(image, position))
        self._obstacle_sprites = pygame.sprite.Group(self._obstacles)

        # Charger les pumps
        self._pumps = []
        for key, value in config['Pumps'].items():
            image, x, y = value.split(',')
            position = (self._evaluate_position(x), self._evaluate_position(y))
            self._pumps.append(Pump(image, position))
        self._pump_sprites = pygame.sprite.Group(self._pumps)

        # Charger les pads
        self._pads = []
        for key, value in config['Pads'].items():
            number, image, x, y, fuel, cash = value.split(',')
            position = (self._evaluate_position(x), self._evaluate_position(y))
            self._pads.append(Pad(int(number), image, position, int(fuel), int(cash)))
        self._pad_sprites = pygame.sprite.Group(self._pads)

    # Modif M5 Fin

    def handle_event(self, event: pygame.event.Event) -> None:
        """ Gère les événements PyGame. """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and self._taxi.is_destroyed():
                self._taxi.reset()
                self._retry_current_astronaut()
                return

        if self._taxi:
            self._taxi.handle_event(event)

    def update(self) -> None:
        """
        Met à jour le niveau de jeu. Cette méthode est appelée à chaque itération de la boucle de jeu.
        """
        if not self._music_started:
            self._music.play(-1)
            self._music_started = True

        if self._fade_out_start_time:
            elapsed_time = pygame.time.get_ticks() - self._fade_out_start_time
            volume = max(0.0, 1.0 - (elapsed_time / LevelScene._FADE_OUT_DURATION))
            self._music.set_volume(volume)
            if volume == 0:
                self._fade_out_start_time = None

        if self._taxi is None:
            return

        if self._astronaut:
            self._astronaut.update()
            self._hud.set_trip_money(self._astronaut.get_trip_money())

            if self._astronaut.is_onboard():
                self._taxi.board_astronaut(self._astronaut)
                # Modif A8 Début:
                # Afficher le texte "Pad X Please" lorsque l'astronaute monte dans le taxi
                if self._astronaut.target_pad:
                    pad_number = self._astronaut.target_pad.number
                    self._display_pad_request(f"PAD {pad_number} PLEASE", pad_number)
                # Modif A8 Fin:


                if self._astronaut.target_pad is Pad.UP:
                    if self._gate.is_closed():
                        self._gate.open()
                    elif self._taxi.has_exited():
                        self._taxi.unboard_astronaut()
                        self._taxi = None
                        self._fade_out_start_time = pygame.time.get_ticks()
                        SceneManager().change_scene(f"level{self._level + 1}_load", LevelScene._FADE_OUT_DURATION)
                        return
            elif self._astronaut.has_reached_destination():
                if self._nb_taxied_astronauts < len(self._astronaut_data) - 1:
                    self._nb_taxied_astronauts += 1
                    self._astronaut = None
                    self._last_taxied_astronaut_time = time.time()
            elif self._taxi.hit_astronaut(self._astronaut):
                # Modif A11 Début:
                self._astronaut.react_to_collision()
                # Modif A11 Fin
                self._retry_current_astronaut()
            # Modif: C9 Début
            elif self._taxi.burn_astronaute(self._astronaut):  # Vérifier si le réacteur brûle l'astronaute
                print("Un astronaute a été brûlé par un réacteur !")
                self._astronaut.react_to_collision()  # Réaction de l'astronaute
                self._retry_current_astronaut()
            # Modif: C9 Fin
            elif self._taxi.pad_landed_on:
                if self._taxi.pad_landed_on.number == self._astronaut.source_pad.number:
                    if self._astronaut.is_waiting_for_taxi():
                        self._astronaut.jump(self._taxi.get_door_x()) # C7
            elif self._astronaut.is_jumping_on_starting_pad():
                self._astronaut.wait()
        else:
            if time.time() - self._last_taxied_astronaut_time >= LevelScene._TIME_BETWEEN_ASTRONAUTS:
                # Début modif M15 : Créer l'astronaute dynamiquement au besoin
                if self._nb_taxied_astronauts < len(self._astronaut_data):
                    data = self._astronaut_data[self._nb_taxied_astronauts]
                    self._astronaut = Astronaut(*data)
                    print(f"Astronaute {self._nb_taxied_astronauts + 1} a été créé.")  # Afficher un message
                # Fin modif M15

        # Mettez à jour le taxi uniquement s'il existe
        if self._taxi:
            self._taxi.update()

            # Modif A11 Début:
            is_astronaut_onboard = self._astronaut and self._astronaut.is_onboard()

            # Vérification du crash dû au manque d'essence
            # Modif Début A14
            if self._taxi.crash_due_to_fuel():
                print("Crash dû au manque d'essence.")
                self._hud.loose_live()
                self._taxi._fuel_level = 1.0  # Réinitialiser le niveau d'essence
                if is_astronaut_onboard:
                    self._astronaut.react_to_collision()
                self._retry_current_astronaut()
                return
            # Modif Fin A14

            for pad in self._pads:
                if self._taxi.land_on_pad(pad):
                    pass
                elif self._taxi.crash_on(pad): # M4
                    self._hud.loose_live()
                    if is_astronaut_onboard:
                        self._astronaut.set_trip_money(0)
                        self._astronaut.react_to_collision()

            for obstacle in self._obstacles:
                if self._taxi.crash_on(obstacle): # M4
                    self._hud.loose_live()
                    if is_astronaut_onboard:
                        self._astronaut.set_trip_money(0)
                        self._astronaut.react_to_collision()

            if self._gate.is_closed() and self._taxi.crash_on(self._gate): # M4
                self._hud.loose_live()
                if is_astronaut_onboard:
                        self._astronaut.set_trip_money(0)
                        self._astronaut.react_to_collision()
            # Modif A11 Fin

            for pump in self._pumps:
                if self._taxi.crash_on(pump): # M4
                    self._hud.loose_live()
                    if is_astronaut_onboard:
                        self._astronaut.set_trip_money(0)
                        self._astronaut.react_to_collision()
                elif self._taxi.refuel_from(pump):
                    # Modif A15 Début : Remplissage progressif du réservoir
                    if self._taxi._fuel_level < 2.0:
                        self._taxi._fuel_level += 0.003  # Remplir progressivement
                        self._hud.update_fuel(self._taxi._fuel_level)  # Mettre à jour l'affichage du HUD
                    # Modif A15 Fin
                

    def render(self, screen: pygame.Surface) -> None:
        """
        Effectue le rendu du niveau pour l'afficher à l'écran.
        :param screen: écran (surface sur laquelle effectuer le rendu)
        """
        screen.blit(self._surface, (0, 0))
        self._obstacle_sprites.draw(screen)
        self._gate.draw(screen)
        self._pump_sprites.draw(screen)
        self._pad_sprites.draw(screen)
        if self._taxi:
            self._taxi.draw(screen)
        if self._astronaut:
            self._astronaut.draw(screen)
        self._hud.render(screen)

        # Afficher le texte si visible
        if self._text_visible and self._text_to_display:
            text_surface = self._text_to_display.copy()
            text_surface.set_alpha(self._text_alpha)
            screen.blit(text_surface, self._text_rect)

    def surface(self) -> pygame.Surface:
        return self._surface

    def _reinitialize(self) -> None:
        """ Initialise (ou réinitialise) le niveau. """
        self._nb_taxied_astronauts = 0
        self._retry_current_astronaut()
        self._hud.reset()

    def _retry_current_astronaut(self) -> None:
        """ Replace le niveau dans l'état où il était avant la course actuelle. """
        self._gate.close()

        self._processed_pads.clear()

        # Début modif M15 : Sauvegarder les données des astronautes au lieu de les créer directement
        
        self._astronaut_data = [ # C11 self_gate 
            (self._pads[3], self._pads[0], self._gate, 10.00),
            (self._pads[0], Pad.UP, self._gate, 10.00)
        ]
        # Fin modif M15

        self._last_taxied_astronaut_time = time.time()
        self._astronaut = None


#Modif A8 Début:
    def _display_pad_request(self, text: str, pad_number: int) -> None:
        """
        Affiche un texte au centre de l'écran avec des effets visuels :
        - Apparition graduelle (0.25 s)
        - Maintien visible (1.75 s)
        - Disparition graduelle (0.5 s)
        :param text: Le texte à afficher.
        :param pad_number: Numéro du pad.
        """
        # Si un texte est déjà en cours d'affichage ou si le pad a déjà été traité, ne rien faire
        if pad_number in self._processed_pads:
            return

        # Ajouter le pad aux pads traités
        self._processed_pads.add(pad_number)

        def fade_text():
            font = pygame.font.Font(None, 72)  # Police par défaut, taille 72
            text_surface = font.render(text, True, (255, 255, 255))  # Texte en blanc
            text_rect = text_surface.get_rect(center=(self._settings.SCREEN_WIDTH // 2,
                                                      self._settings.SCREEN_HEIGHT // 2))
            self._text_to_display = text_surface
            self._text_rect = text_rect

            try:
                # Apparition graduelle (0.25 s)
                for alpha in range(0, 256, 25):
                    self._text_alpha = alpha
                    self._text_visible = True
                    time.sleep(0.025)

                # Maintenir visible (1.75 s)
                time.sleep(1.75)

                # Disparition graduelle (0.5 s)
                for alpha in range(255, -1, -15):
                    self._text_alpha = alpha
                    time.sleep(0.05)

            finally:
                # Fin de l'affichage
                self._text_visible = False
                self._text_to_display = None
                self._text_alpha = 0


        # Lancer le processus d'affichage dans un thread
        thread = threading.Thread(target=fade_text)
        thread.start()

#Modfi A8 FIn