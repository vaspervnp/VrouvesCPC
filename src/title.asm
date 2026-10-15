;==============================================================================
; title.asm - title screen: scene and keys, story, defenders, invaders
;==============================================================================
TITLE_PAGE_FRAMES equ 450

title_screen:
        call palette_black
        ld a,#ff
        ld (back_mask),a
        call show_back
        call clear_screen_a
        call title_static
        xor a
        ld (tpage),a
        call title_page
        call set_palette
        ld hl,0
        ld (ttimer),hl
.loop:  call wait_frame
        call kbd_update
        ld a,K_L
        call key_hit
        jr nc,.nl
        ld a,(lang)
        xor 1
        ld (lang),a
        call title_static
        call title_page
.nl:    ld a,K_M
        call key_hit
        call c,toggle_music
        ld a,K_RIGHT
        call key_hit
        jr c,.next
        ld a,J_RIGHT
        call key_hit
        jr c,.next
        call fire_hit
        ret c
        ld hl,(ttimer)
        inc hl
        ld (ttimer),hl
        ld de,TITLE_PAGE_FRAMES
        or a
        sbc hl,de
        jr c,.loop
.next:  ld hl,0
        ld (ttimer),hl
        ld a,(tpage)
        inc a
        cp 4
        jr c,.p
        xor a
.p:     ld (tpage),a
        call title_page
        jr .loop

title_static:
        call tgt_scr_a
        ld de,0
        ld bc,40*256+80
        xor a
        call fill_rect
        ld de,168
        ld bc,32*256+80
        xor a
        call fill_rect
        ld de,37
        ld bc,2*256+80
        ld a,PENBYTE_2
        call fill_rect
        ld de,168
        ld bc,2*256+80
        ld a,PENBYTE_2
        call fill_rect
        call text_big
        ld bc,#0800
        call set_colors
        ld a,S_TITLE             ; in the active language only
        ld e,10
        call print_id_centered
        call text_normal
        ld bc,#0800
        call set_colors
        ld a,T_START
        ld e,172
        call print_id_centered
        ld bc,#0500
        call set_colors
        ld a,S_LANGHINT
        ld e,181
        call print_id_centered
        ld bc,#0400
        call set_colors
        ld a,T_CREDIT
        ld e,190
        jp print_id_centered

title_page:
        call tgt_scr_a
        ld de,40
        ld bc,128*256+80
        xor a
        call fill_rect
        call text_normal
        ld a,(tpage)
        or a
        jp z,.keys
        dec a
        jp z,.story
        dec a
        jr z,.def
        ld bc,#0900
        call set_colors
        ld a,T_ENEHDR
        ld e,43
        call print_id_centered
        ld hl,inv_list
        jr .cast
.def:   ld bc,#0800
        call set_colors
        ld a,T_DEFHDR
        ld e,43
        call print_id_centered
        ld hl,def_list
.cast:  ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld a,d
        or e
        ret z
        ld a,(hl)
        inc hl
        ld (tmp_i),a
        ld a,(hl)
        inc hl
        ld (tmp_y),a
        push hl
        push de
        ld d,3                  ; a patch of grass behind the sprite
        ld a,(tmp_y)
        dec a
        ld e,a
        ld bc,14*256+6
        ld a,PENBYTE_1
        call fill_rect
        pop hl
        ld d,4
        ld a,(tmp_y)
        ld e,a
        call draw_sprite_raw
        ld d,5
        ld a,(tmp_y)
        ld e,a
        call set_at
        ld bc,#0500
        call set_colors
        ld a,(tmp_i)
        call print_id
        pop hl
        jr .cast
.keys:  call title_art_draw
        ld bc,#0500
        call set_colors
        ld de,12*256+108
        call set_at
        ld a,T_CTRL
        call print_id
        ld de,30*256+108
        call set_at
        ld a,T_CTRL2
        jp print_id
.story: ld bc,#0500
        call set_colors
        ld de,46
        call set_at
        ld a,T_STORY
        jp print_id

; unpack title_art (gen/title_art.asm) onto lines 40-167 of screen A, line
; by line: 1..127 = that many bytes follow, 129..255 = the next byte n-128
; times, 128 = end of the line, 0 = end
title_art_draw:
        ld hl,title_art
        ld a,40
.line:  ld (tmp_y),a
        push hl
        ld e,a
        ld d,0
        call line_addr
        ex de,hl                ; DE = screen
        pop hl
.tok:   ld a,(hl)
        inc hl
        or a
        ret z
        jp m,.run
        ld c,a
        ld b,0
        ldir
        jr .tok
.run:   and #7f
        jr z,.nl
        ld b,a
        ld a,(hl)
        inc hl
.rep:   ld (de),a
        inc de
        djnz .rep
        jr .tok
.nl:    ld a,(tmp_y)
        inc a
        jr .line

def_list:
        dw spr_cretan
        db T_CAST1,54
        dw spr_yiayia
        db T_CAST2,73
        dw spr_bride
        db T_CAST3,92
        dw spr_psssst
        db T_CAST4,111
        dw spr_cauldron
        db T_CAST5,130
        dw spr_baker
        db T_CAST6,149
        dw 0

inv_list:
        dw spr_drone_a
        db T_ENE1,58
        dw spr_guard_a
        db T_ENE2,80
        dw spr_tank_va
        db T_ENE3,102
        dw 0
