import pygame

from game_settings import GameSettings
from file_error import FileError # C3



class HUD:
    """ Singleton pour l'affichage tête haute (HUD). """

    _LIVES_ICONS_FILENAME = "img/hud_lives.png"
    _LIVES_ICONS_SPACING = 10
    _FUEL_GAUGE_FULL = "img/fuel_gauge_full.png"  # Modif Début A14 : Ajouter image jauge pleine
    _FUEL_GAUGE_EMPTY = "img/fuel_gauge_empty.png"  # Ajouter image jauge vide

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(HUD, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, '_initialized'):
            self._settings = GameSettings()

            try:
                # Modif Début A14
                self._fuel_gauge_full = pygame.image.load(HUD._FUEL_GAUGE_FULL).convert_alpha()  # Charger jauge pleine
                self._fuel_gauge_empty = pygame.image.load(HUD._FUEL_GAUGE_EMPTY).convert_alpha()  # Charger jauge vide
                self._fuel_level = 1.0  # Niveau d'essence entre 0 (vide) et 1 (plein)

                self._fuel_pos = pygame.Vector2(
                    (self._settings.SCREEN_WIDTH - self._fuel_gauge_full.get_width()) // 2,
                    self._settings.SCREEN_HEIGHT - self._fuel_gauge_full.get_height() - 10
                )
                self._fuel_font = pygame.font.Font(self._settings.FONT_BOOMBOX2, 14)  # Police pour "FUEL"
                self._fuel_text_surface = self._fuel_font.render("FUEL", True, (255, 255, 255))  # Texte "FUEL"

                # Modif Fin A14


                # Modif M8 Début : Changer la police utilisée pour afficher les montants d’argent
                self._money_font = pygame.font.Font(self._settings.FONT_BOOMBOX2, 28)
                # Modif M8 Fin

                self._bank_money = 0
                self._bank_money_surface = self._render_bank_money_surface()
                self._bank_money_pos = pygame.Vector2(20, self._settings.SCREEN_HEIGHT - (self._bank_money_surface.get_height() + 10))

                self._trip_money = 0
                self._trip_money_surface = self._render_trip_money_surface()

                self._lives = self._settings.NB_PLAYER_LIVES
                self._lives_icon = pygame.image.load(HUD._LIVES_ICONS_FILENAME).convert_alpha()
                self._lives_pos= pygame.Vector2(20, self._settings.SCREEN_HEIGHT - (self._lives_icon.get_height() + 40))

                self.visible = False
                self._initialized = True

            except FileNotFoundError as e: # C3
                error_message = str(e)
                filename = error_message.split("No file '")[1].split("'")[0]
                error = FileError(f"FATAL ERROR loading {filename}")
                error.run()

    def render(self, screen: pygame.Surface) -> None:

        # Modif Début A14 : Afficher la jauge d'essence
        fuel_width = self._fuel_gauge_full.get_width() * (self._fuel_level / 2.0)
        gauge_surface = self._fuel_gauge_empty.copy()
        gauge_surface.blit(
            self._fuel_gauge_full,
            (0, 0),
            (0, 0, fuel_width, self._fuel_gauge_full.get_height())
        )
        screen.blit(gauge_surface, (self._fuel_pos.x, self._fuel_pos.y))
        text_x = self._fuel_pos.x + (self._fuel_gauge_full.get_width() - self._fuel_text_surface.get_width()) // 2
        text_y = self._fuel_pos.y + (self._fuel_gauge_full.get_height() - self._fuel_text_surface.get_height()) // 2
        screen.blit(self._fuel_text_surface, (text_x, text_y))
        # Modif Fin A14

        spacing = self._lives_icon.get_width() + HUD._LIVES_ICONS_SPACING
        for n in range(self._lives):
            screen.blit(self._lives_icon, (self._lives_pos.x + (n * spacing), self._lives_pos.y))

        screen.blit(self._bank_money_surface, (self._bank_money_pos.x, self._bank_money_pos.y))

        x = self._settings.SCREEN_WIDTH - self._trip_money_surface.get_width() - 20
        y = self._settings.SCREEN_HEIGHT - self._trip_money_surface.get_height() - 10
        screen.blit(self._trip_money_surface, (x, y))

    # Modif Début A14
    def update_fuel(self, level: float) -> None:
        """ Met à jour le niveau d'essence à afficher. """

        self._fuel_level = max(0.0, min(level, 2.0))
        # Modif Fin A14

    def add_bank_money(self, amount: float) -> None:
        self._bank_money += round(amount, 2)
        self._bank_money_surface = self._render_bank_money_surface()

    def get_lives(self) -> int:
        return self._lives

    def loose_live(self) -> None:
        if self._lives > 0:
            self._lives -= 1

    def reset(self) -> None:
        self._bank_money = 0
        self._bank_money_surface = self._render_bank_money_surface()
        self._lives = self._settings.NB_PLAYER_LIVES

    def set_trip_money(self, trip_money: float) -> None:
        if self._trip_money != trip_money:
            self._trip_money = trip_money
            self._trip_money_surface = self._render_trip_money_surface()

    def _render_bank_money_surface(self) -> pygame.Surface:
        money_str = f"{self._bank_money:.2f}"
        return self._money_font.render(f"${money_str: >8}", True, (51, 51, 51))

    def _render_trip_money_surface(self) -> pygame.Surface:
        money_str = f"{self._trip_money:.2f}"
        return self._money_font.render(f"${money_str: >5}", True, (51, 51, 51))
