/*
 * Unofficial Behringer Control Development Kit - Example: hello
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
#include "system.h"
#include "bootfun.h"
#include "lib.h"

/*
 * Program entry point.
 */
int main() {
	/* let interrupts be handled by bootloader */
	*PM0 &= ~0x8000;
	eint();

	/* display message */
	disp_put("ALLO");
	sleep(30);

	/* and return to waiting for new firmware */
	return 0;
}

