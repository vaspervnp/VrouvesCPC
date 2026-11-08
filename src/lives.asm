;==============================================================================
; lives.asm - the lives of the difficulty chosen on the title (Easy 4, Medium
; 3, Hard 2, Hardest none): a stage lost with a life left is played again,
; with the score as it was when the stage began.  Resident; tails_install
; sets the lives and rt_chk when a game starts.
;==============================================================================
; after game_run.  Carry: on as before (won, quit, or lost with no life
; left); no carry: lost, a life gone, play the stage again.
rt_retry:
        ld hl,(score)
        ld a,(game_over)
        cp 2
        jr z,.lost
        ld (rt_chk),hl          ; won (or quit): the score to go back to
        ret
.lost:  ld a,(rt_lives)
        sub 1
        ret c
        ld (rt_lives),a
        ld hl,(rt_chk)
        ld (score),hl
        ret
