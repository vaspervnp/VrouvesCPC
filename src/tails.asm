;==============================================================================
; tails.asm - code that runs from the hidden 48 byte tails of screen blocks
; (#x7D0-#x7FF), for want of room in the resident code: the neighbour bonus
; (synergy.asm), parts of the score (score.asm) and the lives (lives.asm).  The #4000 screen's first
; four tails hold the enemy dispatch blocks and the #C000 screen's first four
; the mirrored enemy frames; these take the other eight.  They are part of the
; title overlay, and tails_install copies them there when a game starts.
;==============================================================================
TAIL_CHUNKS equ 8
SYN_SRC:
        include "synergy.asm"
        include "score.asm"
        include "lives.asm"

        org SYN_SRC+TAIL_CHUNKS*48      ; back to the overlay

; called as the title screen hands over to the game: the chunks to the
; tails, and a new score
tails_install:
        ld hl,0
        ld (score),hl
        ld hl,SYN_SRC
        ld de,TAIL_SYNDATA
        ld a,TAIL_CHUNKS
.l:     ld bc,48
        ldir
        ex de,hl
        ld bc,#800-48
        add hl,bc
        ld b,a
        ld a,h
        cp #87                  ; past the #4000 screen: on to the #C000 one
        jr nz,.s
        ld h,#e7
.s:     ld a,b
        ex de,hl
        dec a
        jr nz,.l
        ld hl,dif_lives         ; the lives for the difficulty chosen
        ld a,(difficulty)
        add a,l
        ld l,a
        jr nc,.d
        inc h
.d:     ld a,(hl)
        ld (rt_lives),a
        scf
        ret

dif_lives: db 3,2,0,4
