import pygame

# Initialisation de Pygame
pygame.init()

# Initialisation du joystick
pygame.joystick.init()
if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Joystick détecté : {joystick.get_name()}")
else:
    print("Aucun joystick détecté.")
    pygame.quit()
    exit()

# Boucle principale
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.JOYBUTTONDOWN:
            print(f"Bouton {event.button} pressé.")
            if event.button == 1:
                print("Bouton")

    # Détection des axes
    # Axe 0 : Gauche/Droite | Axe 4 : Haut/Bas
    axis_x = joystick.get_axis(0)  # Gauche/Droite
    axis_y = joystick.get_axis(4)  # Haut/Bas

    if axis_x < -0.5:
        print("Flèche gauche")
    elif axis_x > 0.5:
        print("Flèche droite")

    if axis_y < -0.5:
        print("Flèche haut")
    elif axis_y > 0.5:
        print("Flèche bas")

    # Petite pause pour éviter une surcharge de messages
    pygame.time.wait(100)

# Quitter Pygame
pygame.quit()
