;==============================================================================
; shepherd.asm - the Shepherd (stages 10-20): a sling with the longest reach,
; drones too; a stone that hits a guard throws him back along the road.  In
; the Lyra area (lyra.asm), like the Priest.
;==============================================================================
KNOCK_STEPS equ 8               ; path steps

; proj_step, a stone hitting IX: a guard is thrown back the way he
; came (KNOCK_STEPS), never behind where he started.  Preserves A; uses BC, DE, HL.
knockback:
        push af
        ld a,(ix+E_TYPE)
        cp ET_GUARD
        jr nz,.done
        ld b,KNOCK_STEPS
.st:    ld a,(ix+E_PROG)
        or (ix+E_PROG+1)
        jr z,.done              ; at the start of his road
        push bc
        call enemy_seg          ; HL = the segment: dx, dy, steps
        inc hl
        inc hl
        ld a,(ix+E_REM)
        cp (hl)
        jr c,.in
        dec (ix+E_SEG)          ; at its start: back into the one before
        ld (ix+E_REM),0
        call enemy_seg
        inc hl
        inc hl
.in:    inc (ix+E_REM)
        dec hl
        ld a,(ix+E_Y)           ; enemy_step backwards
        sub (hl)
        ld (ix+E_Y),a
        dec hl
        ld a,(ix+E_SUB)
        sub 1
        jr nc,.s
        ld a,(ix+E_X)
        sub (hl)
        ld (ix+E_X),a
        ld a,2
.s:     ld (ix+E_SUB),a
        ld a,(ix+E_PROG)
        sub 1
        ld (ix+E_PROG),a
        jr nc,.p
        dec (ix+E_PROG+1)
.p:     pop bc
        djnz .st
.done:  pop af
        ret
