import copy
from pieces import Pawn, Rook, Knight, Bishop, Queen, King

class Board:
    def __init__(self):
        self.grid = [[None]*8 for _ in range(8)] # 8×8 격자
        self.move_history = [] # (piece, from, to) 기록
        self.white_to_move = True # 다음 수는 흰색
        self.setup_initial_positions() # 기물 배치

    def setup_initial_positions(self):
        # 초기 기물 배치
        for i in range(8):
            self.grid[1][i] = Pawn('black')
            self.grid[6][i] = Pawn('white')
        back_rank = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for col, cls in enumerate(back_rank):
            self.grid[0][col] = cls('black')
            self.grid[7][col] = cls('white')

    def move_piece(self, from_pos, to_pos):
        fx, fy = from_pos
        tx, ty = to_pos
        # 1) 유효 기물인지 & get_valid_moves 에 포함된 수인지 검사
        piece = self.grid[fy][fx]
        if not piece or to_pos not in piece.get_valid_moves(from_pos, self):
            return False
        # 2) 실제 이동 로직 적용
        self._apply_move(piece, from_pos, to_pos)
        # 3) 기록·상태 업데이트
        self.move_history.append((piece, from_pos, to_pos))
        piece.has_moved = True
        self.white_to_move = not self.white_to_move
        return True

    def _apply_move(self, piece, from_pos, to_pos):
        fx, fy = from_pos
        tx, ty = to_pos

        # 1) 캐슬링: King이 두 칸 이동한 경우
        if isinstance(piece, King) and abs(tx - fx) == 2:
            rook_src = 7 if tx > fx else 0
            rook_dst = fx + (1 if tx > fx else -1)
            rook = self.grid[fy][rook_src]
            self.grid[fy][rook_dst] = rook
            self.grid[fy][rook_src] = None
            rook.has_moved = True

        # 2) 앙파상 캡처: Pawn이 대각선 이동했는데 이동 칸이 비어있다면
        if isinstance(piece, Pawn) and fx != tx and self.grid[ty][tx] is None:
            self.grid[fy][tx] = None

        # 3) 일반 이동
        self.grid[fy][fx] = None
        self.grid[ty][tx] = piece

    def is_in_check(self, color):
         # 1) 해당 색의 King 위치 찾기
        king_pos = next(((x, y) for y in range(8) for x in range(8)
                         if isinstance(self.grid[y][x], King) and self.grid[y][x].color == color), None)
        if not king_pos:
            return False

        # 2) 상대 색을 attacker 로 지정
        attacker = 'black' if color == 'white' else 'white'
        return self._square_attacked(king_pos, attacker)

    def _square_attacked(self, square, attacker_color):
        x0, y0 = square

        # 1) Pawn 공격 (한 칸 대각선)
        step = -1 if attacker_color == 'white' else 1
        for dx in (-1, 1):
            x, y = x0 + dx, y0 + step
            if 0 <= x < 8 and 0 <= y < 8:
                p = self.grid[y][x]
                if isinstance(p, Pawn) and p.color == attacker_color:
                    return True

        # 2) Knight 공격 (8가지 L자 점프)
        for dx, dy in [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]:
            x, y = x0 + dx, y0 + dy
            if 0 <= x < 8 and 0 <= y < 8:
                p = self.grid[y][x]
                if isinstance(p, Knight) and p.color == attacker_color:
                    return True

        # 3) Rook/Queen 슬라이딩 (직선 4방향)
        for dx, dy, types in [
            (1,0,(Rook,Queen)),(-1,0,(Rook,Queen)),(0,1,(Rook,Queen)),(0,-1,(Rook,Queen)),
            (1,1,(Bishop,Queen)),(1,-1,(Bishop,Queen)),(-1,1,(Bishop,Queen)),(-1,-1,(Bishop,Queen))
        ]:
            x, y = x0, y0
            while True:
                x += dx; y += dy
                if not (0 <= x < 8 and 0 <= y < 8):
                    break
                p = self.grid[y][x]
                if p and p.color == attacker_color and isinstance(p, types):
                    return True
                if p:
                    break # 다른 기물에 막힘

        # 4) King 인접 공격 (8칸)
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                if dx == 0 and dy == 0:
                    continue
                x, y = x0 + dx, y0 + dy
                # 인접 8칸 체크
                if 0 <= x < 8 and 0 <= y < 8:
                    p = self.grid[y][x]
                    if isinstance(p, King) and p.color == attacker_color:
                        return True
        return False


    def _would_cause_check(self, from_pos, to_pos):
    # 체크 유발되는 수가 있는지 검사
        b2 = copy.deepcopy(self)
        piece = b2.grid[from_pos[1]][from_pos[0]]
        b2._apply_move(piece, from_pos, to_pos)
        return b2.is_in_check('white' if self.white_to_move else 'black')

    def has_any_legal_moves(self, color):
    # 스테일메이트(무승부) 검사
        for y in range(8):
            for x in range(8):
                p = self.grid[y][x]
                if p and p.color == color and p.get_valid_moves((x, y), self):
                    return True
        return False

    def is_checkmate(self, color):
        # 체크메이트
        return self.is_in_check(color) and not self.has_any_legal_moves(color)

    def is_stalemate(self, color):
        # 스테일메이트
        return not self.is_in_check(color) and not self.has_any_legal_moves(color)

    def _can_castle_kingside(self, color):
        y = 7 if color == 'white' else 0
        king = self.grid[y][4]
        rook = self.grid[y][7]
        # 1) King·Rook 존재 및 미이동
        # 2) 중간 칸(5,6)이 비어야 함
        # 3) (4,5,6)칸이 공격받지 않아야 함
       
        if not (isinstance(king, King) and isinstance(rook, Rook)):
            return False
       
        if king.has_moved or rook.has_moved:
            return False
        
        for x in (5, 6):
            if self.grid[y][x] is not None:
                return False
       
        for x in (4, 5, 6):
            if self._square_attacked((x, y), color):
                return False
        return True

    def _can_castle_queenside(self, color):
        # 유사 로직, 칸 인덱스(1,2,3) 및 (2,3,4) 체크
        y = 7 if color == 'white' else 0
        king = self.grid[y][4]
        rook = self.grid[y][0]
        if not (isinstance(king, King) and isinstance(rook, Rook)):
            return False
        if king.has_moved or rook.has_moved:
            return False
       
        for x in (1, 2, 3):
            if self.grid[y][x] is not None:
                return False
        
        for x in (2, 3, 4):
            if self._square_attacked((x, y), color):
                return False
        return True

