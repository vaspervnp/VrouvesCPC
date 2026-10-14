;==============================================================================
; hw.asm - hardware: gate array, CRTC, interrupts, keyboard, AY sound
;==============================================================================

hw_init:
        ld bc,#f782             ; PPI: A out, B in, C out
        out (c),c
        ld bc,#7f8c             ; mode 0, both ROMs off
        out (c),c
        call set_palette
        ld bc,#7f10             ; border
        out (c),c
        ld a,#54                ; black
        out (c),a
        ld a,#ff                ; showing #C000
        ld (back_mask),a
        call show_back
        ld bc,#bc0d
        out (c),c
        ld bc,#bd00
        out (c),c
        ret

set_palette:
        ld hl,palette_hw
        ld e,0
.l:     ld bc,#7f00
        out (c),e
        ld a,(hl)
        out (c),a
        inc hl
        inc e
        ld a,e
        cp 16
        jr nz,.l
        ret

; all pens black (used while screens are rebuilt)
palette_black:
        ld e,0
.l:     ld bc,#7f00
        out (c),e
        ld a,#54
        out (c),a
        inc e
        ld a,e
        cp 16
        jr nz,.l
        ret

; point the CRTC at the buffer selected by back_mask (#FF = #C000, #7F = #4000)
show_back:
        ld bc,#bc0c
        out (c),c
        ld a,(back_mask)
        inc a
        ld a,#30
        jr z,.s
        ld a,#10
.s:     ld b,#bd
        out (c),a
        ret

; wait for the next frame (vsync)
wait_frame:
        ld a,(framecnt)
        ld b,a
.w:     ld a,(framecnt)
        cp b
        jr z,.w
        ret

; show the back buffer, wait so we run at most 25 fps, swap buffers
flip:
        call show_back
        call wait_frame                 ; the new screen is latched at frame start
.w2:    ld a,(last_flip)
        ld b,a
        ld a,(framecnt)
        sub b
        cp 2
        jr c,.w2
        ld a,(framecnt)
        ld (last_flip),a
        ld a,(back_mask)
        xor #80
        ld (back_mask),a
        ld hl,(dl_cur_base)
        ld de,(dl_oth_base)
        ld (dl_cur_base),de
        ld (dl_oth_base),hl
        ld hl,(dl_cur_ptr)
        ld de,(dl_oth_ptr)
        ld (dl_cur_ptr),de
        ld (dl_oth_ptr),hl
        ret

;------------------------------------------------------------------------------
; interrupt: 300 Hz; work only on the one that follows VSYNC
;------------------------------------------------------------------------------
int_handler:
        push af
        push bc
        push de
        push hl
        push iy
        ld b,#f5
        in a,(c)
        rra
        jr nc,.out
        ld hl,framecnt
        inc (hl)
        call snd_update
        call kbd_scan
.out:   pop iy
        pop hl
        pop de
        pop bc
        pop af
        ei
        ret

kbd_scan:
        ld bc,#f40e
        out (c),c
        ld bc,#f6c0
        out (c),c
        ld bc,#f600
        out (c),c
        ld bc,#f792
        out (c),c
        ld hl,keys
        ld a,#40
.l:     ld b,#f6
        out (c),a
        ld b,#f4
        in d,(c)
        ld (hl),d               ; live state
        ld e,a
        push hl
        ld bc,10
        add hl,bc
        ld a,(hl)               ; latch: remembers presses until read
        and d
        ld (hl),a
        pop hl
        ld a,e
        inc hl
        inc a
        cp #4a
        jr nz,.l
        ld bc,#f782
        out (c),c
        ld bc,#f600
        out (c),c
        ret

; A = AY register, C = value.  Uses A, B.
psg_write:
        ld b,#f4
        out (c),a
        ld b,#f6
        ld a,#c0
        out (c),a
        xor a
        out (c),a
        ld b,#f4
        out (c),c
        ld b,#f6
        ld a,#80
        out (c),a
        xor a
        out (c),a
        ret

;------------------------------------------------------------------------------
; keyboard helpers (main loop side)
;------------------------------------------------------------------------------
kbd_update:
        ld hl,kcur
        ld de,kold
        ld bc,10
        ldir
        di
        ld hl,keys+10           ; latched presses since the last update
        ld de,kcur
        ld bc,10
        ldir
        ld hl,keys
        ld de,keys+10
        ld bc,10
        ldir
        ei
        ret

; HL = matrix, A = key code (line*8+bit) -> carry set if pressed
key_test:
        push bc
        ld c,a
        rrca
        rrca
        rrca
        and 15
        add a,l
        ld l,a
        jr nc,.n
        inc h
.n:     ld a,c
        and 7
        inc a
        ld b,a
        ld a,(hl)
.r:     rrca
        djnz .r
        ccf
        pop bc
        ret

key_down:
        push hl
        ld hl,kcur
        call key_test
        pop hl
        ret

; pressed now but not on the previous frame
key_hit:
        push af
        call key_down
        jr nc,.no
        pop af
        push hl
        ld hl,kold
        call key_test
        pop hl
        ccf
        ret
.no:    pop af
        or a
        ret

; any of the "fire" keys hit?
fire_hit:
        ld a,K_SPACE
        call key_hit
        ret c
        ld a,K_RETURN
        call key_hit
        ret c
        ld a,K_ENTER
        call key_hit
        ret c
        ld a,K_COPY
        call key_hit
        ret c
        ld a,J_FIRE1
        call key_hit
        ret c
        ld a,J_FIRE2
        jp key_hit

;------------------------------------------------------------------------------
; sound: two music channels (A melody, B bass) + effects on channel C
;------------------------------------------------------------------------------
C_PTR   equ 0
C_START equ 2
C_DUR   equ 4
C_VOL   equ 5
C_PREG  equ 6
C_VREG  equ 7
C_VSTART equ 8
C_VMIN  equ 9
C_NOTES equ 10
C_SIZE  equ 12

snd_init:
        di
        xor a
        ld (sfx_active),a
        ld hl,chan_init
        ld de,chan_a
        ld bc,C_SIZE*2
        ldir
        ld a,1
        ld (chan_a+C_DUR),a
        ld (chan_b+C_DUR),a
        ld a,7
        ld c,#3c
        call psg_write
        ei
        ret

chan_init:
        dw music_a,music_a
        db 1,0,0,8,13,9
        dw music_a_notes
        dw music_b,music_b
        db 1,0,2,9,12,7
        dw music_b_notes

snd_update:
        ld a,(mus_on)
        or a
        jr nz,.mus
        ld a,8
        ld c,0
        call psg_write
        ld a,9
        ld c,0
        call psg_write
        jr .fx
.mus:   ld iy,chan_a
        call mus_chan
        ld iy,chan_b
        call mus_chan
.fx:    jp sfx_update

mus_chan:
        dec (iy+C_DUR)
        jr nz,.decay
        ld l,(iy+C_PTR)
        ld h,(iy+C_PTR+1)
        ld a,(hl)
        cp #ff
        jr nz,.got
        ld l,(iy+C_START)
        ld h,(iy+C_START+1)
        ld a,(hl)
.got:   inc hl
        ld (iy+C_PTR),l
        ld (iy+C_PTR+1),h
        ld c,a                  ; note in high nibble, duration index in low
        and 15
        ld e,a
        ld d,0
        ld hl,music_durs
        add hl,de
        ld a,(hl)
        ld (iy+C_DUR),a
        ld a,c
        rrca
        rrca
        rrca
        rrca
        and 15
        jr z,.rest
        add a,a
        ld e,a
        ld d,0
        ld l,(iy+C_NOTES)
        ld h,(iy+C_NOTES+1)
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld a,(iy+C_PREG)
        ld c,e
        call psg_write
        ld a,(iy+C_PREG)
        inc a
        ld c,d
        call psg_write
        ld a,(iy+C_VSTART)
        ld (iy+C_VOL),a
        jr .setvol
.rest:  xor a
        ld (iy+C_VOL),a
        jr .setvol
.decay: ld a,(framecnt)
        and 3
        ret nz
        ld a,(iy+C_VOL)
        cp (iy+C_VMIN)
        ret z
        ret c
        dec a
        ld (iy+C_VOL),a
.setvol:
        ld c,(iy+C_VOL)
        ld a,(iy+C_VREG)
        jp psg_write

; A = effect number
sfx_play:
        push hl
        push de
        push bc
        ld e,a
        ld d,0
        ld hl,sfx_prio
        add hl,de
        ld c,(hl)
        ld a,(sfx_active)
        or a
        jr z,.ok
        ld a,(sfx_cur_prio)
        cp c
        jr z,.ok
        jr nc,.skip
.ok:    ld a,c
        ld (sfx_cur_prio),a
        ld hl,sfx_table
        add hl,de
        add hl,de
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        di
        ld (sfx_ptr),hl
        ld a,1
        ld (sfx_active),a
        ei
.skip:  pop bc
        pop de
        pop hl
        ret

sfx_update:
        ld a,(sfx_active)
        or a
        jr z,.silent
        ld hl,(sfx_ptr)
        ld a,(hl)
        cp #ff
        jr z,.end
        inc hl
        ld c,a
        ld a,10
        call psg_write
        ld a,(hl)
        inc hl
        ld (sfx_noise),a
        or a
        jr z,.nn
        ld c,a
        ld a,6
        call psg_write
.nn:    ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld (sfx_ptr),hl
        ld c,e
        ld a,4
        call psg_write
        ld c,d
        ld a,5
        call psg_write
        ld c,#38
        ld a,d
        or e
        jr nz,.t
        set 2,c
.t:     ld a,(sfx_noise)
        or a
        jr z,.m
        res 5,c
.m:     ld a,7
        jp psg_write
.end:   xor a
        ld (sfx_active),a
.silent:
        ld c,0
        ld a,10
        call psg_write
        ld c,#3c
        ld a,7
        jp psg_write
