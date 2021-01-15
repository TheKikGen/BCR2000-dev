#!/usr/bin/env make -f
#
# Unofficial Behringer Control Development Kit
#   - Makefile for use with original Behringer firmware
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

# location of common directory
COMMON=..

# basename of output files
TARGET=test
# architecture to compile for, all gcc tools will be prepended with this
ARCH=arm-eabi

# Official firmware image to run with
# should at least work for bcf2000 and bcr2000 firmware 1.07 and 1.10
FIRMWARE_SRC_SYX=bcf2000_1-10.syx

SRCS=main.c
OBJS=$(patsubst %.c, %.o, $(SRCS))
ELF=$(TARGET).elf
BIN=$(TARGET).bin
SYX=$(TARGET).syx

CFLAGS=-mthumb -mthumb-interwork
LDFLAGS=-Tbc2000-os.lds
ASFLAGS=

# BCFW tools
BCFWCONVERT=$(COMMON)/../bcfwconvert.py
BCFWFLASH=$(COMMON)/../bcfwflash.py

# patched firmware image generated from FIRMWARE_SRC_SYX
#   this file is used in bc2000-os.lds
FIRMWARE_OBJ=osimage.o

all: $(SYX)

.SUFFIXES: .c .S .o .elf .bin .syx
.PHONY: all clean upload

clean:
	rm -f $(ELF) $(BIN) $(OBJS) $(SYX) prolog.o model.h $(FIRMWARE_OBJ)

$(TARGET).elf: prolog.o $(OBJS) $(FIRMWARE_OBJ)
	$(ARCH)-ld $(LDFLAGS) -o $@ prolog.o $(OBJS)

%.o: %.c model.h
	$(ARCH)-gcc $(CFLAGS) -c -o $@ $<

prolog.o: prolog.S
	$(ARCH)-as $(ASFLAGS) -o $@ $<

$(BIN): $(TARGET).elf
	$(ARCH)-objcopy -O binary $< $@

$(SYX): $(BIN)
	$(BCFWCONVERT) -i $< -I os -o $@ -O syx -f

$(FIRMWARE_OBJ): $(FIRMWARE_SRC_SYX)
	@# create os image from official syx file
	$(BCFWCONVERT) -i $< -I syx -o $@ -O os -f
	@# align length so jumps will work
	size=`ls -l $@ | awk '{print $$5}'`; \
	dd if=/dev/zero bs=1 count=$$((4-($$size%4))) of=$@ seek=$$size status=noxfer
	@# make sure that known jump address is present at expected location 160=0xa0
	od -v -j 160 -N 4 -A x -t x4 $@ | grep -q '^\w\+\b\s*02000135\b'
	@# substitute for new jump to just after this image
	ls -l $@ | awk '{val=$$5+0x02000000; printf("%c%c%c%c", and(val, 0xff), \
			and(rshift(val,8),0xff), and(rshift(val,16),0xff), rshift(val,24));}' | \
		dd of=$@ seek=160 bs=1 count=4 conv=notrunc status=noxfer
	@# and convert to an object file for linkin
	$(ARCH)-objcopy -I binary $(FIRMWARE_OBJ) -O elf32-littlearm -B arm \
		$(FIRMWARE_OBJ).real && mv $(FIRMWARE_OBJ).real $(FIRMWARE_OBJ)

model.h: $(FIRMWARE_SRC_SYX)
	@# find out model from firmware file
	echo "/* generated file */" >$@
	sum=`openssl md5 $< | awk '{print $$2;}'`; \
	if [ "$$sum" = "56d3ed69162d82882faa6d46389e20ab" ]; then \
		echo "#define FIRMWARE_MODEL_BCF2000 1" >>$@; \
		echo "#define FIRMWARE_VERSION 110" >>$@; \
		echo "#define MODEL_BCF2000" \
	elif [ "$$sum" = "f57e050a185dcf0401b3afee4f40d21a" ]; then \
		echo "#define FIRMWARE_MODEL_BCF2000 1" >>$@; \
		echo "#define FIRMWARE_VERSION 107" >>$@; \
		echo "#define MODEL_BCF2000" \
	elif [ "$$sum" = "9da7697dc27d5876a5fe21d2c565cde4" ]; then \
		echo "#define FIRMWARE_MODEL_BCR2000 1" >>$@; \
		echo "#define FIRMWARE_VERSION 110" >>$@; \
		echo "#define MODEL_BCR2000 1" \
	elif [ "$$sum" = "49feac9145ad83d0f739011ca8ea5cc4" ]; then \
		echo "#define FIRMWARE_MODEL_BCR2000 1" >>$@; \
		echo "#define FIRMWARE_VERSION 107" >>$@; \
		echo "#define MODEL_BCR2000 1" \
	else \
		rm -f model.h; \
		echo "Unrecognised firmware, sorry cannot continue."; \
		exit 1; \
	fi

$(FIRMWARE_SRC_SYX):
	@echo "A Behringer Control firmware image is required to run."
	@echo "You should be able to download it from"
	@echo "   http://www.behringer.com/EN/Support/B-Control-Downloads.aspx"
	@echo "Then review the variable FIRMWARE_SRC_SYX in this Makefile."
	@false

upload: $(SYX)
	$(BCFWFLASH) -u -i $(SYX)

.PHONY: disassemble-elf disassemble-bin-arm disassemble-bin-thumb
disassemble: $(ELF)
	objdump -D -j .text $(ELF)
disassemble-bin-arm: $(BIN)
	objdump -b binary -m armv5 -D $(BIN)
disassemble-bin-thumb: $(BIN)
	objdump --disassembler-options=force-thumb -b binary -m armv5 -D $(BIN)

