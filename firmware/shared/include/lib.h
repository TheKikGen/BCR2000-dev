/*
 * Unofficial Behringer Control Development Kit - Convenience function headers
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
#ifndef __LIB_H__
#define __LIB_H__

/* standard strlen function */
extern int strlen(const char *src);

/* sleep for a while, seems to be almost x/16 seconds (non-optimised) */
extern void sleep(int x);

/* display a string by scrolling (len>=4) */
extern void disp_scroll(const char *msg);
extern void disp_scroll_right(const char *msg);

/* display a short as hex */
extern void disp_hword(short x);

/* display a word as hex by scrolling */
extern void disp_word(int x);

#endif /* __LIB_H__ */
