/*
 * Unofficial Behringer Control Development Kit
 *   - Test program that hooks into the original Behringer firmware
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
#include "prolog.h"

/*
 * Display put function
 *
 * As this is a callout to the original firmware, the address must be known.
 * Now this is different for some firmware versions, so after the Makefile has
 * detected the model and version of the firmware, we now pick the address for
 * the firmware supplied.
 */
#include "model.h"
#if defined(FIRMWARE_MODEL_BCF2000)
#	if (FIRMWARE_VERSION == 110 || FIRMWARE_VERSION == 107)
#		define DISPLAY_PUT_OFFSET 0x16e6
#	endif
#elif defined(FIRMWARE_MODEL_BCR2000)
#	if (FIRMWARE_VERSION == 110 || FIRMWARE_VERSION == 107)
#		define DISPLAY_PUT_OFFSET 0x168a
#	endif
#endif
#ifndef DISPLAY_PUT_OFFSET
#	error "Don't known location of display routine in firmware."
#endif

typedef void (*disp_put_t)(const char *msg);
static disp_put_t disp_put  = (disp_put_t)((0x02000000 + DISPLAY_PUT_OFFSET) | 1);


/* sleep for a while, seems to be almost x/16 seconds (non-optimised) */
void sleep(int x) {
	int i;
	for (i=0; i<(1<<14)*x; i++) {
		asm("nop; nop; nop; nop;");
	}
}

/* display a string by scrolling (len>=4) */
void disp_scroll_left(const char *msg, int len) {
	int i;
	for (i=0; i<=len-4; i++) {
		disp_put(msg+i);
		sleep(4);
	}
}

/*
 * Program entry point.
 *
 * At return the prolog calls the original OS.
 */
int main() {
	eint();

	disp_scroll_left("   HI  THERE    ",16);
	sleep(5);

	return 0;
}

