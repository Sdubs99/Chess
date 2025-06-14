import os
import sys
import pygame
from board import Board
from pieces import Pawn, Queen, Rook, Bishop, Knight, IMAGE_FILES

# ������ ��� ���� ����������������������������������������������������������������������������������������������������������
WINDOW_SIZE  = 640
SQUARE_SIZE  = WINDOW_SIZE // 8
PANEL_WIDTH  = 200
SCREEN_WIDTH = WINDOW_SIZE + PANEL_WIDTH
SCREEN_HEIGHT= WINDOW_SIZE

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Python Chess")
        self.clock  = pygame.time.Clock()
        self.font   = pygame.font.SysFont(None, 24)

        # assets ���
        base_dir    = os.path.dirname(os.path.abspath(__file__))
        assets_dir  = os.path.normpath(os.path.join(base_dir, '..', 'assets'))

        # ���� �̹��� �ε� & ���� ũ��� ������
        board_img_path = os.path.join(assets_dir, 'board.png')
        board_img_orig = pygame.image.load(board_img_path)
        self.board_img = pygame.transform.scale(
            board_img_orig,
            (WINDOW_SIZE, WINDOW_SIZE)
        )

        # ü���� ���� �ʱ�ȭ
        self.board    = Board()
        self.selected = None

    def prompt_promotion(self, color):
        choices = ['queen', 'rook', 'bishop', 'knight']
        base_dir   = os.path.dirname(os.path.abspath(__file__))
        pieces_dir = os.path.normpath(os.path.join(base_dir, '..', 'assets', 'pieces'))

        # �ĺ� �̹��� �ε�
        imgs = []
        for ptype in choices:
            fname = IMAGE_FILES[color][ptype]
            img   = pygame.image.load(os.path.join(pieces_dir, fname))
            img   = pygame.transform.scale(img, (SQUARE_SIZE, SQUARE_SIZE))
            imgs.append(img)

        # ������ ��������
        overlay = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # �� �̹��� ȭ�� �߾ӿ� ��ġ
        start_x = (WINDOW_SIZE - 4 * SQUARE_SIZE) // 2
        y       = (WINDOW_SIZE - SQUARE_SIZE) // 2
        rects   = []
        for i, img in enumerate(imgs):
            x = start_x + i * SQUARE_SIZE
            self.screen.blit(img, (x, y))
            rects.append(pygame.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE))

        pygame.display.flip()

        # ���� Ŭ�� ���
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    for idx, rect in enumerate(rects):
                        if rect.collidepoint(mx, my):
                            return choices[idx]

    def draw(self):
        # ���� �׸���
        self.screen.blit(self.board_img, (0, 0))

        # �⹰ �׸���
        for y in range(8):
            for x in range(8):
                piece = self.board.grid[y][x]
                if piece:
                    p_img = pygame.image.load(piece.image_path)
                    p_img = pygame.transform.scale(p_img, (SQUARE_SIZE, SQUARE_SIZE))
                    self.screen.blit(p_img, (x * SQUARE_SIZE, y * SQUARE_SIZE))

        # ���̶���Ʈ & ���̵� �г�
        self.draw_highlights()
        self.draw_side_panel()

    def draw_highlights(self):
        if not self.selected:
            return

        sx, sy = self.selected
        piece  = self.board.grid[sy][sx]

        # ���õ� ĭ ����
        sel_surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        sel_surf.fill((0, 255, 0, 100))
        self.screen.blit(sel_surf, (sx * SQUARE_SIZE, sy * SQUARE_SIZE))

        # �̵� ���� ĭ ����
        for mx, my in piece.get_valid_moves((sx, sy), self.board):
            mv_surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            mv_surf.fill((255, 255, 0, 80))
            self.screen.blit(mv_surf, (mx * SQUARE_SIZE, my * SQUARE_SIZE))

    def draw_side_panel(self):
        # �г� ���
        panel = pygame.Surface((PANEL_WIDTH, WINDOW_SIZE))
        panel.fill((30, 30, 30))
        self.screen.blit(panel, (WINDOW_SIZE, 0))

        # �� ǥ��
        turn_text = "White to move" if self.board.white_to_move else "Black to move"
        surf      = self.font.render(turn_text, True, (255, 255, 255))
        self.screen.blit(surf, (WINDOW_SIZE + 10, 20))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                x, y   = mx // SQUARE_SIZE, my // SQUARE_SIZE

                if 0 <= x < 8 and 0 <= y < 8:
                    # ù Ŭ��: �� ���� �⹰�� ����
                    if self.selected is None:
                        piece = self.board.grid[y][x]
                        if piece and (piece.color == 'white') == self.board.white_to_move:
                            self.selected = (x, y)
                    # �� ��° Ŭ��: �̵� & ���θ��
                    else:
                        moved = self.board.move_piece(self.selected, (x, y))
                        if moved:
                            piece = self.board.grid[y][x]
                            if isinstance(piece, Pawn) and (y == 0 or y == 7):
                                ptype = self.prompt_promotion(piece.color)
                                cls_map = {
                                    'queen':  Queen,
                                    'rook':   Rook,
                                    'bishop': Bishop,
                                    'knight': Knight
                                }
                                self.board.grid[y][x] = cls_map[ptype](piece.color)
                        self.selected = None

        return True

    def run(self):
        running = True
        while running:
            # �̺�Ʈ ó��
            running = self.handle_events()
            # �׸���
            self.draw()
            pygame.display.flip()
            self.clock.tick(30)

            # ������� ����
            loser = 'white' if self.board.white_to_move else 'black'
            if self.board.is_checkmate(loser):
                winner = 'Black' if loser == 'white' else 'White'
                self.show_game_over(f"Checkmate! {winner} wins")
                break
            elif self.board.is_stalemate(loser):
                self.show_game_over("Stalemate! Draw")
                break

        pygame.quit()

    def show_game_over(self, text):
        overlay = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        font_big = pygame.font.SysFont(None, 48)
        surf     = font_big.render(text, True, (255, 255, 255))
        rect     = surf.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//2))
        self.screen.blit(surf, rect)
        pygame.display.flip()
        pygame.time.wait(2000)