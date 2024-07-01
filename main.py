import pygame
import numpy as np
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import random
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Fluid Simulation - Revenue Progress")

# Colors
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)

# Fluid properties
INITIAL_PARTICLES = 1000
GRAVITY = 0.1
PARTICLE_RADIUS = 2
PARTICLE_DIAMETER = PARTICLE_RADIUS * 2

# Grid properties
GRID_SIZE = 10

# Revenue goal
REVENUE_GOAL = 1000000  # Target revenue
current_revenue = 0 + INITIAL_PARTICLES  # Current revenue
particles = []

# Particle class using numpy for efficient operations
class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0

def create_particles(num_particles):
    for _ in range(num_particles):
        x = np.random.rand() * WIDTH
        y = np.random.rand() * HEIGHT
        particles.append(Particle(x, y))

def update_particles():
    global current_revenue
    target_particles = current_revenue
    additional_particles = target_particles - len(particles)
    if additional_particles > 0:
        create_particles(additional_particles)

def get_effective_height():
    num_particles = len(particles)
    sample_size = int(math.log2(num_particles))
    sample_indices = random.sample(range(num_particles), sample_size)
    sample_heights = [particles[i].y for i in sample_indices]
    sample_heights.extend([particles[0].y, particles[-1].y])
    effective_height = max(sample_heights)
    return effective_height

def update_particle_positions(particles):
    for particle in particles:
        # Apply gravity
        particle.vy += GRAVITY
        # Update position
        particle.x += particle.vx
        particle.y += particle.vy

        # Boundary conditions
        if particle.y > HEIGHT - PARTICLE_RADIUS:
            particle.y = HEIGHT - PARTICLE_RADIUS
            particle.vy *= -0.5  # Some energy loss on bounce

        if particle.x > WIDTH - PARTICLE_RADIUS:
            particle.x = WIDTH - PARTICLE_RADIUS
            particle.vx *= -0.5

        if particle.x < PARTICLE_RADIUS:
            particle.x = PARTICLE_RADIUS
            particle.vx *= -0.5

def handle_collisions():
    grid = defaultdict(list)
    effective_height = get_effective_height()
    

    # Populate grid up to the effective height
    for particle in particles:
        if particle.y <= effective_height:
            grid_x = int(particle.x // GRID_SIZE)
            grid_y = int(particle.y // GRID_SIZE)
            grid[(grid_x, grid_y)].append(particle)

    def process_cell(cell_particles):
        for i, p1 in enumerate(cell_particles):
            for j in range(i + 1, len(cell_particles)):
                p2 = cell_particles[j]
                dx = p1.x - p2.x
                dy = p1.y - p2.y
                distance = np.sqrt(dx**2 + dy**2)

                # Avoid division by zero and handle valid distances
                if 0 < distance < PARTICLE_DIAMETER:
                    overlap = PARTICLE_DIAMETER - distance
                    if distance != 0:
                        dx /= distance
                        dy /= distance
                    else:
                        dx = dy = 0

                    half_overlap = overlap * 0.5  # Using multiplication for simplicity
                    dx_overlap = dx * half_overlap
                    dy_overlap = dy * half_overlap
                    p1.x += dx_overlap
                    p1.y += dy_overlap
                    p2.x -= dx_overlap
                    p2.y -= dy_overlap

    # Parallel processing for collision handling
    with ThreadPoolExecutor() as executor:
        executor.map(process_cell, grid.values())

# Main loop
running = True
clock = pygame.time.Clock()
create_particles(INITIAL_PARTICLES)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                current_revenue += 1000  # Increase revenue for demonstration
            elif event.key == pygame.K_DOWN:
                current_revenue = max(0, current_revenue - 1000)  # Decrease revenue for demonstration

    # Update particles
    update_particles()

    # Parallel processing for updating particle positions
    with ThreadPoolExecutor() as executor:
        executor.map(update_particle_positions, [particles])

    # Handle collisions
    handle_collisions()

    # Draw everything
    screen.fill(BLACK)
    for particle in particles:
        pygame.draw.circle(screen, BLUE, (int(particle.x), int(particle.y)), PARTICLE_RADIUS)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
