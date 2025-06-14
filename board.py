import copy
from pieces import Pawn, Rook, Knight, Bishop, Queen, King

class Board:
    def __init__(self):
        self.grid = [[None]*8 for _ in range(8)]
        self.move_history = []
        self.white_to_move = True
        self.setup_initial_positions()

    def setup_initial_positions(self):
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
        piece = self.grid[fy][fx]
        if not piece or to_pos not in piece.get_valid_moves(from_pos, self):
            return False
        self._apply_move(piece, from_pos, to_pos)
        self.move_history.append((piece, from_pos, to_pos))
        piece.has_moved = True
        self.white_to_move = not self.white_to_move
        return True

    def _apply_move(self, piece, from_pos, to_pos):
        fx, fy = from_pos
        tx, ty = to_pos
        if isinstance(piece, King) and abs(tx - fx) == 2:
            rook_src = 7 if tx > fx else 0
            rook_dst = fx + (1 if tx > fx else -1)
            rook = self.grid[fy][rook_src]
            self.grid[fy][rook_dst] = rook
            self.grid[fy][rook_src] = None
            rook.has_moved = True
        if isinstance(piece, Pawn) and fx != tx and self.grid[ty][tx] is None:
            self.grid[fy][tx] = None
        self.grid[fy][fx] = None
        self.grid[ty][tx] = piece

    def is_in_check(self, color):
        king_pos = next(((x, y) for y in range(8) for x in range(8)
                         if isinstance(self.grid[y][x], King) and self.grid[y][x].color == color), None)
        if not king_pos:
            return False
        attacker = 'black' if color == 'white' else 'white'
        return self._square_attacked(king_pos, attacker)

    def _square_attacked(self, square, attacker_color):
        x0, y0 = square
        step = -1 if attacker_color == 'white' else 1
        for dx in (-1, 1):
            x, y = x0 + dx, y0 + step
            if 0 <= x < 8 and 0 <= y < 8:
                p = self.grid[y][x]
                if isinstance(p, Pawn) and p.color == attacker_color:
                    return True
        for dx, dy in [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]:
            x, y = x0 + dx, y0 + dy
            if 0 <= x < 8 and 0 <= y < 8:
                p = self.grid[y][x]
                if isinstance(p, Knight) and p.color == attacker_color:
                    return True
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
                    break
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                if dx == 0 and dy == 0:
                    continue
                x, y = x0 + dx, y0 + dy
                # boundary check 추가
                if 0 <= x < 8 and 0 <= y < 8:
                    p = self.grid[y][x]
                    if isinstance(p, King) and p.color == attacker_color:
                        return True
        return False


    def _would_cause_check(self, from_pos, to_pos):
        b2 = copy.deepcopy(self)
        piece = b2.grid[from_pos[1]][from_pos[0]]
        b2._apply_move(piece, from_pos, to_pos)
        return b2.is_in_check('white' if self.white_to_move else 'black')

    def has_any_legal_moves(self, color):
        for y in range(8):
            for x in range(8):
                p = self.grid[y][x]
                if p and p.color == color and p.get_valid_moves((x, y), self):
                    return True
        return False

    def is_checkmate(self, color):
        return self.is_in_check(color) and not self.has_any_legal_moves(color)

    def is_stalemate(self, color):
        return not self.is_in_check(color) and not self.has_any_legal_moves(color)

    def _can_castle_kingside(self, color):
        y = 7 if color == 'white' else 0
        king = self.grid[y][4]
        rook = self.grid[y][7]
        # King·Rook 존재 및 타입 체크
        if not (isinstance(king, King) and isinstance(rook, Rook)):
            return False
        # 둘 다 아직 이동한 적 없어야 함
        if king.has_moved or rook.has_moved:
            return False
        # 사이 칸(5,6)이 비어 있어야 함
        for x in (5, 6):
            if self.grid[y][x] is not None:
                return False
        # King이 지나는 칸(4,5,6)이 공격받지 않아야 함
        for x in (4, 5, 6):
            if self._square_attacked((x, y), color):
                return False
        return True

    def _can_castle_queenside(self, color):
        y = 7 if color == 'white' else 0
        king = self.grid[y][4]
        rook = self.grid[y][0]
        if not (isinstance(king, King) and isinstance(rook, Rook)):
            return False
        if king.has_moved or rook.has_moved:
            return False
        # 사이 칸(1,2,3)이 비어 있어야 함
        for x in (1, 2, 3):
            if self.grid[y][x] is not None:
                return False
        # King이 지나는 칸(2,3,4)이 공격받지 않아야 함
        for x in (2, 3, 4):
            if self._square_attacked((x, y), color):
                return False
        return True

