import pygame

from game_settings import GameSettings


class Pad(pygame.sprite.Sprite):
    """ Plateforme. """

    UP = None  # Pad.UP est utilisé pour indiquer la sortie du niveau

    _TEXT_COLOR = (255, 255, 255)
    _HEIGHT = 40

    # Début modif M3 : Cache global pour éviter les allocations multiples
    _image_cache = {}
    # Fin modif M3

    def __init__(self, number: int, filename: str, pos: tuple, astronaut_start_x: int, astronaut_end_x: int) -> None:
        """
        Initialise une instance de plateforme.
        :param number: le numéro de la plateforme
        :param filename: le nom du fichier graphique à utiliser
        :param pos: la position (x, y) de la plateforme à l'écran
        :param astronaut_start_x: la distance horizontale à partir du bord où apparaissent les astronautes
        :param astronaut_end_x: la distance horizontale à partir du bord où disparaissent les astronautes
        """
        super(Pad, self).__init__()

        self.number = number
        # Début modif M3 : Chargement ou récupération de l'image depuis le cache
        if filename in Pad._image_cache:
            print(f"Image '{filename}' récupérée depuis le cache.")
            self.image = Pad._image_cache[filename]
        else:
            print(f"Chargement de l'image '{filename}' en mémoire.")
            self.image = pygame.image.load(filename).convert_alpha()
            Pad._image_cache[filename] = self.image
        # Fin modif M3
        self.mask = pygame.mask.from_surface(self.image)

        font = GameSettings().pad_font
        self._label_text = font.render(f"  PAD {number}  ", True, Pad._TEXT_COLOR)
        text_width, text_height = self._label_text.get_size()

        background_height = text_height + 4
        background_width = text_width + background_height  # + hauteur, pour les coins arrondis
        self._label_background = Pad._build_label(background_width, background_height)

        # Début modif M2 : Recherche de la vraie zone plate en haut
        collision_bounds = self._get_top_flat_zone()
        if collision_bounds:
            collision_x_min, collision_x_max, y_position = collision_bounds
            collision_center_x = (collision_x_min + collision_x_max) / 2

            # Centrer le texte
            text_offset_x = collision_center_x - text_width / 2

            # Centrer l’arrière-plan gris
            background_offset_x = collision_center_x - background_width / 2
        else:
            # Aucun plateau détecté, centrage par défaut
            text_offset_x = (self.image.get_width() - text_width) / 2
            background_offset_x = (self.image.get_width() - background_width) / 2

        self._label_text_offset = (text_offset_x, 3)  # Appliquer l'offset calculé pour le texte
        self._label_background_offset = (background_offset_x, 2)  # Appliquer l'offset calculé pour le background
        # Fin modif M2

        self.image.blit(self._label_background, self._label_background_offset)  # Dessine l'arrière-plan du texte
        self.image.blit(self._label_text, self._label_text_offset)

        self.rect = self.image.get_rect()
        self.rect.x = pos[0]
        self.rect.y = pos[1]

        self.astronaut_start = pygame.Vector2(self.rect.x + astronaut_start_x, self.rect.y - 24)
        self.astronaut_end = pygame.Vector2(self.rect.x + astronaut_end_x, self.rect.y - 24)

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.image, self.rect)

    def get_center(self): # M16
        return (self.rect.x + self.rect.width / 2, self.rect.y + self.rect.height / 2)

    def update(self, *args, **kwargs) -> None:
        pass

    # Début modif M2 : Méthode pour détecter la vraie zone plate
    def _get_top_flat_zone(self) -> tuple:
        """
        Trouve la première grande zone plate (surface de collision continue) en haut du masque.
        :return: (x_min, x_max, y_position) de la zone plate
        """
        width, height = self.mask.get_size()

        for y in range(height):  # Parcourir les lignes du haut vers le bas
            collision_points = [x for x in range(width) if self.mask.get_at((x, y))]
            if len(collision_points) > 1:  # Trouver une ligne avec une zone continue
                x_min = min(collision_points)
                x_max = max(collision_points)
                return x_min, x_max, y  # Retourne la première zone plate trouvée

        return None  # Aucune zone plate détectée
    # Fin modif M2

    @staticmethod
    def _build_label(width: int, height: int) -> pygame.Surface:
        """
        Construit l'étiquette (text holder) semi-transparente sur laquelle on affiche le nom de la plateforme.
        :param width: largeur de l'étiquette
        :param height: hauteur de l'étiquette
        :return: une surface contenant un rectangle arrondi semi-transparent (l'étiquette)
        """
        surface = pygame.Surface((width, height), pygame.SRCALPHA)

        radius = height / 2
        pygame.draw.circle(surface, (0, 0, 0), (radius, radius), radius)
        pygame.draw.circle(surface, (0, 0, 0), (width - radius, radius), radius)
        pygame.draw.rect(surface, (0, 0, 0), (radius, 0, width - 2 * radius, height))

        surface.lock()
        for x in range(surface.get_width()):
            for y in range(surface.get_height()):
                r, g, b, a = surface.get_at((x, y))
                if a != 0:
                    surface.set_at((x, y), (r, g, b, 128))
        surface.unlock()

        return surface
