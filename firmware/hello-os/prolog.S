@
@ Unofficial Behringer Control Development Kit
@   - Assembler prolog for hooking into the official firmware with
@     an adapted jump
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
	.global	os
	.global eint
	.global dint

	@ user-supplied main
	.extern main

	@ symbols set by linker
	.extern _bstart
	.extern _bend

	.arm

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

	@ and return to operating system
	b	os

   _a_main: .word main


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
	@ continue running the main operating system
	@
os:	ldr	%r0, =0x02000135
	bx	%r0

