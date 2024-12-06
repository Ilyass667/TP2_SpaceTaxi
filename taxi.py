from enum import Enum, auto

import pygame

from astronaut import Astronaut
from hud import HUD
from obstacle import Obstacle
from pad import Pad
from pump import Pump


class ImgSelector(Enum):
    """ Sélecteur d'image de taxi. """
    IDLE = auto()
    BOTTOM_REACTOR = auto()
    TOP_REACTOR = auto()
    REAR_REACTOR = auto()
    BOTTOM_AND_REAR_REACTORS = auto()
    TOP_AND_REAR_REACTORS = auto()
    GEAR_OUT = auto()
    GEAR_SHOCKS = auto()
    GEAR_OUT_AND_BOTTOM_REACTOR = auto()
    DESTROYED = auto()


class Taxi(pygame.sprite.Sprite):
    """ Un taxi spatial. """

    _TAXIS_FILENAME = "img/taxis.png"
    _NB_TAXI_IMAGES = 6

    _FLAG_LEFT = 1 << 0  # indique si le taxi va vers la gauche
    _FLAG_TOP_REACTOR = 1 << 1  # indique si le réacteur du dessus est allumé
    _FLAG_BOTTOM_REACTOR = 1 << 2  # indique si le réacteur du dessous est allumé
    _FLAG_REAR_REACTOR = 1 << 3  # indique si le réacteur arrière est allumé
    _FLAG_GEAR_OUT = 1 << 4  # indique si le train d'atterrissage est sorti
    _FLAG_DESTROYED = 1 << 5  # indique si le taxi est détruit

    _REACTOR_SOUND_VOLUME = 0.25

    _REAR_REACTOR_POWER = 0.001
    _BOTTOM_REACTOR_POWER = 0.0005
    _TOP_REACTOR_POWER = 0.00025

    _MAX_ACCELERATION_X = 0.075
    _MAX_ACCELERATION_Y_UP = 0.08
    _MAX_ACCELERATION_Y_DOWN = 0.05

    _MAX_VELOCITY_SMOOTH_LANDING = 0.50  # vitesse maximale permise pour un atterrissage en douceur
    #Modif A15 Début
    _MAX_VELOCITY_ROUGH_LANDING = 1.0  # Vitesse maximale pour un atterrissage difficile (entre crash et doux)
    #Modif A15 Fin

    _CRASH_ACCELERATION = 0.10

    _FRICTION_MUL = 0.9995  # la vitesse horizontale est multipliée par la friction
    _GRAVITY_ADD = 0.005  # la gravité est ajoutée à la vitesse verticale


    _REAR_REACTOR_CONSUMPTION = 0.001
    _BOTTOM_REACTOR_CONSUMPTION = 0.0005
    _TOP_REACTOR_CONSUMPTION = 0.00025

    def __init__(self, pos: tuple) -> None:
        """
        Initialise une instance de taxi.
        :param pos:
        """
        super(Taxi, self).__init__()
        #Modif A15 Début
        self._smooth_landing_sound = pygame.mixer.Sound("snd/smooth_landing_snd.wav")
        self._rough_landing_sound = pygame.mixer.Sound("snd/rough_landing_snd.wav")
        #Modif A15 Fin

        #Modif A14 Début
        self._fuel_level = 2.0  # Niveau d'essence initial (de 0 à 1)
        #Modif A14 Fin

        self._initial_pos = pos
        self._elevation = None # A4
        self._elevation_offset = 5 # A4

        self._hud = HUD()

        self._reactor_sound = pygame.mixer.Sound("snd/170278__knova__jetpack-low.wav")
        self._reactor_sound.set_volume(0)
        self._reactor_sound.play(-1)

        self._crash_sound = pygame.mixer.Sound("snd/237375__squareal__car-crash.wav")

        self._surfaces, self._masks = Taxi._load_and_build_surfaces()

        self._reinitialize()

    @property
    def pad_landed_on(self) -> None:
        return self._pad_landed_on

    def board_astronaut(self, astronaut: Astronaut) -> None:
        self._astronaut = astronaut

    def crash_on(self, obj) -> bool:
        """
        Vérifie si le taxi est en situation de crash contre un objet (Pad, Obstacle ou Pump).
        :param obj: objet avec lequel vérifier (Pad, Obstacle ou Pump)
        :return: True si le taxi est en contact avec l'objet, False sinon
        """
        if self._flags & Taxi._FLAG_DESTROYED == Taxi._FLAG_DESTROYED:
            return False

        # Vérifier si l'objet est de type Pad, Obstacle ou Pump et si le taxi entre en collision avec l'objet
        if isinstance(obj, (Pad, Obstacle, Pump)):
            if self.rect.colliderect(obj.rect):
                if pygame.sprite.collide_mask(self, obj):
                    self._flags = self._FLAG_DESTROYED
                    self._crash_sound.play()
                    self._velocity = pygame.Vector2(0, 0) # C5 refait
                    self._acceleration = pygame.Vector2(0, 0) # C5 refait
                    return True

        return False

    def draw(self, surface: pygame.Surface) -> None:
        """ Dessine le taxi sur la surface fournie comme argument. """
        surface.blit(self.image, self.rect)

    def handle_event(self, event: pygame.event.Event) -> None:
        """ Gère les événements du taxi. """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if self._pad_landed_on is None:
                    if self._flags & Taxi._FLAG_GEAR_OUT != Taxi._FLAG_GEAR_OUT:
                        # pas de réacteurs du dessus et arrière lorsque le train d'atterrissage est sorti
                        self._flags &= ~(Taxi._FLAG_TOP_REACTOR | Taxi._FLAG_REAR_REACTOR)

                    self._flags ^= Taxi._FLAG_GEAR_OUT  # flip le bit pour refléter le nouvel état

                    self._select_image()

    def has_exited(self) -> bool:
        """
        Vérifie si le taxi a quitté le niveau (par la sortie).
        :return: True si le taxi est sorti du niveau, False sinon
        """
        if self.rect.y <= -self.rect.height:
            # Modif C13 Début
            self._reactor_sound.stop()
            # Modif C13 Fin
            return True
        return False

    # Modif: C6 Début
    def burn_astronaute(self, astronaut: Astronaut) -> bool:
        """
        Vérifie si le réacteur du taxi brûle un astronaute.
        :param astronaut: astronaute pour lequel vérifier
        :return: True si le réacteur touche l'astronaute, False sinon
        """
        if astronaut.is_onboard():
            return False

        # Récupérer les zones des réacteurs actifs
        reactor_rects = self.get_reactor_rects()

        for reactor, rect in reactor_rects.items():
            if rect.colliderect(astronaut.rect):
                print(f"Collision détectée avec le réacteur {reactor}.")
                return True

        return False
    # Modif: C6 Fin

    # Modif: C9 Début
    def get_reactor_rects(self) -> dict:
        """
        Renvoie les rectangles représentant les zones des réacteurs.
        :return: Un dictionnaire contenant les rectangles pour chaque réacteur.
        """
        reactor_rects = {}

        if self._flags & self._FLAG_BOTTOM_REACTOR:
            reactor_rects["bottom"] = pygame.Rect(
                self.rect.x + self.rect.width // 3,
                self.rect.y + self.rect.height - 5,
                self.rect.width // 3,
                5
            )

        if self._flags & self._FLAG_TOP_REACTOR:
            reactor_rects["top"] = pygame.Rect(
                self.rect.x + self.rect.width // 3,
                self.rect.y,
                self.rect.width // 3,
                5
            )

        if self._flags & self._FLAG_REAR_REACTOR:
            reactor_rects["rear"] = pygame.Rect(
                self.rect.x,
                self.rect.y + self.rect.height // 2 - 5,
                5,
                10
            )

        return reactor_rects
    #Modif: C9 Fin


    def hit_astronaut(self, astronaut: Astronaut) -> bool:
        """
        Vérifie si le taxi frappe un astronaute.
        :param astronaut: astronaute pour lequel vérifier
        :return: True si le taxi frappe l'astronaute, False sinon
        """
        if self._pad_landed_on or astronaut.is_onboard():
            return False

        if self.rect.colliderect(astronaut.rect):
            if pygame.sprite.collide_mask(self, astronaut):
                return True

        return False

    def is_destroyed(self) -> bool:
        """
        Vérifie si le taxi est détruit.
        :return: True si le taxi est détruit, False sinon
        """
        return self._flags & Taxi._FLAG_DESTROYED == Taxi._FLAG_DESTROYED

    def land_on_pad(self, pad: Pad) -> bool:
        """
        Vérifie si le taxi est en situation d'atterrissage sur une plateforme.
        :param pad: plateforme pour laquelle vérifier
        :return: True si le taxi est atterri, False sinon
        """
        gear_out = self._flags & Taxi._FLAG_GEAR_OUT == Taxi._FLAG_GEAR_OUT
        if not gear_out:
            return False

        if not self.rect.colliderect(pad.rect):
            return False

        if pygame.sprite.collide_mask(self, pad):
            # Vérifier le type d'atterrissage
            is_rough_landing = Taxi._MAX_VELOCITY_SMOOTH_LANDING < abs(
                self._velocity.y) <= Taxi._MAX_VELOCITY_ROUGH_LANDING

            if abs(self._velocity.y) > Taxi._MAX_VELOCITY_ROUGH_LANDING:
                # Considérer comme un crash normal
                return False

            # Jouer le son correspondant
            if is_rough_landing:
                self._rough_landing_sound.play()
            else:
                self._smooth_landing_sound.play()

            # Atterrissage réussi, réinitialiser la position
            self.rect.bottom = pad.rect.top + 4
            self._pos.y = float(self.rect.y)
            self._flags &= Taxi._FLAG_LEFT | Taxi._FLAG_GEAR_OUT
            self._velocity.x = self._velocity.y = self._acceleration.x = self._acceleration.y = 0.0
            self._pad_landed_on = pad
            if self._astronaut and self._astronaut.target_pad.number == pad.number:
                self.unboard_astronaut()
            return True

        return False

    def refuel_from(self, pump: Pump) -> bool:
        """
        Vérifie si le taxi est en position de faire le plein d'essence.
        :param pump: pompe pour laquelle vérifier
        :return: True si le taxi est en bonne position, False sinon
        """
        if self._pad_landed_on is None:
            return False

        if not self.rect.colliderect(pump.rect):
            return False

        return True

    def reset(self) -> None:
        """ Réinitialise le taxi. """
        self._reinitialize()


    def unboard_astronaut(self) -> None:
        """ Fait descendre l'astronaute qui se trouve à bord. """
        if self._astronaut.target_pad is not Pad.UP:
            self._astronaut.move(self.get_door_x(), self._pad_landed_on.rect.y - self._astronaut.rect.height)
            self._astronaut.jump(self._astronaut.target_pad.astronaut_end.x)

        self._hud.add_bank_money(self._astronaut.get_trip_money())
        self._astronaut.set_trip_money(0.0)
        self._hud.set_trip_money(0.0)
        self._astronaut = None

    # Modif: A14 Début
    def crash_due_to_fuel(self) -> bool:
        """
        Vérifie si le taxi manque d'essence, provoquant un crash.
        :return: True si le taxi manque d'essence et doit crasher, False sinon.
        """
        if self._flags & Taxi._FLAG_DESTROYED == Taxi._FLAG_DESTROYED:
            return False
        if self._fuel_level <= 0 and not self.is_destroyed():
            self._flags = Taxi._FLAG_DESTROYED
            self._crash_sound.play()    
            self._velocity = pygame.Vector2(0, 0) # C5 refait
            self._acceleration = pygame.Vector2(0, 0) # C5 refait
            return True
        return False
    # Modif: A14 Fin

    def get_door_x(self): # C7
        if self._flags & Taxi._FLAG_LEFT:
            return self.rect.left + 20
        else:
            return self.rect.left + 15

    def update(self, *args, **kwargs) -> None:
        """
        Met à jour le taxi. Cette méthode est appelée à chaque itération de la boucle de jeu.
        :param args: inutilisé
        :param kwargs: inutilisé
        """
        # Modif Début A14 : Consommation d'essence
        self._consume_fuel()
        if self._fuel_level <= 0:
            return
        # Modif Fin A14

        # ÉTAPE 1 - gérer les touches présentement enfoncées
        self._handle_keys()

        # ÉTAPE 2 - calculer la nouvelle position du taxi
        self._velocity.x += self._acceleration.x
        self._velocity.x *= Taxi._FRICTION_MUL
        self._velocity.y += self._acceleration.y
        if self._pad_landed_on is None:
            self._velocity.y += Taxi._GRAVITY_ADD

        self._pos.x += self._velocity.x
        self._pos.y += self._velocity.y


        self.rect.x = round(self._pos.x)
        self.rect.y = round(self._pos.y)

        # ÉTAPE 3 - fait entendre les réacteurs ou pas
        reactor_flags = Taxi._FLAG_TOP_REACTOR | Taxi._FLAG_REAR_REACTOR | Taxi._FLAG_BOTTOM_REACTOR
        if self._flags & reactor_flags:
            self._reactor_sound.set_volume(Taxi._REACTOR_SOUND_VOLUME)
        else:
            self._reactor_sound.set_volume(0)

        # ÉTAPE 4 - sélectionner la bonne image en fonction de l'état du taxi
        self._select_image()

    # Modif Début A14
    def _consume_fuel(self) -> None:
        """ Réduit le niveau d'essence en fonction des réacteurs actifs. """

        if self._flags & Taxi._FLAG_DESTROYED == Taxi._FLAG_DESTROYED:
            return

        consumption = 0
        if self._flags & Taxi._FLAG_BOTTOM_REACTOR:
            consumption += Taxi._BOTTOM_REACTOR_CONSUMPTION
        if self._flags & Taxi._FLAG_TOP_REACTOR:
            consumption += Taxi._TOP_REACTOR_CONSUMPTION
        if self._flags & Taxi._FLAG_REAR_REACTOR:
            consumption += Taxi._REAR_REACTOR_CONSUMPTION

        self._fuel_level -= consumption
        self._hud.update_fuel(self._fuel_level)
    # Modif Fin A14

    def _handle_keys(self) -> None:
        """ Change ou non l'état du taxi en fonction des touches présentement enfoncées. """
        if self._flags & Taxi._FLAG_DESTROYED == Taxi._FLAG_DESTROYED:
            return

        keys = pygame.key.get_pressed()

        gear_out = self._flags & Taxi._FLAG_GEAR_OUT == Taxi._FLAG_GEAR_OUT

        if keys[pygame.K_LEFT] and keys[pygame.K_RIGHT]:  # C2 elif pour le reste des cas
            self._flags &= ~Taxi._FLAG_REAR_REACTOR
            self._acceleration.x = 0.0

        elif keys[pygame.K_LEFT] and not gear_out:
            self._flags |= Taxi._FLAG_LEFT | Taxi._FLAG_REAR_REACTOR
            self._acceleration.x = max(self._acceleration.x - Taxi._REAR_REACTOR_POWER, -Taxi._MAX_ACCELERATION_X)

        elif keys[pygame.K_RIGHT] and not gear_out:
            self._flags &= ~Taxi._FLAG_LEFT
            self._flags |= self._FLAG_REAR_REACTOR
            self._acceleration.x = min(self._acceleration.x + Taxi._REAR_REACTOR_POWER, Taxi._MAX_ACCELERATION_X)

        elif not (keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]):
            self._flags &= ~Taxi._FLAG_REAR_REACTOR
            self._acceleration.x = 0.0

        if keys[pygame.K_DOWN] and keys[pygame.K_UP]: # C2 elif pour le reste des cas
            self._flags &= ~(Taxi._FLAG_TOP_REACTOR | Taxi._FLAG_BOTTOM_REACTOR)
            self._acceleration.y = 0.0

        elif keys[pygame.K_DOWN] and not gear_out:
            self._flags &= ~Taxi._FLAG_BOTTOM_REACTOR
            self._flags |= Taxi._FLAG_TOP_REACTOR
            self._acceleration.y = min(self._acceleration.y + Taxi._TOP_REACTOR_POWER, Taxi._MAX_ACCELERATION_Y_DOWN)

        elif keys[pygame.K_UP]:
            self._flags &= ~Taxi._FLAG_TOP_REACTOR
            self._flags |= Taxi._FLAG_BOTTOM_REACTOR
            self._acceleration.y = max(self._acceleration.y - Taxi._BOTTOM_REACTOR_POWER, -Taxi._MAX_ACCELERATION_Y_UP)
            if self._pad_landed_on:
                self._pad_landed_on = None

        elif not (keys[pygame.K_UP] or keys[pygame.K_DOWN]):
            self._flags &= ~(Taxi._FLAG_TOP_REACTOR | Taxi._FLAG_BOTTOM_REACTOR)
            self._acceleration.y = 0.0

        if self.check_take_off_distance():
            if keys[pygame.K_UP] and gear_out:
                self._flags &= ~Taxi._FLAG_GEAR_OUT

    def check_take_off_distance(self) -> bool:
        """
        Verifie si le taxi et dépasse une hauteur de la zone d'atterrissage.
        """
        taxi_y = self.rect.y

        if self._pad_landed_on and self._elevation is None: # A4
            self._elevation = taxi_y
        elif self._elevation is not None:
            if taxi_y < self._elevation - self._elevation_offset:
                self._elevation = None
                return True

        return False



    def _reinitialize(self) -> None:
        """ Initialise (ou réinitialise) les attributs de l'instance. """
        self._flags = 0
        self._select_image()

        self.rect = self.image.get_rect()
        self.rect.x = self._initial_pos[0] - self.rect.width / 2
        self.rect.y = self._initial_pos[1] - self.rect.height / 2

        # M1
        self._pos = pygame.Vector2(round(self.rect.x), round(self.rect.y))
        self._velocity = pygame.Vector2(0, 0)
        self._acceleration = pygame.Vector2(0, 0)
        # Réinitialiser le niveau de carburant
        self._fuel_level = 2.0

        self._pad_landed_on = None
        self._taking_off = False

        self._astronaut = None
        self._hud.set_trip_money(0.0)

    def _select_image(self) -> None:
        """ Sélectionne l'image et le masque à utiliser pour l'affichage du taxi en fonction de son état. """
        facing = self._flags & Taxi._FLAG_LEFT

        if self._flags & Taxi._FLAG_DESTROYED:
            self.image = self._surfaces[ImgSelector.DESTROYED][facing]
            self.mask = self._masks[ImgSelector.DESTROYED][facing]
            return

        condition_flags = Taxi._FLAG_TOP_REACTOR | Taxi._FLAG_REAR_REACTOR
        if self._flags & condition_flags == condition_flags:
            self.image = self._surfaces[ImgSelector.TOP_AND_REAR_REACTORS][facing]
            self.mask = self._masks[ImgSelector.TOP_AND_REAR_REACTORS][facing]
            return

        condition_flags = Taxi._FLAG_BOTTOM_REACTOR | Taxi._FLAG_REAR_REACTOR
        if self._flags & condition_flags == condition_flags:
            self.image = self._surfaces[ImgSelector.BOTTOM_AND_REAR_REACTORS][facing]
            self.mask = self._masks[ImgSelector.BOTTOM_AND_REAR_REACTORS][facing]
            return

        if self._flags & Taxi._FLAG_REAR_REACTOR:
            self.image = self._surfaces[ImgSelector.REAR_REACTOR][facing]
            self.mask = self._masks[ImgSelector.REAR_REACTOR][facing]
            return

        condition_flags = Taxi._FLAG_GEAR_OUT | Taxi._FLAG_BOTTOM_REACTOR
        if self._flags & condition_flags == condition_flags:
            self.image = self._surfaces[ImgSelector.GEAR_OUT_AND_BOTTOM_REACTOR][facing]
            self.mask = self._masks[ImgSelector.GEAR_OUT_AND_BOTTOM_REACTOR][facing]
            return

        if self._flags & Taxi._FLAG_BOTTOM_REACTOR:
            self.image = self._surfaces[ImgSelector.BOTTOM_REACTOR][facing]
            self.mask = self._masks[ImgSelector.BOTTOM_REACTOR][facing]
            return

        if self._flags & Taxi._FLAG_TOP_REACTOR:
            self.image = self._surfaces[ImgSelector.TOP_REACTOR][facing]
            self.mask = self._masks[ImgSelector.TOP_REACTOR][facing]
            return

        if self._flags & Taxi._FLAG_GEAR_OUT:
            self.image = self._surfaces[ImgSelector.GEAR_OUT][facing]
            self.mask = self._masks[ImgSelector.GEAR_OUT][facing]
            return

        if self._flags & Taxi._FLAG_DESTROYED:
            self.image = self._surfaces[ImgSelector.DESTROYED][facing]
            self.mask = self._masks[ImgSelector.DESTROYED][facing]
            return

        self.image = self._surfaces[ImgSelector.IDLE][facing]
        self.mask = self._masks[ImgSelector.IDLE][facing]

    @staticmethod
    def _load_and_build_surfaces() -> tuple:
        """
        Charge et découpe la feuille de sprites (sprite sheet) pour le taxi.
        Construit les images et les masques pour chaque état.
        :return: un tuple contenant deux dictionnaires (avec les états comme clés):
                     - un dictionnaire d'images (pygame.Surface)
                     - un dictionnaire de masques (pygame.Mask)
        """
        surfaces = {}
        masks = {}
        sprite_sheet = pygame.image.load(Taxi._TAXIS_FILENAME).convert_alpha()
        sheet_width = sprite_sheet.get_width()
        sheet_height = sprite_sheet.get_height()

        # taxi normal - aucun réacteur - aucun train d'atterrissage
        surface = pygame.Surface((sheet_width / Taxi._NB_TAXI_IMAGES, sheet_height), flags=pygame.SRCALPHA)
        source_rect = surface.get_rect()
        surface.blit(sprite_sheet, (0, 0), source_rect)
        flipped = pygame.transform.flip(surface, True, False)
        surfaces[ImgSelector.IDLE] = surface, flipped
        masks[ImgSelector.IDLE] = pygame.mask.from_surface(surface), pygame.mask.from_surface(flipped)

        # taxi avec réacteur du dessous
        surface = pygame.Surface((sheet_width / Taxi._NB_TAXI_IMAGES, sheet_height), flags=pygame.SRCALPHA)
        source_rect = surface.get_rect()
        surface.blit(sprite_sheet, (0, 0), source_rect)
        source_rect.x = source_rect.width
        surface.blit(sprite_sheet, (0, 0), source_rect)
        flipped = pygame.transform.flip(surface, True, False)
        surfaces[ImgSelector.BOTTOM_REACTOR] = surface, flipped
        masks[ImgSelector.BOTTOM_REACTOR] = masks[ImgSelector.IDLE]

        # taxi avec réacteur du dessus
        surface = pygame.Surface((sheet_width / Taxi._NB_TAXI_IMAGES, sheet_height), flags=pygame.SRCALPHA)
        source_rect = surface.get_rect()
        surface.blit(sprite_sheet, (0, 0), source_rect)
        source_rect.x = 2 * source_rect.width
        surface.blit(sprite_sheet, (0, 0), source_rect)
        flipped = pygame.transform.flip(surface, True, False)
        surfaces[ImgSelector.TOP_REACTOR] = surface, flipped
        masks[ImgSelector.TOP_REACTOR] = masks[ImgSelector.IDLE]

        # taxi avec réacteur arrière
        surface = pygame.Surface((sheet_width / Taxi._NB_TAXI_IMAGES, sheet_height), flags=pygame.SRCALPHA)
        source_rect = surface.get_rect()
        surface.blit(sprite_sheet, (0, 0), source_rect)
        source_rect.x = 3 * source_rect.width
        surface.blit(sprite_sheet, (0, 0), source_rect)
        flipped = pygame.transform.flip(surface, True, False)
        surfaces[ImgSelector.REAR_REACTOR] = surface, flipped
        masks[ImgSelector.REAR_REACTOR] = masks[ImgSelector.IDLE]

        # taxi avec réacteurs du dessous et arrière
        surface = pygame.Surface((sheet_width / Taxi._NB_TAXI_IMAGES, sheet_height), flags=pygame.SRCALPHA)
        source_rect = surface.get_rect()
        surface.blit(sprite_sheet, (0, 0), source_rect)
        source_rect.x = source_rect.width
        surface.blit(sprite_sheet, (0, 0), source_rect)
        source_rect.x = 3 * source_rect.width
        surface.blit(sprite_sheet, (0, 0), source_rect)
        flipped = pygame.transform.flip(surface, True, False)
        surfaces[ImgSelector.BOTTOM_AND_REAR_REACTORS] = surface, flipped
        masks[ImgSelector.BOTTOM_AND_REAR_REACTORS] = masks[ImgSelector.IDLE]

        # taxi avec réacteurs du dessus et arrière
        surface = pygame.Surface((sheet_width / Taxi._NB_TAXI_IMAGES, sheet_height), flags=pygame.SRCALPHA)
        source_rect = surface.get_rect()
        surface.blit(sprite_sheet, (0, 0), source_rect)
        source_rect.x = 2 * source_rect.width
        surface.blit(sprite_sheet, (0, 0), source_rect)
        source_rect.x = 3 * source_rect.width
        surface.blit(sprite_sheet, (0, 0), source_rect)
        flipped = pygame.transform.flip(surface, True, False)
        surfaces[ImgSelector.TOP_AND_REAR_REACTORS] = surface, flipped
        masks[ImgSelector.TOP_AND_REAR_REACTORS] = masks[ImgSelector.IDLE]

        # taxi avec train d'atterrissage
        surface = pygame.Surface((sheet_width / Taxi._NB_TAXI_IMAGES, sheet_height), flags=pygame.SRCALPHA)
        source_rect = surface.get_rect()
        surface.blit(sprite_sheet, (0, 0), source_rect)
        source_rect.x = 4 * source_rect.width
        surface.blit(sprite_sheet, (0, 0), source_rect)
        flipped = pygame.transform.flip(surface, True, False)
        surfaces[ImgSelector.GEAR_OUT] = surface, flipped
        masks[ImgSelector.GEAR_OUT] = pygame.mask.from_surface(surface), pygame.mask.from_surface(flipped)

        # taxi avec train d'atterrissage comprimé
        surface = pygame.Surface((sheet_width / Taxi._NB_TAXI_IMAGES, sheet_height), flags=pygame.SRCALPHA)
        source_rect = surface.get_rect()
        source_rect.x = 5 * source_rect.width
        surface.blit(sprite_sheet, (0, 0), source_rect)
        flipped = pygame.transform.flip(surface, True, False)
        surfaces[ImgSelector.GEAR_SHOCKS] = surface, flipped
        masks[ImgSelector.GEAR_SHOCKS] = pygame.mask.from_surface(surface), pygame.mask.from_surface(flipped)

        # taxi avec réacteur du dessous et train d'atterrissage
        surface = pygame.Surface((sheet_width / Taxi._NB_TAXI_IMAGES, sheet_height), flags=pygame.SRCALPHA)
        source_rect = surface.get_rect()
        surface.blit(sprite_sheet, (0, 0), source_rect)
        source_rect.x = source_rect.width
        surface.blit(sprite_sheet, (0, 0), source_rect)
        source_rect.x = 4 * source_rect.width
        surface.blit(sprite_sheet, (0, 0), source_rect)
        flipped = pygame.transform.flip(surface, True, False)
        surfaces[ImgSelector.GEAR_OUT_AND_BOTTOM_REACTOR] = surface, flipped
        masks[ImgSelector.GEAR_OUT_AND_BOTTOM_REACTOR] = masks[ImgSelector.GEAR_OUT]

        # taxi détruit
        surface = pygame.Surface((sheet_width / Taxi._NB_TAXI_IMAGES, sheet_height), flags=pygame.SRCALPHA)
        source_rect = surface.get_rect()
        surface.blit(sprite_sheet, (0, 0), source_rect)
        surface = pygame.transform.flip(surface, False, True)
        flipped = pygame.transform.flip(surface, True, False)
        surfaces[ImgSelector.DESTROYED] = surface, flipped
        masks[ImgSelector.DESTROYED] = pygame.mask.from_surface(surface), pygame.mask.from_surface(flipped)

        return surfaces, masks
