#!/usr/bin/env make -f
#
# Unofficial Behringer Control Development Kit - Makefile
#
#  Copyright (C) 2010 Willem van Engen <dev-bc2000@willem.engen.nl>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

# set this to either BCF2000 or BCR2000, depending on your target
MODEL=BCF2000

# location of common directory
COMMON=..

# basename of output files
TARGET=test
# architecture to compile for, all gcc tools will be prepended with this
ARCH=arm-eabi

SRCS=main.c $(SHARED)/lib.c
OBJS=$(patsubst %.c, %.o, $(SRCS))
ELF=$(TARGET).elf
BIN=$(TARGET).bin
SYX=$(TARGET).syx

CFLAGS=-mthumb -mthumb-interwork -I$(SHARED)/include -D$(MODEL)

LIBS=`$(ARCH)-gcc -print-libgcc-file-name`
LDFLAGS=-T$(SHARED)/bc2000.lds
ASFLAGS=

# BCFW tools
BCFWCONVERT=$(COMMON)/../bcfwconvert.py
BCFWFLASH=$(COMMON)/../bcfwflash.py

SHARED=$(COMMON)/shared

all: $(SYX)

.SUFFIXES: .c .S .o .elf .bin .syx
.PHONY: all clean upload

clean:
	rm -f $(ELF) $(BIN) $(OBJS) $(SYX) prolog.o

$(TARGET).elf: prolog.o $(OBJS)
	$(ARCH)-ld $(LDFLAGS) -o $@ prolog.o $(OBJS) $(LIBS)

%.o: %.c
	$(ARCH)-gcc $(CFLAGS) -c -o $@ $<

prolog.o: $(SHARED)/prolog.S
	$(ARCH)-as $(ASFLAGS) -o $@ $<

$(BIN): $(TARGET).elf
	$(ARCH)-objcopy -O binary $< $@

$(SYX): $(BIN)
	$(BCFWCONVERT) -m $(MODEL) -i $< -I os -o $@ -O syx -f

upload: $(SYX)
	$(BCFWFLASH) -u -i $(SYX)

.PHONY: disassemble-elf disassemble-bin-arm disassemble-bin-thumb
disassemble: $(ELF)
	objdump -D -j .text $(ELF)
disassemble-bin-arm: $(BIN)
	objdump -b binary -m armv5 -D $(BIN)
disassemble-bin-thumb: $(BIN)
	objdump --disassembler-options=force-thumb -b binary -m armv5 -D $(BIN)

