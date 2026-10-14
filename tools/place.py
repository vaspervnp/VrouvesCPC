#!/usr/bin/env python3
"""Emit script tokens that walk the cursor from (7,3) and build towers.
usage: place.py "type:col,row type:col,row ..." -> tokens on stdout"""
import sys
c, r = 7, 3
toks = []
for item in sys.argv[1].split():
    t, pos = item.split(':')
    tc, tr = map(int, pos.split(','))
    while c < tc: toks += ['R', 'W7']; c += 1
    while c > tc: toks += ['L', 'W7']; c -= 1
    while r < tr: toks += ['D', 'W7']; r += 1
    while r > tr: toks += ['U', 'W7']; r -= 1
    toks += [t, 'W5', '_', 'W7']
print(' '.join(toks))
