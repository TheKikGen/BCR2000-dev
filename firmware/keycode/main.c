/*
 * Unofficial Behringer Control Development Kit - example: keycode
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
/*
 * Example program: keycode
 *
 * When a key is pressed, the keycode is showed on the display, and a
 * midi system exclusive packet is sent with the keycode inside.
 * When STORE and LEARN are pressed simultaneously, the program exits.
 */
#include "system.h"
#include "bootfun.h"
#include "lib.h"
#include "hardware.h"

/*
 * Program entry point.
 */
int main() {
	char i;

	/* let interrupts be handled by bootloader */
	*PM0 &= ~0x8000;
	eint();

	/* show something so it's visible the device is on */
	disp_put(" -- ");

	/* display key codes until learn+store is pressed */
	while (!get_key(KEY_LEARN) || !get_key(KEY_STORE)) {
		for (i=0; i<0x29; i++) {
			if (get_key(i)) {
				disp_hword(i);
			}
		}
	}

	return 0;
}

