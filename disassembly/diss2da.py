#!/usr/bin/env python
#
#  ARM disassembly annotation extractor
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

#
# Convert an annotated disassembly (based on binary objdump) to a file with
# annotations only that can be used to reconstruct it when combined with
# the original binary file.
#

import sys, os, re, getopt

_usage = r"""
extract annotations from ARM disassembly
Usage: %s [-h] [-f] [-i input_file] [-o out_file]

    -i   name of disassembly input file (default: standard input)
    -o   name of disassembler annotation output file (default: standard output)
    -f   force overwriting of the output file
    -h   show this help
"""[1:] % (sys.argv[0])


def line(addr, cmd, outf):
	'''output a line or pop multiple lines if cmd is array'''
	if hasattr(cmd, '__iter__'):
			while len(cmd)>0: line(addr, cmd.pop(0), outf)
	else:
		outf.write("%x: %s\n"%(addr, cmd))

def findlen(s):
	'''find the number of elements of a .<data> argument.
	   e.g. "01 92 85 00*5 29 04" returns 10.'''
	count = 0
	# seperate by either comma's or whitespace
	parts = s.split(',')
	if len(parts)==1: parts = s.split()
	for p in parts:
		tparts = p.split('*')
		if len(tparts)>1: count += int(tparts[1], 10)
		else: count += 1
	return count

def parse_diss(inf, outf):
	outf.write(": .___ disassembly annotation\n")
	outf.write(": .daversion 0.1\n")

	i = 0
	addr = -1
	nextlines = []
	prevaddr = addr
	for l in inf.readlines():
		i += 1
		parsed = False
		comment = None

		# ignore three dots output by objdump
		if re.match(r'\s*\.{3}\s*$', l):
			continue

		# rebase command resets previous address
		if re.match(r'\s*\.rebase', l):
			prevaddr = -1

		# dot-commands are for the next address
		if re.match(r'\s*\.', l):
			nextlines.append(l.rstrip())
			continue

		# standalone comments on line
		if re.match(r'\s*;', l):
			nextlines.append('.cs '+l.rstrip())
			continue

		# empty lines are empty standalone comments
		if re.match(r'\s*$', l):
			nextlines.append('.cs')
			continue

		# code:   " addr: <hex> <opcode>"
		m = re.match(r'\s*([0-9a-f]+):\s+(([0-9a-f]+\s)+)\s*([a-z]+.*?)(\s*;.*)?$', l)
		if not parsed and m:
			addr = int(m.group(1),16)
			comment = m.group(5)
			parsed = True

		# ascii data
		m = re.match(r'\s*([0-9a-f]+):(\s+.ascii)?\s*(\s+((".*?")(\s*\*\s*[0-9]+)?(\s*,?)))(\s*;.*)?$', l)
		if not m:
			m = re.match(r'\s*([0-9a-f]+):(\s+.ascii)?\s*(\s+((\'.*?\')(\s*\*\s*[0-9]+)?(\s*,)?))(\s*;.*)?$', l)
		if m:
			addr = int(m.group(1),16)
			data = m.group(3)
			comment = m.group(7)
			parsed = '.ascii [%x]'%(len(data.strip())-2)

		# data
		for q in (('.byte','2'), ('.short','4'), ('.word','8')):
			m = re.match(r'\s*([0-9a-f]+):(\s+'+q[0]+')?\s*((\s+[0-9a-f]{'+q[1]+'}(\s*\*\s*[0-9]+)?(\s*,)?)+)(\s*;.*)?$', l)
			if m:
				addr = int(m.group(1),16)
				data = m.group(3)
				comment = m.group(7)
				parsed = q[0]+' [%x]'%findlen(data)

		if parsed:
			if addr > prevaddr: line(addr, nextlines, outf)
			if comment: line(addr, ".cl "+comment.rstrip(), outf)
			if parsed != True: line(addr, parsed, outf)
			prevaddr = addr
		else:
			# unrecognised line
			sys.stderr.write('ignoring line %d\n'%i)


##############################################################################
## Main program

if __name__ == "__main__":
    #
    # parse options
    #
    try:
        opts, args = getopt.getopt(sys.argv[1:], "i:o:hf")
    except getopt.GetoptError:
        sys.stderr.write(_usage)
        sys.exit(1)

    inf             = sys.stdin
    outf            = sys.stdout
    infile          = None
    outfile         = None
    force_overwrite = False
    param_given     = False

    for o, a in opts:
        param_given = True
        if o == "-i":
            infile = a
        if o == "-o":
            outfile = a
        if o == "-h":
            sys.stderr.write(_usage)
            sys.exit(0)
        if o == "-f":
            force_overwrite = True

    #
    # validate options
    #
    if len(args) > 0:
        sys.stderr.write(_usage)
        sys.exit(1)

    #
    # open files
    #
    if infile:
        try:
            inf = open(infile, 'rb')
        except:
            sys.stderr.write("Unable to open %s.\n" % infile)
            sys.exit(1)

    if outfile:
        if os.path.exists(outfile) and not force_overwrite:
            sys.stderr.write("Output file %s exists.\n" % outfile)
            sys.exit(1)
        try:
            outf = open(outfile, 'w')
        except:
            sys.stderr.write("Unable to open %s.\n" % outfile)
            sys.exit(1)

    parse_diss(inf, outf)

# vim:ts=4:sw=4:expandtab:
