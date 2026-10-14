;==============================================================================
; LET'S GO FOR VROUVES / ΠΑΜΕ ΓΙΑ ΒΡΟΥΒΕΣ
; Amstrad CPC 64K, Mode 0 tower defense.  Assemble with rasm.
;
; Memory map (firmware is switched off):
;   #0038         interrupt vector (jp int_handler)
;   #0040-#3FFF   code, data, variables
;   #4000-#7FFF   screen buffer B
;   #8000-#B47F   background buffer (playfield, 80 x 168)
;   #B500-#B8FF   line tables
;   #B900-#BEFF   sprite mask table, dirty lists, entity arrays
;   #BF00-#BFFF   stack
;   #C000-#FFFF   screen buffer A
;==============================================================================
        BUILDSNA
        BANKSET 0

        ifndef DEBUG
DEBUG       equ 0           ; rasm -DDEBUG=1: frame meter, rich start
        endif

LOAD_ADDR   equ #0040
BGBUF       equ #8000
TAB_PF      equ #B500       ; playfield line -> screen address (lo page, hi page)
TAB_BG      equ #B700       ; playfield line -> background address
SQUARES     equ #B480       ; 64 x 16 bit
MASKTAB     equ #B900
DLIST0      equ #BA00
DLIST1      equ #BB00
DL_CAP      equ 63
ENT_START   equ #BC00
enemies     equ #BC00       ; 16 x 16
towers      equ #BD00       ; 32 x 8
projs       equ #BE00       ; 20 x 10
fxs         equ #BEC8       ; 12 x 4
ENT_END     equ #BEF8
STACK_TOP   equ #C000


PF_Y        equ 16
PF_H        equ 168
NCOL        equ 20
NROW        equ 14
TH          equ 12

; keyboard matrix codes (line*8 + bit)
K_UP        equ 0
K_RIGHT     equ 1
K_DOWN      equ 2
K_ENTER     equ 6
K_LEFT      equ 8
K_COPY      equ 9
K_RETURN    equ 18
K_P         equ 27
K_O         equ 34
K_H         equ 44
K_Q         equ 67
K_A         equ 69
K_L         equ 36
K_M         equ 38
K_N         equ 46
K_SPACE     equ 47
K_6         equ 48
K_5         equ 49
K_4         equ 56
K_3         equ 57
K_S         equ 60
K_1         equ 64
K_2         equ 65
K_ESC       equ 66
J_UP        equ 72
J_DOWN      equ 73
J_LEFT      equ 74
J_RIGHT     equ 75
J_FIRE2     equ 76
J_FIRE1     equ 77
K_DEL       equ 79

        org LOAD_ADDR
start:
        di
        ld sp,STACK_TOP
        im 1
        ld a,#c3
        ld (#0038),a
        ld hl,int_handler
        ld (#0039),hl
        ld hl,bss_start
        ld de,bss_start+1
        ld bc,bss_end-bss_start-1
        ld (hl),0
        ldir
        call hw_init
        call build_tables
        call dirty_reset
        ld hl,SQUARES           ; table of squares 0..63
        ld de,0
        ld bc,1
.sq:    ld (hl),e
        inc hl
        ld (hl),d
        inc hl
        ex de,hl
        add hl,bc
        ex de,hl
        inc bc
        inc bc
        ld a,l
        cp lo(SQUARES+128)
        jr nz,.sq
        ld hl,#a5f3
        ld (seed),hl
        ld a,1
        ld (mus_on),a
        call snd_init
        ei
.main:  call title_screen
        ld a,(framecnt)
        ld hl,seed
        xor (hl)
        ld (hl),a
        call game_run
        jr .main

        include "hw.asm"
        include "gfx.asm"
        include "game.asm"
        include "title.asm"
        include "gen/assets.asm"

code_end:

;------------------------------------------------------------------------------
; variables (not saved in the binary, cleared at start)
;------------------------------------------------------------------------------
bss_start:
framecnt:   defs 1
last_flip:  defs 1
back_mask:  defs 1
keys:       defs 20         ; live state, then latch
kcur:       defs 10
kold:       defs 10
mus_on:     defs 1
chan_a:     defs C_SIZE
chan_b:     defs C_SIZE
sfx_active: defs 1
sfx_ptr:    defs 2
sfx_cur_prio: defs 1
sfx_noise:  defs 1
tgt_tab:    defs 1
tgt_mask:   defs 1
both_fn:    defs 2
spr_src:    defs 2
spr_h:      defs 1
rr_h:       defs 1
rr_w:       defs 1
dl_cur_base: defs 2
dl_cur_ptr: defs 2
dl_oth_base: defs 2
dl_oth_ptr: defs 2
fill_val:   defs 1
txt_pairs:  defs 4
txt_x:      defs 1
txt_y:      defs 1
txt_x0:     defs 1
txt_dw:     defs 1
txt_dh:     defs 1
gl_ptr:     defs 2
pn_cnt:     defs 1
pn_nz:      defs 1
pn_zero:    defs 1
lang:       defs 1
seed:       defs 2
tpage:      defs 1
ttimer:     defs 2
tmp_i:      defs 1
tmp_y:      defs 1

; cleared by game_init
game_vars:
funds:      defs 2
hp:         defs 1
wave_num:   defs 1
wave_state: defs 1
cd_sec:     defs 1
cd_sub:     defs 1
sp_ptr:     defs 2
sp_left:    defs 1
sp_timer:   defs 1
sp_type:    defs 1
sp_iv:      defs 1
en_count:   defs 1
gen_ctr:    defs 1
game_over:  defs 1
quit:       defs 1
paused:     defs 1
cur_c:      defs 1
cur_r:      defs 1
sel_type:   defs 1
rep_t:      defs 1
hud_flags:  defs 1
ban_on:     defs 1
ban_id1:    defs 1
ban_id2:    defs 1
ban_timer:  defs 1
ps_on:      defs 1
ps_id1:     defs 1
ps_id2:     defs 1
sacks_gone: defs 1
tmp_cost:   defs 1
tmp_idx:    defs 1
tr_range:   defs 1
tr_range2:  defs 2
tr_cd:      defs 1
tr_dmg:     defs 1
tr_flags:   defs 1
tr_proj:    defs 1
tr_sfx:     defs 1
best_prog:  defs 2
best_ix:    defs 2
sp_ptype:   defs 1
sp_pdmg:    defs 1
sp_pflag:   defs 1
end_wait:   defs 1
dbg_el:     defs 1
game_vars_end:
bss_end:

        assert bss_end <= #4000
        assert (DLIST0 & #ff) == 0
        assert ENT_END <= #BF00

        print "code+data end: ",{hex}code_end,"  bss end: ",{hex}bss_end,"  free: ",#4000-bss_end

        RUN start
        SAVE 'VROUVES.BIN',LOAD_ADDR,code_end-LOAD_ADDR
