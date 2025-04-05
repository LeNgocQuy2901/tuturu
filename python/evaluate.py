import chess

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

def evaluate_board(board):
    piece_values = {
        chess.PAWN: 100, chess.ROOK: 500, chess.KNIGHT: 320,
        chess.BISHOP: 330, chess.QUEEN: 900, chess.KING: 20000
    }
    value = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            base_value = piece_values.get(piece.piece_type, 0)
            sign = 1 if piece.color == chess.WHITE else -1
            if piece.piece_type == chess.PAWN:
                table_value = PAWN_TABLE[square] if piece.color == chess.WHITE else PAWN_TABLE[63 - square]
            elif piece.piece_type == chess.KNIGHT:
                table_value = KNIGHT_TABLE[square] if piece.color == chess.WHITE else KNIGHT_TABLE[63 - square]
            else:
                table_value = 0
            value += sign * (base_value + table_value)
    center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
    for square in center_squares:
        if board.piece_at(square):
            value += (10 if board.color_at(square) == chess.WHITE else -10)
    white_king = board.king(chess.WHITE)
    black_king = board.king(chess.BLACK)
    if white_king and chess.square_file(white_king) in (0, 7):
        value -= 20
    if black_king and chess.square_file(black_king) in (0, 7):
        value += 20
    if board.has_castling_rights(chess.WHITE):
        value += 50
    if board.has_castling_rights(chess.BLACK):
        value -= 50
    return value
