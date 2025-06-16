import os
import sys

# ─── frozen vs. 개발 환경 분기 ────────────────────
if getattr(sys, 'frozen', False):
    # PyInstaller onefile 로 묶였을 때
    BASE_DIR = sys._MEIPASS
else:
    # .py 로 실행할 때
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── assets/pieces 폴더 경로 결정 ───────────────────
# game.py 에서와 같은 상위 assets 폴더를 찾기 위해
ASSETS_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'assets'))
# 대소문자나 위치가 다를 경우를 대비해… (필요 없으면 지워도 됩니다)
if not os.path.isdir(ASSETS_DIR):
    alt = os.path.join(BASE_DIR, 'assets')
    if os.path.isdir(alt):
        ASSETS_DIR = alt
    else:
        raise FileNotFoundError(f"assets 폴더를 찾을 수 없습니다: {ASSETS_DIR!r} 또는 {alt!r}")

PIECES_DIR = os.path.join(ASSETS_DIR, 'pieces')

# ─── 이미지 파일명 매핑 ─────────────────────────────
IMAGE_FILES = {
    'white': {
        'pawn':   'W Pawn.png',
        'rook':   'W Rook.png',
        'knight': 'W Knight.png',
        'bishop': 'W Bishop.png',
        'queen':  'W Queen.png',
        'king':   'W King.png',
    },
    'black': {
        'pawn':   'B Pawn.png',
        'rook':   'B Rook.png',
        'knight': 'B Knight.png',
        'bishop': 'B Bishop.png',
        'queen':  'B Queen.png',
        'king':   'B King.png',
    }
}

class Piece:
    def __init__(self, color, ptype):
        self.color = color
        self.ptype = ptype
        self.has_moved = False
        self.image_path = os.path.join(PIECES_DIR, IMAGE_FILES[color][ptype])

    def get_valid_moves(self, pos, board):
        return []

class Pawn(Piece):
    def __init__(self, color):
        super().__init__(color, 'pawn')

    def get_valid_moves(self, pos, board):
        x, y = pos
        moves = []
        dir = -1 if self.color == 'white' else 1
        # 1) 한 칸 전진
        if 0 <= y + dir < 8 and board.grid[y + dir][x] is None:
            moves.append((x, y + dir))
            # 2) 두 칸 전진 (첫 이동 시)
            if not self.has_moved and board.grid[y + 2*dir][x] is None:
                moves.append((x, y + 2*dir))
        # 3) 일반 대각선 캡처
        for dx in (-1, 1):
            nx, ny = x + dx, y + dir
            if 0 <= nx < 8 and 0 <= ny < 8:
                target = board.grid[ny][nx]
                if target and target.color != self.color:
                    moves.append((nx, ny))
        # 4) 앙파상 (en passant)
        last = board.move_history[-1] if board.move_history else None
        if last and isinstance(last[0], Pawn) and abs(last[2][1] - last[1][1]) == 2:
            lx, ly = last[2]
            if ly == y and abs(lx - x) == 1:
                moves.append((lx, y + dir))
        # 5) ‘내가 이 수를 두면 내 킹이 체크가 되지 않는가?’ 필터
        return [m for m in moves if not board._would_cause_check(pos, m)]

class Rook(Piece):
    def __init__(self, color):
        super().__init__(color, 'rook')
    # 4방향 슬라이딩
    def get_valid_moves(self, pos, board):
        moves = []
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            x, y = pos
            while True:
                x += dx; y += dy
                if not (0 <= x < 8 and 0 <= y < 8): break
                target = board.grid[y][x]
                if target is None:
                    moves.append((x,y)); continue
                if target.color != self.color:
                    moves.append((x,y))
                break
        return [m for m in moves if not board._would_cause_check(pos, m)]

class Bishop(Piece):
    def __init__(self, color):
        super().__init__(color, 'bishop')
    # 4대각선 슬라이딩
    def get_valid_moves(self, pos, board):
        moves = []
        for dx, dy in [(1,1),(1,-1),(-1,1),(-1,-1)]:
            x, y = pos
            while True:
                x += dx; y += dy
                if not (0 <= x < 8 and 0 <= y < 8): break
                target = board.grid[y][x]
                if target is None:
                    moves.append((x,y)); continue
                if target.color != self.color:
                    moves.append((x,y))
                break
        return [m for m in moves if not board._would_cause_check(pos, m)]

class Knight(Piece):
    def __init__(self, color):
        super().__init__(color, 'knight')
    # 8가지 L자 점프
    def get_valid_moves(self, pos, board):
        moves = []
        for dx, dy in [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]:
            x, y = pos[0] + dx, pos[1] + dy
            if 0 <= x < 8 and 0 <= y < 8:
                target = board.grid[y][x]
                if target is None or target.color != self.color:
                    moves.append((x,y))
        return [m for m in moves if not board._would_cause_check(pos, m)]

class Queen(Piece):
    def __init__(self, color):
        super().__init__(color, 'queen')

    def get_valid_moves(self, pos, board):
        # 룩 + 비숍 이동을 합친다
        return Rook(self.color).get_valid_moves(pos, board) + Bishop(self.color).get_valid_moves(pos, board)

class King(Piece):
    def __init__(self, color):
        super().__init__(color, 'king')

    def get_valid_moves(self, pos, board):
        moves = []
        # 1) 인접 8칸 이동
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                if dx==0 and dy==0: continue
                x, y = pos[0] + dx, pos[1] + dy
                if 0 <= x < 8 and 0 <= y < 8:
                    target = board.grid[y][x]
                    if target is None or target.color != self.color:
                        moves.append((x,y))
        # 2) 캐슬링 (킹이 움직인 적 없고, 현재 체크 상태도 아니면)
        if not self.has_moved and not board.is_in_check(self.color):
            if board._can_castle_kingside(self.color): moves.append((pos[0]+2,pos[1]))
            if board._can_castle_queenside(self.color): moves.append((pos[0]-2,pos[1]))
        return [m for m in moves if not board._would_cause_check(pos, m)]
