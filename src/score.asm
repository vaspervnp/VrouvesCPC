;==============================================================================
; score.asm - the parts of the score that live in hidden screen block tails
; (see tails.asm); the rest is resident: score, pay and score_add (game.asm).
; Points: the damage an invader would have done, for each one stopped; the
; damage of each defender built (taken away again when it is sold); the
; seconds left when a wave is called early; the vrouves left after a stage.
;==============================================================================
        org TAIL_SCBUILD,SYN_SRC+5*48
; try_build: the defender's price paid, its damage as points
sc_build:
        ld a,(tmp_cost)
        ld c,a
        ld b,0
        ld hl,(funds)
        or a
        sbc hl,bc
        ld (funds),hl
        ld a,(sel_type)
        call ttype_ptr
        inc hl
        inc hl
        inc hl
        ld c,(hl)               ; its damage
        ld b,0
        jp score_add
sc_build_end:
        assert sc_build_end <= TAIL_SCBUILD+48

        org TAIL_SCSELL,SYN_SRC+6*48
; try_sell, HL = the defender's stats: half its price back, its points gone
sc_sell:
        push hl
        ld de,7
        add hl,de
        ld c,(hl)
        ld b,0
        ld hl,(funds)
        add hl,bc
        ld (funds),hl
        pop hl
        inc hl
        inc hl
        inc hl
        ld c,(hl)
        ld hl,(score)
        or a
        sbc hl,bc
        jr nc,.s
        ld hl,0
.s:     ld (score),hl
        ret
sc_sell_end:
        assert sc_sell_end <= TAIL_SCSELL+48

        org TAIL_SCSHOW,SYN_SRC+7*48
; the top bar's second line, when it has nothing else to say: the score and
; the lives left (the texts in lives.asm)
sc_show:
        ld hl,sc_txt_en
        ld a,(lang)
        or a
        jr z,.e
        ld hl,sc_txt_gr
.e:     call print_str          ; HL: past it, the lives text
        push hl
        ld hl,(score)
        ld a,5
        call print_num
        pop hl
        call print_str
        ld a,(rt_lives)
        ld l,a
        ld h,0
        ld a,1
        jp print_num
sc_show_end:
        assert sc_show_end <= TAIL_SCSHOW+48
