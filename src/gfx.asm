;==============================================================================
; gfx.asm - line tables, draw targets, sprites, dirty rectangles, text
;==============================================================================

; line address tables: low bytes on one page, high bytes on the next
build_tables:
        ; playfield line -> screen #C000 + (y+PF_Y) address
        ld a,#ff
        ld (tgt_mask),a
        xor a
        ld (tgt_tab),a
        ld e,PF_Y
        ld bc,TAB_PF
.pf:    push bc
        ld d,0
        call line_addr
        pop bc
        ld a,l
        ld (bc),a
        inc b
        ld a,h
        ld (bc),a
        dec b
        inc c
        inc e
        ld a,e
        cp PF_Y+PF_H
        jr nz,.pf
        ; playfield line -> background buffer
        ld hl,TAB_BG
        ld de,BGBUF
        ld b,PF_H
.bg:    ld (hl),e
        inc h
        ld (hl),d
        dec h
        inc l
        push hl
        ld hl,80
        add hl,de
        ex de,hl
        pop hl
        djnz .bg
        ; sprite mask table: pen 0 pixels are transparent
        ld hl,MASKTAB
.m:     ld c,0
        ld a,l
        and #aa
        jr nz,.m1
        ld c,#aa
.m1:    ld a,l
        and #55
        jr nz,.m2
        ld a,c
        or #55
        ld c,a
.m2:    ld (hl),c
        inc l
        jr nz,.m
        ret

;------------------------------------------------------------------------------
; draw targets
;------------------------------------------------------------------------------
tgt_back:
        ld a,hi(TAB_PF)
        ld (tgt_tab),a
        ld a,(back_mask)
        ld (tgt_mask),a
        ret
tgt_bg:
        ld a,hi(TAB_BG)
        ld (tgt_tab),a
        ld a,#ff
        ld (tgt_mask),a
        ret
tgt_scr_a:
        ld a,#ff
        jr tgt_scr
tgt_scr_b:
        ld a,#7f
tgt_scr:
        ld (tgt_mask),a
        xor a
        ld (tgt_tab),a
        ret
; the screen currently displayed (title / end screens)
tgt_front:
        ld a,(back_mask)
        xor #80
        jr tgt_scr

; run the routine at HL once for each screen buffer
both_screens:
        ld (both_fn),hl
        call tgt_scr_a
        call .go
        call tgt_scr_b
.go:    ld hl,(both_fn)
        jp (hl)

; E = line, D = byte column -> HL = address in the current target.  Uses A.
line_addr:
        ld a,(tgt_tab)
        or a
        jr z,.scr
        ld h,a
        ld l,e
        ld a,(hl)
        inc h
        ld h,(hl)
        add a,d
        ld l,a
        jr nc,.n
        inc h
.n:     ld a,(tgt_mask)
        and h
        ld h,a
        ret
.scr:   push bc                 ; #C000 + (y>>3)*80 + (y&7)*#800 + x
        ld a,e
        and #f8
        ld l,a
        ld h,0
        add hl,hl
        ld b,h
        ld c,l
        add hl,hl
        add hl,hl
        add hl,bc
        ld a,e
        and 7
        add a,a
        add a,a
        add a,a
        add a,#c0
        add a,h
        ld h,a
        ld a,l
        add a,d
        ld l,a
        jr nc,.n2
        inc h
.n2:    pop bc
        ld a,(tgt_mask)
        and h
        ld h,a
        ret

;------------------------------------------------------------------------------
; sprites: w (1..4 bytes), h, then w*h bytes; pen 0 = transparent
;------------------------------------------------------------------------------
; HL = sprite, D = x (bytes), E = y; records a dirty rectangle
draw_sprite:
        ld c,(hl)
        inc hl
        ld b,(hl)
        inc hl
        call dirty_add
        ret c                   ; list full: skip rather than leave a trail
        jr draw_sprite_wh

draw_sprite_raw:
        ld c,(hl)
        inc hl
        ld b,(hl)
        inc hl
draw_sprite_wh:
        ld a,b
        exx
        ld b,a                  ; B' = rows left
        exx
        ex de,hl                ; DE = data, HL = x,y
        ld a,c                  ; entry = unroll + (4-w)*8
        neg
        add a,4
        add a,a
        add a,a
        add a,a
        ld bc,.unroll
        add a,c
        ld c,a
        jr nc,.n
        inc b
.n:     ld (.jp+1),bc
        ld a,(tgt_tab)          ; how to step to the next line
        cp hi(TAB_BG)
        ld bc,.nscr
        jr nz,.s
        ld bc,.nbg
.s:     ld (.nl+1),bc
        push de
        ex de,hl
        call line_addr          ; HL = first line
        pop de
.row:   push hl
        ld b,hi(MASKTAB)
.jp:    jp .unroll
.unroll:
        repeat 4
        ld a,(de)
        inc de
        ld c,a
        ld a,(bc)
        and (hl)
        or c
        ld (hl),a
        inc hl
        rend
        pop hl
.nl:    jp .nscr
.nscr:  ld a,h                  ; screen: +#800, wrapping to the next char row
        add a,8
        ld h,a
        and #38
        jr nz,.cnt
        ld a,l
        add a,80
        ld l,a
        ld a,h
        adc a,#c0
        ld h,a
        jr .cnt
.nbg:   ld bc,80                ; background buffer: linear
        add hl,bc
.cnt:   exx
        dec b
        exx
        jr nz,.row
        ret

;------------------------------------------------------------------------------
; dirty rectangle lists (one per screen buffer).  Entry: x, y, w, h
;------------------------------------------------------------------------------
dirty_reset:
        ld hl,dlist0
        ld (dl_cur_base),hl
        ld (dl_cur_ptr),hl
        ld hl,dlist1
        ld (dl_oth_base),hl
        ld (dl_oth_ptr),hl
        ret

; D,E,C,B = x,y,w,h.  Preserves everything but A.  Carry set if full.
dirty_add:
        push hl
        ld hl,(dl_cur_ptr)
        ld a,l
        cp DL_CAP*4
        jr nc,.full
        ld (hl),d
        inc hl
        ld (hl),e
        inc hl
        ld (hl),c
        inc hl
        ld (hl),b
        inc hl
        ld (dl_cur_ptr),hl
        pop hl
        or a
        ret
.full:  pop hl
        scf
        ret

dirty_add_both:
        call dirty_add
        push hl
        ld hl,(dl_oth_ptr)
        ld a,l
        cp DL_CAP*4
        jr nc,.full
        ld (hl),d
        inc hl
        ld (hl),e
        inc hl
        ld (hl),c
        inc hl
        ld (hl),b
        inc hl
        ld (dl_oth_ptr),hl
.full:  pop hl
        ret

; copy every rectangle of the back buffer's list from the background
restore_dirty:
        ld hl,(dl_cur_base)
.loop:  ld de,(dl_cur_ptr)
        ld a,l
        cp e
        jr nz,.go
        ld a,h
        cp d
        jr z,.done
.go:    ld d,(hl)
        inc hl
        ld e,(hl)
        inc hl
        ld c,(hl)
        inc hl
        ld b,(hl)
        inc hl
        push hl
        call mark_rect
        call restore_rect
        pop hl
        jr .loop
.done:  ld hl,(dl_cur_base)
        ld (dl_cur_ptr),hl
        ret

; D,E,C,B = x,y,w,h : stamp the 16x16 cells the rectangle covers (STAMPMAP,
; 10 x 11 cells, within one 256-byte page) so enemies underneath know they
; must be redrawn.  Preserves B,C,D,E.
mark_rect:
        push bc
        push de
        ld a,d
        rrca
        rrca
        rrca
        and 31
        ld l,a                  ; first column
        ld a,d
        add a,c
        dec a
        rrca
        rrca
        rrca
        and 31
        sub l
        inc a
        ld d,a                  ; columns
        ld a,e
        add a,b
        dec a
        and #f0
        ld c,a                  ; last row * 16
        ld a,e
        and #f0
        ld e,a                  ; first row * 16
        ld a,c
        sub e
        rrca
        rrca
        rrca
        rrca
        inc a
        ld b,a                  ; rows
        ld a,e
        rrca
        ld c,a                  ; first row * 8
        rrca
        rrca
        add a,c                 ; first row * 10
        add a,l
        add a,lo(STAMPMAP)
        ld l,a
        ld h,hi(STAMPMAP)
        ld a,10
        sub d
        ld e,a                  ; skip to the next row
        ld a,(stamp)
        ld c,a
.r:     ld a,d
.c:     ld (hl),c
        inc l
        dec a
        jr nz,.c
        ld a,l
        add a,e
        ld l,a
        djnz .r
        pop de
        pop bc
        ret

; D,E,C,B = x,y,w,h : background -> back buffer.  Rows of up to 8 bytes are
; copied by unrolled LDIs; with C = 255 and at most 255 bytes per call they
; never touch B, which counts the rows.  The steps to the next line are
; patched in.  Wider rectangles go in 8-byte strips.
restore_rect:
        ld a,c
        cp 9
        jr c,.narrow
        push bc
        push de
        ld a,8
        ld c,a
        call .narrow
        pop de
        pop bc
        ld a,d
        add a,8
        ld d,a
        ld a,c
        sub 8
        ld c,a
        jr restore_rect
.narrow:
        neg
        ld (.sstep+1),a         ; screen: back w bytes (and +#800 below)
        add a,80
        ld (.bstep+1),a         ; background: 80-w
        ld a,c
        neg
        add a,8
        add a,a                 ; LDI is 2 bytes
        ld hl,.ldi8
        add a,l
        ld l,a
        jr nc,.e
        inc h
.e:     ld (.loop+1),hl
        ld c,255
        ld l,e
        ld h,hi(TAB_PF)
        ld a,(hl)
        inc h
        ld h,(hl)
        add a,d
        ld l,a
        jr nc,.n1
        inc h
.n1:    ld a,(back_mask)
        and h
        ld h,a
        push hl
        ld l,e
        ld h,hi(TAB_BG)
        ld a,(hl)
        inc h
        ld h,(hl)
        add a,d
        ld l,a
        jr nc,.n2
        inc h
.n2:    pop de                  ; DE = screen, HL = background
.loop:  jp .ldi8
.ldi8:  repeat 8
        ldi
        rend
        ld a,l                  ; background: next line
.bstep: add a,0
        ld l,a
        adc a,h
        sub l
        ld h,a
        ld a,e                  ; screen: next line
.sstep: add a,0
        ld e,a
        ld a,d
        adc a,7
        ld d,a
        and #38
        jr z,.wrap
.next:  djnz .loop
        ret
.wrap:  ld a,e
        add a,80
        ld e,a
        ld a,d
        adc a,#c0
        ld d,a
        jr .next

; whole background -> both screens
bg_to_screens:
        ld e,0
.l:     push de
        ld l,e
        ld h,hi(TAB_BG)
        ld a,(hl)
        inc h
        ld h,(hl)
        ld l,a
        push hl
        ld l,e
        ld h,hi(TAB_PF)
        ld a,(hl)
        inc h
        ld d,(hl)
        ld e,a
        pop hl
        push hl
        push de
        ld bc,80
        ldir
        pop de
        res 7,d
        pop hl
        ld bc,80
        ldir
        pop de
        inc e
        ld a,e
        cp PF_H
        jr nz,.l
        ret

; D,E,C,B = x,y,w,h ; A = fill byte ; current target
fill_rect:
        ld (fill_val),a
.row:   push bc
        call line_addr
        ld a,(fill_val)
        ld b,c
.c:     ld (hl),a
        inc hl
        djnz .c
        pop bc
        inc e
        djnz .row
        ret

clear_screen_a:
        ld hl,#c000
        ld de,#c001
        ld bc,#3fff
        ld (hl),0
        ldir
        ret

;------------------------------------------------------------------------------
; text: 3x6 glyphs in 4x8 cells (or 8x16 when double width/height)
;------------------------------------------------------------------------------
; B = ink pen, C = paper pen
set_colors:
        ld d,0
        ld hl,pen_left
        ld e,b
        add hl,de
        ld b,(hl)
        ld hl,pen_left
        ld e,c
        add hl,de
        ld c,(hl)
        ld hl,txt_pairs
        ld a,c
        srl a
        or c
        ld (hl),a
        inc hl
        ld a,b
        srl a
        or c
        ld (hl),a
        inc hl
        ld a,c
        srl a
        or b
        ld (hl),a
        inc hl
        ld a,b
        srl a
        or b
        ld (hl),a
        ret

; D = column (0-39), E = line
set_at:
        ld a,d
        add a,a
        ld (txt_x),a
        ld a,e
        ld (txt_y),a
        ret

text_normal:
        xor a
        ld (txt_dw),a
        ld (txt_dh),a
        ret
text_big:
        ld a,1
        ld (txt_dw),a
        ld (txt_dh),a
        ret

; A = glyph
put_glyph:
        ld l,a
        ld h,0
        add hl,hl
        ld d,h
        ld e,l
        add hl,hl
        add hl,de
        ld de,font
        add hl,de
        ld (gl_ptr),hl
        ld a,(txt_y)
        ld e,a
        ld a,(txt_x)
        ld d,a
        call line_addr          ; HL = first line, stepped down from here
        ld a,(txt_dh)
        or a
        jr nz,.tall
        xor a
        call glyph_line
        ld b,6
.g:     push bc
        ld de,(gl_ptr)
        ld a,(de)
        inc de
        ld (gl_ptr),de
        call glyph_line
        pop bc
        djnz .g
        xor a
        call glyph_line
        jr .adv
.tall:  xor a
        call glyph_line
        xor a
        call glyph_line
        ld b,6
.t:     push bc
        ld de,(gl_ptr)
        ld a,(de)
        inc de
        ld (gl_ptr),de
        push af
        call glyph_line
        pop af
        call glyph_line
        pop bc
        djnz .t
        xor a
        call glyph_line
        xor a
        call glyph_line
.adv:   ld a,(txt_dw)
        or a
        ld a,(txt_x)
        jr z,.n
        add a,2
.n:     add a,2
        ld (txt_x),a
        ret

; A = 3 pixel bits ; HL = line address, moved to the next line
glyph_line:
        ld c,a
        push hl
        ld a,(txt_dw)
        or a
        jr nz,.wide
        ld a,c
        srl a
        call pair_byte
        ld (hl),a
        inc hl
        ld a,c
        and 1
        add a,a
        call pair_byte
        ld (hl),a
        jr next_line_pop
.wide:  ld b,3
.w:     ld a,c
        and 4
        ld a,0
        jr z,.off
        ld a,3
.off:   call pair_byte
        ld (hl),a
        inc hl
        sla c
        djnz .w
        xor a
        call pair_byte
        ld (hl),a
next_line_pop:
        pop hl
; HL -> same column on the next line of the current target
next_line:
        ld a,(tgt_tab)
        cp hi(TAB_BG)
        jr z,.bg
        ld a,h
        add a,8
        ld h,a
        and #38
        ret nz
        ld a,l
        add a,80
        ld l,a
        ld a,h
        adc a,#c0
        ld h,a
        ret
.bg:    ld a,l
        add a,80
        ld l,a
        ret nc
        inc h
        ret

pair_byte:
        push hl
        ld hl,txt_pairs
        add a,l
        ld l,a
        jr nc,.n
        inc h
.n:     ld a,(hl)
        pop hl
        ret

; HL = string (#FE newline, #FF end; codes >= NUM_GLYPHS are byte pairs)
print_str:
        ld a,(txt_x)
        ld (txt_x0),a
.l:     ld a,(hl)
        inc hl
        cp #ff
        ret z
        cp #fe
        jr nz,.c
        ld a,(txt_x0)
        ld (txt_x),a
        ld a,(txt_dh)
        or a
        ld a,(txt_y)
        jr z,.s
        add a,8
.s:     add a,8
        ld (txt_y),a
        jr .l
.c:     push hl
        call print_code
        pop hl
        jr .l

print_code:
        cp NUM_GLYPHS
        jp c,put_glyph
        call pair_ptr
        ld a,(hl)
        inc hl
        push hl
        call print_code
        pop hl
        ld a,(hl)
        jr print_code

; A = pair code -> HL
pair_ptr:
        sub NUM_GLYPHS
        ld l,a
        ld h,0
        add hl,hl
        ld de,pair_table
        add hl,de
        ret

; A = string id -> HL
get_str:
        ld l,a
        ld h,0
        add hl,hl
        ld a,(lang)
        or a
        ld de,strtab_en
        jr z,.e
        ld de,strtab_gr
.e:     add hl,de
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        ret

print_id:
        call get_str
        jp print_str

; A = string id ; E = line : print centred (first line length)
print_id_centered:
        push de
        call get_str
        pop de
        push hl
        call str_len
        ld a,(txt_dw)
        or a
        ld a,40
        jr z,.n
        ld a,20
.n:     sub c
        srl a
        ld d,a
        ld a,(txt_dw)
        or a
        ld a,d
        jr z,.n2
        add a,a
.n2:    add a,a
        ld (txt_x),a
        ld a,e
        ld (txt_y),a
        pop hl
        jp print_str

; HL = string -> C = length of first line
str_len:
        push de
        push hl
        ld c,0
.l:     ld a,(hl)
        inc hl
        cp #fe
        jr nc,.d
        push hl
        call len_code
        pop hl
        jr .l
.d:     pop hl
        pop de
        ret

len_code:
        cp NUM_GLYPHS
        jr nc,.p
        inc c
        ret
.p:     call pair_ptr
        ld a,(hl)
        inc hl
        push hl
        call len_code
        pop hl
        ld a,(hl)
        jr len_code

; HL = value, A = digits ; pn_zero != 0 pads with zeros
print_num:
        ld (pn_cnt),a
        ld e,a
        ld a,5
        sub e
        add a,a
        ld e,a
        ld d,0
        ld ix,pow10
        add ix,de
        ld a,(pn_zero)
        ld (pn_nz),a
.d:     ld e,(ix+0)
        ld d,(ix+1)
        inc ix
        inc ix
        ld c,0
.s:     or a
        sbc hl,de
        jr c,.u
        inc c
        jr .s
.u:     add hl,de
        ld a,(pn_cnt)
        cp 1
        jr z,.show
        ld a,c
        or a
        jr nz,.show
        ld a,(pn_nz)
        or a
        jr nz,.show
        xor a
        jr .put
.show:  ld a,1
        ld (pn_nz),a
        ld a,c
        add a,GLYPH_0
.put:   push hl
        push ix
        call put_glyph
        pop ix
        pop hl
        ld a,(pn_cnt)
        dec a
        ld (pn_cnt),a
        jr nz,.d
        ret

pow10:  dw 10000,1000,100,10,1
