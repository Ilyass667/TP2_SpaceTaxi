import pygame

class JoystickManager: # A5
    """Classe pour gérer les joysticks."""

    def __init__(self):
        pygame.joystick.init()
        self._joystick = None
        self._joystick_found = False

    def _find_joystick(self):
        """Cherche un joystick connecté et l'initialise une seule fois."""
        joystick_count = pygame.joystick.get_count()
        
        if joystick_count > 0 and self._joystick is None:
            self._joystick = pygame.joystick.Joystick(0)
            self._joystick.init()
            self._joystick_found = True
            print(f"Joystick '{self._joystick.get_name()}' détecté.")
            
        elif joystick_count == 0 and self._joystick is not None:
            self._joystick = None

    def get_joystick(self):
        """Retourne l'objet joystick si détecté."""
        return self._joystick

    def is_joystick_connected(self):
        """Retourne True si un joystick est connecté, sinon False."""
        return self._joystick is not None
