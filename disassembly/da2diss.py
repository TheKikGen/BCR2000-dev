#!/usr/bin/env python
#
#  Annotated ARM disassembler
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
# Disassemble a binary file with the help of a disassembly annotation file,
# containing comments and disassembling hints.
#

import sys, os, re, tempfile, getopt
from subprocess import Popen, PIPE

_usage = r"""
annotated ARM disassembler
Usage: %s [-h] [-f] [-i input_file] [-o out_file] file_to_disassemble

    -i   name of annotation input file (default: standard input)
    -o   name of output file (default: standard output)
    -f   force overwriting of the output file
    -h   show this help
"""[1:] % (sys.argv[0])


def hexdump(filename, offset, count, width):
    '''return hexdump of bytes, little endian'''
    b = []
    last = None
    f = open(filename, 'rb')
    f.seek(offset)
    dupcount = 0
    for i in range(count):
        val = 0
        for j in range(width):
            d = ord(f.read(1))
            val += d << (j*8)
        if val == last:
            dupcount += 1
            b[-1] = format(last, '0%dx'%(width*2))+'*%d'%dupcount
        else:
            last = val
            dupcount = 1
            b.append(format(val, '0%dx'%(width*2)))
    f.close()
    return ' '.join(b)

def stringdump(filename, offset, count):
    '''return string from file'''
    f = open(filename, 'rb')
    f.seek(offset)
    s = f.read(count)
    f.close()
    return '"'+s+'"'

def disassemble(realbin, addr, count, offset, dopts, outbuf, linecomment):
    global objdump
    execmd = [objdump, '-D', '-m','armv5', '-b','binary', \
              '--disassembler-options='+dopts, '--adjust-vma=%d'%(offset), \
              '--start-address=%d'%(addr), '--stop-address=%d'%(addr+count), realbin]
    dstarted = False
    for curline in Popen(execmd, stdout=PIPE).communicate()[0].splitlines():
        if not dstarted:
            # skip header
            if curline.strip().startswith('%x:'%addr):
                dstarted = True
                # remove existing comment, not really useful
                m = re.match(r'^(.*)\s+\((adr\s[^)]+\s)?0x[0-9a-f]+\)$', curline)
                if m: curline = m.group(1)
                m = re.match(r'^(.*)\s+;.*$', curline)
                if m: curline = m.group(1)
                curline += linecomment
                linecomment = ''
                outbuf.append(curline)
        else:
            outbuf.append(curline)

def outbuf_flush(outbuf, outf):
    while len(outbuf) > 0:
        outf.write(outbuf.pop(0)+'\n')

def parse_da(inf, bin, outf):
    # parse header first
    if not re.match(r':\s+.__', inf.readline()) or \
       not re.match(r':\s+.daversion', inf.readline()):
        sys.stderr.write('Unrecognised header, probably no disassembly annotation file.\n')
        sys.exit(1)

    offset = 0
    realbin = bin
    lineno = 2
    dopts = ''
    prevaddr = -1
    linecomment = ''
    outbuf = []
    outparsed = True
    for l in inf.readlines():
        lineno += 1
        line = None

        m = re.match(r'\s*([0-9a-f]+):(\s*(\.\w+)\s(.*))$', l)
        if not m:
            sys.stderr.write('ignoring malformed line %d\n'%lineno)
            continue

        addr = int(m.group(1), 16)
        fullcmd = m.group(2).rstrip()
        cmd = m.group(3)
        args = m.group(4).rstrip()

        # output disassembly for previous address
        if addr != prevaddr:
            # if output was not parsed otherwise, disassemble
            if not outparsed:
                disassemble(realbin, prevaddr, addr-prevaddr, offset, dopts, outbuf, linecomment)
                linecomment = ''
            # now do the output
            outbuf_flush(outbuf, outf)
            outparsed = False
        
        # instruction mode (no args)
        if cmd == '.arm':
            dopts = ''
            outbuf.append(fullcmd)
        elif cmd == '.thumb':
            dopts = 'force-thumb'
            outbuf.append(fullcmd)
        # comments (comment as arg)
        elif cmd == '.cs':
            outbuf.append(args)
        elif cmd == '.cl':
            linecomment = args
        # address offset change (args: <file_offset_in_hex>)
        # this basically sets the argument as the new address zero
        elif cmd == '.rebase':
            # do the rebase
            parts = args.split()
            if len(parts) != 1:
                sys.stderr.write('ignoring malformed line %d: need one argument for rebase')
                continue
            offset = -int(parts[0], 16)
            if offset < 0:
                # objdump's adjust-vma option needs to be >0, so we create a new
                # file start starts at a different position for this
                realbin = bin+'.da2diss.tmp'
                tmpfile = open(realbin, 'w')
                orgfile = open(bin, 'rb')
                orgfile.seek(-offset)
                length = os.path.getsize(bin) + offset
                while length:
                    s = min(1024, length)
                    tmpfile.write(orgfile.read(s))
                    length -= s
                orgfile.close()
                tmpfile.close()
                offset = 0
            prevaddr = -1
            outbuf.append(fullcmd)
        # data (args: \[<number_of_items_in_hex>\])
        elif cmd in ['.ascii', '.byte', '.short', '.word']:
            m = re.match(r'\s*\[\s*([0-9a-f]+)\s*\]', args)
            if not m:
                sys.stderr.write('ignoring malformed line %d: wrong data argument\n'%lineno)
            else:
                count = int(m.group(1), 16)
                if cmd == '.ascii':
                    line = stringdump(realbin, addr-offset, count)
                else:
                    if cmd == '.byte': x=1
                    elif cmd == '.short': x=2
                    elif cmd == '.word': x=4
                    else: pass # unreachable code
                    line = hexdump(realbin, addr-offset, count, x)
                line = '%8x:\t%s'%(addr, line)
                if linecomment:
                    line += linecomment
                    linecomment = ''
                outbuf.append(line)
                outparsed = True
        # unrecognised
        else:
            sys.stderr.write('ignoring malformed line %d: unknown command "%s"'%(lineno,cmd))

        prevaddr = addr

    # handle remaining output
    if not outparsed:
        addr += 8 # should be enough for one arm or two thumb cmds
        disassemble(realbin, prevaddr, addr-prevaddr, offset, dopts, outbuf, linecomment)
    # now do the output
    outbuf_flush(outbuf, outf)

    # remove tempfile if it was so
    if bin != realbin: os.remove(realbin)


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
    if len(args) != 1:
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

    global objdump
    objdump = Popen(['which','objdump'], stdout=PIPE).communicate()[0].strip()
    if not objdump:
        sys.stderr.write('Need to have objdump in PATH\n')
        sys.exit(1)
    parse_da(inf, args[0], outf)

# vim:ts=4:sw=4:expandtab:
