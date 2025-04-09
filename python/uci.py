import sys
from game import Game  # class Game bạn đã viết
import chess

def uci_loop():
    print("id name MyPythonEngine")
    print("id author YourName")
    print("uciok")
    sys.stdout.flush()

    game = Game()

    while True:
        line = sys.stdin.readline().strip()
        if line == "":
            continue
        if line == "uci":
            print("id name MyPythonEngine")
            print("id author YourName")
            print("uciok")
        elif line == "isready":
            print("readyok")
        elif line == "ucinewgame":
            game.reset_board()
        elif line == "quit":
            break
        elif line.startswith("position"):
            tokens = line.split()
            if "startpos" in tokens:
                game.reset_board()
                if "moves" in tokens:
                    idx = tokens.index("moves")
                    moves = tokens[idx + 1:]
                    for move in moves:
                        game.push_move_uci(move)
        elif line.startswith("go"):
            bestmove = game.get_best_move()
            print(f"bestmove {bestmove}")
        sys.stdout.flush()

if __name__ == "__main__":
    uci_loop()
