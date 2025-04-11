import pygame
import chess

BOARD_WIDTH, HEIGHT = 600, 600
SIDEBAR_WIDTH = 120
WIDTH = BOARD_WIDTH + SIDEBAR_WIDTH
SQUARE_SIZE = BOARD_WIDTH // 8

WHITE = (240, 217, 181)
BROWN = (181, 136, 99)
HIGHLIGHT = (186, 202, 68)
SIDEBAR_BG = (30, 30, 30)
TEXT_COLOR = (255, 255, 255)
BUTTON_COLOR = (200, 50, 50)

PIECE_IMAGES = {}
PIECES = ['p', 'r', 'n', 'b', 'q', 'k', 'p1', 'r1', 'n1', 'b1', 'q1', 'k1']
for piece in PIECES:
    try:
        PIECE_IMAGES[piece] = pygame.image.load(f'assets/{piece}.png')
        PIECE_IMAGES[piece] = pygame.transform.scale(PIECE_IMAGES[piece], (SQUARE_SIZE, SQUARE_SIZE))
    except pygame.error:
        print(f"Không thể load ảnh cho quân {piece}")

def draw_board(screen):
    for row in range(8):
        for col in range(8):
            color = WHITE if (row + col) % 2 == 0 else BROWN
            pygame.draw.rect(screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

def draw_pieces(screen, board):
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            col, row = chess.square_file(square), 7 - chess.square_rank(square)
            symbol = piece.symbol()
            if symbol.isupper():
                symbol = symbol.lower() + "1"
            screen.blit(PIECE_IMAGES[symbol], (col * SQUARE_SIZE, row * SQUARE_SIZE))

def highlight_moves(screen, board, square):
    legal_moves = [move for move in board.legal_moves if move.from_square == square]
    for move in legal_moves:
        col, row = chess.square_file(move.to_square), 7 - chess.square_rank(move.to_square)
        pygame.draw.circle(screen, HIGHLIGHT,
                           (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2), 10)

def draw_sidebar(screen, font, depth, ai_time, exit_button_rect):
    pygame.draw.rect(screen, SIDEBAR_BG, (BOARD_WIDTH, 0, SIDEBAR_WIDTH, HEIGHT))

    depth_text = font.render(f"Độ sâu: {depth}", True, TEXT_COLOR)
    time_text = font.render(f"Thời gian: {ai_time:.2f}s", True, TEXT_COLOR)

    screen.blit(depth_text, (BOARD_WIDTH + 10, 50))
    screen.blit(time_text, (BOARD_WIDTH + 10, 100))

    pygame.draw.rect(screen, BUTTON_COLOR, exit_button_rect)
    exit_text = font.render("Thoát", True, TEXT_COLOR)
    screen.blit(exit_text, exit_button_rect.move(10, 10))
