import pygame
import random
import time
import math

from enum import Enum, auto
from pad import Pad
from gate import Gate
from file_error import FileError # C3


class AstronautState(Enum):
    """ Différents états d'un astronaute. """
    WAITING = auto()
    WAVING = auto()
    JUMPING_RIGHT = auto()
    JUMPING_LEFT = auto()
    ONBOARD = auto()
    REACHED_DESTINATION = auto()
    INTEGRATION = auto()  # A9



class Astronaut(pygame.sprite.Sprite):
    """ Un astronaute. """

    _ASTRONAUT_FILENAME = "img/astronaut.png"
    _NB_WAITING_IMAGES = 1
    _NB_WAVING_IMAGES = 4
    _NB_JUMPING_IMAGES = 6

    _VELOCITY = 0.2
    _LOOSE_ONE_CENT_EVERY = 0.05  # perd 1 cent tous les 5 centièmes de seconde
    _ONE_CENT = 0.01
    _WAVING_DELAYS = 10.0, 30.0
    _INTEGRATION_DELAY = 2.0  # A9

    #M6 variable 
    _shared_frames = None
    _shared_clips = None

    # temps d'affichage pour les trames de chaque état affiché/animé
    _FRAME_TIMES = { AstronautState.WAITING : 0.1,
                     AstronautState.WAVING : 0.1,
                     AstronautState.JUMPING_LEFT : 0.15,
                     AstronautState.JUMPING_RIGHT : 0.15}

    def __init__(self, source_pad: Pad, target_pad: Pad, gate: Gate ,trip_money: float) -> None:
        """
        Initialise une instance d'astronaute.
        :param source_pad: le pad sur lequel apparaîtra l'astronaute
        :param target_pad: le pad où souhaite se rendre l'astronaute
        :param trip_money: le montant de départ pour la course (diminue avec le temps)
        """
        super(Astronaut, self).__init__()

        self._source_pad = source_pad
        self._target_pad = target_pad
        self._gate = gate # C11

        self._trip_money = self.calculate_distance_trip_money(trip_money) # M16
        self._time_is_money = 0.0
        self._last_saved_time = None

        self._hey_taxi_clips, self._pad_please_clips, self._hey_clips = Astronaut._load_clips()

        waiting_frames, waving_frames_full, jumping_left_frames, jumping_right_frames = Astronaut._load_and_build_frames()

        self._all_frames = {AstronautState.WAITING: waiting_frames,
                            AstronautState.WAVING: waving_frames_full,
                            AstronautState.JUMPING_LEFT: jumping_left_frames,
                            AstronautState.JUMPING_RIGHT: jumping_right_frames}

        self.image, self.mask = self._all_frames[AstronautState.WAITING][0]
        self.rect = self.image.get_rect()
        self.rect.x = self._source_pad.astronaut_start.x
        self.rect.y = self._source_pad.astronaut_start.y

        self._pos_x = float(self.rect.x)  # sert pour les calculs de position, plus précis qu'un entier
        self._target_x = 0.0  # position horizontale où l'astronaute tente de se rendre lorsqu'il saute
        self._velocity = 0.0

        self._waving_delay = 0  # temps avant d'envoyer la main (0 initialement, aléatoire ensuite)

        self._state = AstronautState.WAITING
        self._frames = self._all_frames[self._state]
        self._state_time = 0  # temps écoulé dans l'état actuel
        self._current_frame = 0
        self._last_frame_time = time.time()

        self._state = AstronautState.INTEGRATION  # A9
        self._waiting_frame = self._all_frames[AstronautState.WAITING][0][0] # A9
        self._pxels_data = [] # A9
        self._pxels_start_timestamp = 0  # A9
        self._integration_done = False # A9

        self._state = AstronautState.INTEGRATION  # Début dans l'état d'intégration
        self._waiting_frame = self._all_frames[AstronautState.WAITING][0][0]
        self._integration_pixels = []
        self._integration_start_time = 0  # Temps de début de l'intégration
        self._integration_complete = False  # Pour suivre l'état d'intégration

    @property
    def source_pad(self) -> Pad:
        return self._source_pad

    @property
    def target_pad(self) -> Pad:
        return self._target_pad

    def get_trip_money(self) -> float:
        return self._trip_money
    
    def calculate_distance_trip_money(self, trip_money: float) -> float: # M16
        """
        Calcule le montant du voyage en fonction de la distance entre les centres
        des pads source et destination.
        """
        source_center = self._source_pad.get_center()
        target_center = None

        if self._target_pad is not Pad.UP:
            target_center = self._target_pad.get_center()
        else:
            target_center = self._gate.get_center()
            
        distance = math.sqrt((target_center[0] - source_center[0])**2 + 
                             (target_center[1] - source_center[1])**2)

        trip_money_calulated = distance * Astronaut._ONE_CENT + trip_money

        return max(trip_money_calulated, 0)

    def has_reached_destination(self) -> bool:
        return self._state == AstronautState.REACHED_DESTINATION

    def is_jumping_on_starting_pad(self) -> bool:
        """
        Vérifie si l'astronaute est en train de se déplacer sur sa plateforme de départ.
        Pour que ce soit le cas, il doit :
            - être en train de sauter
            - être situé à sa hauteur de départ (donc sur une plateforme à la même hauteur)
            - être situé horizontalement dans les limites de la plateforme de départ
        :return: True si c'est le cas, False sinon
        """
        if self._state not in (AstronautState.JUMPING_LEFT, AstronautState.JUMPING_RIGHT):
            return False
        if self.rect.y != self._source_pad.astronaut_start.y:
            return False
        if self._source_pad.astronaut_start.x <= self.rect.x <= self._source_pad.rect.x + self._source_pad.rect.width:
            return True
        return False

    def is_onboard(self) -> bool:
        return self._state == AstronautState.ONBOARD

    def is_waiting_for_taxi(self) -> bool:
        return self._state in (AstronautState.WAITING, AstronautState.WAVING)

    def jump(self, target_x) -> None:
        """
        Commande à l'astronaute de se déplacer vers une destination horizontale (les astronautes
        ne se déplacent que horizontalement dans Space Taxi).
        :param target_x: cible horizontale (position x à l'écran)
        """
        self._target_x = target_x
        if self._target_x < self.rect.x:
            self._velocity = -Astronaut._VELOCITY
            self._state = AstronautState.JUMPING_LEFT
        elif self._target_x > self.rect.x:
            self._velocity = Astronaut._VELOCITY
            self._state = AstronautState.JUMPING_RIGHT
        self._state_time = 0
        self._frames = self._all_frames[self._state]
        self._current_frame = 0

    def move(self, x: int, y: int) -> None:
        """
        Place l'astronaute à la position (x,y) à l'écran.
        :param x: position horizontale
        :param y: position verticale
        """
        self.rect.x = x
        self.rect.y = y

        self._pos_x = float(self.rect.x)

    def set_trip_money(self, trip_money: float) -> None:
        self._trip_money = trip_money

    def draw(self, surface: pygame.Surface) -> None:
        """
        Affiche l'astronaute sur la surface donnée. Si l'état actuel est INTEGRATION,
        affiche progressivement les pixels de l'image associée. Sinon, affiche l'image normale.

        :param surface: Surface de jeu où dessiner l'astronaute.
        """
        if self._state == AstronautState.INTEGRATION:
            self._draw_integration_pixels(surface)
        elif self._state != AstronautState.ONBOARD:
            surface.blit(self.image, self.rect)


    def _draw_integration_pixels(self, surface: pygame.Surface) -> None:
        """
        Affiche progressivement les pixels de l'image associée pendant l'intégration.

        :param surface: Surface de jeu où dessiner l'astronaute.
        """
        elapsed_time = time.time() - self._pxels_start_timestamp
        progress_ratio = min(1, elapsed_time / Astronaut._INTEGRATION_DELAY)
        num_pixels_to_render = int(progress_ratio * len(self._pxels_data))

        # Afficher progressivement les pixels
        for i in range(num_pixels_to_render):
            pixel = self._pxels_data[i]
            x, y = pixel
            surface.set_at(
                (self.rect.x + x, self.rect.y + y),
                self._waiting_frame.get_at(pixel)
            )


    def _load_integration_pixels(self) -> None: # A9
        """
        Crée et mélange une liste de tous les pixels de l'image dans l'état d'attente (WAITING),
        utilisée pour afficher progressivement l'astronaute lors de l'intégration.
        """

        width, height = self._waiting_frame.get_width(), self._waiting_frame.get_height()
        self._pxels_data = [(x, y) for x in range(width) for y in range(height)]
        random.shuffle(self._pxels_data)

    def update(self, *args, **kwargs) -> None:
        """
        Met à jour l'astronaute. Cette méthode est appelée à chaque itération de la boucle de jeu.
        :param args: inutilisé
        :param kwargs: inutilisé
        """
        current_time = time.time()

        if self._state == AstronautState.INTEGRATION: # A9
            if self._integration_done is False:
                self._load_integration_pixels()
                self._pxels_start_timestamp = time.time()
                self._integration_done = True

            if time.time() - self._pxels_start_timestamp >= Astronaut._INTEGRATION_DELAY:
                self._state = AstronautState.WAITING
                self._state_time = 0
                self._frames = self._all_frames[self._state]
                self._current_frame = 0

        # ÉTAPE 1 - diminuer le montant de la course si le moment est venu
        if self._last_saved_time is None:
            self._last_saved_time = current_time
        else:
            self._time_is_money += current_time - self._last_saved_time
            self._last_saved_time = current_time
            if self._time_is_money >= Astronaut._LOOSE_ONE_CENT_EVERY:
                self._time_is_money = 0.0
                self._trip_money = max(0.0, self._trip_money - Astronaut._ONE_CENT)

        if self._state in (AstronautState.ONBOARD, AstronautState.REACHED_DESTINATION):
            # pas d'animation dans ces états
            return

        # ÉTAPE 2 - changer de trame si le moment est venu
        if self._state in Astronaut._FRAME_TIMES:
            if current_time - self._last_frame_time >= Astronaut._FRAME_TIMES[self._state]:
                self._current_frame = (self._current_frame + 1) % len(self._frames)
                self._last_frame_time = current_time

        # M10 - refactoriser le code de changement detat

        # ÉTAPE 3 - changer d'état si le moment est venu
        self._state_time += current_time - self._last_frame_time
        if self._state == AstronautState.WAITING:
            if self._state_time >= self._waving_delay:
                self._call_taxi()
                self._change_state(AstronautState.WAVING)
        elif self._state == AstronautState.WAVING:
            last_frame = self._current_frame == len(self._frames) - 1
            spent_state_time = self._state_time >= self._FRAME_TIMES[AstronautState.WAVING] * len(self._frames)
            if last_frame and spent_state_time:
                self._change_state(AstronautState.WAITING)
                self._waving_delay = random.uniform(*Astronaut._WAVING_DELAYS)
        elif self._state in (AstronautState.JUMPING_RIGHT, AstronautState.JUMPING_LEFT):
            if self.rect.x == self._target_x:
                if self._target_pad is not Pad.UP and self._target_x == self._target_pad.astronaut_end.x:
                    self._state = AstronautState.REACHED_DESTINATION
                    print("Arriver donc on met effet desintegre")
                else:
                    self._state = AstronautState.ONBOARD
                    print("Entre dans taxi Donc on met effet desintegre")
                    if self._target_pad is None:
                    # Modif Début M13
                        self._play_destination_clip()
                    else:
                       self._play_destination_clip()
                    # Modif Fin M13
                return

            self._pos_x += self._velocity
            self.rect.x = round(self._pos_x)

        self.image, self.mask = self._frames[self._current_frame]

    def wait(self) -> None:
        """ Replace l'astronaute dans l'état d'attente. """
        self._change_state(AstronautState.WAITING)

    def _change_state(self, new_state: AstronautState) -> None:
        """
        Change l'état de l'astronaute.
        :param new_state: le nouvel état
        """
        self._state = new_state
        self._state_time = 0
        self._frames = self._all_frames[new_state]
        self._current_frame = 0

    # fin M10
    def _call_taxi(self) -> None:
        """ Joue le son d'appel du taxi. """
        if self._state == AstronautState.WAITING:
            clip = random.choice(self._hey_taxi_clips)
            clip.play()

    # Debut Modif M13
    def _play_destination_clip(self) -> None:
        """
        Joue un clip audio pour indiquer la destination de l'astronaute.
        """
        if self._target_pad is not None and self._pad_please_clips:
            clip_index = self._target_pad.number if self._target_pad.number < len(self._pad_please_clips) else -1
            if clip_index >= 0:
                self._pad_please_clips[clip_index].play()
        else:
                self._pad_please_clips[0].play()
    # Fin Modif M13

    @staticmethod
    def _load_and_build_frames() -> tuple:
        """
        Charge et découpe la feuille de sprites (sprite sheet) pour un astronaute.
        :return: un tuple contenant dans l'ordre:
                     - une liste de trames (image, masque) pour attendre
                     - une liste de trames (image, masque) pour envoyer la main
                     - une liste de trames (image, masque) pour se déplacer vers la gauche
                     - une liste de trames (image, masque) pour se déplacer vers la droite
        """
        try:

            # M6 - Ne pas dupliquer les surfaces
            if Astronaut._shared_frames is not None:
                return Astronaut._shared_frames
        
            nb_images = Astronaut._NB_WAITING_IMAGES + Astronaut._NB_WAVING_IMAGES + Astronaut._NB_JUMPING_IMAGES
            sprite_sheet = pygame.image.load(Astronaut._ASTRONAUT_FILENAME).convert_alpha()
            sheet_width = sprite_sheet.get_width()
            sheet_height = sprite_sheet.get_height()
            image_size = (sheet_width / nb_images, sheet_height)

            # astronaute qui attend
            waiting_surface = pygame.Surface(image_size, flags=pygame.SRCALPHA)
            source_rect = waiting_surface.get_rect()
            waiting_surface.blit(sprite_sheet, (0, 0), source_rect)
            waiting_mask = pygame.mask.from_surface(waiting_surface)
            waiting_frames = [(waiting_surface, waiting_mask)]

            # astronaute qui envoie la main (les _NB_WAVING_IMAGES prochaines images)
            waving_frames = []
            first_frame = Astronaut._NB_WAITING_IMAGES
            for frame in range(first_frame, first_frame + Astronaut._NB_WAVING_IMAGES):
                surface = pygame.Surface(image_size, flags=pygame.SRCALPHA)
                source_rect = surface.get_rect()
                source_rect.x = frame * source_rect.width
                surface.blit(sprite_sheet, (0, 0), source_rect)
                mask = pygame.mask.from_surface(surface)
                waving_frames.append((surface, mask))
            

            # M11 - l'astronaute agite le bras
            waving_frames_full = []
            waving_frames_full.extend(waving_frames[:5]) 
            waving_frames_full.extend(waving_frames[3:1:-1])  

            for _ in range(3): 
                waving_frames_full.extend(waving_frames[3:])
                waving_frames_full.extend(waving_frames[3:1:-1])

            waving_frames_full.extend(waving_frames[1::-1])
            # fin  M11

            # astronaute qui se déplace en sautant (les _NB_JUMPING_IMAGES prochaines images)
            jumping_left_frames = []
            jumping_right_frames = []
            first_frame = Astronaut._NB_WAITING_IMAGES + Astronaut._NB_WAVING_IMAGES
            for frame in range(first_frame, first_frame + Astronaut._NB_JUMPING_IMAGES):
                surface = pygame.Surface(image_size, flags=pygame.SRCALPHA)
                source_rect = surface.get_rect()
                source_rect.x = frame * source_rect.width
                surface.blit(sprite_sheet, (0, 0), source_rect)
                mask = pygame.mask.from_surface(surface)
                jumping_right_frames.append((surface, mask))

                flipped_surface = pygame.transform.flip(surface, True, False)
                flipped_mask = pygame.mask.from_surface(flipped_surface)
                jumping_left_frames.append((flipped_surface, flipped_mask))
            
            
        except FileNotFoundError as e: # C3
            error_message = str(e)
            filename = error_message.split("No file '")[1].split("'")[0]
            error = FileError(f"FATAL ERROR loading {filename}")
            error.run()

        #return waiting_frames, waving_frames, jumping_left_frames, jumping_right_frames
        #M6 stockage des frames partagées
        Astronaut._shared_frames = (waiting_frames, waving_frames_full, jumping_left_frames, jumping_right_frames)
        return Astronaut._shared_frames


    @staticmethod
    def _load_clips() -> tuple:
        """
        Charge les clips sonores (voix).
        :return: un tuple contenant dans l'ordre:
                     - une liste de clips (pygame.mixer.Sound) "Hey, taxi"
                     - une liste de clips (pygame.mixer.Sound) "Pad # please" ou "Up please"
                     - une liste de clips (pygame.mixer.Sound) "Hey!"
        """

        try: 
            hey_taxis = [pygame.mixer.Sound("voices/gary_hey_taxi_01.mp3"),
                        pygame.mixer.Sound("voices/gary_hey_taxi_02.mp3"),
                        pygame.mixer.Sound("voices/gary_hey_taxi_03.mp3")]

            pad_pleases = [pygame.mixer.Sound("voices/gary_up_please_01.mp3"),
                        pygame.mixer.Sound("voices/gary_pad_1_please_01.mp3"),
                        pygame.mixer.Sound("voices/gary_pad_2_please_01.mp3"),
                        pygame.mixer.Sound("voices/gary_pad_3_please_01.mp3"),
                        pygame.mixer.Sound("voices/gary_pad_4_please_01.mp3"),
                        pygame.mixer.Sound("voices/gary_pad_5_please_01.mp3")]

            heys = [pygame.mixer.Sound("voices/gary_hey_01.mp3")]

        except FileNotFoundError as e: # C3
            error_message = str(e)
            filename = error_message.split("No file '")[1].split("'")[0]
            error = FileError(f"FATAL ERROR loading {filename}")
            error.run()

        #return hey_taxis, pad_pleases, heys
        #M6 stockage dans l'attribut de classe 
        Astronaut._shared_clips = (hey_taxis, pad_pleases, heys)
        return Astronaut._shared_clips
        # M6
      
    
    #Modif A11 Début:
    def react_to_collision(self) -> None:
        """ Joue un son lorsque l'astronaute est frappé par un taxi. """
        if self._hey_clips:
            random.choice(self._hey_clips).play()
    #Modif A11 Fin
