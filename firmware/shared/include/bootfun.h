/*
 * Unofficial Behringer Control Development Kit
 *   - Function definitions for those located inside the bootloader.
 *
 *  Copyright (C) 2012 Willem van Engen <dev-bc2000@willem.engen.nl>
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
#ifndef __BOOTFUN_H__
#define __BOOTFUN_H__

/* start address of bootloader in memory */
#define BOOTLOADER_BASE 0x2180000

/* Convenience macro to define a function; my disassembly starts at 0x60 so
 * this offset is included here. The |1 in the definitions is because these
 * are thumb functions.
 * The addresses for the BCR2000 differ slightly from the BCF2000, so
 * depending on the device one is used. */
#if defined(BCF2000)
#define DEFINE_FUNC(ret, name, args, addr_bcf, addr_bcr) \
	typedef ret (*name##_t)args; \
	static name##_t name = (name##_t)((BOOTLOADER_BASE)+0x60+(addr_bcf));
#elif defined(BCR2000)
#define DEFINE_FUNC(ret, name, args, addr_bcf, addr_bcr) \
	typedef ret (*name##_t)args; \
	static name##_t name = (name##_t)((BOOTLOADER_BASE)+0x60+(addr_bcr));
#else
#error "Select model: either BCF2000 or BCR2000 needs to be defined."
/* define something to avoid compile errors in this header file */
#define DEFINE_FUNC(ret, name, args, addr_bcf, addr_bcr)
#endif


/* Return if key is pressed or not for a key index (<0x29)
 *   char get_key(int idx)
 */
DEFINE_FUNC(char, get_key, (int idx), 0x134c|1, 0x1378|1);

/* Put a message of four characters on the display
 * valid characters: " 1234567890ABCDEFLMOPS-nobt"
 *    void disp_put(const char *msg)
 */
DEFINE_FUNC(void, disp_put, (const char *msg), 0x13a8|1, 0x13d8|1);

/* Midi send; make unknown arguments zero */
DEFINE_FUNC(void, midi_send_byte, (char byte, int p, int q), 0xe00|1, 0xe00|1);
DEFINE_FUNC(void, midi_send_block, (char *data, int len, int p, int q), 0xf2c|1, 0xf2c|1);
/* Send Behringer SysEx header with cmd as command */
DEFINE_FUNC(void, midi_send_behringer, (char cmd, int p, int q), 0xf54|1, 0xf54|1);

/* Set a led for a led index (=<0xc0); only lowest bit of on is relevant. */
DEFINE_FUNC(void, set_led, (int idx, char on), 0x136c|1, 0x1398|1);


#undef DEFINE_FUNC

#endif /* __BOOTFUN_H__ */
