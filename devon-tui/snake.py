import pygame
import sys
import random

# Initialize Pygame
pygame.init()

# Set up the game window
width = 800
height = 600
display = pygame.display.set_mode((width, height))
pygame.display.set_caption("Snake Game")

# Define colors
black = (0, 0, 0)
white = (255, 255, 255)
red = (255, 0, 0)

# Game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    
    # Fill the display with white
    display.fill(white)
    
    # Update the display
    pygame.display.update()
