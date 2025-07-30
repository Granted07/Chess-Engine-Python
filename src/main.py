import pygame
import sys
from const import *
from game import Game
from square import Square
from move import Move
from minimax import get_best_move_optimized

class Main:

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.depth = int(input("Analysis Depth: "))
        pygame.display.set_caption('Chess Engine')
        self.game = Game()

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
                            game.show_bg(screen)
                            game.show_last_move(screen)
                            game.show_moves(screen)
                            if game.next_player == 'white':
                                best_move = get_best_move_optimized(
                                    board,
                                    depth=depth,
                                    maximizing_player=False,
                                    time_limit=3.0,
                                    verbose=True
                                )
                                if best_move:
                                    piece, (start_row, start_col), move = best_move
                                    print(
                                        f"AI plays: {piece.name} {start_row},{start_col} -> {move.final.row},{move.final.col}")

                            game.next_turn()
                    dragger.undrag_piece()

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
