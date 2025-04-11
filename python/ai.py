import chess
import time
import threading
from evaluate import evaluate_board
from concurrent.futures import ThreadPoolExecutor

transposition_table = {}
MAX_THREADS = 4  # Giới hạn số luồng

CENTER_SQUARES = [chess.E4, chess.D4, chess.E5, chess.D5]

def move_score(board, move):
    score = 0
    if board.is_capture(move):
        captured_piece = board.piece_at(move.to_square)
        attacker_piece = board.piece_at(move.from_square)
        if captured_piece and attacker_piece:
            score += 1000 + 10 * captured_piece.piece_type - attacker_piece.piece_type

    if move.promotion:
        score += 900

    board.push(move)
    if board.is_check():
        score += 500
    board.pop()

    if move.to_square in CENTER_SQUARES:
        score += 100

    return score

def order_moves(board):
    return sorted(board.legal_moves, key=lambda move: move_score(board, move), reverse=True)

def quiescence_search(board, alpha, beta, maximizing_player, start_time=None, time_limit=9.5):
    if start_time and time.time() - start_time > time_limit:
        return evaluate_board(board)

    stand_pat = evaluate_board(board)
    if maximizing_player:
        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat
    else:
        if stand_pat <= alpha:
            return alpha
        if beta > stand_pat:
            beta = stand_pat

    for move in order_moves(board):
        if board.is_capture(move):
            board.push(move)
            score = quiescence_search(board, alpha, beta, not maximizing_player, start_time, time_limit)
            board.pop()

            if maximizing_player:
                if score > alpha:
                    alpha = score
                if alpha >= beta:
                    break
            else:
                if score < beta:
                    beta = score
                if beta <= alpha:
                    break

    return alpha if maximizing_player else beta

def minimax(board, depth, alpha, beta, maximizing_player, save_move=False, data=None, start_time=None, time_limit=9.5):
    if data is None:
        data = [[], 0]
    if start_time and time.time() - start_time > time_limit:
        return data

    key = (board.fen(), depth, maximizing_player)
    if key in transposition_table:
        return transposition_table[key]

    if depth == 0 or board.is_game_over():
        score = quiescence_search(board, alpha, beta, maximizing_player, start_time, time_limit)
        data[1] = score
        return data

    moves = order_moves(board)

    if maximizing_player:
        max_eval = float('-inf')
        for move in moves:
            board.push(move)
            evaluation = minimax(board, depth - 1, alpha, beta, False, False, data, start_time, time_limit)[1]
            board.pop()

            if save_move and evaluation >= max_eval:
                if evaluation > data[1]:
                    data.clear()
                    data[1] = evaluation
                    data[0] = [move]
                elif evaluation == data[1]:
                    data[0].append(move)

            max_eval = max(max_eval, evaluation)
            alpha = max(alpha, evaluation)
            if beta <= alpha:
                break

        transposition_table[key] = data
        return data

    else:
        min_eval = float('inf')
        for move in moves:
            board.push(move)
            evaluation = minimax(board, depth - 1, alpha, beta, True, False, data, start_time, time_limit)[1]
            board.pop()

            min_eval = min(min_eval, evaluation)
            beta = min(beta, evaluation)
            if beta <= alpha:
                break

        transposition_table[key] = data
        return data

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
