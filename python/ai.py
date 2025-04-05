import chess
import random
import pygame
import copy
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

def best_move(board, depth, time_limit=5000):
    board_copy = copy.deepcopy(board)
    best_move = None
    max_eval = float('-inf')
    start_time = pygame.time.get_ticks()
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
