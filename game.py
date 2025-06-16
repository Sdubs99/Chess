import os
import sys
import pygame
from board import Board
from pieces import Pawn, Queen, Rook, Bishop, Knight, IMAGE_FILES

# ─── frozen vs. 개발 환경 분기 ─────────────────────────
if getattr(sys, 'frozen', False):
    # PyInstaller onefile 로 묶였을 때
    BASE_DIR = sys._MEIPASS
else:
    # .py로 실행할 때
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ─── assets 폴더 위치 결정 ────────────────────────────
# 기본: BASE_DIR/../assets
ASSETS_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'assets'))
# 없으면: BASE_DIR/assets
if not os.path.isdir(ASSETS_DIR):
    alt = os.path.join(BASE_DIR, 'assets')
    if os.path.isdir(alt):
        ASSETS_DIR = alt
    else:
        raise FileNotFoundError(f"assets 폴더를 찾을 수 없습니다: {ASSETS_DIR!r} 또는 {alt!r}") 

# ─── 리소스 경로 상수 ─────────────────────────────────
BOARD_IMG_PATH = os.path.join(ASSETS_DIR,    'board.png')
PIECES_DIR     = os.path.join(ASSETS_DIR, 'pieces')

# ─── 상수 정의 ─────────────────────────────────────────
WINDOW_SIZE   = 640
SQUARE_SIZE   = WINDOW_SIZE // 8
PANEL_WIDTH   = 200
SCREEN_WIDTH  = WINDOW_SIZE + PANEL_WIDTH
SCREEN_HEIGHT = WINDOW_SIZE

class Button:
    def __init__(self, rect, text, font, callback):
        self.rect      = pygame.Rect(rect)
        self.text      = text
        self.font      = font
        self.callback  = callback
        self.text_surf = font.render(text, True, (255,255,255))
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)

    def draw(self, screen):
        pygame.draw.rect(screen, (70,70,70), self.rect)
        pygame.draw.rect(screen, (200,200,200), self.rect, 2)
        screen.blit(self.text_surf, self.text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

class Game:
    def __init__(self):
        pygame.init()
        self.screen    = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Python Chess")
        self.clock     = pygame.time.Clock()
        self.font      = pygame.font.SysFont(None, 24)
        self.restart_game = False

        # 보드 이미지 로드 & 스케일
        board_img_orig = pygame.image.load(BOARD_IMG_PATH)
        self.board_img = pygame.transform.scale(board_img_orig, (WINDOW_SIZE, WINDOW_SIZE))

        # 체스판 로직 초기화
        self.board    = Board()
        self.selected = None

    def prompt_promotion(self, color):
        # 1) 승진 후보(queen, rook, bishop, knight) 이미지 로드
        # 2) 반투명 검은 오버레이
        # 3) 후보 이미지를 보드 중앙에 가로로 배치
        # 4) 클릭 대기 → 선택된 ptype 반환
        choices   = ['queen', 'rook', 'bishop', 'knight']
        imgs      = []
        for ptype in choices:
            fname = IMAGE_FILES[color][ptype]
            img   = pygame.image.load(os.path.join(PIECES_DIR, fname))
            img   = pygame.transform.scale(img, (SQUARE_SIZE, SQUARE_SIZE))
            imgs.append(img)

        # 반투명 오버레이
        overlay = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE), pygame.SRCALPHA)
        overlay.fill((0,0,0,180))
        self.screen.blit(overlay, (0,0))

        # 후보 이미지 배치
        start_x = (WINDOW_SIZE - 4*SQUARE_SIZE) // 2
        y       = (WINDOW_SIZE - SQUARE_SIZE) // 2
        rects   = []
        for i, img in enumerate(imgs):
            x = start_x + i * SQUARE_SIZE
            self.screen.blit(img, (x, y))
            rects.append(pygame.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE))
        pygame.display.flip()

        # 클릭 대기
        while True:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    mx, my = ev.pos
                    for idx, rect in enumerate(rects):
                        if rect.collidepoint(mx, my):
                            return choices[idx]

    def draw(self):
        # 보드
        self.screen.blit(self.board_img, (0,0))
        # 기물
        for y in range(8):
            for x in range(8):
                piece = self.board.grid[y][x]
                if piece:
                    p_img = pygame.image.load(piece.image_path)
                    p_img = pygame.transform.scale(p_img, (SQUARE_SIZE, SQUARE_SIZE))
                    self.screen.blit(p_img, (x*SQUARE_SIZE, y*SQUARE_SIZE))
        # 하이라이트 / 사이드패널
        self.draw_highlights()
        self.draw_side_panel()

    def draw_highlights(self):
        if not self.selected: return
        sx, sy = self.selected
        piece  = self.board.grid[sy][sx]

        # 선택된 칸 녹색 반투명으로 표시
        sel = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        sel.fill((0,255,0,100))
        self.screen.blit(sel, (sx*SQUARE_SIZE, sy*SQUARE_SIZE))

        for mx, my in piece.get_valid_moves((sx, sy), self.board):
            mv = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            mv.fill((255,255,0,80))
            self.screen.blit(mv, (mx*SQUARE_SIZE, my*SQUARE_SIZE))

    def draw_side_panel(self):
        panel = pygame.Surface((PANEL_WIDTH, WINDOW_SIZE))
        panel.fill((30,30,30))
        self.screen.blit(panel, (WINDOW_SIZE,0))
        # 턴에 따라 움직일 순서 표시
        turn_text = "White to move" if self.board.white_to_move else "Black to move"
        surf = self.font.render(turn_text, True, (255,255,255))
        self.screen.blit(surf, (WINDOW_SIZE+10,20))

    def handle_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit() 

            # ESC → Pause 메뉴
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                action = self.show_pause_menu()
                if action == 'resume':
                    return True
                if action == 'restart':
                    self.restart_game = True
                    return False
                if action == 'quit':
                    pygame.quit(); sys.exit()

            # 마우스 클릭
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                x, y   = mx//SQUARE_SIZE, my//SQUARE_SIZE
                if 0 <= x < 8 and 0 <= y < 8:
                    if self.selected is None:
                        piece = self.board.grid[y][x]
                        if piece and (piece.color=='white') == self.board.white_to_move:
                            self.selected = (x, y)
                    else:
                        moved = self.board.move_piece(self.selected, (x,y))
                        if moved:
                            piece = self.board.grid[y][x]
                            if isinstance(piece, Pawn) and (y==0 or y==7):
                                ptype = self.prompt_promotion(piece.color)
                                cls_map = {
                                    'queen': Queen, 'rook': Rook,
                                    'bishop': Bishop, 'knight': Knight
                                }
                                self.board.grid[y][x] = cls_map[ptype](piece.color)
                        self.selected = None
        return True

    def show_pause_menu(self):
        overlay    = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE), pygame.SRCALPHA)
        overlay.fill((0,0,0,180)); self.screen.blit(overlay,(0,0))
        title_surf = pygame.font.SysFont(None,48).render("Paused",True,(255,255,255))
        self.screen.blit(title_surf, title_surf.get_rect(center=(WINDOW_SIZE//2,WINDOW_SIZE//2-80)))

        btn_font   = pygame.font.SysFont(None,32)
        W, H       = 140, 40; mid = WINDOW_SIZE//2
        self.pause_action = None

        # 버튼 클릭하면 상태 반환
        resume_btn = Button((mid-W//2,WINDOW_SIZE//2-20,W,H),"Resume",btn_font,
                            lambda: setattr(self,'pause_action','resume'))
        restart_btn= Button((mid-W-10,WINDOW_SIZE//2+40,W,H),"Restart",btn_font,
                            lambda: setattr(self,'pause_action','restart'))
        quit_btn   = Button((mid+10,WINDOW_SIZE//2+40,W,H),"Quit",btn_font,
                            lambda: setattr(self,'pause_action','quit'))

        while True:
            for ev in pygame.event.get():
                if ev.type==pygame.QUIT: return 'quit'
                if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE: return 'resume'
                resume_btn.handle_event(ev)
                restart_btn.handle_event(ev)
                quit_btn.handle_event(ev)

            resume_btn.draw(self.screen)
            restart_btn.draw(self.screen)
            quit_btn.draw(self.screen)
            pygame.display.flip(); self.clock.tick(30)
            if self.pause_action: return self.pause_action

    def run(self):
        while True:
            # Restart 버튼 눌렀을 때 새판 생성
            self.board        = Board()
            self.selected     = None
            self.restart_game = False
            result = None

            # 플레이 루프 입력·그리기·판정 반복
            while True:
                cont = self.handle_events()
                if not cont:
                    break
                self.draw(); pygame.display.flip(); self.clock.tick(30)
                to_move = 'white' if self.board.white_to_move else 'black'
                if self.board.is_checkmate(to_move):
                    winner = 'Black' if to_move=='white' else 'White'
                    result = f"Checkmate! {winner} wins"; break
                if self.board.is_stalemate(to_move):
                    result = "Stalemate! Draw"; break

            if self.restart_game:
                continue
            if result is None:
                continue

            # result 가 채워지면(게임 오버) show_game_over 호출
            action = self.show_game_over(result)
            if action=='restart':
                continue
            else:
                break

        pygame.quit()

    def show_game_over(self, text):
        # 오버레이 + 메시지
        # Restart/Quit 버튼 생성
        overlay  = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE), pygame.SRCALPHA)
        overlay.fill((0,0,0,180)); self.screen.blit(overlay,(0,0))
        surf     = pygame.font.SysFont(None,48).render(text,True,(255,255,255))
        self.screen.blit(surf, surf.get_rect(center=(WINDOW_SIZE//2,WINDOW_SIZE//2-50)))

        font_btn = pygame.font.SysFont(None,32)
        W,H      = 120,40; mid=WINDOW_SIZE//2
        restart_btn = Button((mid-W-10,WINDOW_SIZE//2+10,W,H),"Restart",font_btn,self._on_restart)
        quit_btn    = Button((mid+10,WINDOW_SIZE//2+10,W,H),"Quit",font_btn,self._on_quit)

        self.restart_game = False
        while True:
            for ev in pygame.event.get():
                if ev.type==pygame.QUIT:
                    pygame.quit(); sys.exit()
                restart_btn.handle_event(ev)
                quit_btn.handle_event(ev)
            restart_btn.draw(self.screen)
            quit_btn.draw(self.screen)
            pygame.display.flip(); self.clock.tick(30)
            if self.restart_game:
                self.restart_game=False
                return 'restart'
    
    # 재시작
    def _on_restart(self):
        self.restart_game = True

    # 종료
    def _on_quit(self):
        pygame.quit()
        sys.exit()
