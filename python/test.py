import threading
import pygame
import chess
import random
import time
import copy

# Các hằng số và màu sắc
WIDTH, HEIGHT = 600, 600
SQUARE_SIZE = WIDTH // 8
WHITE = (240, 217, 181)
BROWN = (181, 136, 99)
HIGHLIGHT = (186, 202, 68)

# Khởi tạo pygame trước khi load ảnh
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess Game")

# Load ảnh quân cờ
PIECE_IMAGES = {}
PIECES = ['p', 'r', 'n', 'b', 'q', 'k', 'p1', 'r1', 'n1', 'b1', 'q1', 'k1']
for piece in PIECES:
    try:
        PIECE_IMAGES[piece] = pygame.image.load(f'assets/{piece}.png')
        PIECE_IMAGES[piece] = pygame.transform.scale(PIECE_IMAGES[piece], (SQUARE_SIZE, SQUARE_SIZE))
    except pygame.error:
        print(f"Không thể load ảnh cho quân {piece}")

# Khởi tạo bàn cờ
board = chess.Board()
selected_square = None
ai_thinking = False
ai_move = None
ai_move_time = 0
clock = pygame.time.Clock()

# Bảng định vị đơn giản cho các quân cờ (tối ưu cho quân trắng, lật ngược cho đen)
PAWN_TABLE = [
    0, 0, 0, 0, 0, 0, 0, 0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5, 5, 10, 25, 25, 10, 5, 5,
    0, 0, 5, 20, 20, 5, 0, 0,
    5, -5, -10, 0, 0, -10, -5, 5,
    5, 10, 10, -20, -20, 10, 10, 5,
    0, 0, 0, 0, 0, 0, 0, 0
]

KNIGHT_TABLE = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20, 0, 0, 0, 0, -20, -40,
    -30, 0, 10, 15, 15, 10, 0, -30,
    -30, 5, 15, 20, 20, 15, 5, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -30, 5, 10, 15, 15, 10, 5, -30,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50
]


# Các hàm vẽ
def draw_board():
    for row in range(8):
        for col in range(8):
            color = WHITE if (row + col) % 2 == 0 else BROWN
            pygame.draw.rect(screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))


def draw_pieces():
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            col, row = chess.square_file(square), 7 - chess.square_rank(square)
            symbol = piece.symbol()
            if symbol.isupper():
                symbol = symbol.lower() + "1"
            screen.blit(PIECE_IMAGES[symbol], (col * SQUARE_SIZE, row * SQUARE_SIZE))


def highlight_moves(square):
    legal_moves = [move for move in board.legal_moves if move.from_square == square]
    for move in legal_moves:
        col, row = chess.square_file(move.to_square), 7 - chess.square_rank(move.to_square)
        pygame.draw.circle(screen, HIGHLIGHT,
                           (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2), 10)


# Hàm đánh giá bàn cờ cải tiến
def evaluate_board(board):
    piece_values = {
        chess.PAWN: 100, chess.ROOK: 500, chess.KNIGHT: 320,
        chess.BISHOP: 330, chess.QUEEN: 900, chess.KING: 20000
    }
    value = 0

    # Đánh giá giá trị quân cờ và vị trí
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            base_value = piece_values.get(piece.piece_type, 0)
            sign = 1 if piece.color == chess.WHITE else -1

            # Thêm giá trị vị trí
            if piece.piece_type == chess.PAWN:
                table_value = PAWN_TABLE[square] if piece.color == chess.WHITE else PAWN_TABLE[63 - square]
            elif piece.piece_type == chess.KNIGHT:
                table_value = KNIGHT_TABLE[square] if piece.color == chess.WHITE else KNIGHT_TABLE[63 - square]
            else:
                table_value = 0  # Có thể thêm bảng cho các quân khác

            value += sign * (base_value + table_value)

    # Đánh giá kiểm soát trung tâm
    center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
    for square in center_squares:
        if board.piece_at(square):
            value += (10 if board.color_at(square) == chess.WHITE else -10)

    # Phạt nếu vua ở gần biên
    white_king = board.king(chess.WHITE)
    black_king = board.king(chess.BLACK)
    if white_king and chess.square_file(white_king) in (0, 7):
        value -= 20
    if black_king and chess.square_file(black_king) in (0, 7):
        value += 20

    # Thưởng nếu được nhập thành
    if board.has_castling_rights(chess.WHITE):
        value += 50
    if board.has_castling_rights(chess.BLACK):
        value -= 50

    return value


# Hàm Minimax với Alpha-Beta Pruning
def minimax(board, depth, alpha, beta, maximizing_player):
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)

    if maximizing_player:
        max_eval = float('-inf')
        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval


# Hàm tìm nước đi tốt nhất cho AI
def best_move(board, depth, time_limit=7000):
    board_copy = copy.deepcopy(board)
    best_move = None
    max_eval = float('-inf')
    start_time = pygame.time.get_ticks()

    # Sắp xếp nước đi để tối ưu Alpha-Beta (ưu tiên nước bắt quân)
    moves = sorted(board_copy.legal_moves, key=lambda m: board_copy.is_capture(m), reverse=True)

    for move in moves:
        if pygame.time.get_ticks() - start_time > time_limit:
            break
        board_copy.push(move)
        eval = minimax(board_copy, depth - 1, float('-inf'), float('inf'), False)
        board_copy.pop()
        if eval > max_eval:
            max_eval = eval
            best_move = move

    return best_move or random.choice(list(board.legal_moves))


# Hàm thực thi AI trong luồng riêng
def ai_thread(board_state):
    global ai_thinking, ai_move, ai_move_time
    ai_thinking = True
    ai_move_time = pygame.time.get_ticks()
    move = best_move(board_state, depth=5, time_limit=7000)
    ai_move = move
    ai_thinking = False


# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and not ai_thinking:
            x, y = pygame.mouse.get_pos()
            col, row = x // SQUARE_SIZE, y // SQUARE_SIZE
            square = chess.square(col, 7 - row)

            if selected_square is None:
                if board.piece_at(square) and board.color_at(square) == board.turn:
                    selected_square = square
            else:
                move = chess.Move(selected_square, square)
                if move in board.legal_moves:
                    board.push(move)
                    if not board.turn and not ai_thinking:  # Đến lượt AI (đen)
                        board_copy = copy.deepcopy(board)
                        threading.Thread(target=ai_thread, args=(board_copy,), daemon=True).start()
                selected_square = None

    screen.fill((0, 0, 0))
    draw_board()
    draw_pieces()

    if selected_square is not None:
        highlight_moves(selected_square)

    if ai_move and not ai_thinking and pygame.time.get_ticks() - ai_move_time >= 1000:
        if ai_move in board.legal_moves:
            board.push(ai_move)
        ai_move = None

    pygame.display.flip()
    clock.tick(60)

pygame.quit()