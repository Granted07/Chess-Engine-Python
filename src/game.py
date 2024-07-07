import math

import pygame

from const import *
class Game:
    def __init__(self):
        pass

    @staticmethod
    def show_bg(surface):
        f = 1
        for row in range(ROWS):
            f = math.fabs(f-1)
            for col in range(COLS):
                if f == 1:
                    color,f = (0,0,0),0
                else:
                    color,f = (255,255,255),1
                rect = (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                pygame.draw.rect(surface, color, rect)