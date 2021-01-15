/*
 * Unofficial Behringer Control Development Kit
 *   - Linker script for Behringer Control operating system images
 *
 *  Copyright (C) 2010 Willem van Engen <dev-bc2000@willem.engen.nl>
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License along
 *  with this program; if not, write to the Free Software Foundation, Inc.,
 *  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
 */
OUTPUT_FORMAT(elf32-littlearm);
OUTPUT_ARCH(arm);

MEMORY {
	flash (rx)  : ORIGIN = 0x00000000, LENGTH = 512k  /* flash chip */
	iram  (rwx) : ORIGIN = 0x00200000, LENGTH = 4k    /* cpu-internal ram */
	sram  (rwx) : ORIGIN = 0x02000000, LENGTH = 2M    /* external ram */
}

SECTIONS {

	/* The bootloader copies the operating system image from flash to the start
   	 * of the ram start of the ram and deobfuscates it. */
	.text : AT(0) {
		* (vectors);
		* (.text .glue_7 .glue_7t .rodata .data);
	} > sram

	/* statically allocated variables  TODO put in iram */
	_bstart = .;
	.bss : {
		* (.bss);
		* (COMMON);
		. = ALIGN(4); /* so we can clear it using words */
	}
	_bend = . ;

	/* end of everything, used by malloc() and friends for heap */
	_end = .;
}

/* Interrupt routine: if a function irq() is defined use that, else use a
 * default implementation that returns immediately. */
PROVIDE(irq = _irq_dummy);

