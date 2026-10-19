;==============================================================================
; tape.asm - the cassette version's loader, in place of disk.asm (rasm
; -DTAPE=1).  The firmware is switched off, so the blocks after VROUVES.BIN
; are in a format of our own (tools/make_cdt.py), read straight from the PPI:
;   pilot (600us pulses), sync (two 150us pulses), then bytes, MSB first,
;   each bit two pulses (200us for 0, 400us for 1):
;   block id, data length (2), the data, XOR of all the bytes before.
; The border stripes while a block loads; a block with another id is
; skipped, so after a load error the tape can be wound back a little.
;==============================================================================
TP_BIT    equ 46                ; edge loop counts for two pulses: 0 is ~30, 1 ~63
TP_PILOT  equ 38                ; and for one pilot pulse ~48 (a 1 pulse ~31)

; descriptors, as for the disk: block id, -, -, destination
disk_title:
        db 1,0,0
        dw TITLE_AREA
disk_ending:
        db NUM_STAGES+2,0,0
        dw #C000
disk_stages:
        repeat NUM_STAGES,tp_k
        db tp_k+1,0,0
        dw STAGE_AREA
        rend

; A = stage (0..)
stage_load:
        ld l,a
        add a,a
        add a,a
        add a,l
        ld l,a
        ld h,0
        ld de,disk_stages
        add hl,de
        ; fall through

; HL = descriptor.  The screen is blacked out and the music stopped while
; the block loads, with interrupts off.
disk_load:
        ld a,(hl)
        ld (tp_id),a
        inc hl
        inc hl
        inc hl
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        ld (tp_dest),hl
        call palette_black
        ld a,(mus_on)
        push af
        xor a
        ld (mus_on),a
        call wait_frame         ; let the music fall silent
        call wait_frame
        di
        push ix
        push iy
        ld bc,#f610             ; cassette motor on
        out (c),c
        ld bc,#7f10             ; the border, from now on B = gate array
        out (c),c
.find:  ld a,#f5
        in a,(#ff)
        ld e,a                  ; E = tape level
.pil:   ld h,0                  ; pilot pulses in a row
.pl:    ld d,0
        call tp_edge
        jr z,.find
        ld a,d
        cp TP_PILOT
        jr c,.sync
        cp 2*TP_PILOT
        jr nc,.pil
        inc h
        jr nz,.pl
        dec h
        jr .pl
.sync:  ld a,h                  ; a short pulse after a long pilot
        cp 128
        jr c,.pil
        ld d,0
        call tp_edge            ; the second sync pulse
        jr z,.find
        call tp_byte
        jr c,.find
        ld iyl,a                ; the checksum
        ld hl,tp_id
        cp (hl)
        jr nz,.find             ; another block: wait for the next one
        call tp_byte
        jr c,.find
        ld ixl,a
        call tp_byte
        jr c,.find
        ld ixh,a                ; IX = length
        ld a,iyl
        xor ixl
        xor ixh
        ld iyl,a
        ld hl,(tp_dest)
.dat:   call tp_byte
        jr c,.find
        ld (hl),a
        inc hl
        xor iyl
        ld iyl,a
        dec ix
        ld a,ixh
        or ixl
        jr nz,.dat
        call tp_byte
        jr c,.find
        xor iyl
        jr nz,.find             ; bad checksum: wind back and play again
        ld a,#54                ; border black, motor off
        out (c),a
        ld bc,#f600
        out (c),c
        pop iy
        pop ix
        ei
        pop af
        ld (mus_on),a
        ret

; -> A = the next byte, carry if the signal was lost
tp_byte:
        ld c,1                  ; a marker bit that falls out after 8 bits
.b:     ld d,0
        call tp_edge
        jr z,.err
        call tp_edge
        jr z,.err
        ld a,d
        cp TP_BIT               ; NC: a 1
        ccf
        rl c
        jr nc,.b
        ld a,c
        or a
        ret
.err:   scf
        ret

; wait for the tape level to change: D counts up (12us a turn), E = level.
; NZ: an edge, with the border striped; Z: none before D wrapped.
tp_edge:
.l:     inc d
        ret z
        ld a,#f5
        in a,(#ff)
        xor e
        jp p,.l
        ld a,e
        cpl
        ld e,a
        rlca
        and 1
        or #4c                  ; bright red or mauve
        out (c),a
        ret

tp_id:   db 0
tp_dest: dw 0
