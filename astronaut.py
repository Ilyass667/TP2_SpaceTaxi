import pygame
import random
import time

from enum import Enum, auto
from pad import Pad


class AstronautState(Enum):
    """ Différents états d'un astronaute. """
    WAITING = auto()
    WAVING = auto()
    JUMPING_RIGHT = auto()
    JUMPING_LEFT = auto()
    ONBOARD = auto()
    REACHED_DESTINATION = auto()


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

    # temps d'affichage pour les trames de chaque état affiché/animé
    _FRAME_TIMES = { AstronautState.WAITING : 0.1,
                     AstronautState.WAVING : 0.1,
                     AstronautState.JUMPING_LEFT : 0.15,
                     AstronautState.JUMPING_RIGHT : 0.15}
    #--------M6 --- Bs ----on ne duplique pas les images et les masques 
    _all_frames = None

    @staticmethod
    def _initialiser_chaque_frames():
        """Charge les trames (images et masques) une seule fois."""
        if Astronaut._all_frames is None:
            Astronaut._all_frames = Astronaut._load_and_build_frames()

    def __init__(self, source_pad: Pad, target_pad: Pad, trip_money: float) -> None:
        """
        Initialise une instance d'astronaute.
        :param source_pad: le pad sur lequel apparaîtra l'astronaute
        :param target_pad: le pad où souhaite se rendre l'astronaute
        :param trip_money: le montant de départ pour la course (diminue avec le temps)
        """
        super().__init__()
        Astronaut._initialiser_chaque_frames()  # Initialiser les trames partagées si nécessaire
        self._frames = Astronaut._all_frames  # Pas besoin de redéballer
        self.image, self.mask = self._frames[AstronautState.WAITING][0]
        self.rect = self.image.get_rect()
        self.rect.x = source_pad.astronaut_start.x
        self.rect.y = source_pad.astronaut_start.y

        # Attributs spécifiques à l'instance
        self._source_pad = source_pad
        self._target_pad = target_pad
        self._trip_money = trip_money
        self._time_is_money = 0.0
        self._last_saved_time = None
        self._state = AstronautState.WAITING
        self._frames = self._all_frames[self._state]
        self._state_time = 0 # temps écoulé dans l'état actuel
        self._current_frame = 0
        self._last_frame_time = time.time()
        self._waving_delay = 0  # temps avant d'envoyer la main (0 initialement, aléatoire ensuite)
        self._hey_taxi_clips, self._pad_please_clips, self._hey_clips = Astronaut._load_clips()

    

        self._pos_x = float(self.rect.x)  # sert pour les calculs de position, plus précis qu'un entier
        self._target_x = 0.0  # position horizontale où l'astronaute tente de se rendre lorsqu'il saute
        self._velocity = 0.0
        
    @property
    def source_pad(self) -> Pad:
        return self._source_pad

    @property
    def target_pad(self) -> Pad:
        return self._target_pad

    def draw(self, surface: pygame.Surface) -> None:
        """ Dessine l'astronaute, sauf s'il est à bord du taxi. """
        if self._state != AstronautState.ONBOARD:
            surface.blit(self.image, self.rect)

    def get_trip_money(self) -> float:
        return self._trip_money

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

    def update(self, *args, **kwargs) -> None:
        """
        Met à jour l'astronaute. Cette méthode est appelée à chaque itération de la boucle de jeu.
        :param args: inutilisé
        :param kwargs: inutilisé
        """
        current_time = time.time()

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
        if current_time - self._last_frame_time >= Astronaut._FRAME_TIMES[self._state]:
            self._current_frame = (self._current_frame + 1) % len(self._frames)
            self._last_frame_time = current_time

#-------M 10 BS ----------------refactoriser le code de chqngement d etat-------------------------------------------------
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
                    """if self._target_pad is not Pad.UP and self._target_x == self._target_pad.astronaut_end.x:
                    self._state = AstronautState.REACHED_DESTINATION
                else:
                    self._state = AstronautState.ONBOARD"""
                    next_state = (AstronautState.REACHED_DESTINATION 
                                  if self._target_pad is not Pad.UP and self._target_x == self._target_pad.astronaut_end.x
                          else AstronautState.ONBOARD)
                    self._change_state(next_state)

                    if next_state == AstronautState.ONBOARD:
                         if self._target_pad is None:
                            self._pad_please_clips[0].play()
                         else:
                            self._pad_please_clips[self._target_pad.number].play()

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
#------------------------------------------------------------------------------------------------------------------------------
    def _call_taxi(self) -> None:
        """ Joue le son d'appel du taxi. """
        if self._state == AstronautState.WAITING:
            clip = random.choice(self._hey_taxi_clips)
            clip.play()

    @staticmethod
    def _load_and_build_frames() -> dict:
        """
        Charge et découpe la feuille de sprites (sprite sheet) pour un astronaute.
        :return: un tuple contenant dans l'ordre:
                     - une liste de trames (image, masque) pour attendre
                     - une liste de trames (image, masque) pour envoyer la main
                     - une liste de trames (image, masque) pour se déplacer vers la gauche
                     - une liste de trames (image, masque) pour se déplacer vers la droite
        """
       
        nb_images = Astronaut._NB_WAITING_IMAGES + Astronaut._NB_WAVING_IMAGES + Astronaut._NB_JUMPING_IMAGES
        sprite_sheet = pygame.image.load(Astronaut._ASTRONAUT_FILENAME).convert_alpha()
        sheet_width = sprite_sheet.get_width()
        sheet_height = sprite_sheet.get_height()
        image_size = (sheet_width / nb_images, sheet_height)

        # Fonction pour extraire une trame
        def extract_frame(frame_index):
            surface = pygame.Surface(image_size, flags=pygame.SRCALPHA)
            source_rect = surface.get_rect()
            source_rect.x = frame_index * source_rect.width
            surface.blit(sprite_sheet, (0, 0), source_rect)
            mask = pygame.mask.from_surface(surface)
            return surface, mask

    # Trames pour chaque état
        waiting_frames = [extract_frame(0)]
        waving_frames = [extract_frame(i) for i in range(1, 1 + Astronaut._NB_WAVING_IMAGES)]

     #--M11 bs lastronaute agite le bras -----------------------------------      
        #waving_frames.extend(waving_frames[1:-1][::-1])
        waving_frames_full = []
        waving_frames_full.extend(waving_frames[:5])  # 1, 2, 3, 4, 5
        waving_frames_full.extend(waving_frames[3:1:-1])  # 4, 3

        for _ in range(3):  # Répéter (3, 4, 5, 4, 3) trois fois
            waving_frames_full.extend(waving_frames[2:])
            waving_frames_full.extend(waving_frames[3:1:-1])

        waving_frames_full.extend(waving_frames[1::-1])
#-------------------------------------------------------------------------------
        # astronaute qui se déplace en sautant (les _NB_JUMPING_IMAGES prochaines images)
        jumping_right_frames = [extract_frame(i) for i in range(5, 5 + Astronaut._NB_JUMPING_IMAGES)]
        jumping_left_frames = [(pygame.transform.flip(surface, True, False), mask)
                            for surface, mask in jumping_right_frames]

        return {
            AstronautState.WAITING: waiting_frames,
            AstronautState.WAVING: waving_frames_full,
            AstronautState.JUMPING_RIGHT: jumping_right_frames,
            AstronautState.JUMPING_LEFT: jumping_left_frames
        }

    @staticmethod
    def _load_clips() -> tuple:
        """
        Charge les clips sonores (voix).
        :return: un tuple contenant dans l'ordre:
                     - une liste de clips (pygame.mixer.Sound) "Hey, taxi"
                     - une liste de clips (pygame.mixer.Sound) "Pad # please" ou "Up please"
                     - une liste de clips (pygame.mixer.Sound) "Hey!"
        """
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

        return hey_taxis, pad_pleases, heys
