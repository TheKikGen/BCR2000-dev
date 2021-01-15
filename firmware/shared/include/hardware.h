/*
 * Unofficial Behringer Control Development Kit - led- & keycode definitions
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
#ifndef __HARDWARE_H__
#define __HARDWARE_H__

/*
 * Key indices for get_key()
 */
#define KEY_ENC		(x)		/* encoder push (0-7) */
#define KEY_ROW1(x)	(0x08+x)	/* row 1 below encoders (0-7) */
#define KEY_ROW2(x)	(0x10+x)	/* row 2 below encoders (0-7) */
#define KEY_GRP(x)	(0x18+x)	/* encoder groups (0-3) */
#define KEY_STORE	 0x20
#define KEY_LEARN	 0x21
#define KEY_EDIT 	 0x22
#define KEY_EXIT 	 0x23
#define KEY_BR(x)	(0x24+x)	/* bottom right buttons (0-3) */
#define KEY_PPREV	 0x1c		/* previous preset */
#define KEY_PNEXT	 0x1d		/* next preset */

/*
 * Led indices for set_led()
 */
#define LED_ROW1(x)	(0x47+8*x)	/* row 1 below encoders (0-7) */
#define LED_ROW2(x)	(0x80+x)	/* row 2 below encoders (0-7) */
#define LED_GRP(x)	(0x88+x)	/* encoder groups (0-3) */
#define LED_MIDI_IN	 0x90		/* flashes when set */
#define LED_MIDI_A	 0x91		/* flashes when set */
#define LED_MIDI_B	 0x92		/* flashes when set */
#define LED_FOOT_SW	 0x93		/* flashes when set */
#define LED_FOOT_CTRL	 0x94		/* flashes when set */
#define LED_USB_MODE	 0x95
#define LED_STORE	 0x98
#define LED_LEARN	 0x99
#define LED_EDIT	 0x9a
#define LED_EXIT	 0x9b
#define LED_BR(x)	(0x9c+x)	/* bottom right buttons (0-3) */
/* leds of encoder x (BCF:0-7, BCR:0-31), position p (0-14) */
#define LED_ENC(x,p)	( 8*(x%8) + (x>>3)*0x80 + (x>7?0x40:0) +  \
                             p%8  +               (p>7?0x40:0)   )
/* leds of display, digit x (0-3), segment p (0-7) */
#define LED_DISP(x,p)	(0xa0+(x*8+p))



/* Q: Why aren't LED_ROW?(x) defined as LED_ROW(x), noting LED_ENC(x,p)?
 * A: I'd like to keep a relation between the encoder index and led index,
 *    since they visually belong to each other. Perhaps LED_ROW(x,y) would
 *    be slightly cleaner. Let me know if you think so.
 *
 * Q: What's does (x>>3)*0x80+(x>7?0x40:0) do ?
 * A: Using this formula allows one to iterate over all LEDs easily.
 *      for  0<=x<= 7, returns 0x000
 *      for  8<=x<=15, returns 0x0c0
 *      for 16<=x<=23, returns 0x140
 *      for 24<=x<=31, returns 0x1c0
 */

#endif /* __HARDWARE_H__ */
