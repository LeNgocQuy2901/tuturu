import pygame
import threading
import chess
import copy
import chess.polyglot
from ai import best_move

class Game:
    def __init__(self):
        self.board = chess.Board()
        self.view_board = chess.Board()  # Board để xem lại
        self.history_index = 0           # Chỉ số để biết đang xem tới bước thứ mấy
        self.selected_square = None
        self.ai_thinking = False
        self.ai_color = chess.BLACK
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
                    self.history_index = len(self.board.move_stack)
                    self.view_board = self.board.copy()

                    self.sync_view_board()
                    self.check_game_end()
                    if not self.board.turn and not self.ai_thinking:
                        board_copy = copy.deepcopy(self.board)
                        threading.Thread(target=self.ai_move_thread, args=(board_copy,), daemon=True).start()
                self.selected_square = None

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.history_index = max(0, self.history_index - 1)
                self.update_view_board()
            elif event.key == pygame.K_RIGHT:
                self.history_index = min(len(self.board.move_stack), self.history_index + 1)
                self.update_view_board()

    def sync_view_board(self):
        self.history_index = len(self.board.move_stack)
        self.update_view_board()

    def update_view_board(self):
        self.view_board = chess.Board()
        for move in self.board.move_stack[:self.history_index]:
            self.view_board.push(move)


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

        try:
            with chess.polyglot.open_reader("baron30.bin") as reader:
                try:
                    entry = reader.find(board_state)
                    self.ai_move = entry.move
                    print(f"[AI] Sử dụng opening book: {self.ai_move}")
                except IndexError:
                    print("[AI] Không có nước trong opening book. Dùng minimax.")
                    self.ai_move = best_move(board_state, depth=3)
        except Exception as e:
            print("[Lỗi] Mở file book thất bại:", e)
            self.ai_move = best_move(board_state, depth=3)

        self.ai_thinking = False


    def update_ai_move(self):
        if self.ai_move and not self.ai_thinking and pygame.time.get_ticks() - self.ai_move_time >= 1000:
            if self.ai_move in self.board.legal_moves:
                self.board.push(self.ai_move)
                self.history_index = len(self.board.move_stack)
                self.view_board = self.board.copy()

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
def reset_board(self):
    import chess
    self.board = chess.Board()

def push_move_uci(self, move_uci):
    import chess
    move = chess.Move.from_uci(move_uci)
    if move in self.board.legal_moves:
        self.board.push(move)

def get_best_move(self):
    from ai import best_move  # nếu bạn viết AI ở ai.py
    move = best_move(self.board)
    return move.uci()
