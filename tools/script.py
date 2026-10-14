#!/usr/bin/env python3
"""Compose a Caprice32 autocmd script.
tokens: W<n> = n idle keypresses, S = screenshot, R/L/U/D = cursor keys,
        Q = exit, anything else is typed as is ("_" types a space)."""
import sys
out = ['run"vrouves\n']
for tok in sys.argv[1:]:
    if tok[0] == 'W':
        out.append('x' * int(tok[1:]))
    elif tok == 'S':
        out.append('\\(CAP32_SCRNSHOT)')
    elif tok == 'Q':
        out.append('\\(CAP32_EXIT)')
    elif tok in ('R', 'L', 'U', 'D'):
        out.append({'R': 'p', 'L': 'o', 'U': 'q', 'D': 'a'}[tok])
    else:
        out.append(tok.replace('_', ' '))
sys.stdout.write(''.join(out))
