;==============================================================================
; synergy.asm - a defender hits harder or softer when one of its partner
; type sits right next to it (left, right, above or below, not diagonally):
;   a Bride next to a Cretan       +50%
;   a Yiayia next to a Baker       +20%
;   a Baker next to a Cretan       -50%
;   Psssst next to a Cretan        -20%
; Before a defender is built, the bonus it would get there shows at the end
; of the info line, green or red.
;
; There is no room left in the resident code, so this lives in the hidden
; 48 byte tails of screen blocks (#67D0 ... #7FD0 on the #4000 screen, #E7D0
; on the #C000 one), which nothing else uses during a game.  It is part of
; the title overlay, and syn_install copies it there when a game starts.
;==============================================================================
SYN_CHUNKS equ 5
SYN_SRC:
        org TAIL_SYNDATA,SYN_SRC
; per defender type: partner type (0: none), damage factor in 16ths, its text
syn_tab:
        db 0,0,0                                ; cretan
        db TT_BAKER,19,lo(syn_t20p)             ; yiayia
        db TT_CRETAN,24,lo(syn_t50p)            ; bride
        db TT_CRETAN,13,lo(syn_t20m)            ; psssst
        db 0,0,0                                ; cauldron
        db TT_CRETAN,8,lo(syn_t50m)             ; baker
syn_t50p: db G_PLUS,G_5,G_0,G_PCT,#ff
syn_t20p: db G_PLUS,G_2,G_0,G_PCT,#ff
syn_t50m: db G_MINUS,G_5,G_0,G_PCT,#ff
syn_t20m: db G_MINUS,G_2,G_0,G_PCT,#ff
syn_data_end:
        assert syn_data_end <= TAIL_SYNDATA+48
        assert hi(syn_data_end-1) == hi(syn_tab)

        org TAIL_SYNFIND,SYN_SRC+48
; A = type, D,E = col,row -> NZ and HL = its syn_tab entry when a partner
; is next door, Z when not.  Uses A, BC.
syn_find:
        dec a
        ld l,a
        add a,a
        add a,l
        add a,lo(syn_tab)
        ld l,a
        ld h,hi(syn_tab)
        ld a,(hl)
        or a
        ret z
        ld (syn_loop+2),a       ; the partner, into the CP below
        push hl
        ld hl,towers
        ld b,MAX_TW
        jp syn_loop
syn_find_end:
        assert syn_find_end <= TAIL_SYNFIND+48

        org TAIL_SYNLOOP,SYN_SRC+96
syn_loop:
        ld a,(hl)               ; T_TYPE
        cp 0
        jr nz,.n
        inc hl
        ld a,(hl)               ; T_COL
        inc hl
        ld c,(hl)               ; T_ROW
        dec hl
        dec hl
        sub d
        jr z,.col               ; same column: the rows one apart
        inc a                   ; else the columns one apart...
        and #fd
        jr nz,.n
        ld a,c                  ; ...on the same row
        cp e
        jr z,.hit
        jr .n
.col:   ld a,c
        sub e
        inc a
        and #fd
        jr z,.hit
.n:     ld a,l                  ; the towers fill one page
        add a,TW_SZ
        ld l,a
        djnz syn_loop
        pop hl
        xor a
        ret
.hit:   pop hl
        or 1
        ret
syn_loop_end:
        assert syn_loop_end <= TAIL_SYNLOOP+48

        org TAIL_SYNDMG,SYN_SRC+144
; tower_think, instead of ld a,(hl) / ld (tr_dmg),a: HL = the damage in the
; tower's stats, IY = tower.  Preserves HL; uses A, BC, DE.
syn_dmg:
        ld a,(hl)
        ld (tr_dmg),a
        push hl
        ld a,(iy+T_TYPE)
        ld d,(iy+T_COL)
        ld e,(iy+T_ROW)
        call syn_find
        jr z,.x
        inc hl
        ld b,(hl)               ; damage * factor / 16, rounded
        ld a,(tr_dmg)
        ld e,a
        ld d,0
        ld hl,8
.m:     add hl,de
        djnz .m
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld a,h
        ld (tr_dmg),a
.x:     pop hl
        ret
syn_dmg_end:
        assert syn_dmg_end <= TAIL_SYNDMG+48

        org TAIL_SYNHUD,SYN_SRC+192
; hud_info, after the selected defender's line: the bonus it would get on
; the cursor cell
syn_hud:
        call cur_cell
        ld a,(sel_type)
        call syn_find
        ret z
        inc hl
        ld a,(hl)               ; factor: above 16 a bonus, below a penalty
        inc hl
        ld l,(hl)
        ld h,hi(syn_tab)
        push hl
        ld bc,#0a00             ; green
        cp 17
        jr nc,.c
        ld b,#09                ; red
.c:     call set_colors
        ld de,36*256+HUD_Y2
        call set_at
        pop hl
        jp print_str
syn_hud_end:
        assert syn_hud_end <= TAIL_SYNHUD+48

        org SYN_SRC+SYN_CHUNKS*48       ; back to the overlay

; called as the title screen hands over to the game: the chunks to the tails
syn_install:
        ld hl,SYN_SRC
        ld de,TAIL_SYNDATA
        ld a,SYN_CHUNKS
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
        scf
        ret
