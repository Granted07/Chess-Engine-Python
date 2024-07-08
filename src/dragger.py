import pygame

from const import *


class Dragger:
    def __init__(self):
        self.piece = None
        self.dragging: bool = False
        self.mouseX = 0
        self.mouseY = 0
        self.initial_row = 0
        self.initial_col = 0

    def update_blit(self, surface):
        self.piece.set_texture(size=120)
        texture = self.piece.texture
        img = pygame.image.load(texture)
        img_center = (self.mouseX, self.mouseY)
        self.piece.texture_rect = img.get_rect(center=img_center)
        surface.blit(img, self.piece.texture_rect)

    def update_mouse(self, pos: tuple):
        self.mouseX, self.mouseY = pos

    def save_initial(self, pos: tuple):
        self.initial_row, self.initial_col = pos[1] // SQUARE_SIZE, pos[0] // SQUARE_SIZE

    def drag_piece(self, piece):
        self.piece = piece
        self.dragging = 1

    def undrag_piece(self):
        self.piece = None
        self.dragging = 0
