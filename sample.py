from oracle import *
import sys
import numpy as np
from tqdm import tqdm

if len(sys.argv) < 2:
    print("Usage: python sample.py <filename>")
    sys.exit(-1)


def n_padding(ctext, L):
    # divide the blocks
    IV, C1, C2 = ctext[:L], ctext[L:2*L], ctext[2*L:]
    print('Determining padding...')
    for i in range(L):
        C1_alt = C1.copy()
        # avoid setting a value to -1
        if C1_alt[i] > 1:
            C1_alt[i] -= 1
        else:
            C1_alt[i] += 1
        # send to oracle
        rc = int(chr(Oracle_Send(IV + C1_alt + C2, 3)))
        # padding error
        if not rc:
            print('Padding is', L - i, 'bytes.')
            return L - i

def guess_block2(ctext, pad, L):
    # divide the blocks
    IV, C1, C2 = ctext[:L], ctext[L:2*L], ctext[2*L:]
    print('Guessing Block 2...')
    # set current guess
    curr_guess = [0] * L
    # set the padding
    for i in range(L-pad, L, 1):
        curr_guess[i] = pad
    # loop through the rest of the block from right to left
    for i in tqdm(range(L-pad-1, -1, -1)):
        # block 1 is the IV of block 2
        iv = C1.copy()
        for p in range(i+1, L, 1):
            iv[p] = iv[p] ^ curr_guess[p] ^ (L-i)
        # find the value without a padding error
        for j in range(256):
            iv[i] = j
            data = IV + iv + C2
            rc = int(chr(Oracle_Send(data, 3)))
            if rc:
                curr_guess[i] = (L-i) ^ j ^ C1[i]
                break
    return "".join([chr(b) for b in curr_guess])	


def guess_block1(ctext, L):
    # divide the blocks
    IV, C1 = ctext[:L], ctext[L:2*L] 
    print('Guessing Block 1...')
    # set current guess
    curr_guess = [0] * 16
    for i in tqdm(range(L-1, -1, -1)):
        iv = IV.copy()
        for p in range(i+1, L, 1):
            iv[p] = iv[p] ^ curr_guess[p] ^ (L-i)
        for j in range(256):
            iv[i] = j
            data = iv + C1
            rc = int(chr(Oracle_Send(data, 2)))
            if rc:
                curr_guess[i] = (L-i) ^ j ^ IV[i]
                break
    return "".join([chr(b) for b in curr_guess])


def decrypt(ctext, L):
    Oracle_Connect()
    pad = n_padding(ctext, L)
    msg_2 = guess_block2(ctext, pad, L)
    msg_1 = guess_block1(ctext, L)
    Oracle_Disconnect()
    print(msg_1 + msg_2)


f = open(sys.argv[1])
data = f.read()
f.close()
L = 16
ctext = [(int(data[i:i+2],16)) for i in range(0, len(data), 2)]
decrypt(ctext, L)
