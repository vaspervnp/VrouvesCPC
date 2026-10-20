;==============================================================================
; hiscore.asm - the high score table, part of the title overlay (disk only).
; HISCORE.BIN, one sector on the disk: "VRV1", then 8 entries of a 3 letter
; name (glyph codes) and a score.  It is read whenever the title shows; after
; a game good enough for it, the player enters a name and the sector is
; written back.
;==============================================================================
HS_BUF  equ #B000               ; the sector, in the background buffer (free here)
HS_ENT  equ HS_BUF+4
HS_N    equ 8
HS_PAGE equ 4                   ; its title page

hs_desc:
        db DISK_HISCORE_TRACK,DISK_HISCORE_SECTOR,1
        dw HS_BUF

; the table from the disk; the one built in if the sector holds no table
hs_load:
        ld hl,hs_desc
        call disk_load
        ld hl,HS_BUF
        ld de,hs_default
        ld b,4
.c:     ld a,(de)
        cp (hl)
        jr nz,.bad
        inc hl
        inc de
        djnz .c
        ret
.bad:   ld hl,hs_default
        ld de,HS_BUF
        ld bc,4+HS_N*5
        ldir
        ret

; with the title on screen: a game just ended with a score for the table?
hs_check:
        ld a,#ff
        ld (hs_new),a
        ld de,(score)
        ld hl,0
        ld (score),hl           ; looked at once only
        ld hl,(HS_ENT+(HS_N-1)*5+3)
        or a
        sbc hl,de               ; carry: better than the last one
        ret nc
        ld (hs_score),de
        call hs_name
        call hs_insert
        call hs_write
        ld a,HS_PAGE
        ld (tpage),a
        jp title_page

; the name, three letters: UP / DOWN pick, FIRE / RIGHT next, LEFT back
hs_name:
        xor a
        ld (hs_pos),a
        ld hl,hs_idx
        ld (hl),a
        inc hl
        ld (hl),a
        inc hl
        ld (hl),a
        call tgt_scr_a
        ld de,40
        ld bc,128*256+80
        xor a
        call fill_rect
        call text_normal
        ld bc,#0800
        call set_colors
        ld hl,tr_newhs_en
        ld bc,tr_newhs_gr
        ld e,52
        call raw_center
        call text_big
        ld de,15*256+66
        call set_at
        ld hl,(hs_score)
        ld a,5
        call print_num
        call text_normal
        ld bc,#0500
        call set_colors
        ld hl,tr_name_en
        ld bc,tr_name_gr
        ld e,96
        call raw_center
        ld bc,#0700
        call set_colors
        ld hl,tr_keys_en
        ld bc,tr_keys_gr
        ld e,150
        call raw_center
.draw:  call text_big
        ld b,0                  ; the three letters, the one being picked in yellow
.d:     push bc
        ld a,b
        add a,a
        add a,17
        ld d,a
        ld e,114
        call set_at
        pop bc
        push bc
        ld a,(hs_pos)
        cp b
        ld bc,#0500
        jr nz,.w
        ld b,#08
.w:     call set_colors
        pop bc
        push bc
        ld hl,hs_idx
        ld a,l
        add a,b
        ld l,a
        jr nc,.i
        inc h
.i:     ld a,(hl)
        call name_glyph
        call put_glyph
        pop bc
        inc b
        ld a,b
        cp 3
        jr nz,.d
        call text_normal
.l:     call wait_frame
        call kbd_update
        ld a,K_UP
        call key_hit
        jr c,.up
        ld a,J_UP
        call key_hit
        jr c,.up
        ld a,K_DOWN
        call key_hit
        jr c,.dn
        ld a,J_DOWN
        call key_hit
        jr c,.dn
        ld a,K_LEFT
        call key_hit
        jr c,.lf
        ld a,J_LEFT
        call key_hit
        jr c,.lf
        ld a,K_RIGHT
        call key_hit
        jr c,.nx
        ld a,J_RIGHT
        call key_hit
        jr c,.nx
        call fire_hit
        jr nc,.l
.nx:    ld a,SFX_BUILD
        call sfx_play
        ld hl,hs_pos
        inc (hl)
        ld a,(hl)
        cp 3
        jp nz,.draw
        ret
.lf:    ld hl,hs_pos
        ld a,(hl)
        or a
        jr z,.l
        dec (hl)
        jp .draw
.up:    call .cur
        dec (hl)
        jp p,.snd
        ld (hl),NAME_NCHARS-1
        jr .snd
.dn:    call .cur
        inc (hl)
        ld a,(hl)
        cp NAME_NCHARS
        jr c,.snd
        ld (hl),0
.snd:   ld a,SFX_MOVE
        call sfx_play
        jp .draw
.cur:   ld hl,hs_idx            ; HL = the letter being picked
        ld a,(hs_pos)
        add a,l
        ld l,a
        ret nc
        inc h
        ret

; A = index into name_chars -> A = glyph
name_glyph:
        ld hl,name_chars
        add a,l
        ld l,a
        jr nc,.n
        inc h
.n:     ld a,(hl)
        ret

; the new entry into the table, the ones below it down a place
hs_insert:
        ld hl,HS_ENT+3          ; find its place: before the first lower score
        ld b,0
.f:     ld e,(hl)
        inc hl
        ld d,(hl)
        push hl
        ld hl,(hs_score)
        or a
        sbc hl,de               ; NC: not lower than this one... carry: lower
        pop hl
        jr z,.n                 ; a tie stays below
        jr nc,.got
.n:     inc hl
        inc hl
        inc hl
        inc hl
        inc b
        ld a,b
        cp HS_N
        jr nz,.f
        ret
.got:   ld a,b
        ld (hs_new),a
        ld c,a                  ; DE = its entry
        add a,a
        add a,a
        add a,c
        ld e,a
        ld d,0
        ld hl,HS_ENT
        add hl,de
        push hl
        ld a,HS_N-1             ; move (HS_N-1-place) entries down by 5
        sub b
        jr z,.put
        ld b,a                  ; bytes = entries * 5
        add a,a
        add a,a
        add a,b
        ld c,a
        ld b,0
        ld hl,HS_ENT+(HS_N-1)*5-1
        ld de,HS_ENT+HS_N*5-1
        lddr
.put:   pop de
        ld hl,hs_idx
        ld b,3
.p:     ld a,(hl)
        push hl
        call name_glyph
        pop hl
        ld (de),a
        inc hl
        inc de
        djnz .p
        ld hl,(hs_score)
        ex de,hl
        ld (hl),e
        inc hl
        ld (hl),d
        ret

; the sector back to the disk (a write protected disk: nothing saved)
hs_write:
        ld bc,FDC_MOTOR
        ld a,1
        out (c),a
        ld b,30                 ; the motor gets up to speed
.sp:    push bc
        call wait_frame
        pop bc
        djnz .sp
        ld a,7                  ; recalibrate, then seek
        call fdc_out
        xor a
        call fdc_out
        call fdc_wait_seek
        ld a,#0f
        call fdc_out
        xor a
        call fdc_out
        ld a,DISK_HISCORE_TRACK
        call fdc_out
        call fdc_wait_seek
        ld hl,hs_wcmd
        ld b,9
.c:     ld a,(hl)
        inc hl
        push bc
        call fdc_out
        pop bc
        djnz .c
        ld hl,HS_BUF
        ld bc,FDC_MSR
        di                      ; a byte every 32 microseconds
.x:     in a,(c)
        jp p,.x
        and #20
        jr z,.done
        inc c
        ld a,(hl)
        out (c),a
        dec c
        inc hl
        jp .x
.done:  ei
        call fdc_results
        ld bc,FDC_MOTOR
        xor a
        out (c),a
        ret

; MFM write data, drive 0: C H R N EOT GPL DTL
hs_wcmd:
        db #45,0,DISK_HISCORE_TRACK,0,DISK_HISCORE_SECTOR,2,DISK_HISCORE_SECTOR,#2a,#ff

; the title page with the table; the newest entry in yellow
hs_show:
        ld bc,#0800
        call set_colors
        ld hl,tr_hshdr_en
        ld bc,tr_hshdr_gr
        ld e,43
        call raw_center
        ld hl,HS_ENT
        ld b,0
.r:     push bc
        push hl
        ld a,(hs_new)
        cp b
        ld bc,#0500
        jr nz,.c
        ld b,#08
.c:     call set_colors
        pop hl
        pop bc
        push bc
        push hl
        ld a,b                  ; the line: 58 + 13 * place
        add a,a
        add a,b
        add a,a
        add a,a
        add a,b
        add a,58
        ld e,a
        ld d,11
        push de
        call set_at
        pop de
        pop hl
        pop bc
        push bc
        push de
        push hl
        ld l,b                  ; the place
        inc l
        ld h,0
        ld a,1
        call print_num
        pop hl
        pop de
        push de
        ld d,15
        call set_at
        ld de,hs_tmp            ; the name, with an end mark
        ld bc,3
        ldir
        push hl
        ld hl,hs_tmp
        call print_str
        pop hl
        pop de
        ld d,22
        push hl
        call set_at
        pop hl
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        push hl
        ex de,hl
        ld a,5
        call print_num
        pop hl
        pop bc
        inc b
        ld a,b
        cp HS_N
        jr nz,.r
        ret

; HL = english, BC = greek text (glyph codes), E = line: centred
raw_center:
        ld a,(lang)
        or a
        jr z,.e
        ld h,b
        ld l,c
.e:     push hl
        push de
        call str_len
        pop de
        ld a,40
        sub c
        and #fe
        ld (txt_x),a
        ld a,e
        ld (txt_y),a
        pop hl
        jp print_str

hs_new:   db #ff                ; the place of the newest entry (#FF none)
hs_pos:   db 0
hs_idx:   db 0,0,0
hs_score: dw 0
hs_tmp:   db 0,0,0,#ff
