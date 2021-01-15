@
@ Unofficial Behringer Control Development Kit
@   - Common assembler prologue to be used with linker script bc2000.lds
@
@  Copyright (C) 2010 Willem van Engen <dev-bc2000@willem.engen.nl>
@
@  This program is free software; you can redistribute it and/or modify
@  it under the terms of the GNU General Public License as published by
@  the Free Software Foundation; either version 2 of the License, or
@  (at your option) any later version.
@
@  This program is distributed in the hope that it will be useful,
@  but WITHOUT ANY WARRANTY; without even the implied warranty of
@  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
@  GNU General Public License for more details.
@
@  You should have received a copy of the GNU General Public License along
@  with this program; if not, write to the Free Software Foundation, Inc.,
@  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
@
	.global start
	.global bootloader
	.global eint
	.global dint
	.global _irq_dummy

	@ user-supplied main
	.extern main

	@ symbols set by linker
	.extern _bstart
	.extern _bend

	@ bootloader's load address
	.equ _bootloader_base, 0x2180000

	.arm


	.section "vectors"
	@ entry point called by bootloader
	b	start
	@ irq handler called by bootloader when PM0&0x8000 is cleared
	b	_irq


	.text
	@
	@ Entry point: setup memory and run main
	@
start:
	@ clear bss
	ldr	%r0, =_bstart
	ldr	%r1, =_bend
	mov	%r2, #0
   bss_loop:
	cmp	%r0, %r1
	bge	run_main
	str	%r2, [%r0], #4
	b	bss_loop

   run_main:
	@ call main
	ldr	%r0, _a_main
	mov	%lr, %pc
	bx	%r0

	@ and return to bootloader
	b	bootloader

   _a_main: .word main


	@
	@ IRQ function: call real irq handler
	@	The use of bx makes sure thumb works as well. Note that registers are
	@   saved already by the bootloader's IRQ handler that call us.
	@
_irq:
	ldr	%r3, _a_irq
	bx	%r3
	
	@ default dummy irq implementation (see linker script)
_irq_dummy:
	bx	%lr

   _a_irq: .word irq

	@
	@ enable interrupts
	@
eint:	msr	CPSR_c, 0x53
	bx	%lr

	@
	@ disable interrupts
	@
dint:	msr	CPSR_c,	0xd3
	bx	%lr

	@
	@ run the bootloader's load function to flash firmware
	@	but first clear highest bit of PM0 to indicate that the bootloader's
 	@   IRQ handler shouldn't pass them on to the operating system's handler.
	@
bootloader:
	bl	dint
	ldr	%r2, =0x0600620
	ldrh	%r1, [%r2]
	mov	%r3, #0x8000
	sub	%r3, #1
	and	%r1, %r3
	strh	%r1, [%r2]
	bl	eint
	ldr	%r0, =_bootloader_base+0x60+0x5a6+1
	bx	%r0

