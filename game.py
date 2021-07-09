import numpy as np
import random
import time
from draughts import *

def user_game(position=None, side=None, mode='random'):
    draughtb = BitDraughts() if position is None else BitDraughts(position, side)
    draughtb.print_board()

    while not draughtb.end_game():
        moves = draughtb.get_moves()
        print(str([bin(m) for m in moves]))
        move = moves[random.randint(0, len(moves)-1)]
        if mode == 'user':
            move = moves[int(input('choose a move by index: '))]
        draughtb.make_move(move)
        draughtb.print_board()

    return False

start = time.time()
user_game(mode='user')
end = time.time()

print('that took '+str(end-start)+' seconds')
