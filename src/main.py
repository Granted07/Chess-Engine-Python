import pygame
import sys
from const import *
from game import Game
from square import Square
from move import Move
from minimax import get_best_move_optimized
import time

AI_MOVE_EVENT = pygame.USEREVENT + 1

class Main:

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.depth = 4
        # self.depth = int(input("Analysis Depth: "))
        pygame.display.set_caption('Chess Engine')
        self.game = Game()

    def play_ai_move(self):
        game = self.game
        board = game.board

        best_move = get_best_move_optimized(
            board,
            depth=self.depth,
            maximizing_player=True,
            time_limit=3.0,
            verbose=True
        )

        if not best_move:
            return

        piece, (_, _), move = best_move
        captured = board.squares[move.final.row][move.final.col].has_piece()

        board.move(piece, move)
        game.sound_effect(captured)
        board.set_true_en_passant(piece)

        game.show_bg(self.screen)
        game.show_last_move(self.screen)
        game.show_moves(self.screen)
        game.show_pieces(self.screen)
        game.show_hover(self.screen)

        game.next_turn()

    def mainloop(self):
        game = self.game
        screen = self.screen
        depth = self.depth
        dragger = self.game.dragger
        board = self.game.board
        while True:
            game.show_bg(screen)
            game.show_last_move(screen)
            game.show_pieces(screen)
            game.show_moves(screen)
            game.show_hover(screen)

            if dragger.dragging:
                game.show_bg(screen)
                game.show_last_move(screen)
                game.show_moves(screen)
                game.show_pieces(screen)
                game.show_hover(screen)
                dragger.update_blit(screen)

            for event in pygame.event.get():

                if event.type == AI_MOVE_EVENT:
                    self.play_ai_move()

                # i) click
                if event.type == pygame.MOUSEBUTTONDOWN:
                    dragger.update_mouse(event.pos)
                    # print(event.pos)
                    clicked_row = dragger.mouseY // SQUARE_SIZE
                    clicked_col = dragger.mouseX // SQUARE_SIZE
                    # print(dragger.mouseX, dragger.mouseY)
                    # print(clicked_row, clicked_col)
                    if board.squares[clicked_row][clicked_col].has_piece():
                        piece = board.squares[clicked_row][clicked_col].piece
                        # valid piece (colour)
                        if piece.colour == game.next_player:
                            board.calc_moves(piece, clicked_row, clicked_col, bl=True)
                            dragger.save_initial(event.pos)
                            dragger.drag_piece(piece)
                            # show methods
                            game.show_bg(screen)
                            game.show_last_move(screen)
                            game.show_moves(screen)
                            game.show_pieces(screen)

                # ii) mouse track
                if event.type == pygame.MOUSEMOTION:
                    if dragger.dragging:
                        dragger.update_mouse(event.pos)

                # iii) release
                if event.type == pygame.MOUSEBUTTONUP:
                    if dragger.dragging:
                        dragger.update_mouse(event.pos)
                        released_row = dragger.mouseY // SQUARE_SIZE
                        released_col = dragger.mouseX // SQUARE_SIZE
                        # fetch valid moves
                        initial = Square(dragger.initial_row, dragger.initial_col)
                        final = Square(released_row, released_col)
                        move = Move(initial, final)
                        if board.valid_move(dragger.piece, move):
                            captured = board.squares[released_row][released_col].has_piece()
                            board.move(dragger.piece, move)
                            game.sound_effect(captured)
                            board.set_true_en_passant(dragger.piece)
                            game.next_turn()
                    dragger.undrag_piece()
                    game.show_bg(screen)
                    game.show_last_move(screen)
                    game.show_moves(screen)
                    game.show_pieces(screen)
                    game.show_hover(screen)
                    if game.next_player == 'black':
                        pygame.event.post(pygame.event.Event(AI_MOVE_EVENT))

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        game.reset()
                        game = self.game
                        screen = self.screen
                        dragger = self.game.dragger
                        board = self.game.board

                    if event.key == pygame.K_a:  # Press 'A' for analysis
                        pass

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_t:
                        game.change_theme()

                # quit
                elif event.type == pygame.QUIT:
                    sys.exit()

            pygame.display.update()


main = Main()
main.mainloop()
