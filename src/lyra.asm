;==============================================================================
; lyra.asm - the Lyra player (stages 8-10).  His tune reaches every invader
; around him, walkers and drones alike (armour counts), and charms the drones
; into slowing down.  Not resident: it lives in the Lyra area at the top of
; the stage files that have him, with his picture, sound and texts.
;==============================================================================
; tower_think, with a target in reach: IY = tower, tr_* its stats
fire_lyra:
        ld a,2                  ; notes over two of them at most
        ld (tmp_idx),a
        ld ix,enemies
        ld b,MAX_EN
.l:     push bc
        ld a,(ix+E_TYPE)
        or a
        jr z,.n
        call in_range
        jr nc,.n
        ld a,(ix+E_TYPE)
        cp ET_DRONE
        jr nz,.w
        ld (ix+E_SLOW),30
.w:     ld a,(tmp_idx)
        or a
        jr z,.nofx
        dec a
        ld (tmp_idx),a
        ld d,(ix+E_X)
        ld e,(ix+E_Y)
        ld a,FX_NOTE
        call spawn_fx
.nofx:  ld a,(tr_dmg)
        ld c,0
        call damage_enemy
.n:     ld de,EN_SZ
        add ix,de
        pop bc
        djnz .l
        ret
