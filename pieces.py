import os
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PIECES_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'assets', 'pieces'))

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
        filename = IMAGE_FILES[color][ptype]
        self.image_path = os.path.join(PIECES_DIR, filename)

    def get_valid_moves(self, pos, board):
        return []


class Pawn(Piece):
    def __init__(self, color):
        super().__init__(color, 'pawn')

    def get_valid_moves(self, pos, board):
        x, y = pos
        moves = []
        dir = -1 if self.color == 'white' else 1
        # one step forward
        if 0 <= y + dir < 8 and board.grid[y + dir][x] is None:
            moves.append((x, y + dir))
            # two steps if not moved
            if not self.has_moved and board.grid[y + 2*dir][x] is None:
                moves.append((x, y + 2*dir))
        # captures
        for dx in (-1, 1):
            nx, ny = x + dx, y + dir
            if 0 <= nx < 8 and 0 <= ny < 8:
                target = board.grid[ny][nx]
                if target and target.color != self.color:
                    moves.append((nx, ny))
        # en passant
        last = board.move_history[-1] if board.move_history else None
        if last and isinstance(last[0], Pawn) and abs(last[2][1] - last[1][1]) == 2:
            lx, ly = last[2]
            if ly == y and abs(lx - x) == 1:
                moves.append((lx, y + dir))
        # filter out moves causing self-check
        return [m for m in moves if not board._would_cause_check(pos, m)]

class Rook(Piece):
    def __init__(self, color):
        super().__init__(color, 'rook')

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
        # combine rook and bishop moves
        return Rook(self.color).get_valid_moves(pos, board) + Bishop(self.color).get_valid_moves(pos, board)

class King(Piece):
    def __init__(self, color):
        super().__init__(color, 'king')

    def get_valid_moves(self, pos, board):
        moves = []
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                if dx==0 and dy==0: continue
                x, y = pos[0] + dx, pos[1] + dy
                if 0 <= x < 8 and 0 <= y < 8:
                    target = board.grid[y][x]
                    if target is None or target.color != self.color:
                        moves.append((x,y))
        # castling logic
        if not self.has_moved and not board.is_in_check(self.color):
            if board._can_castle_kingside(self.color): moves.append((pos[0]+2,pos[1]))
            if board._can_castle_queenside(self.color): moves.append((pos[0]-2,pos[1]))
        return [m for m in moves if not board._would_cause_check(pos, m)]
