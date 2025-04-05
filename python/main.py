import pygame
from ui import draw_board, draw_pieces, highlight_moves
from game import Game

WIDTH, HEIGHT = 600, 600
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess Game")

game = Game()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        else:
            game.handle_event(event)

    screen.fill((0, 0, 0))
    draw_board(screen)
    draw_pieces(screen, game.board)
    if game.selected_square is not None:
        highlight_moves(screen, game.board, game.selected_square)
    game.update_ai_move()
    pygame.display.flip()
    game.clock.tick(60)

pygame.quit()
