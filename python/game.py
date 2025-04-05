import pygame
import threading
import chess
import copy
from ai import best_move

class Game:
    def __init__(self):
        self.board = chess.Board()
        self.selected_square = None
        self.ai_thinking = False
        self.ai_move = None
        self.ai_move_time = 0
        self.clock = pygame.time.Clock()
        self.running = True

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and not self.ai_thinking:
            x, y = pygame.mouse.get_pos()
            col, row = x // 75, y // 75
            square = chess.square(col, 7 - row)
            if self.selected_square is None:
                if self.board.piece_at(square) and self.board.color_at(square) == self.board.turn:
                    self.selected_square = square
            else:
                move = self.create_move(self.selected_square, square)
                if move in self.board.legal_moves:
                    self.board.push(move)
                    self.check_game_end()
                    if not self.board.turn and not self.ai_thinking:
                        board_copy = copy.deepcopy(self.board)
                        threading.Thread(target=self.ai_move_thread, args=(board_copy,), daemon=True).start()
                self.selected_square = None

    def create_move(self, from_sq, to_sq):
        piece = self.board.piece_at(from_sq)
        if piece and piece.piece_type == chess.PAWN:
            rank = chess.square_rank(to_sq)
            if (piece.color == chess.WHITE and rank == 7) or (piece.color == chess.BLACK and rank == 0):
                return chess.Move(from_sq, to_sq, promotion=chess.QUEEN)
        return chess.Move(from_sq, to_sq)

    def ai_move_thread(self, board_state):
        self.ai_thinking = True
        self.ai_move_time = pygame.time.get_ticks()
        move = best_move(board_state, depth=5, time_limit=7000)
        self.ai_move = move
        self.ai_thinking = False

    def update_ai_move(self):
        if self.ai_move and not self.ai_thinking and pygame.time.get_ticks() - self.ai_move_time >= 1000:
            if self.ai_move in self.board.legal_moves:
                self.board.push(self.ai_move)
                self.check_game_end()
            self.ai_move = None

    def check_game_end(self):
        if self.board.is_checkmate():
            print("Chiếu hết!")
            self.running = False
        elif self.board.is_stalemate():
            print("Hết nước đi (Stalemate)!")
            self.running = False
        elif self.board.is_insufficient_material():
            print("Hòa vì thiếu quân!")
            self.running = False
        elif self.board.is_seventyfive_moves():
            print("Hòa do 75 nước không ăn quân hoặc đi tốt!")
            self.running = False
        elif self.board.can_claim_threefold_repetition():
            print("Hòa do lặp lại vị trí!")
            self.running = False
