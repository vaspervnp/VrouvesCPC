;==============================================================================
; tails.asm - code that runs from the hidden 48 byte tails of screen blocks
; (#x7D0-#x7FF), for want of room in the resident code: the neighbour bonus
; (synergy.asm) and parts of the score (score.asm).  The #4000 screen's first
; four tails hold the enemy dispatch blocks and the #C000 screen's first four
; the mirrored enemy frames; these take the other eight.  They are part of the
; title overlay, and tails_install copies them there when a game starts.
;==============================================================================
TAIL_CHUNKS equ 8
SYN_SRC:
        include "synergy.asm"
        include "score.asm"

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
        ld hl,0
        ld (rt_chk),hl
        call make_mirrors
        call make_dispatch
        scf
        ret

dif_lives: db 3,2,0,4

; the screen tails the enemy drawing uses, once a game: they stay
; untouched while it lasts
; mirrored enemy frames into the hidden tails of the #C000 screen blocks
make_mirrors:
        ld hl,mirror_tab
        ld b,4
.s:     push bc
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld c,(hl)
        inc hl
        ld a,(hl)
        inc hl
        push hl
        ld h,a
        ld l,c
        inc hl
        inc hl
        inc hl
        ex de,hl                ; HL = source, DE = end of the first row
        ld b,12
.r:     push bc
        ld b,4
.c:     ld a,(hl)               ; swap the two pixels of the byte
        rrca
        and #55
        ld c,a
        ld a,(hl)
        rlca
        and #aa
        or c
        inc hl
        ld (de),a
        dec de
        djnz .c
        ex de,hl
        ld bc,8
        add hl,bc
        ex de,hl
        pop bc
        djnz .r
        pop hl
        pop bc
        djnz .s
        ret

; Enemy frames are drawn row by row by small handlers, one per kind of row.
; For each pattern of row kinds make_dispatch writes 12 CALLs and a RET into
; the hidden tail of a #4000 screen block (#47D0, #4FD0, ...), so drawing a
; frame does no decoding at all.
make_dispatch:
        ld hl,disp_cls
        ld d,#47
.p:     ld e,#d0
        ld b,12
.r:     ld a,b
        and 3
        jr nz,.k
        ld c,(hl)               ; 2 bits per row, MSB first
        inc hl
.k:     rlc c
        rlc c
        ld a,c
        and 3
        add a,a
        push hl
        ld hl,row_handlers
        add a,l
        ld l,a
        jr nc,.n
        inc h
.n:     ld a,#cd                ; CALL handler
        ld (de),a
        inc de
        ld a,(hl)
        ld (de),a
        inc de
        inc hl
        ld a,(hl)
        ld (de),a
        inc de
        pop hl
        djnz .r
        ld a,#c9                ; RET
        ld (de),a
        ld a,d
        add a,8
        ld d,a
        cp #47+DISP_COUNT*8
        jr nz,.p
        ret

row_handlers:
        dw er_m4,er_f4,er_mid,er_z

