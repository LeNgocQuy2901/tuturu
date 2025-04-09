import chess
import pygame
from evaluate import evaluate_board

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

def best_move(board, depth):
    ai_color = board.turn  # TRUE nếu là Trắng, FALSE nếu là Đen
    best_move_found = None
    max_eval = float('-inf')

    def move_score(board, move):
        score = 0
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            if victim and attacker:
                score += 10 * victim.piece_type - attacker.piece_type
        if board.gives_check(move):
            score += 3
        return score

    moves = sorted(board.legal_moves, key=lambda m: move_score(board, m), reverse=True)

    for move in moves:
        board.push(move)
        eval = minimax(board, depth - 1, float('-inf'), float('inf'), False)
        board.pop()

        # 🧠 Nếu AI là Đen, đảo dấu lại để Đen chọn điểm thấp
        eval = eval if ai_color == chess.WHITE else -eval

        if eval > max_eval:
            max_eval = eval
            best_move_found = move

    return best_move_found if best_move_found else moves[0]
