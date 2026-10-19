;==============================================================================
; disk.asm - a minimal loader that drives the uPD765 disc controller directly
; (the firmware is switched off).  Files are read sector by sector from known
; positions on the disk (src/gen/diskmap.asm, made by tools/diskmap.py).
;==============================================================================
FDC_MSR     equ #FB7E
FDC_MOTOR   equ #FA7E

; descriptors: track, first sector, number of sectors, destination
TITLE_SECTORS equ (title_end-TITLE_AREA+511)/512
STAGE_SECTORS equ (STAGE_SIZE+511)/512

disk_title:
        db DISK_NEXT_TRACK,DISK_NEXT_SECTOR,TITLE_SECTORS
        dw TITLE_AREA
; ENDING.SCR (16K) comes right after TITLE.BIN, in whole 1K blocks
ENDING_BLOCK equ DISK_NEXT_BLOCK+(title_end-TITLE_AREA+1023)/1024
disk_ending:
        db (ENDING_BLOCK*2)/9,#C1+(ENDING_BLOCK*2)%9,32
        dw #C000
; disk_stages: one descriptor per stage file, in src/gen/diskmap.asm

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

; HL = descriptor.  The screen is blacked out and the music held while
; loading; whole sectors are read, so up to 511 bytes past the end of the
; data are overwritten (the #4000 screen or the background buffer).
disk_load:
        ld a,(hl)
        ld (dk_track),a
        inc hl
        ld a,(hl)
        ld (dk_sector),a
        inc hl
        ld a,(hl)
        ld (dk_count),a
        inc hl
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        ld (dk_dest),hl
        call palette_black
        ld a,(mus_on)
        push af
        xor a
        ld (mus_on),a
        ld (dk_err),a
        ld bc,FDC_MOTOR
        inc a
        out (c),a               ; motor on, let it spin up
        ld b,30
.sp:    push bc
        call wait_frame
        pop bc
        djnz .sp
        ld a,3                  ; specify: step rate, head times, no DMA
        call fdc_out
        ld a,#a1
        call fdc_out
        ld a,3
        call fdc_out
.recal: ld a,7                  ; recalibrate: back to track 0
        call fdc_out
        xor a
        call fdc_out
        call fdc_wait_seek
.sec:   ld a,#0f                ; seek
        call fdc_out
        xor a
        call fdc_out
        ld a,(dk_track)
        call fdc_out
        call fdc_wait_seek
        call fdc_read
        jr nc,.ok
        ld hl,dk_err            ; error: retry, from track 0 every 4th time
        inc (hl)
        ld a,(hl)
        and 3
        jr z,.recal
        jr .sec
.ok:    ld (dk_dest),hl
        ld hl,dk_sector
        ld a,(hl)
        inc a
        cp #ca
        jr c,.s
        ld a,(dk_track)
        inc a
        ld (dk_track),a
        ld a,#c1
.s:     ld (hl),a
        ld hl,dk_count
        dec (hl)
        jr nz,.sec
        ld bc,FDC_MOTOR
        xor a
        out (c),a
        pop af
        ld (mus_on),a
        ret

; read sector (dk_track, dk_sector) to (dk_dest) -> HL = end, carry on error
fdc_read:
        ld a,(dk_sector)
        ld (dk_eot),a
        ld hl,dk_cmd
        ld b,9
.c:     ld a,(hl)
        inc hl
        push bc
        call fdc_out
        pop bc
        djnz .c
        ld hl,(dk_dest)
        ld bc,FDC_MSR
        di                      ; a byte every 32 microseconds
.x:     in a,(c)
        jp p,.x
        and #20
        jr z,.done
        inc c
        in a,(c)
        ld (hl),a
        dec c
        inc hl
        jp .x
.done:  ei
        push hl
        call fdc_results
        pop hl
        ld a,(dk_res)           ; ST0: normal, or "abnormal" for end of cylinder
        and #c0
        ret z
        cp #40
        scf
        ret nz
        ld a,(dk_res+1)         ; ST1 = #80: end of cylinder, the usual way out
        cp #80
        ret z
        scf
        ret

; the read command (MFM read data, drive 0: C H R N EOT GPL DTL) with the
; loader's position kept inside it
dk_cmd:     db #46,0
dk_track:   db 0
            db 0
dk_sector:  db 0
            db 2
dk_eot:     db 0
            db #2a,#ff
dk_count:   db 0
dk_dest:    dw 0

fdc_wait_seek:
        ld a,8                  ; sense interrupt status until the seek ends
        call fdc_out
        call fdc_results
        ld a,(dk_res)
        and #20
        jr z,fdc_wait_seek
        ret

; A -> FDC
fdc_out:
        ld bc,FDC_MSR
        push af
.w:     in a,(c)
        add a,a                 ; RQM -> carry, DIO -> sign
        jr nc,.w
        jp m,.w
        pop af
        inc c
        out (c),a
        ret

; result bytes -> dk_res
fdc_results:
        ld hl,dk_res
.r:     ld bc,FDC_MSR
.w:     in a,(c)
        jp p,.w
        and #40
        ret z
        inc c
        in a,(c)
        ld (hl),a
        inc hl
        jr .r
