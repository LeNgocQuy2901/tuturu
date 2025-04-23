import math
import chess
import chess.polyglot  # Add explicit import for polyglot module
import time
from evaluate import evaluate_board
import functools
from collections import defaultdict

# Profiling metrics
class SearchProfiler:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.call_counts = defaultdict(int)
        self.total_time = defaultdict(float)
        self.start_times = {}
        
    def start(self, section):
        self.start_times[section] = time.time()
        self.call_counts[section] += 1
        
    def stop(self, section):
        if section in self.start_times:
            elapsed = time.time() - self.start_times[section]
            self.total_time[section] += elapsed
            del self.start_times[section]
            
    def report(self):
        print("\n===== SEARCH PROFILER REPORT =====")
        # Sort sections by total time
        sorted_sections = sorted(self.total_time.items(), 
                                key=lambda x: x[1], 
                                reverse=True)
        
        total_search_time = sum(self.total_time.values())
        
        print(f"{'Section':<25} {'Calls':<10} {'Total Time':<15} {'Avg Time':<15} {'% of Total':<10}")
        print("-" * 75)
        
        for section, time_spent in sorted_sections:
            calls = self.call_counts[section]
            avg_time = time_spent / calls if calls > 0 else 0
            percent = (time_spent / total_search_time * 100) if total_search_time > 0 else 0
            
            print(f"{section:<25} {calls:<10,d} {time_spent:<15.6f}s {avg_time:<15.6f}s {percent:<10.2f}%")

# Global profiler instance
PROFILER = SearchProfiler()

# Decorator for profiling functions
def profile(section_name):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            PROFILER.start(section_name)
            result = func(*args, **kwargs)
            PROFILER.stop(section_name)
            return result
        return wrapper
    return decorator

IMMEDIATE_MATE_SCORE = 100000
POS_INF = 9999999
NEG_INF = -POS_INF
MAX_DEPTH = 64

piece_values = {
    chess.PAWN: 100,
    chess.KNIGHT: 300,
    chess.BISHOP: 320,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0
}

# Precomputed MVV-LVA table for faster move ordering
# Flattened MVV-LVA table based on piece type and capture value
# Format: Indexed by [attacker_piece_type * 6 + victim_piece_type - 1]
# where piece types are: PAWN(1), KNIGHT(2), BISHOP(3), ROOK(4), QUEEN(5), KING(6)
MVV_LVA_FLAT = [
    105, 205, 305, 405, 505, 605, 105, 205, 305, 405, 505, 605, 104, 204, 304,
    404, 504, 604, 104, 204, 304, 404, 504, 604, 103, 203, 303, 403, 503, 603,
    103, 203, 303, 403, 503, 603, 102, 202, 302, 402, 502, 602, 102, 202, 302,
    402, 502, 602, 101, 201, 301, 401, 501, 601, 101, 201, 301, 401, 501, 601,
    100, 200, 300, 400, 500, 600, 100, 200, 300, 400, 500, 600,

    105, 205, 305, 405, 505, 605, 105, 205, 305, 405, 505, 605, 104, 204, 304,
    404, 504, 604, 104, 204, 304, 404, 504, 604, 103, 203, 303, 403, 503, 603,
    103, 203, 303, 403, 503, 603, 102, 202, 302, 402, 502, 602, 102, 202, 302,
    402, 502, 602, 101, 201, 301, 401, 501, 601, 101, 201, 301, 401, 501, 601,
    100, 200, 300, 400, 500, 600, 100, 200, 300, 400, 500, 600
]

# Convert the flat table to a nested dictionary for easier lookup
MVV_LVA = {}
for attacker_type in range(1, 7):  # PAWN=1, KNIGHT=2, BISHOP=3, ROOK=4, QUEEN=5, KING=6
    MVV_LVA[attacker_type] = {}
    for victim_type in range(1, 7):
        # Get the score from the flattened array
        index = (attacker_type - 1) * 6 + (victim_type - 1)
        MVV_LVA[attacker_type][victim_type] = MVV_LVA_FLAT[index]

# Precomputed promotion score table for faster lookup
PROMOTION_SCORES = {
    chess.QUEEN: 8000,
    chess.ROOK: 6000,
    chess.BISHOP: 6000,
    chess.KNIGHT: 6000,
    None: 0
}

class TranspositionEntry:
    def __init__(self, zobrist, value, depth, flag, move):
        self.zobrist = zobrist
        self.value = value
        self.depth = depth
        self.flag = flag
        self.move = move

class TranspositionTable:
    EXACT, LOWER, UPPER = 0, 1, 2

    def __init__(self, size=2**20*64):
        self.table = {}
        self.size = size

    def get(self, key):
        return self.table.get(key)

    def store(self, key, value, depth, flag, move):
        if len(self.table) >= self.size:
            self.table.clear()
        self.table[key] = TranspositionEntry(key, value, depth, flag, move)

class Searcher:
    def __init__(self):
        self.best_move = None
        self.best_eval = 0
        self.stop_search = False
        self.tt = TranspositionTable()
        self.killer_moves = {ply: [] for ply in range(64)}
        self.history = {}
        self.repetition_table = []
        self.static_evals = {}
        self.q_eval_cache = {}  # Cache for quiescence evaluations
        self.see_cache = {}     # Cache for static exchange evaluations

        self.start_time = 0
        self.time_limit = 9.5
        self.nodes = 0

        self.profiler = PROFILER
        self.enable_profiling = False
        
        # Pre-compute piece value difference thresholds for SEE pruning
        self.futility_margin = 90  # Futility pruning margin per depth
        self.delta_margin = 200    # Delta pruning margin beyond piece values

    def is_mate_score(self, score):
        return abs(score) > IMMEDIATE_MATE_SCORE - 1000

    def score_to_ply(self, score):
        return IMMEDIATE_MATE_SCORE - abs(score)

    def has_non_pawn_material(self, board):
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type != chess.PAWN:
                return True
        return False

    @profile("iterative_deepening")
    def iterative_deepening(self, board, max_depth=5, time_limit=9.5):
        self.stop_search = False
        self.best_eval = 0
        self.best_move = None
        self.start_time = time.time()
        self.time_limit = time_limit

        last_completed_best_move = None
        legal_moves = list(board.legal_moves)
        if len(legal_moves) == 1:
            return legal_moves[0]  # Nếu chỉ còn 1 nước thì chơi luôn

        # Reset profiler for a new search
        if self.enable_profiling:
            self.profiler.reset()

        for depth in range(1, max_depth + 1):
            if time.time() - self.start_time > self.time_limit:
                break

            self.current_depth = depth
            eval = self.search(board, depth, 0, NEG_INF, POS_INF)

            if self.stop_search or (time.time() - self.start_time > self.time_limit):
                print(f"[Search] Depth {depth} incomplete (timeout) - best eval: {self.best_eval}")
                break

            elapsed = time.time() - self.start_time
            self.best_eval = eval
            last_completed_best_move = self.best_move

            # Calculate nodes per second
            total_nodes = self.nodes
            nps = total_nodes / elapsed if elapsed > 0 else 0

            # Print progress information with node counts
            if self.is_mate_score(eval):
                mate_in = self.score_to_ply(eval)
                print(f"[Search] Depth {depth} completed in {elapsed:.2f}s - "
                      f"Score: Mate in {mate_in} - Move: {self.best_move} - "
                      f"Nodes: {self.nodes:,} "
                      f"({int(nps):,} NPS)")
            else:
                print(f"[Search] Depth {depth} completed in {elapsed:.2f}s - "
                      f"Score: {eval} - Move: {self.best_move} - "
                      f"Nodes: {self.nodes:,}  "
                      f"({int(nps):,} NPS)")

            if self.is_mate_score(eval) and self.score_to_ply(eval) <= depth:
                print(f"[Search] Found checkmate sequence, stopping search")
                break

        result = last_completed_best_move if last_completed_best_move else self.best_move

        # Print profiling report if enabled
        if self.enable_profiling:
            self.profiler.report()

        return result

    def search(self, board, depth, ply, alpha, beta):
        if time.time() - self.start_time > self.time_limit:
            self.stop_search = True
            return 0
        self.nodes += 1
        
        if depth <= 0:
            return self.quiescence(board, alpha, beta)

        zobrist = chess.polyglot.zobrist_hash(board)
        is_repetition = zobrist in self.repetition_table or board.is_repetition(3)
        if is_repetition:
            return 0
        
        # Probe Transposition Table
        entry = self.tt.get(zobrist)
        tt_hit = entry and entry.depth >= depth

        if tt_hit:
            if entry.flag == self.tt.EXACT:
                return entry.value
            elif entry.flag == self.tt.LOWER and entry.value >= beta:
                return entry.value
            elif entry.flag == self.tt.UPPER and entry.value <= alpha:
                return entry.value

        # Handle checkmate, but don't return early
        # Instead, assign a mate score based on ply depth, so we find the shortest mate
        if board.is_checkmate():
            mate_score = -IMMEDIATE_MATE_SCORE + ply
            return mate_score
            
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
      
        # Null move pruning
        do_null = depth >= 3 and not board.is_check() and self.has_non_pawn_material(board)
        if do_null:
            R = 3 if depth >= 6 else 2
            board.push(chess.Move.null())
            value = -self.search(board, depth - 1 - R, ply + 1, -beta, -beta + 1)
            board.pop()

            if value >= beta and not self.is_mate_score(value):
                return beta
            
        legal_moves = list(board.legal_moves)

        best_val = NEG_INF
        best_move = None
        move_count = 0
        is_pv = beta > alpha + 1

        self.repetition_table.append(zobrist)

        tt_move = self.tt.get(zobrist).move if self.tt.get(zobrist) else None

        # Move ordering
        ordered_moves = self.order_moves(board, legal_moves, tt_move, ply)

        # Profile static evaluation
        if self.enable_profiling:
            self.profiler.start("static_eval")
        if self.tt.get(zobrist):
            static_eval = self.tt.get(zobrist).value
        else:
            static_eval = evaluate_board(board)
            
        improving = False
        if ply >= 2 and not board.is_check():
            improving = static_eval > self.static_evals.get(ply-2, NEG_INF)
        self.static_evals[ply] = static_eval
        if self.enable_profiling:
            self.profiler.stop("static_eval")

        for move in ordered_moves:
            if time.time() - self.start_time > self.time_limit:
                self.stop_search = True
                break

            gives_check = board.gives_check(move)
            is_capture = board.is_capture(move)

            # SEE pruning - skip bad captures in non-PV nodes (except at very shallow depths)
            if depth >= 2 and is_capture and not is_pv and not gives_check:
                # Use SEE to determine if this is a bad capture
                if self.see(board, move) < 0:
                    # Skip obviously bad captures at higher depths
                    if depth >= 4:
                        continue
                    # For lower depths, only skip very bad captures
                    elif self.see(board, move) < -150:
                        continue

            board.push(move)
            move_count += 1
            is_quiet = not is_capture and not move.promotion
            refutation_move = move == tt_move or move in self.killer_moves.get(ply, [])
            history_score = self.history.get(move.uci(), 0)

            # LMR conditions
            do_full_search = True
            val = 0

            # History pruning for quiet moves
            do_prune = False
            if depth >= 2 and move_count > 1 and is_quiet and not is_pv:
                if history_score < -8000 * depth:
                    do_prune = True

            # Late Move Pruning (LMP) for quiet moves
            if not do_prune and depth <= 8 and is_quiet and move_count >= 3 + depth * depth / 2 and not is_pv:
                do_prune = True

            # Futility pruning for non-PV quiet moves
            if not do_prune and depth <= 7 and not is_pv and not board.is_check() and is_quiet and \
               not gives_check and not self.is_mate_score(alpha):
                futility_margin = 90 * depth
                if static_eval + futility_margin <= alpha:
                    do_prune = True

            if do_prune:
                board.pop()
                continue

            # Late Move Reduction (LMR)
            do_lmr = depth >= 3 and move_count > (2 + 2 * is_pv) and \
                     not board.is_check() and not is_capture and not move.promotion

            # Adjust LMR based on SEE for captures
            if is_capture and depth >= 3 and move_count > (2 + is_pv):
                # If capture is neutral or slightly bad according to SEE, consider LMR
                see_score = self.see(board, move)
                if see_score <= 0:
                    do_lmr = True

            if do_lmr:
                # Simple LMR calculation
                if depth < 3 or move_count < 4:
                    reduction = 0
                else:
                    reduction = int(0.75 + math.log(depth) * math.log(move_count) / 2.25)

                # Adjust reduction based on conditions
                reduction += 0 if is_pv else 1
                reduction += 0 if gives_check else 1
                reduction += 0 if improving else 1
                reduction -= 2 if refutation_move else 0

                # Less reduction for promising captures based on SEE
                if is_capture and self.see(board, move) > 0:
                    reduction = max(0, reduction - 1)

                # Ensure we don't reduce too much
                reduction = min(depth - 1, max(1, int(reduction)))

                # Reduced depth search with zero window
                val = -self.search(board, depth - reduction, ply + 1, -alpha - 1, -alpha)
                do_full_search = (val > alpha)

            # Normal search if LMR wasn't done or the reduced search was promising
            if not do_lmr or do_full_search:
                # PVS - Principal Variation Search
                if move_count == 1:
                    # First move - do a full window search
                    val = -self.search(board, depth - 1, ply + 1, -beta, -alpha)
                else:
                    # Try a null window search first
                    val = -self.search(board, depth - 1, ply + 1, -alpha - 1, -alpha)

                    # If the null window search fails high (and we're not at our bounds)
                    if val > alpha and val < beta:
                        # Research with full window
                        val = -self.search(board, depth - 1, ply + 1, -beta, -alpha)
                        
            board.pop()

            if self.stop_search:
                break

            if val > best_val:
                best_val = val
                best_move = move
                if ply == 0:
                    self.best_move = move

            alpha = max(alpha, val)
            if alpha >= beta:
                if not board.is_capture(move):
                    if move not in self.killer_moves[ply]:
                        self.killer_moves[ply].append(move)
                        if len(self.killer_moves[ply]) > 2:
                            self.killer_moves[ply] = self.killer_moves[ply][-2:]
                self.history[move.uci()] = self.history.get(move.uci(), 0) + depth * depth
                break

        self.repetition_table.pop()

        flag = self.tt.EXACT
        if best_val <= alpha:
            flag = self.tt.UPPER
        elif best_val >= beta:
            flag = self.tt.LOWER

        self.tt.store(zobrist, best_val, depth, flag, best_move)

        return best_val

    @profile("quiescence")
    def quiescence(self, board, alpha, beta, ply=0, max_ply=8):
        """
        Enhanced quiescence search using SEE for more accurate capture evaluation.
        Only considers captures that pass the SEE threshold for winning or equal trades.
        """
        if time.time() - self.start_time > self.time_limit:
            return evaluate_board(board)
            
        if board.is_repetition(3):
            return 0
            
        # Prevent explosion in highly tactical positions
        if ply >= max_ply:
            return evaluate_board(board)
            
        self.nodes += 1
        
        # Check for checkmate or stalemate
        if board.is_checkmate():
            return -IMMEDIATE_MATE_SCORE + ply
        if board.is_stalemate():
            return 0
            
        # Stand pat score
        stand_pat = evaluate_board(board)
        
        # Beta cutoff with stand pat score
        if stand_pat >= beta:
            return beta
            
        # Update alpha with stand pat score if it's better
        if alpha < stand_pat:
            alpha = stand_pat
            
        # Probe transposition table
        zobrist = chess.polyglot.zobrist_hash(board)
        entry = self.tt.get(zobrist)
        if entry and entry.depth >= ply:
            if entry.flag == self.tt.EXACT:
                return entry.value
            elif entry.flag == self.tt.LOWER and entry.value >= beta:
                return entry.value
            elif entry.flag == self.tt.UPPER and entry.value <= alpha:
                return entry.value
                
        # Initialize best score and move
        best_score = stand_pat
        best_move = None
        
        # Get all potential capturing moves
        captures = []
        for move in board.legal_moves:
            if board.is_capture(move) or move.promotion:
                # Use SEE to filter out losing captures early
                if board.is_capture(move) and not move.promotion:
                    # Skip clearly bad captures based on SEE
                    if self.see(board, move) < 0:
                        continue
                        
                # Score the move for ordering
                score = self._score_capture_for_qsearch(board, move)
                captures.append((move, score))
                
        # Sort moves by score (highest first)
        captures.sort(key=lambda x: x[1], reverse=True)
        
        # Delta pruning: if even the best possible capture plus margin cannot improve alpha, skip
        if not board.is_check() and len(captures) > 0:
            best_possible_capture_value = 900  # Queen value
            if stand_pat + best_possible_capture_value + self.delta_margin < alpha:
                # Even a free queen cannot improve alpha
                return alpha
                
        # Search the captures
        for move, _ in captures:
            if time.time() - self.start_time > self.time_limit:
                return best_score
                
            board.push(move)
            score = -self.quiescence(board, -beta, -alpha, ply + 1, max_ply)
            board.pop()
            
            if score > best_score:
                best_score = score
                best_move = move
                if score > alpha:
                    alpha = score
                    if alpha >= beta:
                        break
                        
        # Store the result in the transposition table
        if best_score >= beta:
            self.tt.store(zobrist, best_score, ply, self.tt.LOWER, best_move)
        elif best_score > stand_pat:
            self.tt.store(zobrist, best_score, ply, self.tt.EXACT, best_move)
        else:
            self.tt.store(zobrist, best_score, ply, self.tt.UPPER, best_move)
            
        return best_score

    def _potentially_good_capture(self, board, move):
        """
        Ultra-fast first-pass filter for obviously bad captures.
        Returns True for captures that might be good, False for obviously bad ones.
        """
        # All en passant captures are considered potentially good
        if board.is_en_passant(move):
            return True
            
        from_piece = board.piece_at(move.from_square)
        to_piece = board.piece_at(move.to_square)
        
        if not from_piece or not to_piece:
            return False
            
        # Pawn captures are usually good
        if from_piece.piece_type == chess.PAWN:
            return True
            
        # Capturing a higher or equal value piece is potentially good
        # This is much faster than the full _is_good_capture check
        return piece_values[to_piece.piece_type] >= piece_values[from_piece.piece_type]

    def _score_capture_for_qsearch(self, board, move):
        """
        Fast and specialized move scoring function just for quiescence search.
        Optimized for capturing moves and promotions.
        """
        # Queen promotions get highest priority
        if move.promotion == chess.QUEEN:
            return 30000
            
        # Handle other promotions
        if move.promotion:
            return 20000 + PROMOTION_SCORES[move.promotion]
            
        # Score captures using MVV-LVA
        if board.is_capture(move):
            captured = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            
            if captured and attacker:
                # Use precomputed MVV-LVA table for fastest lookup
                return MVV_LVA[attacker.piece_type][captured.piece_type]
                
        # Moves that give check
        if board.gives_check(move):
            return 500
            
        return 0
        
    def _is_good_capture(self, board, move):
        """
        Simplified SEE (Static Exchange Evaluation) to quickly determine
        if a capture is likely good or bad. Avoids full SEE calculation.
        """
        # Create a cache key for this position and move
        cache_key = (chess.polyglot.zobrist_hash(board), move.uci())
        
        # Check if we've already calculated this
        if cache_key in self.see_cache:
            return self.see_cache[cache_key]
            
        # Get the pieces involved
        from_piece = board.piece_at(move.from_square)
        to_piece = board.piece_at(move.to_square)
        
        if not from_piece or not to_piece:
            return False
            
        # Special case: pawn captures are usually good
        if from_piece.piece_type == chess.PAWN:
            result = True
            self.see_cache[cache_key] = result
            return result
            
        # If capturing higher value piece, it's potentially good
        if piece_values[to_piece.piece_type] >= piece_values[from_piece.piece_type]:
            result = True
            self.see_cache[cache_key] = result
            return result
            
        # For captures of lower value pieces, check if the square is defended
        board.push(move)
        is_attacked = board.is_attacked_by(not board.turn, move.to_square)
        board.pop()
        
        # If capturing piece would be recaptured by a lower value piece, it's bad
        result = not is_attacked
        
        # Cache the result
        self.see_cache[cache_key] = result
        
        # Prevent cache from growing too large
        if len(self.see_cache) > 50000:
            self.see_cache.clear()
            
        return result

    @profile("see")
    def see(self, board, move):
        """
        Full Static Exchange Evaluation (SEE).
        Accurately calculates the outcome of a sequence of captures on a square.
        Returns the material balance after the best sequence of captures.
        """
        if not board.is_capture(move):
            return 0
            
        # Create a cache key for this position and move
        cache_key = (chess.polyglot.zobrist_hash(board), move.uci())
        
        # Check if we've already calculated this
        if cache_key in self.see_cache:
            return self.see_cache[cache_key]
        
        # Get the target square and the first attacker
        to_square = move.to_square
        from_square = move.from_square
        
        # Special handling for en passant captures
        if board.is_en_passant(move):
            # In en passant, we capture a pawn
            gain = [piece_values[chess.PAWN]]
            # Make the capture and evaluate the rest of the exchange sequence
            board.push(move)
            # Since the en passant capture is terminal (no further captures on this square),
            # we can just return the gain
            board.pop()
            result = gain[0]
            self.see_cache[cache_key] = result
            return result
        
        # Get the target piece (the initially captured piece)
        target_piece = board.piece_at(to_square)
        if target_piece is None:  # Not a capture
            return 0
            
        # The value of the captured piece
        target_value = piece_values[target_piece.piece_type]
        
        # The attacker
        attacker = board.piece_at(from_square)
        if attacker is None:  # Shouldn't happen, but check anyway
            return 0
            
        # First gain is capturing the initial piece
        gain = [target_value]
        
        # Track the last attacker's value as we'll need to subtract it later
        last_attacker_value = piece_values[attacker.piece_type]
        
        # Make a temporary copy of the board to simulate captures
        temp_board = board.copy()
        temp_board.push(move)
        
        # Now we have the situation where the capturing piece is on the target square
        # and we need to find the least valuable attacker that can recapture
        
        # Keep finding the next attacker until no more attackers are found
        side_to_move = not board.turn  # Side to move after the initial capture
        
        while True:
            # Find the least valuable attacker for the side to move
            next_attacker = self._find_least_valuable_attacker(temp_board, to_square, side_to_move)
            
            # If no attacker found, we're done with this exchange sequence
            if next_attacker is None:
                break
                
            # Get the attacker's piece type
            attacker_piece = temp_board.piece_at(next_attacker)
            attacker_value = piece_values[attacker_piece.piece_type]
            
            # Make the capture
            capture_move = chess.Move(next_attacker, to_square)
            temp_board.push(capture_move)
            
            # Record the gain/loss: lose the previous attacker, gain the new one
            gain.append(last_attacker_value - gain[-1])
            
            # Update for next iteration
            last_attacker_value = attacker_value
            side_to_move = not side_to_move
        
        # Now we have all potential gains/losses in the sequence
        # We need to work backwards through the exchange sequence to determine
        # if each capture is worthwhile (assuming optimal play from both sides)
        
        # Start with the last gain
        for i in range(len(gain) - 2, -1, -1):
            # The side to move at step i has the choice: capture and get gain[i+1],
            # or stop capturing. They'll choose the maximum value.
            gain[i] = max(-gain[i+1], gain[i])
        
        # Store result in cache
        result = gain[0]
        self.see_cache[cache_key] = result
        
        # Keep the cache at a reasonable size
        if len(self.see_cache) > 100000:
            self.see_cache.clear()
            
        return result
    
    def _find_least_valuable_attacker(self, board, target_square, side):
        """
        Find the least valuable piece of the given side that attacks the target square.
        Returns the square of the attacker, or None if no attacker.
        """
        # Check in order of increasing value: pawn, knight, bishop, rook, queen, king
        piece_types = [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]
        
        # Get all attackers from the given side
        all_attackers = board.attackers(side, target_square)
        if not all_attackers:
            return None
            
        # Find the least valuable attacker
        for piece_type in piece_types:
            for attacker_square in all_attackers:
                piece = board.piece_at(attacker_square)
                if piece and piece.piece_type == piece_type and piece.color == side:
                    # Make sure this move would be legal (not pinned to king)
                    if board.is_legal(chess.Move(attacker_square, target_square)):
                        return attacker_square
        
        return None  # No legal attackers found
    
    def see_capture(self, board, move, threshold=0):
        """
        Determines if a capture is favorable based on SEE with a threshold.
        Returns True if the SEE score is >= threshold, False otherwise.
        Use threshold=0 to check if a capture is at least equal.
        """
        if not board.is_capture(move):
            return False
            
        see_score = self.see(board, move)
        return see_score >= threshold

    def move_score(self, board, move, ply):
        """Optimized move scoring function for faster move ordering"""
        if self.enable_profiling:
            self.profiler.start("move_scoring")
        
        # 1. Fast path for TT moves (highest priority)
        tt_entry = self.tt.get(chess.polyglot.zobrist_hash(board))
        if tt_entry and tt_entry.move == move:
            if self.enable_profiling:
                self.profiler.stop("move_scoring")
            return 10_000_000
        
        # Get move details directly to avoid repeated lookups
        from_square = move.from_square
        to_square = move.to_square
        promotion = move.promotion
        move_uci = move.uci()
        
        # 2. Capture scoring using precomputed MVV-LVA table (direct lookup)
        if board.is_capture(move):
            captured_piece = board.piece_at(to_square)
            capturing_piece = board.piece_at(from_square)
            if captured_piece and capturing_piece:
                # Use precomputed MVV-LVA table for faster lookup
                score = MVV_LVA[capturing_piece.piece_type][captured_piece.piece_type]
                
                # 3. Promotion scoring (combined with capture if applicable)
                if promotion:
                    score += PROMOTION_SCORES[promotion]  # Use precomputed table
                
                # 4. Killer move bonus 
                if move in self.killer_moves.get(ply, []):
                    score += 4000
                
                # 5. History heuristic
                score += self.history.get(move_uci, 0)
                
                if self.enable_profiling:
                    self.profiler.stop("move_scoring")
                return score
        
        # Non-capture moves
        score = 0
        
        # Promotion scoring
        if promotion:
            score += PROMOTION_SCORES[promotion]  # Use precomputed table
        
        # Killer move bonus
        if move in self.killer_moves.get(ply, []):
            score += 4000
        
        # History heuristic
        score += self.history.get(move_uci, 0)
            
        if self.enable_profiling:
            self.profiler.stop("move_scoring")
        
        return score

    def order_moves(self, board, legal_moves, tt_move, ply):
        """
        Optimized move ordering that avoids expensive sorting operations.
        Uses a pick-best approach which is faster than sorting the whole list.
        """
        
        if self.enable_profiling:
            self.profiler.start("move_ordering")
        
        # Use more efficient data structure for multiple access
        remaining_moves = list(legal_moves)
        ordered = []
        
        # 1. First handle TT move if available (highest priority)
        if tt_move:
            for i, move in enumerate(remaining_moves):
                if move == tt_move:
                    ordered.append(move)
                    remaining_moves.pop(i)
                    break
        
        # Exit early if we have no more moves to order
        if not remaining_moves:
            if self.enable_profiling:
                self.profiler.stop("move_ordering")
            return ordered
            
        # 2. Add captures and promotions with MVV-LVA ordering
        captures_indices = []
        capture_scores = []
        
        for i, move in enumerate(remaining_moves):
            if board.is_capture(move) or move.promotion:
                # Score the capture using MVV-LVA
                score = self._score_capture(board, move, ply)
                captures_indices.append(i)
                capture_scores.append(score)
                
        # Process captures in score order (highest first)
        while captures_indices:
            # Find the best score
            best_idx = capture_scores.index(max(capture_scores))
            move_idx = captures_indices[best_idx]
            
            # Add best move to ordered list
            ordered.append(remaining_moves[move_idx])
            
            # Remove from our tracking lists
            best_move_original_idx = captures_indices[best_idx]
            capture_scores.pop(best_idx)
            captures_indices.pop(best_idx)
            
            # Adjust indices that come after the removed move
            for j in range(len(captures_indices)):
                if captures_indices[j] > best_move_original_idx:
                    captures_indices[j] -= 1
        
        # Rebuild remaining_moves list after removing captures
        remaining_moves = [move for move in remaining_moves if not (board.is_capture(move) or move.promotion)]
        
        # 3. Add killer moves
        killers = []
        for move in remaining_moves:
            if move in self.killer_moves.get(ply, []):
                killers.append(move)
                
        ordered.extend(killers)
        
        # 4. Add remaining quiet moves with history heuristic ordering
        quiet_moves = [move for move in remaining_moves if move not in killers]
        
        if quiet_moves:
            # For a small number of moves, just do a simple highest-score pick
            if len(quiet_moves) <= 5:
                while quiet_moves:
                    best_score = NEG_INF
                    best_idx = 0
                    
                    for i, move in enumerate(quiet_moves):
                        score = self.history.get(move.uci(), 0)
                        if score > best_score:
                            best_score = score
                            best_idx = i
                            
                    ordered.append(quiet_moves[best_idx])
                    quiet_moves.pop(best_idx)
            else:
                # For more moves, use a more efficient insertion sort approach
                scored_quiet = [(move, self.history.get(move.uci(), 0)) for move in quiet_moves]
                scored_quiet.sort(key=lambda x: x[1], reverse=True)
                ordered.extend([m for m, _ in scored_quiet])
                
        if self.enable_profiling:
            self.profiler.stop("move_ordering")
            
        return ordered
    
    def _score_capture(self, board, move, ply):
        """
        Enhanced helper function to score a capture or promotion move using SEE.
        This provides more accurate move ordering for captures.
        """
        # Fast handling of promotions
        if move.promotion:
            return PROMOTION_SCORES[move.promotion]
            
        # Use MVV-LVA as the base score
        captured_piece = board.piece_at(move.to_square)
        capturing_piece = board.piece_at(move.from_square)
        
        if not captured_piece or not capturing_piece:
            return 0
        
        # Start with the basic MVV-LVA score
        base_score = MVV_LVA[capturing_piece.piece_type][captured_piece.piece_type]
        
        # If this is a valuable capture (e.g., capturing with a pawn or capturing a more valuable piece),
        # we can just use MVV-LVA for speed
        if piece_values[captured_piece.piece_type] >= piece_values[capturing_piece.piece_type] or \
           capturing_piece.piece_type == chess.PAWN:
            return base_score
            
        # For potentially bad captures (trading a higher value piece for a lower one),
        # run the full SEE algorithm to get a more accurate score
        see_score = self.see(board, move)
        
        if see_score > 0:
            # Good capture according to SEE, give it a high score
            return base_score
        elif see_score == 0:
            # Equal capture, use normal MVV-LVA but reduced slightly
            return base_score - 50
        else:
            # Bad capture according to SEE, penalize it but still keep it in consideration
            # We scale the penalty based on how bad the exchange is
            return base_score + see_score - 200
        
        return base_score

if __name__ == '__main__':
    import chess, sys
    # Usage: python searcher.py [depth] [time_limit] [profile]
    depth = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    time_limit = float(sys.argv[2]) if len(sys.argv) > 2 else 9.5
    enable_profile = len(sys.argv) > 3 and sys.argv[3].lower() in ('true', 'yes', '1')
    
    board = chess.Board()
    searcher = Searcher()
    searcher.enable_profiling = enable_profile
    
    print(f"Starting search: depth={depth}, time_limit={time_limit}, profiling={'enabled' if enable_profile else 'disabled'}")
    
    if enable_profile:
        # Just use our integrated profiler
        best_move = searcher.iterative_deepening(board, max_depth=depth, time_limit=time_limit)
        print(f"Best move: {best_move}")
    else:
        # Use cProfile for overall profiling
        import cProfile, pstats, io
        pr = cProfile.Profile()
        pr.enable()
        best_move = searcher.iterative_deepening(board, max_depth=depth, time_limit=time_limit)
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumtime')
        ps.print_stats(20)
        print(s.getvalue())
        print(f"Best move: {best_move}")

