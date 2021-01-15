/*
 * Unofficial Behringer Control Development Kit - example: ledcode
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
 * Example program: ledcode
 *
 * This program helps to discover which code each led has on the BCF2000.
 * A digit can be entered by choosing a button from the two top rows below the
 * encoders. The first row is 0..7, the second 8..f. After two digits are
 * entered, the corresponding led value is turned on.
 * When STORE and LEARN are pressed simultaneously, the program exits.
 */
#include "system.h"
#include "bootfun.h"
#include "lib.h"
#include "hardware.h"

/* display a byte as hex, possibly masking lsbyte */
void disp_byte(char number, char maskfirst) {
	char *buf = "    ";
	buf[2] = (number>>4)&0xf;
	buf[2] += (buf[2] > 9) ? 'A'-10 : '0';
	if (maskfirst) {
		buf[3] = '-';
	} else {
		buf[3] = number&0xf;
		buf[3] += (buf[3] > 9) ? 'A'-10 : '0';
	}
	disp_put(buf);
}

/*
 * Program led point.
 */
int main() {
	char i;
	char led = 0;
	char entered;

	/* let interrupts be handled by bootloader */
	*PM0 &= ~0x8000;
	eint();

	/* show something so it's visible the device is on */
	disp_put("  --");

	/* display key codes until learn+store is pressed */
	while (!get_key(KEY_LEARN) || !get_key(KEY_STORE)) {
		/* get first digit and wait until released */
		entered = 0;
		while ((!get_key(KEY_LEARN) || !get_key(KEY_STORE)) && !entered) {
			for (i=KEY_ROW1(0); i<KEY_ROW1(0)+16; i++) {
				if (get_key(i)) {
					led = (i-KEY_ROW1(0))<<4;
					entered = 1;
					break;
				}
			}
		}
		while (get_key(i));
		disp_byte(led, 1);
		/* and second */
		entered = 0;
		while ((!get_key(KEY_LEARN) || !get_key(KEY_STORE)) && !entered) {
			for (i=KEY_ROW1(0); i<KEY_ROW1(0)+16; i++) {
				if (get_key(i)) {
					led |= i-KEY_ROW1(0);
					entered = 1;
					break;
				}
			}
		}
		while (get_key(i));
		disp_byte(led, 0);
		/* now set the corresponding led */
		set_led(led, 1);
	}

	return 0;
}

