;==============================================================================
; lives.asm - the lives of the difficulty chosen on the title (Easy 4, Medium
; 3, Hard 2, Hardest none): a stage lost with a life left is played again,
; with the score as it was when the stage began.
;
; It fills what the other tail chunks leave over (see tails.asm), so it comes
; in pieces, each placed right after the code of a chunk.
;==============================================================================
        org syn_find_end,SYN_SRC+48+syn_find_end-TAIL_SYNFIND
; after game_run.  Carry: on as before (won, quit, or lost with no life
; left); no carry: lost, a life gone, play the stage again.
rt_retry:
        ld hl,(score)
        ld a,(game_over)
        cp 2
        jp z,rt_lost
        ld (rt_chk),hl          ; won (or quit): the score to go back to
        ret
rt_lives: db 0                  ; set by tails_install
rt_chk:   dw 0                  ; the score when this stage began
rt_a_end:
        assert rt_a_end <= TAIL_SYNFIND+48

        org syn_dmg_end,SYN_SRC+3*48+syn_dmg_end-TAIL_SYNDMG
rt_lost:
        ld a,(rt_lives)
        sub 1
        ret c
        jp rt_lost2
rt_b_end:
        assert rt_b_end <= TAIL_SYNDMG+48

        org syn_data_end,SYN_SRC+syn_data_end-TAIL_SYNDATA
rt_lost2:
        ld (rt_lives),a
        ld hl,(rt_chk)
        ld (score),hl
        ret
rt_c_end:
        assert rt_c_end <= TAIL_SYNDATA+48

; sc_show's texts: "SCORE ", then " LIVES "
        org sc_build_end,SYN_SRC+5*48+sc_build_end-TAIL_SCBUILD
        include "gen/score_text_en.asm"
rt_d_end:
        assert rt_d_end <= TAIL_SCBUILD+48

        org sc_sell_end,SYN_SRC+6*48+sc_sell_end-TAIL_SCSELL
        include "gen/score_text_gr.asm"
rt_e_end:
        assert rt_e_end <= TAIL_SCSELL+48
