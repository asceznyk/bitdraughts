import numpy as np
import math

def count_bits(pieces):
    count = 0
    for i in range(len(bin(pieces))):
        if (pieces >> i) & 1:
            count += 1

    return count

class BitDraughts:
    def __init__(self, statestr=None, side=None):
        self.B, self.W = 0, 1

        self.maskse = 0x07070707
        self.maskne = 0x07070700

        self.masksw = 0x00e0e0e0
        self.masknw = 0xe0e0e0e0

        self.kings = np.uint32(0)

        self.move4b = 0x11
        self.move3b = 0x09
        self.move5b = 0x21

        self.capture4b3b = 0x89
        self.capture4b5b = 0x221
        self.capture3b4b = 0x91
        self.capture5b4b = 0x211

        self.promoteblack = 0xf0000000
        self.promotewhite = 0x0000000f

        self.win = 0

        if statestr is not None:
            self.black = np.uint32(0)
            self.white = np.uint32(0)
            self.set_state(statestr, side)
        else:
            self.side = self.B
            self.black = np.uint32(2**12 - 1)
            self.white = np.uint32(2**32 - 2**20) 

        self.blackwhite = [self.black, self.white]

    def set_state(self, statestr, side=None):
        self.side = self.W if side == 'w' else self.B
        offset = 0

        for char in statestr:
            if char == 'b':
                self.black = self.black | (1 << offset)
            elif char == 'w':
                self.white = self.white | (1 << offset)
            elif char == 'B':
                self.kings = self.kings | (1 << offset)
                self.black = self.black | (1 << offset)
            elif char == 'W':
                self.kings = self.kings | (1 << offset)
                self.white = self.white | (1 << offset)

            offset += 1

    def get_state(self):
        return (self.black, self.white, self.kings, self.side)

    def decode_movescaps(self, moveable, movemask, offset=0):
        return [(movemask << bit + offset) for bit, piece in enumerate(bin(moveable)[:1:-1]) if piece == '1']

    def pawnking_moves(self, empty, rshift, lshift):
        moves = []

        moves.extend(self.decode_movescaps((empty >> 4) & rshift, self.move4b))
        moves.extend(self.decode_movescaps((empty >> 3) & rshift & self.masksw, self.move3b))
        moves.extend(self.decode_movescaps((empty >> 5) & rshift & self.maskse, self.move5b))

        moves.extend(self.decode_movescaps((empty << 4) & lshift, self.move4b, -4))
        moves.extend(self.decode_movescaps((empty << 3) & lshift & self.maskne, self.move3b, -3))
        moves.extend(self.decode_movescaps((empty << 5) & lshift & self.masknw, self.move5b, -5))

        return moves

    def pawnking_captures(self, empty, rshift, lshift, opside):
        captures = []

        takeable = (empty >> 4) & opside
        if takeable:
            captures.extend(self.decode_movescaps((takeable >> 3) & rshift & self.masksw, self.capture4b3b))
            captures.extend(self.decode_movescaps((takeable >> 5) & rshift & self.maskse, self.capture4b5b))

        takeable = (empty >> 3) & opside & self.masksw
        if takeable:
            captures.extend(self.decode_movescaps((takeable >> 4) & rshift, self.capture3b4b))

        takeable = (empty >> 5) & opside & self.maskse
        if takeable:
            captures.extend(self.decode_movescaps((takeable >> 4) & rshift, self.capture5b4b))

        takeable = (empty << 4) & opside
        if takeable:
            captures.extend(self.decode_movescaps((takeable << 3) & lshift & self.maskne, self.capture3b4b, -7))
            captures.extend(self.decode_movescaps((takeable << 5) & lshift & self.masknw, self.capture5b4b, -9))

        takeable = (empty << 3) & opside & self.maskne
        if takeable:
            captures.extend(self.decode_movescaps((takeable << 4) & lshift, self.capture4b3b, -7))

        takeable = (empty << 5) & opside & self.masknw
        if takeable:
            captures.extend(self.decode_movescaps((takeable << 4) & lshift, self.capture4b5b, -9))

        return captures

    def get_moves(self):
        captures = self.get_captures()
        if captures:
            return captures

        moves = []
        empty = np.uint32(~(self.black | self.white))

        if self.side == self.B:
            moves.extend(self.pawnking_moves(empty, self.black, (self.black & self.kings)))
        else:
            moves.extend(self.pawnking_moves(empty, (self.white & self.kings), self.white))

        return moves

    def get_captures(self):
        captures = []
        empty = np.uint32(~(self.black | self.white))

        if self.side == self.B:
            black = self.black
            kings = self.black & self.kings
            captures.extend(self.pawnking_captures(empty, black, kings, self.white))
        else:
            white = self.white
            kings = self.white & self.kings
            captures.extend(self.pawnking_captures(empty, kings, white, self.black))

        sequences = set()
        for capture in captures:
            sequences.update(self.get_sequences(capture))
        return list(sequences)

    def get_sequences(self, capture):
        stack = [capture]
        sequences = []

        while stack:
            capture = stack.pop()

            fullcaps = []
            empty = np.uint32(~(self.black | self.white))

            if self.side == self.B:
                _, white, kings = self.update_board(capture)
                piece = empty & capture
                fullcaps.extend(self.pawnking_captures(empty, piece, (piece & kings), white))
            else:
                black, _, kings = self.update_board(capture)
                piece = empty & capture
                fullcaps.extend(self.pawnking_captures(empty, (piece & kings), piece, black))
            
            fullseq = [((capture | ncap) & ~piece) for ncap in fullcaps]

            for ncap in fullseq:
                stack.append(ncap)

            if not fullcaps:
                sequences.append(capture)

        return sequences

    def update_board(self, move):
        empty = np.uint32(~(self.black | self.white))

        if self.side == self.B:
            fromsq = self.black & move
            tosq = empty & move
            captured = self.white & move

            black = (self.black | tosq) & ~fromsq
            white = self.white & ~captured

        else:
            fromsq = self.white & move
            tosq = empty & move
            captured = self.black & move

            white = (self.white | tosq) & ~fromsq
            black = self.black & ~captured
            
        kings = self.kings
        if self.kings & fromsq:
            kings = (self.kings | tosq) & ~fromsq
            kings = kings & ~captured
            
        return black, white, kings

    def make_move(self, move):
        self.black, self.white, self.kings = self.update_board(move)

        self.kings |= self.black & self.promoteblack
        self.kings |= self.white & self.promotewhite
        self.side = ~self.side

        return self

    def end_game(self):
        if not self.get_moves():
            if count_bits(self.blackwhite[self.side]) > count_bits( self.blackwhite[(~self.side)]):
                self.win = 1
            elif count_bits(self.blackwhite[(~self.side)]) > count_bits( self.blackwhite[self.side]):
                self.win = -1
            return True
        else:
            return False

    def print_board(self, black=0, white=0, kings=0):
        if black | white | kings == 0:
            black, white, kings = self.black, self.white, self.kings

        print(' ')

        for i in range(8):
            rowstr = str(8-i) + ' '

            for j in range(4):
                bi = (4*i + j)
                
                if i % 2 == 0:
                    rowstr += '. '

                if ((black >> bi) & 1):
                    char = 'B ' if ((black >> bi) & (kings >> bi) & 1) else 'b '
                elif ((white >> bi) & 1):
                    char = 'W ' if ((white >> bi) & (kings >> bi) & 1) else 'w '
                else:
                    char = '- '
                rowstr += char

                if i % 2 != 0:
                    rowstr += '. '
                
            print(rowstr)

        print(' ')
