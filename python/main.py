import pygame
from ui import draw_board, draw_pieces, highlight_moves
from game import Game

WIDTH, HEIGHT = 600, 600
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess Game")

font = pygame.font.SysFont(None, 48)

def main_menu(screen):
    background = pygame.image.load("assets/background.jpg")
    background = pygame.transform.scale(background, (WIDTH, HEIGHT))

    button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 25, 200, 50)
    waiting = True
    while waiting:
        screen.blit(background, (0, 0))  # Vẽ ảnh nền

        # Vẽ nút "Chơi Game"
        pygame.draw.rect(screen, (70, 130, 180), button_rect)
        text_surface = font.render("Play Game", True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=button_rect.center)
        screen.blit(text_surface, text_rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    waiting = False


# Gọi menu trước khi khởi tạo game
main_menu(screen)

# Sau khi nhấn "Chơi Game", bắt đầu trò chơi
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
    draw_pieces(screen, game.view_board)
    if game.selected_square is not None and game.history_index == len(game.board.move_stack):
        highlight_moves(screen, game.view_board, game.selected_square)

    game.update_ai_move()

    if game.history_index < len(game.board.move_stack):
        pygame.display.set_caption(f"Chess Game - Đang xem lại bước {game.history_index}/{len(game.board.move_stack)}")
    else:
        pygame.display.set_caption("Chess Game")

    pygame.display.flip()
    game.clock.tick(60)

pygame.quit()
