;==============================================================================
; game.asm - Stage 01: The Kafenio
;==============================================================================

; enemy record (16 bytes)
E_TYPE  equ 0
E_HP    equ 1
E_MAXHP equ 2
E_ARM   equ 3
E_SPD   equ 4           ; path steps per frame * 16
E_ACC   equ 5
E_PROG  equ 6           ; 16 bit: steps walked (for "first" targeting)
E_X     equ 8
E_Y     equ 9
E_SLOW  equ 10
E_ANIM  equ 11
E_GEN   equ 12
E_SEG   equ 13
E_REM   equ 14
E_SUB   equ 15
EN_SZ   equ 16
MAX_EN  equ 16

ET_DRONE equ 1
ET_GUARD equ 2
ET_TANK  equ 3

; tower record (8 bytes)
T_TYPE  equ 0
T_COL   equ 1
T_ROW   equ 2
T_CD    equ 3
T_CX    equ 4
T_CY    equ 5
T_DIS   equ 6
TW_SZ   equ 8
MAX_TW  equ 32

TT_CRETAN equ 1
TT_YIAYIA equ 2
TT_BRIDE  equ 3
TT_PSSSST equ 4
TT_CAULDRON equ 5
TT_BAKER  equ 6

; projectile record (10 bytes)
P_TYPE  equ 0
P_X     equ 1           ; Mode 0 pixels
P_Y     equ 2
P_TGT   equ 3
P_DMG   equ 4
P_FLAG  equ 5           ; bit0 critical, bit7 target lost
P_TX    equ 6
P_TY    equ 7
P_GEN   equ 8
PR_SZ   equ 10
MAX_PR  equ 20

PT_BULLET equ 1
PT_PISTOL equ 2
PT_LASER  equ 3
PT_DAKOS  equ 4

; effect record (4 bytes)
F_TYPE  equ 0
F_X     equ 1
F_Y     equ 2
F_T     equ 3
FX_SZ   equ 4
MAX_FX  equ 12

FX_SPARK equ 1
FX_PUFF  equ 2
FX_BASH  equ 3
FX_POOF  equ 4
FX_BOOM  equ 5
FX_ZAP   equ 6

HUDF_WAVE   equ 1
HUDF_INFO   equ 2
HUDF_STATUS equ 4
HUDF_FUNDS  equ 8
HUDF_HP     equ 16

        if DEBUG
START_FUNDS equ 3000
        else
START_FUNDS equ 120
        endif
FIRST_COUNTDOWN equ 45
NEXT_COUNTDOWN equ 15

;------------------------------------------------------------------------------
; data tables
;------------------------------------------------------------------------------
; enemy types: base hp, hp per wave, speed, armour, reward, base damage, air, -
etype_tab:
        db 6,3,20,0,3,4,1,0             ; bio-drone
        db 16,8,9,2,4,8,0,0             ; compliance guard
        db 50,19,7,4,10,20,0,0          ; weed destroyer (tank)

; towers: cost, range, cooldown, damage, flags (bit0 hits air), projectile, sfx, sell
ttype_tab:
        db 30,30,18,6,1,PT_BULLET,SFX_RIFLE,15          ; cretan
        db 50,18,22,14,0,0,SFX_BASH,25                  ; yiayia
        db 70,28,6,4,1,PT_PISTOL,SFX_PISTOL,35          ; bride
        db 80,36,10,5,1,PT_LASER,SFX_LASER,40           ; psssst
        db 110,22,32,8,0,0,SFX_PUFF,55                  ; cauldron
        db 60,34,36,16,1,PT_DAKOS,SFX_THROW,30          ; baker

tower_sprites:
        dw spr_cretan,spr_yiayia,spr_bride,spr_psssst,spr_cauldron,spr_baker

; per enemy type, per direction (down, left, right), two frames
enemy_sprites:
        dw spr_drone_a,spr_drone_b,spr_drone_a,spr_drone_b,spr_drone_a,spr_drone_b
        dw spr_guard_a,spr_guard_b,spr_guard_la,spr_guard_lb,spr_guard_a,spr_guard_b
        dw spr_tank_va,spr_tank_vb,spr_tank_la,spr_tank_lb,spr_tank_ra,spr_tank_rb

proj_sprites:
        dw spr_bullet,spr_pistol,spr_laser,spr_dakos
; x speed (pixels), y speed (lines)
proj_speed:
        db 6,9, 7,10, 10,15, 3,5

; effects: frame a, frame b, lifetime (8 bytes each)
fx_tab:
        dw spr_spark_a,spr_spark_b
        db 6,0,0,0
        dw spr_puff_a,spr_puff_b
        db 12,0,0,0
        dw spr_bash_a,spr_bash_b
        db 8,0,0,0
        dw spr_poof_a,spr_poof_b
        db 10,0,0,0
        dw spr_boom_a,spr_boom_b
        db 12,0,0,0
        dw spr_zap_a,spr_spark_b
        db 6,0,0,0

sel_keys:
        db K_1,K_2,K_3,K_4,K_5,K_6

;------------------------------------------------------------------------------
; main game loop
;------------------------------------------------------------------------------
game_run:
        call game_init
.loop:  call kbd_update
        call handle_input
        ld a,(quit)
        or a
        ret nz
        ld a,(paused)
        or a
        jr nz,.draw
        call wave_update
        call update_enemies
        call update_towers
        call update_projs
        call update_fx
        call banner_tick
.draw:  call hud_refresh
        if DEBUG
        ld hl,dbg_show
        call both_screens
        endif
        call render
        call flip
        ld a,(game_over)
        or a
        jr z,.loop
        jp end_game

game_init:
        call palette_black
        ; put the sacks back and take the towers off the map
        ld hl,sack_cells
        ld b,NUM_SACKS
.sk:    push bc
        ld d,(hl)
        inc hl
        ld e,(hl)
        inc hl
        ld a,(hl)
        inc hl
        inc hl
        push hl
        push af
        call cell_offset
        ld bc,tilemap
        add hl,bc
        pop af
        ld (hl),a
        pop hl
        pop bc
        djnz .sk
        ld hl,cellmap
        ld bc,NCOL*NROW
.cm:    bit 7,(hl)
        jr z,.cn
        ld a,(hl)
        and #40                 ; a hovering psssst sat on a blocked cell
        jr z,.c0
        ld a,2
.c0:    ld (hl),a
.cn:    cpi
        jp pe,.cm
        ; clear all entity arrays and game variables
        ld hl,ENT_START
        ld de,ENT_START+1
        ld bc,ENT_END-ENT_START-1
        ld (hl),0
        ldir
        ld hl,game_vars
        ld de,game_vars+1
        ld bc,game_vars_end-game_vars-1
        ld (hl),0
        ldir
        ld hl,START_FUNDS
        ld (funds),hl
        ld a,100
        ld (hp),a
        ld a,FIRST_COUNTDOWN
        ld (cd_sec),a
        ld a,25
        ld (cd_sub),a
        ld a,7
        ld (cur_c),a
        ld a,3
        ld (cur_r),a
        ld a,1
        ld (sel_type),a
        ; background
        call tgt_bg
        ld e,0
.r:     ld d,0
.c:     push de
        call draw_tile_bg
        pop de
        inc d
        ld a,d
        cp NCOL
        jr nz,.c
        inc e
        ld a,e
        cp NROW
        jr nz,.r
        call bg_to_screens
        call dirty_reset
        ld a,#7f                ; draw into #4000 first
        ld (back_mask),a
        call hud_full
        ld a,B_STAGE
        ld c,B_CALL
        call banner_show
        if DEBUG
        ld a,DEBUG-1            ; -DDEBUG=n starts at wave n
        ld (wave_num),a
        endif
        call set_palette
        ret

        if DEBUG
dbg_show:                       ; frames per game tick, top right
        call text_normal
        ld bc,#0900
        call set_colors
        ld de,37*256+8
        call set_at
        ld a,(dbg_el)
        ld l,a
        ld h,0
        ld a,3
        jp print_num
        endif

; win or lose: banner, then wait for fire
end_game:
        call kbd_update
        ld a,(game_over)
        cp 1
        ld a,B_WIN
        jr z,.w
        ld a,B_LOSE
.w:     ld c,B_SPACE
        call banner_show
        ld a,SFX_WAVE
        call sfx_play
        ld a,40
        ld (end_wait),a
.l:     call kbd_update
        call update_fx
        call render
        call flip
        ld a,(end_wait)
        or a
        jr z,.k
        dec a
        ld (end_wait),a
        jr .l
.k:     call fire_hit
        jr nc,.l
        ret

;------------------------------------------------------------------------------
; input
;------------------------------------------------------------------------------
handle_input:
        ld a,K_L
        call key_hit
        call c,toggle_lang
        ld a,K_M
        call key_hit
        call c,toggle_music
        ld a,K_H
        call key_hit
        call c,toggle_pause
        ld a,K_ESC
        call key_hit
        jr nc,.ne
        ld a,(paused)
        or a
        jr z,.pz
        ld a,1                  ; ESC while paused: back to the title
        ld (quit),a
        ret
.pz:    call toggle_pause
.ne:    ld a,(paused)
        or a
        ret nz
        call cursor_input
        ld hl,sel_keys
        ld bc,#0601
.sk:    ld a,(hl)
        call key_hit
        jr nc,.nk
        ld a,c
        ld (sel_type),a
        ld a,HUDF_INFO
        call hud_set
.nk:    inc hl
        inc c
        djnz .sk
        call fire_hit
        call c,try_build
        ld a,K_S
        call key_hit
        call c,try_sell
        ld a,K_DEL
        call key_hit
        call c,try_sell
        ld a,K_N
        call key_hit
        call c,call_wave_now
        ret

toggle_lang:
        ld a,(lang)
        xor 1
        ld (lang),a
        call hud_full
        ld a,(ban_on)
        or a
        ret z
        jp banner_draw

toggle_music:
        ld a,(mus_on)
        xor 1
        ld (mus_on),a
        ret

toggle_pause:
        ld a,(paused)
        xor 1
        ld (paused),a
        jr z,.resume
        ld a,(ban_on)
        ld (ps_on),a
        ld a,(ban_id1)
        ld (ps_id1),a
        ld a,(ban_id2)
        ld (ps_id2),a
        ld a,B_PAUSE
        ld c,B_PAUSE2
        call banner_show
        jr .st
.resume:
        ld a,(ps_on)
        or a
        jr z,.clr
        ld a,(ps_id2)
        ld c,a
        ld a,(ps_id1)
        call banner_show
        jr .st
.clr:   call banner_clear
.st:    ld a,HUDF_STATUS
        jp hud_set

cursor_input:
        ld c,0
        ld a,K_UP
        call key_down
        jr nc,.k1
        set 0,c
.k1:     ld a,J_UP
        call key_down
        jr nc,.k2
        set 0,c
.k2:     ld a,K_DOWN
        call key_down
        jr nc,.k3
        set 1,c
.k3:     ld a,J_DOWN
        call key_down
        jr nc,.k4
        set 1,c
.k4:     ld a,K_LEFT
        call key_down
        jr nc,.k5
        set 2,c
.k5:     ld a,J_LEFT
        call key_down
        jr nc,.k6
        set 2,c
.k6:     ld a,K_RIGHT
        call key_down
        jr nc,.k7
        set 3,c
.k7:     ld a,J_RIGHT
        call key_down
        jr nc,.k8
        set 3,c
.k8:     ld a,K_Q
        call key_down
        jr nc,.q1
        set 0,c
.q1:    ld a,K_A
        call key_down
        jr nc,.q2
        set 1,c
.q2:    ld a,K_O
        call key_down
        jr nc,.q3
        set 2,c
.q3:    ld a,K_P
        call key_down
        jr nc,.q4
        set 3,c
.q4:    ld a,c
        or a
        jr nz,.held
        ld (rep_t),a
        ret
.held:  ld a,(rep_t)
        or a
        jr z,.first
        dec a
        ld (rep_t),a
        ret nz
        ld a,2
        jr .go
.first: ld a,7
.go:    ld (rep_t),a
        bit 0,c
        jr z,.nu
        ld a,(cur_r)
        or a
        jr z,.nu
        dec a
        ld (cur_r),a
.nu:    bit 1,c
        jr z,.nd
        ld a,(cur_r)
        cp NROW-1
        jr z,.nd
        inc a
        ld (cur_r),a
.nd:    bit 2,c
        jr z,.nl
        ld a,(cur_c)
        or a
        jr z,.nl
        dec a
        ld (cur_c),a
.nl:    bit 3,c
        jr z,.nr
        ld a,(cur_c)
        cp NCOL-1
        jr z,.nr
        inc a
        ld (cur_c),a
.nr:    ld a,HUDF_INFO
        call hud_set
        ld a,SFX_MOVE
        jp sfx_play

; carry if the selected defender cannot go on the cursor cell
can_build:
        call cur_cell
        ld a,(hl)
        or a
        ret z
        cp 2
        scf
        ret nz
        ld a,(sel_type)
        cp TT_PSSSST
        ret z
        scf
        ret

; D,E = cursor col,row ; HL = cellmap entry
cur_cell:
        ld a,(cur_c)
        ld d,a
        ld a,(cur_r)
        ld e,a
        jp cell_ptr

try_build:
        call can_build
        jr c,.err
        ld a,(sel_type)
        call ttype_ptr
        ld a,(hl)
        ld (tmp_cost),a
        ld c,a
        ld b,0
        ld hl,(funds)
        or a
        sbc hl,bc
        jr c,.err
        ld iy,towers
        ld e,0
.f:     ld a,(iy+T_TYPE)
        or a
        jr z,.got
        ld bc,TW_SZ
        add iy,bc
        inc e
        ld a,e
        cp MAX_TW
        jr nz,.f
.err:   ld a,SFX_ERROR
        jp sfx_play
.got:   ld a,e
        ld (tmp_idx),a
        ld a,(sel_type)
        ld (iy+T_TYPE),a
        ld a,(cur_c)
        ld (iy+T_COL),a
        add a,a
        add a,a
        add a,2
        ld (iy+T_CX),a
        ld a,(cur_r)
        ld (iy+T_ROW),a
        call mul12
        add a,6
        ld (iy+T_CY),a
        ld (iy+T_CD),8
        ld (iy+T_DIS),0
        call cur_cell
        ld a,(hl)               ; 2 = blocked cell (only psssst hovers there)
        and 2
        rrca
        rrca
        rrca
        ld c,a                  ; #40 marks it
        ld a,(tmp_idx)
        or #80
        or c
        ld (hl),a
        ld a,(tmp_cost)
        ld c,a
        ld b,0
        ld hl,(funds)
        or a
        sbc hl,bc
        ld (funds),hl
        call cur_cell
        call redraw_cell
        ld a,SFX_BUILD
        call sfx_play
        ld a,HUDF_FUNDS+HUDF_INFO
        jp hud_set

try_sell:
        call cur_cell
        ld a,(hl)
        bit 7,a
        ret z
        ld c,0
        bit 6,a
        jr z,.s0
        ld c,2
.s0:    ld (hl),c
        and #1f
        call tower_ptr
        push hl
        pop iy
        ld a,(iy+T_TYPE)
        call ttype_ptr
        ld de,7
        add hl,de
        ld c,(hl)
        ld b,0
        ld hl,(funds)
        add hl,bc
        ld (funds),hl
        ld (iy+T_TYPE),0
        call cur_cell
        call redraw_cell
        ld a,SFX_SELL
        call sfx_play
        ld a,HUDF_FUNDS+HUDF_INFO
        jp hud_set

call_wave_now:                  ; early call: half the seconds left become vrouves
        ld a,(wave_state)
        or a
        ret nz
        ld a,(cd_sec)
        srl a
        ld c,a
        ld b,0
        ld hl,(funds)
        add hl,bc
        ld (funds),hl
        ld a,HUDF_FUNDS
        call hud_set
        jp start_wave

;------------------------------------------------------------------------------
; helpers
;------------------------------------------------------------------------------
; A * 12 (A < 22).  Uses C.
mul12:
        ld c,a
        add a,a
        add a,c
        add a,a
        add a,a
        ret

; D,E = col,row -> HL = row*20+col.  Preserves DE.
cell_offset:
        push de
        ld l,e
        ld h,0
        add hl,hl
        add hl,hl
        ld b,h
        ld c,l
        add hl,hl
        add hl,hl
        add hl,bc
        ld e,d
        ld d,0
        add hl,de
        pop de
        ret

cell_ptr:
        call cell_offset
        ld bc,cellmap
        add hl,bc
        ret

; A = tower type -> HL = stats
ttype_ptr:
        dec a
        add a,a
        add a,a
        add a,a
        ld l,a
        ld h,0
        ld bc,ttype_tab
        add hl,bc
        ret

; A = enemy type -> HL = stats
etype_ptr:
        dec a
        add a,a
        add a,a
        add a,a
        ld l,a
        ld h,0
        ld bc,etype_tab
        add hl,bc
        ret

; A = tower index -> HL
tower_ptr:
        add a,a
        add a,a
        add a,a
        ld l,a
        ld h,0
        ld bc,towers
        add hl,bc
        ret

; A (0..63) -> HL = A*A.  Preserves DE.
sq:
        push de
        add a,a
        ld e,a
        ld d,0
        ld hl,SQUARES
        add hl,de
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        pop de
        ret

rand:
        push hl
        ld hl,(seed)
        ld a,h
        rra
        ld a,l
        rra
        xor h
        ld h,a
        ld a,l
        rra
        ld a,h
        rra
        xor l
        ld l,a
        xor h
        ld h,a
        ld (seed),hl
        pop hl
        ret

hud_set:
        ld hl,hud_flags
        or (hl)
        ld (hl),a
        ret

;------------------------------------------------------------------------------
; background cells
;------------------------------------------------------------------------------
; D,E = col,row : copy the cell's tile into the background buffer
draw_tile_bg:
        call cell_offset
        ld bc,tilemap
        add hl,bc
        ld l,(hl)
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld b,h
        ld c,l
        add hl,hl
        add hl,bc
        ld bc,tiles
        add hl,bc
        ld (spr_src),hl
        ld a,d
        add a,a
        add a,a
        ld d,a
        ld a,e
        call mul12
        ld e,a
        ld b,TH
.l:     push bc
        ld l,e
        ld h,hi(TAB_BG)
        ld a,(hl)
        inc h
        ld h,(hl)
        add a,d
        ld l,a
        jr nc,.n
        inc h
.n:     ex de,hl
        push hl
        ld hl,(spr_src)
        ldi
        ldi
        ldi
        ldi
        ld (spr_src),hl
        pop de
        inc e
        pop bc
        djnz .l
        ret

; D,E = col,row : tile + tower into the background, no dirty marking
redraw_cell_nd:
        push de
        call tgt_bg
        call draw_tile_bg
        pop de
        push de
        call cell_ptr
        ld a,(hl)
        bit 7,a
        jr z,.done
        and #1f
        call tower_ptr
        ld a,(hl)
        ld bc,T_DIS
        add hl,bc
        ld c,(hl)
        cp TT_CAULDRON
        jr nz,.ns
        inc c
        dec c
        jr z,.ns
        ld hl,spr_cauldron_x
        jr .dr
.ns:    dec a
        add a,a
        ld l,a
        ld h,0
        ld bc,tower_sprites
        add hl,bc
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
.dr:    pop de
        push de
        ld a,d
        add a,a
        add a,a
        ld d,a
        ld a,e
        call mul12
        ld e,a
        call draw_sprite_raw
.done:  pop de
        ret

; D,E = col,row : redraw the cell and mark it for both screens
redraw_cell:
        call redraw_cell_nd
        ld a,(ban_on)           ; keep a banner on top of rows 6-7
        or a
        jr z,.nb
        ld a,e
        sub 6
        cp 2
        jr nc,.nb
        ld a,d
        dec a
        cp 18
        jp c,banner_draw
.nb:    ld a,d
        add a,a
        add a,a
        ld d,a
        ld a,e
        call mul12
        ld e,a
        ld bc,#0c04
        jp dirty_add_both

;------------------------------------------------------------------------------
; waves
;------------------------------------------------------------------------------
wave_update:
        ld a,(hp)
        or a
        jr nz,.alive
        ld a,2
        ld (game_over),a
        ret
.alive: ld a,(wave_state)
        or a
        jr nz,.active
        ld a,(cd_sub)
        or a
        jr nz,.sub
        ld a,(cd_sec)
        or a
        jp z,start_wave
        dec a
        ld (cd_sec),a
        ld a,25
        ld (cd_sub),a
        ld a,HUDF_STATUS
        call hud_set
.sub:   ld hl,cd_sub
        dec (hl)
        ret
.active:
        call spawn_tick
        ld a,(sp_left)
        or a
        ret nz
        ld a,(en_count)
        or a
        ret nz
        ; wave cleared: bonus 15 + 3*wave
        ld a,(wave_num)
        ld c,a
        add a,a
        add a,c
        add a,15
        ld c,a
        ld b,0
        ld hl,(funds)
        add hl,bc
        ld (funds),hl
        ld a,HUDF_FUNDS+HUDF_STATUS
        call hud_set
        ld a,(wave_num)
        cp NUM_WAVES
        jr nz,.more
        ld a,1
        ld (game_over),a
        ret
.more:  xor a
        ld (wave_state),a
        ld a,NEXT_COUNTDOWN
        ld (cd_sec),a
        ld a,25
        ld (cd_sub),a
        ld a,B_CLEAR
        ld c,B_NEXT
        call banner_show
        ld a,SFX_SELL
        jp sfx_play

start_wave:
        ld a,(wave_num)
        cp NUM_WAVES
        ret nc
        add a,a
        ld l,a
        ld h,0
        ld de,wave_table
        add hl,de
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        ld (sp_ptr),hl
        ld a,(wave_num)
        inc a
        ld (wave_num),a
        ld a,1
        ld (wave_state),a
        call load_group
        ld a,10
        ld (sp_timer),a
        ld a,(wave_num)
        cp NUM_WAVES
        jr nz,.nf
        ld a,B_FINAL
        ld c,#ff
        call banner_show
        ld a,100
        ld (ban_timer),a
        jr .s
.nf:    call banner_clear
.s:     ld a,SFX_WAVE
        call sfx_play
        ld a,HUDF_WAVE+HUDF_STATUS
        jp hud_set

load_group:
        ld hl,(sp_ptr)
        ld a,(hl)
        or a
        jr z,.end
        ld (sp_type),a
        inc hl
        ld a,(hl)
        ld (sp_left),a
        inc hl
        ld a,(hl)
        ld (sp_iv),a
        ld (sp_timer),a
        inc hl
        ld (sp_ptr),hl
        ret
.end:   xor a
        ld (sp_left),a
        ret

spawn_tick:
        ld a,(sp_left)
        or a
        ret z
        ld hl,sp_timer
        dec (hl)
        ret nz
        ld a,(sp_type)
        call spawn_enemy
        jr c,.ok
        ld a,1
        ld (sp_timer),a
        ret
.ok:    ld a,(sp_iv)
        ld (sp_timer),a
        ld hl,sp_left
        dec (hl)
        ret nz
        jp load_group

;------------------------------------------------------------------------------
; enemies
;------------------------------------------------------------------------------
; A = type -> carry if spawned
spawn_enemy:
        ld c,a
        ld ix,enemies
        ld b,MAX_EN
        ld de,EN_SZ
.f:     ld a,(ix+E_TYPE)
        or a
        jr z,.got
        add ix,de
        djnz .f
        or a
        ret
.got:   ld (ix+E_TYPE),c
        ld a,c
        call etype_ptr
        ld a,(wave_num)
        ld b,a
        ld a,(hl)
        inc hl
        ld e,(hl)
        inc hl
.m:     add a,e
        djnz .m
        ld (ix+E_HP),a
        ld (ix+E_MAXHP),a
        ld a,(hl)
        inc hl
        ld (ix+E_SPD),a
        ld a,(hl)
        ld (ix+E_ARM),a
        xor a
        ld (ix+E_ACC),a
        ld (ix+E_PROG),a
        ld (ix+E_PROG+1),a
        ld (ix+E_SLOW),a
        ld (ix+E_SEG),a
        call rand
        ld (ix+E_ANIM),a
        ld a,(gen_ctr)
        inc a
        ld (gen_ctr),a
        ld (ix+E_GEN),a
        call enemy_path
        ld a,(hl)
        ld (ix+E_X),a
        inc hl
        ld a,(hl)
        ld (ix+E_Y),a
        inc hl
        ld a,(hl)
        ld (ix+E_SUB),a
        inc hl
        ld a,(hl)
        ld (ix+E_REM),a
        ld hl,en_count
        inc (hl)
        scf
        ret

; IX = enemy -> HL = its path header
enemy_path:
        ld a,(ix+E_TYPE)
        cp ET_DRONE
        ld hl,path_ground
        ret nz
        ld hl,path_air
        ret

; IX = enemy -> HL = current segment (dx, dy, n)
enemy_seg:
        call enemy_path
        ld a,(ix+E_SEG)
        ld c,a
        add a,a
        add a,c
        add a,4
        ld c,a
        ld b,0
        add hl,bc
        ret

update_enemies:
        ld ix,enemies
        ld b,MAX_EN
.l:     push bc
        ld a,(ix+E_TYPE)
        or a
        call nz,enemy_move
        ld de,EN_SZ
        add ix,de
        pop bc
        djnz .l
        ret

enemy_move:
        ld c,(ix+E_SPD)
        ld a,(ix+E_SLOW)
        or a
        jr z,.ns
        dec (ix+E_SLOW)
        srl c
.ns:    ld a,(ix+E_ACC)
        add a,c
        ld c,a
        and 15
        ld (ix+E_ACC),a
        ld a,c
        rrca
        rrca
        rrca
        rrca
        and 15
        jr z,.anim
        ld b,a
.st:    push bc
        call enemy_step
        pop bc
        jr c,.arrived
        djnz .st
.anim:  inc (ix+E_ANIM)
        ld a,(ix+E_TYPE)
        cp ET_TANK
        ret nz
        ld a,(ix+E_ANIM)
        and 7
        ret nz
        jp tank_crush
.arrived:
        ld a,(ix+E_TYPE)
        call etype_ptr
        ld de,5
        add hl,de
        ld a,(hl)
        ld (ix+E_TYPE),0
        ld hl,en_count
        dec (hl)
        jp base_hit

; one step along the path -> carry if the kafenio was reached
enemy_step:
        call enemy_seg
        ld c,(hl)
        inc hl
        ld b,(hl)
        ld a,(ix+E_Y)
        add a,b
        ld (ix+E_Y),a
        ld a,(ix+E_SUB)
        inc a
        cp 3
        jr c,.s
        ld a,(ix+E_X)
        add a,c
        ld (ix+E_X),a
        xor a
.s:     ld (ix+E_SUB),a
        inc (ix+E_PROG)
        jr nz,.p
        inc (ix+E_PROG+1)
.p:     or a
        dec (ix+E_REM)
        ret nz
        inc (ix+E_SEG)
        call enemy_seg
        inc hl
        inc hl
        ld a,(hl)
        or a
        jr z,.end
        ld (ix+E_REM),a
        ret
.end:   scf
        ret

; A = damage to the kafenio
base_hit:
        ld c,a
        ld a,(hp)
        sub c
        jr nc,.ok
        xor a
.ok:    ld (hp),a
        ld a,HUDF_HP
        call hud_set
        ld a,SFX_HURT
        call sfx_play
        ; fall through
update_sacks:
        ld a,(sacks_gone)
        cp NUM_SACKS
        ret nc
        ld b,a
        ld a,80
        inc b
        jr .t
.th:    sub 20
.t:     djnz .th
        ld c,a
        ld a,(hp)
        cp c
        jr z,.rm
        ret nc
.rm:    ld a,(sacks_gone)
        add a,a
        add a,a
        ld l,a
        ld h,0
        ld bc,sack_cells
        add hl,bc
        ld d,(hl)
        inc hl
        ld e,(hl)
        inc hl
        inc hl
        ld a,(hl)
        push af
        call cell_offset
        ld bc,tilemap
        add hl,bc
        pop af
        ld (hl),a
        call redraw_cell
        ld hl,sacks_gone
        inc (hl)
        jr update_sacks

; IX = enemy ; A = damage ; C bit0 = ignore armour
damage_enemy:
        ld b,a
        bit 0,c
        jr nz,.na
        sub (ix+E_ARM)
        jr c,.min
        jr z,.min
        ld b,a
        jr .na
.min:   ld b,1
.na:    ld a,(ix+E_HP)
        sub b
        jr c,kill_enemy
        jr z,kill_enemy
        ld (ix+E_HP),a
        ret

kill_enemy:
        ld a,(ix+E_TYPE)
        push af
        call etype_ptr
        ld de,4
        add hl,de
        ld c,(hl)
        ld b,0
        ld hl,(funds)
        add hl,bc
        ld (funds),hl
        ld (ix+E_TYPE),0
        ld hl,en_count
        dec (hl)
        pop af
        cp ET_TANK
        ld a,FX_BOOM
        jr z,.b
        ld a,FX_POOF
.b:     ld d,(ix+E_X)
        ld e,(ix+E_Y)
        call spawn_fx
        ld a,SFX_DIE
        call sfx_play
        ld a,HUDF_FUNDS
        jp hud_set

; tanks dent cauldrons next to the road
tank_crush:
        ld a,(ix+E_X)
        add a,2
        rrca
        rrca
        and 63
        ld d,a
        ld a,(ix+E_Y)
        add a,6
        ld e,0
.dv:    sub 12
        jr c,.dd
        inc e
        jr .dv
.dd:    dec d
        call crush_at
        inc d
        inc d
        call crush_at
        dec d
        dec e
        call crush_at
        inc e
        inc e
        jp crush_at

crush_at:
        ld a,d
        cp NCOL
        ret nc
        ld a,e
        cp NROW
        ret nc
        push de
        call cell_ptr
        ld a,(hl)
        bit 7,a
        jr z,.o
        and #1f
        call tower_ptr
        ld a,(hl)
        cp TT_CAULDRON
        jr nz,.o
        push hl
        pop iy
        ld a,(iy+T_DIS)
        or a
        jr nz,.o
        ld (iy+T_DIS),125
        pop de
        push de
        call redraw_cell
        ld a,SFX_CRUSH
        call sfx_play
.o:     pop de
        ret

;------------------------------------------------------------------------------
; towers
;------------------------------------------------------------------------------
update_towers:
        ld iy,towers
        ld b,MAX_TW
.l:     push bc
        ld a,(iy+T_TYPE)
        or a
        call nz,tower_think
        ld de,TW_SZ
        add iy,de
        pop bc
        djnz .l
        ret

tower_think:
        ld a,(iy+T_DIS)
        or a
        jr z,.en
        dec (iy+T_DIS)
        ret nz
        ld d,(iy+T_COL)
        ld e,(iy+T_ROW)
        jp redraw_cell
.en:    ld a,(iy+T_CD)
        or a
        jr z,.rdy
        dec (iy+T_CD)
        ret
.rdy:   ld a,(iy+T_TYPE)
        call ttype_ptr
        inc hl
        ld a,(hl)
        ld (tr_range),a
        push hl
        call sq
        ld (tr_range2),hl
        pop hl
        inc hl
        ld a,(hl)
        ld (tr_cd),a
        inc hl
        ld a,(hl)
        ld (tr_dmg),a
        inc hl
        ld a,(hl)
        ld (tr_flags),a
        inc hl
        ld a,(hl)
        ld (tr_proj),a
        inc hl
        ld a,(hl)
        ld (tr_sfx),a
        call find_target
        jr c,.fire
        ld (iy+T_CD),3
        ret
.fire:  ld a,(tr_cd)
        ld (iy+T_CD),a
        ld a,(tr_sfx)
        call sfx_play
        ld a,(iy+T_TYPE)
        cp TT_YIAYIA
        jp z,fire_yiayia
        cp TT_CAULDRON
        jp z,fire_cauldron
        ld a,(tr_dmg)
        ld c,a
        ld b,0
        ld a,(iy+T_TYPE)
        cp TT_BRIDE
        jr nz,.nc
        call rand
        cp 64
        jr nc,.nc
        ld a,c
        add a,a
        add a,c
        ld c,a
        ld b,1
.nc:    ld a,(tr_proj)
        jp spawn_proj

; IY = tower -> carry and IX = the enemy furthest along within range
find_target:
        ld hl,0
        ld (best_prog),hl
        ld ix,enemies
        ld b,MAX_EN
.l:     push bc
        ld a,(ix+E_TYPE)
        or a
        jr z,.n
        cp ET_DRONE
        jr nz,.gnd
        ld a,(tr_flags)
        and 1
        jr z,.n
.gnd:   call in_range
        jr nc,.n
        ld l,(ix+E_PROG)
        ld h,(ix+E_PROG+1)
        inc hl
        ld de,(best_prog)
        push hl
        or a
        sbc hl,de
        pop hl
        jr c,.n
        jr z,.n
        ld (best_prog),hl
        ld (best_ix),ix
.n:     ld de,EN_SZ
        add ix,de
        pop bc
        djnz .l
        ld hl,(best_prog)
        ld a,h
        or l
        ret z
        ld ix,(best_ix)
        scf
        ret

; IX = enemy, IY = tower -> carry if within tr_range
in_range:
        ld a,(ix+E_X)
        add a,2
        sub (iy+T_CX)
        jr nc,.p1
        neg
.p1:    ld c,a
        add a,a
        add a,c
        ld c,a
        ld a,(tr_range)
        cp c
        jr c,.no
        ld a,(ix+E_Y)
        add a,6
        sub (iy+T_CY)
        jr nc,.p2
        neg
.p2:    ld e,a
        ld a,(tr_range)
        cp e
        jr c,.no
        ld a,c
        call sq
        push hl
        ld a,e
        call sq
        pop de
        add hl,de
        ex de,hl
        ld hl,(tr_range2)
        or a
        sbc hl,de
        ccf
        ret
.no:    or a
        ret

; slows every walker in reach and whacks the target
fire_yiayia:
        push ix
        ld ix,enemies
        ld b,MAX_EN
.l:     push bc
        ld a,(ix+E_TYPE)
        or a
        jr z,.n
        cp ET_DRONE
        jr z,.n
        call in_range
        jr nc,.n
        ld (ix+E_SLOW),40
.n:     ld de,EN_SZ
        add ix,de
        pop bc
        djnz .l
        pop ix
        ld d,(ix+E_X)
        ld e,(ix+E_Y)
        ld a,FX_BASH
        call spawn_fx
        ld a,(tr_dmg)
        ld c,0
        jp damage_enemy

; toxic cloud: hurts (ignoring armour) and slows every walker in reach
fire_cauldron:
        ld ix,enemies
        ld b,MAX_EN
.l:     push bc
        ld a,(ix+E_TYPE)
        or a
        jr z,.n
        cp ET_DRONE
        jr z,.n
        call in_range
        jr nc,.n
        ld (ix+E_SLOW),30
        ld d,(ix+E_X)
        ld e,(ix+E_Y)
        ld a,FX_PUFF
        call spawn_fx
        ld a,(tr_dmg)
        ld c,1
        call damage_enemy
.n:     ld de,EN_SZ
        add ix,de
        pop bc
        djnz .l
        ret

;------------------------------------------------------------------------------
; projectiles
;------------------------------------------------------------------------------
; A = type, C = damage, B = flags, IX = target, IY = tower
spawn_proj:
        ld (sp_ptype),a
        ld a,c
        ld (sp_pdmg),a
        ld a,b
        ld (sp_pflag),a
        ld hl,projs
        ld de,PR_SZ
        ld b,MAX_PR
.f:     ld a,(hl)
        or a
        jr z,.got
        add hl,de
        djnz .f
        ret
.got:   ld a,(sp_ptype)
        ld (hl),a
        inc hl
        ld a,(iy+T_CX)
        add a,a
        ld (hl),a
        inc hl
        ld a,(iy+T_CY)
        sub 4
        ld (hl),a
        inc hl
        push hl
        push ix
        pop hl
        ld de,enemies
        or a
        sbc hl,de
        ld a,l
        rrca
        rrca
        rrca
        rrca
        and 15
        pop hl
        ld (hl),a
        inc hl
        ld a,(sp_pdmg)
        ld (hl),a
        inc hl
        ld a,(sp_pflag)
        ld (hl),a
        inc hl
        ld a,(ix+E_X)
        add a,2
        add a,a
        ld (hl),a
        inc hl
        ld a,(ix+E_Y)
        add a,6
        ld (hl),a
        inc hl
        ld a,(ix+E_GEN)
        ld (hl),a
        ret

update_projs:
        ld iy,projs
        ld b,MAX_PR
.l:     push bc
        ld a,(iy+P_TYPE)
        or a
        call nz,proj_step
        ld de,PR_SZ
        add iy,de
        pop bc
        djnz .l
        ret

proj_step:
        ld a,(iy+P_TGT)
        add a,a
        add a,a
        add a,a
        add a,a
        ld e,a
        ld d,0
        ld ix,enemies
        add ix,de
        ld a,(ix+E_TYPE)
        or a
        jr z,.lost
        ld a,(ix+E_GEN)
        cp (iy+P_GEN)
        jr nz,.lost
        ld a,(ix+E_X)
        add a,2
        add a,a
        ld (iy+P_TX),a
        ld a,(ix+E_Y)
        add a,6
        ld (iy+P_TY),a
        jr .mv
.lost:  set 7,(iy+P_FLAG)
.mv:    ld a,(iy+P_TYPE)
        dec a
        add a,a
        ld e,a
        ld d,0
        ld hl,proj_speed
        add hl,de
        ld c,(hl)
        inc hl
        ld b,(hl)
        ld e,0
        ld a,(iy+P_TX)
        sub (iy+P_X)
        jr c,.xl
        cp c
        jr nc,.xr
        ld c,a
        set 0,e
.xr:    ld a,(iy+P_X)
        add a,c
        ld (iy+P_X),a
        jr .y
.xl:    neg
        cp c
        jr nc,.xl2
        ld c,a
        set 0,e
.xl2:   ld a,(iy+P_X)
        sub c
        ld (iy+P_X),a
.y:     ld a,(iy+P_TY)
        sub (iy+P_Y)
        jr c,.yu
        cp b
        jr nc,.yd
        ld b,a
        set 1,e
.yd:    ld a,(iy+P_Y)
        add a,b
        ld (iy+P_Y),a
        jr .chk
.yu:    neg
        cp b
        jr nc,.yu2
        ld b,a
        set 1,e
.yu2:   ld a,(iy+P_Y)
        sub b
        ld (iy+P_Y),a
.chk:   ld a,e
        cp 3
        ret nz
        ; impact
        ld a,(iy+P_TYPE)
        ld (iy+P_TYPE),0
        cp PT_DAKOS
        jr z,.splash
        push af
        ld a,(iy+P_X)
        srl a
        dec a
        ld d,a
        ld a,(iy+P_Y)
        sub 2
        ld e,a
        pop af
        push af
        cp PT_LASER
        ld a,FX_ZAP
        jr z,.z
        ld a,FX_SPARK
.z:     call spawn_fx
        pop af
        bit 7,(iy+P_FLAG)
        ret nz
        cp PT_LASER
        jr nz,.d
        ld a,(ix+E_ARM)
        or a
        jr z,.d
        dec (ix+E_ARM)
.d:     ld a,(iy+P_DMG)
        ld c,0
        jp damage_enemy
.splash:
        ld a,(iy+P_X)
        srl a
        sub 2
        ld d,a
        ld a,(iy+P_Y)
        sub 6
        ld e,a
        ld a,FX_BASH
        call spawn_fx
        ld ix,enemies
        ld b,MAX_EN
.sl:    push bc
        ld a,(ix+E_TYPE)
        or a
        jr z,.sn
        ld a,(iy+P_X)
        srl a
        ld c,a
        ld a,(ix+E_X)
        add a,2
        sub c
        jr nc,.sp
        neg
.sp:    cp 5
        jr nc,.sn
        ld a,(ix+E_Y)
        add a,6
        sub (iy+P_Y)
        jr nc,.sq
        neg
.sq:    cp 13
        jr nc,.sn
        ld a,(iy+P_DMG)
        ld c,0
        call damage_enemy
.sn:    ld de,EN_SZ
        add ix,de
        pop bc
        djnz .sl
        ret

;------------------------------------------------------------------------------
; effects
;------------------------------------------------------------------------------
; A = type, D,E = x,y (clamped to the playfield).  Preserves IX, IY.
spawn_fx:
        push hl
        push bc
        ld c,a
        ld hl,fxs
        ld b,MAX_FX
.f:     ld a,(hl)
        or a
        jr z,.got
        inc hl
        inc hl
        inc hl
        inc hl
        djnz .f
        jr .out
.got:   ld (hl),c
        inc hl
        ld a,d
        cp 128
        jr c,.x1
        xor a
.x1:    cp 77
        jr c,.x2
        ld a,76
.x2:    ld (hl),a
        inc hl
        ld a,e
        cp 200
        jr c,.y1
        xor a
.y1:    cp 157
        jr c,.y2
        ld a,156
.y2:    ld (hl),a
        inc hl
        push hl
        ld a,c
        call fx_ptr
        ld de,4
        add hl,de
        ld a,(hl)
        pop hl
        ld (hl),a
.out:   pop bc
        pop hl
        ret

; A = effect type -> HL = fx_tab entry
fx_ptr:
        dec a
        add a,a
        add a,a
        add a,a
        ld l,a
        ld h,0
        ld de,fx_tab
        add hl,de
        ret

update_fx:
        ld hl,fxs
        ld b,MAX_FX
.l:     ld a,(hl)
        or a
        jr z,.n
        inc hl
        inc hl
        inc hl
        dec (hl)
        dec hl
        dec hl
        dec hl
        jr nz,.n
        ld (hl),0
.n:     inc hl
        inc hl
        inc hl
        inc hl
        djnz .l
        ret

;------------------------------------------------------------------------------
; rendering into the back buffer
;------------------------------------------------------------------------------
render:
        call tgt_back
        call restore_dirty
        call draw_enemies
        call draw_projs
        call draw_fx
        call draw_flag
        jp draw_cursor

draw_enemies:
        ld ix,enemies
        ld b,MAX_EN
.l:     push bc
        ld a,(ix+E_TYPE)
        or a
        jr z,.n
        ld d,(ix+E_X)
        ld a,(ix+E_Y)
        sub 2
        ld e,a
        ld bc,#0e04
        call dirty_add
        jr c,.n
        call draw_hpbar
        ; sprite: type, direction, frame
        call enemy_seg
        ld a,(hl)
        or a
        jr z,.dn
        ld a,1
        jp m,.dn
        inc a
.dn:    ld c,a
        ld a,(ix+E_TYPE)
        dec a
        ld b,a
        add a,a
        add a,b
        add a,c
        add a,a
        ld c,a
        ld a,(ix+E_ANIM)
        rrca
        rrca
        and 1
        add a,c
        add a,a
        ld l,a
        ld h,0
        ld de,enemy_sprites
        add hl,de
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        ld d,(ix+E_X)
        ld e,(ix+E_Y)
        call draw_sprite_raw
.n:     ld de,EN_SZ
        add ix,de
        pop bc
        djnz .l
        ret

; health bar above a damaged enemy: n = hp*8/maxhp pixels of green
draw_hpbar:
        ld a,(ix+E_HP)
        cp (ix+E_MAXHP)
        ret nc
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        ld e,(ix+E_MAXHP)
        ld d,0
        ld b,0
.dv:    or a
        sbc hl,de
        jr c,.dd
        inc b
        jr .dv
.dd:    ld c,b
        ld d,(ix+E_X)
        ld a,(ix+E_Y)
        sub 2
        ld e,a
        call line_addr
        ld b,4
.k:     ld a,c
        cp 2
        jr nc,.gg
        or a
        jr z,.rr
        ld a,BAR_GR
        ld c,0
        jr .w
.rr:    ld a,BAR_RR
        jr .w
.gg:    sub 2
        ld c,a
        ld a,BAR_GG
.w:     ld (hl),a
        inc hl
        djnz .k
        ret

draw_projs:
        ld iy,projs
        ld b,MAX_PR
.l:     push bc
        ld a,(iy+P_TYPE)
        or a
        jr z,.n
        dec a
        add a,a
        ld e,a
        ld d,0
        ld hl,proj_sprites
        add hl,de
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        bit 0,(iy+P_FLAG)
        jr z,.s
        ld hl,spr_pistol_crit
.s:     ld a,(iy+P_X)
        srl a
        ld d,a
        ld e,(iy+P_Y)
        call draw_sprite
.n:     ld de,PR_SZ
        add iy,de
        pop bc
        djnz .l
        ret

draw_fx:
        ld iy,fxs
        ld b,MAX_FX
.l:     push bc
        ld a,(iy+F_TYPE)
        or a
        jr z,.n
        call fx_ptr
        bit 2,(iy+F_T)
        jr z,.a
        inc hl
        inc hl
.a:     ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        ld d,(iy+F_X)
        ld e,(iy+F_Y)
        call draw_sprite
.n:     ld de,FX_SZ
        add iy,de
        pop bc
        djnz .l
        ret

draw_flag:
        ld hl,spr_flag_a
        ld a,(framecnt)
        and 16
        jr z,.a
        ld hl,spr_flag_b
.a:     ld de,#0e63             ; x 14, y 99
        jp draw_sprite

draw_cursor:
        call cur_cell
        bit 7,(hl)
        jr nz,.ok
        call can_build
        jr c,.bad
        ld a,(sel_type)
        call ttype_ptr
        ld c,(hl)
        ld b,0
        ld hl,(funds)
        or a
        sbc hl,bc
        jr c,.bad
.ok:    ld hl,spr_cursor_ok
        ld a,(framecnt)
        and 8
        jr z,.d
        ld hl,spr_cursor_ok_b
        jr .d
.bad:   ld hl,spr_cursor_bad
.d:     push hl
        ld a,(cur_c)
        add a,a
        add a,a
        ld d,a
        ld a,(cur_r)
        call mul12
        ld e,a
        pop hl
        jp draw_sprite

;------------------------------------------------------------------------------
; banner messages (drawn into the background, rows 6-7)
;------------------------------------------------------------------------------
BAN_X equ 4
BAN_Y equ 72
BAN_W equ 72
BAN_H equ 24

; A = first string, C = second string (#FF none)
banner_show:
        ld (ban_id1),a
        ld a,c
        ld (ban_id2),a
        ld a,1
        ld (ban_on),a
        xor a
        ld (ban_timer),a
banner_draw:
        call tgt_bg
        ld de,BAN_X*256+BAN_Y
        ld bc,BAN_H*256+BAN_W
        ld a,PENBYTE_6
        call fill_rect
        ld de,BAN_X*256+BAN_Y
        ld bc,1*256+BAN_W
        ld a,PENBYTE_8
        call fill_rect
        ld de,BAN_X*256+BAN_Y+BAN_H-1
        ld bc,1*256+BAN_W
        ld a,PENBYTE_8
        call fill_rect
        ld de,BAN_X*256+BAN_Y
        ld bc,BAN_H*256+1
        ld a,PENBYTE_8
        call fill_rect
        ld de,(BAN_X+BAN_W-1)*256+BAN_Y
        ld bc,BAN_H*256+1
        ld a,PENBYTE_8
        call fill_rect
        call text_normal
        ld bc,#0806
        call set_colors
        ld a,(ban_id1)
        ld e,BAN_Y+3
        call print_id_centered
        ld a,(ban_id2)
        cp #ff
        jr z,.m
        ld bc,#0506
        call set_colors
        ld a,(ban_id2)
        ld e,BAN_Y+13
        call print_id_centered
.m:     ld de,BAN_X*256+BAN_Y
        ld bc,BAN_H*256+BAN_W
        jp dirty_add_both

banner_clear:
        ld a,(ban_on)
        or a
        ret z
        xor a
        ld (ban_on),a
        ld e,6
.r:     ld d,1
.c:     push de
        call redraw_cell_nd
        pop de
        inc d
        ld a,d
        cp 19
        jr nz,.c
        inc e
        ld a,e
        cp 8
        jr nz,.r
        ld de,BAN_X*256+BAN_Y
        ld bc,BAN_H*256+BAN_W
        jp dirty_add_both

banner_tick:
        ld a,(ban_timer)
        or a
        ret z
        dec a
        ld (ban_timer),a
        ret nz
        jp banner_clear

;------------------------------------------------------------------------------
; HUD (drawn on both screens)
;------------------------------------------------------------------------------
hud_full:
        ld hl,hud_all
        jp both_screens

hud_all:
        call hud_top
        ld de,HUD_Y1
        ld bc,16*256+80
        xor a
        call fill_rect
        call hud_labels
        call hud_wave
        call hud_funds
        call hud_hp
        call hud_info
        jp hud_status

hud_refresh:
        ld a,(hud_flags)
        bit 3,a                 ; funds changed: did the selection become (un)affordable?
        jr z,.k0
        call sel_affordable
        ld hl,hud_aff
        cp (hl)
        jr z,.k0
        ld a,HUDF_INFO
        call hud_set
.k0:    ld hl,hud_jobs
        ld b,5
.k1:    ld a,(hud_flags)
        and (hl)
        inc hl
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        jr z,.k2
        push hl
        push bc
        ex de,hl
        call both_screens
        pop bc
        pop hl
.k2:    djnz .k1
        xor a
        ld (hud_flags),a
        ret

hud_jobs:
        db HUDF_WAVE
        dw hud_wave
        db HUDF_FUNDS
        dw hud_funds
        db HUDF_HP
        dw hud_hp
        db HUDF_INFO
        dw hud_info
        db HUDF_STATUS
        dw hud_status

; A = 1 if the selected defender can be paid for
sel_affordable:
        ld a,(sel_type)
        call ttype_ptr
        ld c,(hl)
        ld b,0
        ld hl,(funds)
        or a
        sbc hl,bc
        ld a,0
        ccf
        rla
        ret

hud_top:
        ld de,0
        ld bc,16*256+80
        xor a
        call fill_rect
        call text_normal
        ld bc,#0800
        call set_colors
        ld de,0
        call set_at
        ld a,S_TITLE_EN
        call print_id
        ld bc,#0500
        call set_colors
        ld a,S_TITLE_SL
        call print_id
        ld bc,#0900
        call set_colors
        ld a,S_TITLE_GR
        call print_id
        ld bc,#0500
        call set_colors
        ld de,8
        call set_at
        ld a,S_LANGHINT
        call print_id
        ld bc,#0700
        call set_colors
        ld de,29*256+8
        call set_at
        ld a,S_AMSTRAD
        jp print_id

HUD_Y1 equ 184
HUD_Y2 equ 192

hud_wave:
        ld de,HUD_Y1
        ld bc,8*256+22
        xor a
        call fill_rect
        call text_normal
        ld bc,#0500
        call set_colors
        ld de,HUD_Y1
        call set_at
        ld a,S_WAVE
        call print_id
        ld bc,#0800
        call set_colors
        ld de,5*256+HUD_Y1
        call set_at
        ld a,1
        ld (pn_zero),a
        ld a,(wave_num)
        ld l,a
        ld h,0
        ld a,2
        call print_num
        ld a,GLYPH_SLASH
        call put_glyph
        ld hl,NUM_WAVES
        ld a,2
        call print_num
        xor a
        ld (pn_zero),a
        ret

hud_labels:
        ld de,11*2*256+HUD_Y1
        ld bc,8*256+16
        xor a
        call fill_rect
        ld de,23*2*256+HUD_Y1
        ld bc,8*256+10
        xor a
        call fill_rect
        call text_normal
        ld bc,#0500
        call set_colors
        ld de,12*256+HUD_Y1
        call set_at
        ld a,S_FUNDS
        call print_id
        ld de,24*256+HUD_Y1
        call set_at
        ld a,S_HP
        jp print_id

hud_funds:
        call text_normal
        ld bc,#0800
        call set_colors
        ld de,19*256+HUD_Y1
        call set_at
        ld hl,(funds)
        ld a,4
        jp print_num

hud_hp:
        call text_normal
        ld a,(hp)
        cp 30
        ld bc,#0800
        jr nc,.hc
        ld bc,#0900
.hc:    call set_colors
        ld de,28*256+HUD_Y1
        call set_at
        ld a,(hp)
        ld l,a
        ld h,0
        ld a,3
        jp print_num

hud_status:
        ld de,66*256+HUD_Y1
        ld bc,8*256+14
        xor a
        call fill_rect
        call text_normal
        ld de,33*256+HUD_Y1
        call set_at
        ld a,(paused)
        or a
        jr z,.np
        ld bc,#0900
        call set_colors
        ld a,S_PAUSE
        jp print_id
.np:    ld a,(wave_state)
        or a
        jr z,.wait
        ld bc,#0a00
        call set_colors
        ld a,S_GO
        jp print_id
.wait:  ld bc,#0700
        call set_colors
        ld a,S_NEXT
        call print_id
        ld a,1
        ld (pn_zero),a
        ld a,(cd_sec)
        ld l,a
        ld h,0
        ld a,2
        call print_num
        xor a
        ld (pn_zero),a
        ret

hud_info:
        ld de,HUD_Y2
        ld bc,8*256+80
        xor a
        call fill_rect
        call text_normal
        ld de,HUD_Y2
        call set_at
        call cur_cell
        ld a,(hl)
        bit 7,a
        jr z,.build
        and #1f
        call tower_ptr
        ld a,(hl)
        push af
        add a,S_NAME1-1
        push af
        ld bc,#0500
        call set_colors
        pop af
        call print_id
        ld bc,#0800
        call set_colors
        ld de,20*256+HUD_Y2
        call set_at
        ld a,S_SELL
        call print_id
        pop af
        call ttype_ptr
        ld de,7
        add hl,de
        ld l,(hl)
        ld h,0
        ld a,3
        jp print_num
.build: call sel_affordable
        ld (hud_aff),a
        or a
        ld bc,#0800
        jr nz,.aff
        ld bc,#0400
.aff:   call set_colors
        ld a,(sel_type)
        add a,S_INFO1-1
        jp print_id
