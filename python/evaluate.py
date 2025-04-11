import chess

PAWN_TABLE = [
    0, 0, 0, 0, 0, 0, 0, 0,
    75, 75, 75, 75, 75, 75, 75, 75,
    20, 20, 30, 40, 40, 30, 20, 20,
    10, 10, 15, 30, 30, 15, 10, 10,
    5, 5, 10, 25, 25, 10, 5, 5,
    0, 0, 0, 10, 10, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0
]
BISHOP_TABLE = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10, 5, 0, 0, 0, 0, 5, -10,
    -10, 5, 10, 15, 15, 10, 5, -10,
    -10, 0, 15, 20, 20, 15, 0, -10,
    -10, 0, 15, 20, 20, 15, 0, -10,
    -10, 5, 10, 15, 15, 10, 5, -10,
    -10, 5, 0, 0, 0, 0, 5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20
]
ROOK_TABLE = [
    0, 0, 0, 0, 0, 0, 0, 0,
    10, 15, 15, 15, 15, 15, 15, 10,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    0, 0, 0, 5, 5, 0, 0, 0
]
QUEEN_TABLE = [
    -20, -10, -10, -5, -5, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -5, 0, 5, 10, 10, 5, 0, -5,
    -5, 0, 5, 10, 10, 5, 0, -5,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -20, -10, -10, -5, -5, -10, -10, -20
]
KING_TABLE = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -30, -30, -20, -20, -10,
    10, 10, 0, 0, 0, 0, 10, 10,
    20, 30, 10, 0, 0, 10, 30, 20
]
KING_ENDGAME_TABLE = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10, 0, 0, -10, -20, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -30, 0, 0, 0, 0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50
]
KNIGHT_TABLE = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -30, 5, 15, 20, 20, 15, 5, -30,
    -30, 10, 20, 25, 25, 20, 10, -30,
    -30, 5, 20, 25, 25, 20, 5, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50
]

piece_values = {
        chess.PAWN: 100, chess.ROOK: 510, chess.KNIGHT: 310,
        chess.BISHOP: 320, chess.QUEEN: 975, chess.KING: 20000
    }

def is_endgame(board):
    total_material = sum(
        1 for sq in chess.SQUARES
        if (p := board.piece_at(sq)) and p.piece_type != chess.KING
    )
    return total_material < 10

def get_piece_square_value(piece, square, endgame):
    if piece.piece_type == chess.PAWN:
        table = PAWN_TABLE
    elif piece.piece_type == chess.KNIGHT:
        table = KNIGHT_TABLE
    elif piece.piece_type == chess.BISHOP:
        table = BISHOP_TABLE
    elif piece.piece_type == chess.ROOK:
        table = ROOK_TABLE
    elif piece.piece_type == chess.QUEEN:
        table = QUEEN_TABLE
    elif piece.piece_type == chess.KING:
        table = KING_ENDGAME_TABLE if endgame else KING_TABLE
    else:
        table = [0] * 64

    idx = square if piece.color == chess.WHITE else 63 - square
    return table[idx]

def evaluate_material_and_position(board, endgame):
    value = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            color_sign = 1 if piece.color == chess.WHITE else -1
            base = piece_values[piece.piece_type]
            table_val = get_piece_square_value(piece, square, endgame)
            value += color_sign * (base + table_val)
    return value
def evaluate_hanging_pieces(board, piece_value):
    value = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.piece_type != chess.KING:
            attackers = len(board.attackers(not piece.color, square))
            defenders = len(board.attackers(piece.color, square))
            if attackers > defenders:
                penalty = piece_value[piece.piece_type] * 0.15 * (attackers - defenders)
                value -= penalty if piece.color == chess.WHITE else -penalty
    return value

def evaluate_piece_control_center(board):
    value = 0
    central_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
    extended_center = [chess.C3, chess.D3, chess.E3, chess.F3, chess.C4, chess.F4, chess.C5, chess.F5, chess.D6,
                       chess.E6]

    for square in central_squares:
        piece = board.piece_at(square)
        if piece:
            if piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                value += 20 if piece.color == chess.WHITE else -20
            elif piece.piece_type == chess.PAWN:
                value += 15 if piece.color == chess.WHITE else -15
            elif piece.piece_type in [chess.ROOK, chess.QUEEN]:
                value += 10 if piece.color == chess.WHITE else -10

    for square in extended_center:
        piece = board.piece_at(square)
        if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
            value += 10 if piece.color == chess.WHITE else -10

    return value
def evaluate_king_positioning(board):
    value = 0

    for color in [chess.WHITE, chess.BLACK]:
        king_sq = board.king(color)
        if king_sq is None:
            continue

        sign = 1 if color == chess.WHITE else -1
        file = chess.square_file(king_sq)

        # Vua ở biên tốt hơn một chút (an toàn hơn trong trung cuộc)
        if file in (0, 7):
            value -= 20 * sign
        elif file in (1, 6):
            value -= 10 * sign

        # Kiểm tra trạng thái nhập thành
        if color == chess.WHITE:
            if king_sq == chess.G1:
                value += 40  # Nhập thành kingside
            elif king_sq == chess.C1:
                value += 30  # Nhập thành queenside
            elif king_sq == chess.E1 and board.has_castling_rights(color):
                value += 10  # Đang chuẩn bị nhập thành
        else:
            if king_sq == chess.G8:
                value -= 40
            elif king_sq == chess.C8:
                value -= 30
            elif king_sq == chess.E8 and board.has_castling_rights(color):
                value -= 10

        # Không còn quyền nhập thành ⇒ đã nhập thành hoặc bị mất quyền
        if not board.has_kingside_castling_rights(color) and not board.has_queenside_castling_rights(color):
            value += 20 * sign

        # Phạt nhẹ nếu vua nằm giữa bàn (file 3-4)
        if file in (3, 4):
            value -= 10 * sign

    return value
def evaluate_check_and_castling(board):
    value = 0

    # Nếu bị chiếu, trừ điểm
    if board.is_check():
        value += -30 if board.turn == chess.WHITE else 30

    # Đánh giá vị trí xe đầu game (nếu bị di chuyển sớm => trừ điểm nhẹ)
    if board.fullmove_number <= 10:
        for square, color_sign in zip([chess.A1, chess.H1, chess.A8, chess.H8], [1, 1, -1, -1]):
            piece = board.piece_at(square)
            if not piece or piece.piece_type != chess.ROOK:
                value -= 20 * color_sign

    # Đánh giá quyền nhập thành (quyền còn thì cộng điểm)
    for color in [chess.WHITE, chess.BLACK]:
        sign = 1 if color == chess.WHITE else -1
        if board.has_kingside_castling_rights(color):
            value += 50 * sign
        if board.has_queenside_castling_rights(color):
            value += 30 * sign

    # Vua đã nhập thành rồi thì cộng thêm điểm
    if board.king(chess.WHITE) == chess.G1:
        value += 20
    elif board.king(chess.WHITE) == chess.C1:
        value += 10
    if board.king(chess.BLACK) == chess.G8:
        value -= 20
    elif board.king(chess.BLACK) == chess.C8:
        value -= 10

    return value
def evaluate_pawn_structure(pawn_squares, color, white_pawns, black_pawns):
    score = 0
    files = [chess.square_file(sq) for sq in pawn_squares]
    file_counts = {f: files.count(f) for f in range(8)}
    opp_pawns = black_pawns if color == chess.WHITE else white_pawns
    sign = 1 if color == chess.WHITE else -1

    for sq in pawn_squares:
        file = chess.square_file(sq)
        rank = chess.square_rank(sq)

        # Tốt chồng
        if file_counts[file] > 1:
            score -= 25 if file_counts[file] == 2 else 40

        # Tốt cô lập
        is_isolated = all(file_counts.get(f, 0) == 0 for f in [file - 1, file + 1] if 0 <= f <= 7)
        if is_isolated:
            score -= 15

        # Tốt thông
        passed = True
        for f in [file - 1, file, file + 1]:
            if 0 <= f <= 7:
                for opp_sq in opp_pawns:
                    if chess.square_file(opp_sq) == f:
                        opp_rank = chess.square_rank(opp_sq)
                        if (color == chess.WHITE and opp_rank >= rank) or (color == chess.BLACK and opp_rank <= rank):
                            passed = False
                            break
                if not passed:
                    break
        if passed:
            bonus = 20 + ((rank if color == chess.WHITE else 7 - rank) * 10)
            score += bonus

    return score * sign
def evaluate_bishop_pair(board):
    score = 0

    for color in [chess.WHITE, chess.BLACK]:
        bishops = list(board.pieces(chess.BISHOP, color))
        if len(bishops) >= 2:
            bonus = 50
            files = [chess.square_file(sq) for sq in bishops]
            if any(f <= 3 for f in files) and any(f >= 4 for f in files):
                bonus += 10  # Hai tượng kiểm soát cả hai cánh
            score += bonus if color == chess.WHITE else -bonus

    return score
def evaluate_space_advantage(board, white_attacks, black_attacks):
    def space_score(color_attacks, ranks, back_rank):
        score = 0
        for sq in chess.SQUARES:
            rank = chess.square_rank(sq)
            if sq in color_attacks and not board.piece_at(sq):
                if rank in ranks:
                    score += 2
                elif rank == back_rank:
                    score += 1
        return score

    white_space = space_score(white_attacks, [4, 5], 6)
    black_space = space_score(black_attacks, [3, 2], 1)

    white_pawns = len(board.pieces(chess.PAWN, chess.WHITE))
    black_pawns = len(board.pieces(chess.PAWN, chess.BLACK))

    return 5 * (white_space - black_space) + 3 * (white_pawns - black_pawns)
def evaluate_threats(board, piece_value):
    value = 0

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if not piece:
            continue

        color = piece.color
        enemy_color = not color
        sign = 1 if color == chess.WHITE else -1

        attackers = board.attackers(enemy_color, square)
        defenders = board.attackers(color, square)

        if len(attackers) > len(defenders):
            attacker_values = [
                piece_value.get(board.piece_at(attacker).piece_type, 0)
                for attacker in attackers if board.piece_at(attacker)
            ]
            if attacker_values:
                min_attacker_value = min(attacker_values)
                target_value = piece_value.get(piece.piece_type, 0)

                if target_value > min_attacker_value:
                    value += sign * (target_value - min_attacker_value) * 0.1

                if piece.piece_type in (chess.KING, chess.QUEEN):
                    bonus = 20 if piece.piece_type == chess.KING else 15
                    value += sign * bonus

    return value
def evaluate_king_safety(board, white_attacks, black_attacks):
    def king_safety_penalty(king_square, color):
        penalty = 0
        king_file = chess.square_file(king_square)
        king_rank = chess.square_rank(king_square)
        surrounding_squares = []
        for df in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                if df != 0 or dr != 0:
                    f = king_file + df
                    r = king_rank + dr
                    if 0 <= f <= 7 and 0 <= r <= 7:
                        surrounding_squares.append(chess.square(f, r))

        extended_zone = []
        for df in [-2, -1, 0, 1, 2]:
            for dr in [-2, -1, 0, 1, 2]:
                if df != 0 or dr != 0:
                    f = king_file + df
                    r = king_rank + dr
                    if 0 <= f <= 7 and 0 <= r <= 7:
                        extended_zone.append(chess.square(f, r))

        pawn_shield = sum(
            1 for sq in surrounding_squares
            if (p := board.piece_at(sq)) and p.piece_type == chess.PAWN and p.color == color
        )
        attackers = sum(
            2 if (p := board.piece_at(sq)) and p.color != color and p.piece_type in [chess.QUEEN, chess.ROOK] else
            1 if sq in (black_attacks if color == chess.WHITE else white_attacks) else 0
            for sq in extended_zone
        )

        if pawn_shield < 2:
            penalty += (2 - pawn_shield) * 20
        if attackers > 0:
            penalty += attackers * 15
        if king_file in [0, 7]:
            penalty += 10

        return -penalty if color == chess.WHITE else penalty

    value = 0
    white_king = board.king(chess.WHITE)
    black_king = board.king(chess.BLACK)
    if white_king is not None:
        value += king_safety_penalty(white_king, chess.WHITE)
    if black_king is not None:
        value += king_safety_penalty(black_king, chess.BLACK)
    return value
def evaluate_outposts(board):
    center_outpost_squares = [
        chess.C3, chess.D3, chess.E3, chess.F3,
        chess.C4, chess.D4, chess.E4, chess.F4,
        chess.C5, chess.D5, chess.E5, chess.F5,
        chess.C6, chess.D6, chess.E6, chess.F6,
    ]
    value = 0
    for square in center_outpost_squares:
        piece = board.piece_at(square)
        if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
            color = piece.color
            enemy_color = not color
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            is_outpost = True
            defended = len(board.attackers(color, square)) > 0

            for f in [file - 1, file + 1]:
                if 0 <= f <= 7:
                    for sq in board.pieces(chess.PAWN, enemy_color):
                        if chess.square_file(sq) == f:
                            if (color == chess.WHITE and chess.square_rank(sq) >= rank) or \
                                    (color == chess.BLACK and chess.square_rank(sq) <= rank):
                                is_outpost = False
                                break
                    if not is_outpost:
                        break

            if is_outpost:
                bonus = 30 if piece.piece_type == chess.KNIGHT else 20
                if defended:
                    bonus += 10
                if square in [chess.D4, chess.E4, chess.D5, chess.E5]:
                    bonus += 5
                value += bonus if color == chess.WHITE else -bonus
    return value
def evaluate_enemy_territory_control(board, white_attacks, black_attacks):
    value = 0

    white_bonus_squares = {chess.D5, chess.E5, chess.D6, chess.E6}
    black_bonus_squares = {chess.D3, chess.E3, chess.D2, chess.E2}

    for sq in chess.SQUARES:
        if board.piece_at(sq) is not None:
            continue  # bỏ qua ô đã bị chiếm

        rank = chess.square_rank(sq)

        if sq in white_attacks:
            if rank in [5, 6]:
                value += 2
            elif rank == 4:
                value += 1
            if sq in white_bonus_squares:
                value += 1

        if sq in black_attacks:
            if rank in [1, 2]:
                value -= 2
            elif rank == 3:
                value -= 1
            if sq in black_bonus_squares:
                value -= 1

    return 5 * value
def evaluate_turn_and_endgame_push(board, is_endgamechua, current_value):
    value = 0

    # Ưu tiên người đi
    value += 15 if board.turn == chess.WHITE else -15

    if is_endgamechua:
        white_king = board.king(chess.WHITE)
        black_king = board.king(chess.BLACK)

        if white_king and black_king:
            # Đẩy vua trắng lên cao (rank cao hơn), đẩy vua đen xuống thấp
            white_push = chess.square_rank(white_king)
            black_push = 7 - chess.square_rank(black_king)
            value += 10 * (white_push - black_push)

        # Nếu đang dẫn điểm lớn thì khuyến khích ép thắng
        if current_value > 100:
            value += 20
        elif current_value < -100:
            value -= 20

    return value
def evaluate_board(board: chess.Board) -> float:
    if board.is_checkmate():
        return -9999 if board.turn else 9999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    material = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 0
    }

    pst = {
        chess.PAWN: [
            0, 0, 0, 0, 0, 0, 0, 0,
            5, 10, 10, -20, -20, 10, 10, 5,
            5, -5, -10, 0, 0, -10, -5, 5,
            0, 0, 0, 20, 20, 0, 0, 0,
            5, 5, 10, 25, 25, 10, 5, 5,
            10, 10, 20, 30, 30, 20, 10, 10,
            50, 50, 50, 50, 50, 50, 50, 50,
            0, 0, 0, 0, 0, 0, 0, 0
        ],
        chess.KNIGHT: [
            -50, -40, -30, -30, -30, -30, -40, -50,
            -40, -20, 0, 5, 5, 0, -20, -40,
            -30, 5, 10, 15, 15, 10, 5, -30,
            -30, 0, 15, 20, 20, 15, 0, -30,
            -30, 5, 15, 20, 20, 15, 5, -30,
            -30, 0, 10, 15, 15, 10, 0, -30,
            -40, -20, 0, 0, 0, 0, -20, -40,
            -50, -40, -30, -30, -30, -30, -40, -50
        ]
        # Add more PSTs for bishop, rook, queen, king if needed
    }

    score = 0
    piece_map = board.piece_map()

    white_development = 0
    black_development = 0

    white_center_control = 0
    black_center_control = 0

    white_king_safety = 0
    black_king_safety = 0

    for square, piece in piece_map.items():
        value = material[piece.piece_type]
        if piece.color == chess.WHITE:
            score += value
            if piece.piece_type in pst:
                score += pst[piece.piece_type][square]

            if piece.piece_type in [chess.KNIGHT, chess.BISHOP] and square not in [chess.B1, chess.G1, chess.C1, chess.F1]:
                white_development += 1

            if square in [chess.E4, chess.D4, chess.E5, chess.D5, chess.C4, chess.F4, chess.C5, chess.F5]:
                white_center_control += 1
        else:
            score -= value
            if piece.piece_type in pst:
                score -= pst[piece.piece_type][chess.square_mirror(square)]

            if piece.piece_type in [chess.KNIGHT, chess.BISHOP] and square not in [chess.B8, chess.G8, chess.C8, chess.F8]:
                black_development += 1

            if square in [chess.E4, chess.D4, chess.E5, chess.D5, chess.C4, chess.F4, chess.C5, chess.F5]:
                black_center_control += 1

    score += 15 * (white_development - black_development)
    score += 20 * (white_center_control - black_center_control)

    # King safety: bonus if castled
    if board.has_kingside_castling_rights(chess.WHITE) or board.has_queenside_castling_rights(chess.WHITE):
        score += 20
    if board.has_kingside_castling_rights(chess.BLACK) or board.has_queenside_castling_rights(chess.BLACK):
        score -= 20

    # Mobility: number of legal moves
    white_mobility = len(list(board.legal_moves)) if board.turn == chess.WHITE else 0
    board.push(chess.Move.null())
    black_mobility = len(list(board.legal_moves)) if board.turn == chess.BLACK else 0
    board.pop()
    score += 0.1 * (white_mobility - black_mobility)

    # Open file for rook bonus
    for file in range(8):
        white_rook_on_file = any(piece_map.get(chess.square(file, rank)) == chess.Piece(chess.ROOK, chess.WHITE) for rank in range(8))
        black_rook_on_file = any(piece_map.get(chess.square(file, rank)) == chess.Piece(chess.ROOK, chess.BLACK) for rank in range(8))
        file_has_pawn = any(piece_map.get(chess.square(file, rank)) and piece_map.get(chess.square(file, rank)).piece_type == chess.PAWN for rank in range(8))

        if white_rook_on_file and not file_has_pawn:
            score += 10
        if black_rook_on_file and not file_has_pawn:
            score -= 10

    return score if board.turn == chess.WHITE else -score
