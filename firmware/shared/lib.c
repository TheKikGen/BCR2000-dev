/*
 * Unofficial Behringer Control Development Kit - Convenience functions
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
#include "bootfun.h"
#include "lib.h"

/* standard strlen function */
int strlen(const char *src) {
	const char *start = src;
	while (*(src++));
	return src - start;
}

/* sleep for a while, seems to be almost x/16 seconds (non-optimised) */
void sleep(int x) {
	int i;
	for (i=0; i<(1<<14)*x; i++) {
		asm("nop; nop; nop; nop;");
	}
}

/* display a string by scrolling (len>=4) */
void disp_scroll(const char *msg) {
    int i;
	int len = strlen(msg);
    for (i=0; i<=len-4; i++) {
        disp_put(msg+i);
        sleep(5);
    }
}

/* display a string by scrolling left (len>=4) */
void disp_scroll_right(const char *msg) {
    int i;
	int len = strlen(msg);
    for (i=len-4; i>=0; i--) {
        disp_put(msg+i);
        sleep(5);
    }
}
/* display a hword as hex */
void disp_hword(short x) {
	int i;
	char c;
	char *buf = "    ";
	for (i=0; i<4; i++) {
		c = (x>>(12-4*i))&0xf;
		c += (c > 9) ? 'A'-10 : '0';
		buf[i] = c;
	}
	disp_put(buf);
}

/* display a word as hex by scrolling */
void disp_word(int x) {
	int i;
	char c;
	char *buf = "        ";
	for (i=0; i<8; i++) {
		c = (x>>(28-4*i))&0xf;
		c += (c > 9) ? 'A'-10 : '0';
		buf[i] = c;
	}
	disp_scroll(buf);
}

