import pygame
import numpy as np

# Initialize Pygame
pygame.init()

# Set the window size
width, height = 800, 600
screen = pygame.display.set_mode((width, height))

# Set the grid size and cell size
grid_size = 50
cell_size = 10

# Create the initial grid
grid = np.zeros((grid_size, grid_size))

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pressed = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                mouse_pressed = False
        elif event.type == pygame.event.MOUSEMOTION:
            if mouse_pressed:
                x, y = event.pos
                grid[x // cell_size, y // cell_size] = 1
        if event.type == pygame.QUIT:
            running = False

    # Update the grid according to the rules of Conway's Game of Life
    update_grid(grid)

def update_grid(grid):
    new_grid = grid.copy()
    for i in range(grid_size):
        for j in range(grid_size):
            # Count live neighbors
            neighbors = np.sum(grid[max(0, i-1):min(grid_size, i+2), max(0, j-1):min(grid_size, j+2)]) - grid[i, j]

            # Apply rules
            if grid[i, j] == 1:
                if neighbors < 2 or neighbors > 3:
                    new_grid[i, j] = 0
            else:
                if neighbors == 3:
                    new_grid[i, j] = 1

    # Update grid
    grid[:] = new_grid

    return grid

    # Clear the screen
    screen.fill((255, 255, 255))

    # Draw the grid
    for i in range(grid_size):
        for j in range(grid_size):
            if grid[i, j] == 1:
                pygame.draw.rect(screen, (0, 0, 0), (i * cell_size, j * cell_size, cell_size, cell_size))

    # Update the display
    pygame.display.flip()

# Quit Pygame
pygame.quit()