import math

import pygame

from const import *
from board import Board
from src.dragger import Dragger


class Game:
    def __init__(self):
        self.board = Board()
        self.dragger = Dragger()

    @staticmethod
    def show_bg(surface):
        f = 1
        for row in range(ROWS):
            f = math.fabs(f - 1)
            for col in range(COLS):
                if f == 1:
                    colour, f = (31, 165, 209), 0  # dark
                else:
                    colour, f = (167, 216, 232), 1  # light
                rect = (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                pygame.draw.rect(surface, colour, rect)

    def show_pieces(self, surface):
        for row in range(ROWS):
            for col in range(COLS):
                if self.board.squares[row][col].has_piece():
                    piece = self.board.squares[row][col].piece

                    # no dragger piece
                    if piece is not self.dragger.piece:
                        try:
                            piece.set_texture(80)
                        except:
                            pass
                        img = pygame.image.load(piece.texture)
                        img_center = col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2
                        piece.texture_rect = img.get_rect(center=img_center)
                        surface.blit(img, piece.texture_rect)
