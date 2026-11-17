;==============================================================================
; priest.asm - the Priest (stages 13-19): he blesses the defenders next to
; him, who then reload twice as fast, and his bell holds the drones and the
; guards around him still for a moment (the tanks do not listen).  In the
; Lyra area (lyra.asm).
;==============================================================================
; tower_think, with a target in reach: IY = the Priest
fire_priest:
        ld ix,enemies
        ld b,MAX_EN
.l:     push bc
        ld a,(ix+E_TYPE)
        or a
        jr z,.n
        cp ET_TANK
        jr z,.n
        call in_range
        jr nc,.n
        ld (ix+E_SLOW),BELL_STUN  ; still, then slowed (enemy_move)
.n:     ld de,EN_SZ
        add ix,de
        pop bc
        djnz .l
        ld a,(iy+T_CX)          ; the bell rings over him
        sub 2
        ld d,a
        ld a,(iy+T_CY)
        sub 16
        ld e,a
        ld a,FX_BASH
        jp spawn_fx

; tower_think, in a stage with the Priest: IY = a defender about to fire.  A
; Priest next door halves tr_cd.  Uses A, BC, DE, HL; preserves IX, IY.
bless:
        ld a,(iy+T_TYPE)
        cp TT_PRIEST
        ret z
        ld a,TT_PRIEST
        ld (syn_loop+2),a
        ld d,(iy+T_COL)
        ld e,(iy+T_ROW)
        ld hl,towers
        ld b,MAX_TW
        call syn_loop           ; NZ: one is next door
        ret z
        ld hl,tr_cd
        srl (hl)
        ret
