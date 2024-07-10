import math

import pygame

from const import *
from board import Board
from dragger import Dragger
from config import Config


class Game:
    def __init__(self):
        self.hovered_sqr = None
        self.board = Board()
        self.dragger = Dragger()
        self.next_player = 'white'
        self.config = Config()

    def show_bg(self, surface):
        theme = self.config.theme
        f = 1
        for row in range(ROWS):
            f = math.fabs(f - 1)
            for col in range(COLS):
                if f == 1:
                    colour, f = theme.bg.dark, 0  # dark
                else:
                    colour, f = theme.bg.light, 1  # light
                rect = (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                pygame.draw.rect(surface, colour, rect)

    def show_pieces(self, surface):
        for row in range(ROWS):
            for col in range(COLS):
                if self.board.squares[row][col].has_piece():
                    piece = self.board.squares[row][col].piece

                    # no dragger piece
                    if piece is not self.dragger.piece:
                        piece.set_texture(80)
                        img = pygame.image.load(piece.texture)
                        img_center = col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2
                        piece.texture_rect = img.get_rect(center=img_center)
                        surface.blit(img, piece.texture_rect)

    def show_moves(self, surface):
        theme = self.config.theme
        if self.dragger.dragging:
            piece = self.dragger.piece
            for move in piece.moves:
                colour = theme.moves.light if (move.final.row + move.final.col) % 2 == 0 else theme.moves.dark
                rect = (move.final.col * SQUARE_SIZE, move.final.row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                pygame.draw.rect(surface, colour, rect)

    def show_last_moves(self, surface):
        theme = self.config.theme
        if self.board.last_moves:
            initial = self.board.last_moves.initial
            final = self.board.last_moves.final

            for pos in [initial, final]:
                color = theme.trace.light if (pos.row + pos.col) % 2 == 0 else theme.trace.dark
                pygame.draw.rect(surface, color, pos)

    def show_hover(self, surface):
        if self.hovered_sqr:
            # color
            color = (180, 180, 180)
            # rect
            rect = (self.hovered_sqr.col * SQUARE_SIZE, self.hovered_sqr.row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            # blit
            pygame.draw.rect(surface, color, rect, width=3)

    def next_turn(self):
        self.next_player = 'white' if self.next_player == 'black' else 'black'

    def set_hover(self, row, col):
        self.hovered_sqr = self.board.squares[row][col]

    def change_theme(self):
        self.config.change_theme()

    def reset(self):
        self.__init__()
