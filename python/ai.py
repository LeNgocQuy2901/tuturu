import chess
import time
import threading
from evaluate import evaluate_board
from concurrent.futures import ThreadPoolExecutor

transposition_table = {}
MAX_THREADS = 4  # Giới hạn số luồng

CENTER_SQUARES = [chess.E4, chess.D4, chess.E5, chess.D5]

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

def move_score(board, move):
    score = 0

    # Ưu tiên ăn quân (MVV-LVA đơn giản)
    if board.is_capture(move):
        captured = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)
        if captured and attacker:
            score += 10 * captured.piece_type - attacker.piece_type

    # Ưu tiên phong cấp
    if move.promotion:
        score += 900

    # Ưu tiên chiếu
    board.push(move)
    if board.is_check():
        score += 800

    # Kiểm tra nếu quân vừa đi dễ bị bắt ngay sau đó -> trừ điểm
    for reply in board.legal_moves:
        if board.is_capture(reply) and reply.to_square == move.to_square:
            score -= 200
            break

    board.pop()

    # Ưu tiên kiểm soát trung tâm
    if move.to_square in CENTER_SQUARES:
        score += 100

    return score



def order_moves(board):
    moves_with_scores = [(move, move_score(board, move)) for move in board.legal_moves]
    threshold = -500  # Lọc bỏ nước quá kém (tự sát, vô ích)
    filtered = [m for m, s in moves_with_scores if s > threshold]
    return sorted(filtered, key=lambda m: move_score(board, m), reverse=True)


def quiescence_search(board, alpha, beta, maximizing_player, start_time=None, time_limit=9.5):
    if start_time and time.time() - start_time > time_limit:
        return evaluate_board(board)

    stand_pat = evaluate_board(board)
    if maximizing_player:
        if stand_pat >= beta:
            return beta
        alpha = max(alpha, stand_pat)
    else:
        if stand_pat <= alpha:
            return alpha
        beta = min(beta, stand_pat)

    # Chỉ xét các nước đi gây xáo trộn: bắt quân hoặc chiếu
    moves = [
        move for move in board.legal_moves
        if board.is_capture(move) or board.gives_check(move)
    ]
    moves.sort(key=lambda move: move_score(board, move), reverse=True)

    for move in moves:
        board.push(move)
        score = quiescence_search(board, alpha, beta, not maximizing_player, start_time, time_limit)
        board.pop()

        if maximizing_player:
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break  # Beta cut-off
        else:
            if score < beta:
                beta = score
            if beta <= alpha:
                break  # Alpha cut-off

    return alpha if maximizing_player else beta


def minimax(board, depth, alpha, beta, maximizing_player, save_move=False, data=None, start_time=None, time_limit=9.5):
    if data is None:
        data = [[], float('-inf') if maximizing_player else float('inf')]
    if start_time and time.time() - start_time > time_limit:
        return data

    key = (board.fen(), depth, maximizing_player)
    if key in transposition_table:
        return [[], transposition_table[key]]

    if depth == 0 or board.is_game_over():
        score = quiescence_search(board, alpha, beta, maximizing_player, start_time, time_limit)
        transposition_table[key] = score
        return [[], score]

    moves = order_moves(board)

    if maximizing_player:
        max_eval = float('-inf')
        for move in moves:
            if start_time and time.time() - start_time > time_limit:
                break
            board.push(move)
            evaluation = minimax(board, depth - 1, alpha, beta, False, False, None, start_time, time_limit)[1]
            board.pop()

            if save_move:
                if evaluation > data[1]:
                    data.clear()
                    data.extend([[move], evaluation])
                elif evaluation == data[1]:
                    data[0].append(move)

            max_eval = max(max_eval, evaluation)
            alpha = max(alpha, evaluation)
            if beta <= alpha:
                break

        transposition_table[key] = max_eval
        return [[], max_eval]

    else:
        min_eval = float('inf')
        for move in moves:
            if start_time and time.time() - start_time > time_limit:
                break
            board.push(move)
            evaluation = minimax(board, depth - 1, alpha, beta, True, False, None, start_time, time_limit)[1]
            board.pop()

            if save_move:
                if evaluation < data[1]:
                    data.clear()
                    data.extend([[move], evaluation])
                elif evaluation == data[1]:
                    data[0].append(move)

            min_eval = min(min_eval, evaluation)
            beta = min(beta, evaluation)
            if beta <= alpha:
                break

        transposition_table[key] = min_eval
        return [[], min_eval]

def best_move(board, depth=5, max_time=9.5):
    start_time = time.time()
    best_data = [[], float('-inf')]
    data_lock = threading.Lock()

    def search_move(move):
        nonlocal best_data
        temp_board = board.copy()
        temp_board.push(move)
        result = minimax(temp_board, depth - 1, float('-inf'), float('inf'), not board.turn,
                         save_move=False, data=None, start_time=start_time, time_limit=max_time)
        score = result[1]
        with data_lock:
            if score > best_data[1]:
                best_data[0] = [move]
                best_data[1] = score
            elif score == best_data[1]:
                best_data[0].append(move)

    moves = order_moves(board)
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        for move in moves:
            if time.time() - start_time > max_time:
                break
            executor.submit(search_move, move)

    print(f"[AI] Depth {depth}, Best Eval: {best_data[1]}, Move: {best_data[0]}")
    return best_data[0][0] if best_data[0] else None
