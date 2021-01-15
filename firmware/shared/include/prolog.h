/*
 * Unofficial Behringer Control Development Kit
 *   - C function definitions for public functions in prolog.S
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
#ifndef __PROLOG_H__
#define __PROLOG_H__

/* Enable interrupts */
extern void eint();

/* Disable interrupts */
extern void dint();

/* Jump to the bootloader's "load" function (or just return from main) */
extern void bootloader();

#endif /* __PROLOG_H__ */
