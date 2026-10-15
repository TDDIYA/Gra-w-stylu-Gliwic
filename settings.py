import pygame

pygame.init()

WIDTH, HEIGHT = 960, 640
FPS = 60
GROUND_Y = 535
WORLD_WIDTH = 2600

WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
SCREEN = pygame.Surface((WIDTH, HEIGHT))
SCALED_FRAME = pygame.Surface((WIDTH, HEIGHT))
pygame.display.set_caption("Misja Gliwice: Strażnicy Wiedzy")
CLOCK = pygame.time.Clock()

FONT = pygame.font.SysFont("Arial", 20)
SMALL_FONT = pygame.font.SysFont("Arial", 16)
TITLE_FONT = pygame.font.SysFont("Arial", 38, bold=True)
BIG_FONT = pygame.font.SysFont("Arial", 28, bold=True)

WHITE = (247, 246, 239)
INK = (28, 38, 54)
NAVY = (25, 39, 63)
GOLD = (255, 205, 74)
BLUE = (78, 174, 245)
GREEN = (73, 178, 122)
RED = (226, 102, 93)
