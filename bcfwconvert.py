#!/usr/bin/env python
#
#  Unofficial Behringer Control Development Kit - firmware conversion tool
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

import sys, getopt, os

__AUTHOR__  = "Willem van Engen <dev-bc2000@willem.engen.nl>"
__VERSION__ = "2010.08.25"
__LICENSE__ = "GPL version 2 or higher"

_usage = r"""
bc firmware conversion tool version %s by %s
Usage: bcfwconvert [-i in_file] [-I in_format] [-o out_file] [-O out_format] \
                   [-h] [-f] [-s offset] [-b base_address] [-m model_id]

    -i    name of input file (default: standard input)
    -I    format of input file: syx, dump or os
    -o    name of output file (default: standard output)
    -O    format of output file: syx, dump or os
    -f    force overwriting of the output file
    -s    input image offset in bytes (default: 0)
    -b    base address (syx output)
    -m    model id (syx output, default: 0x7f which means any)
    -h    show this help
"""[1:] % (__VERSION__, __AUTHOR__)


##############################################################################
## General helper functions

class BCFWException(Exception):
    pass

def wunpack(x):
    '''convert array of 4 bytes to 32bit word'''
    if len(x) < 4: raise BCFWException('Need 4 bytes or more to unpack')
    return (x[3]<<24) + (x[2]<<16) + (x[1]<<8) + x[0]

def wpack(x, offs=0):
    '''convert 32bit word to array of bytes'''
    return [ (x>> 0)&0xff, (x>> 8)&0xff, (x>>16)&0xff, (x>>24)&0xff ]

def array2str(x):
    '''convert array of bytes to string'''
    out = ''
    for e in x: out += chr(e)
    return out

def str2array(x):
    '''convert string to array of bytes'''
    out = []
    for e in x: out.append(ord(e))
    return out

##############################################################################
## Sysex handling

def syx_implode(data):
    '''convert 7bit data stream to 8bit;
       each 8th byte contains high bits of preceding 7 inverted'''
    if len(data) % 8:
        raise BCFWException('length of sysex blob must be multiple of 8 but is 0x%x'%len(data))
    out = [0] * (len(data)/8*7)
    j = 0
    for i in range(len(data)):
        if i%8 == 7:
            for k in range(7):
                if data[i] & (1<<k): out[j-k-1] |= 0x80
        else:
            out[j] = data[i]
            j += 1
    return out

def syx_explode(data):
    '''convert 8bit array to 7bit by inserting a byte with the high bits
    each 7 bytes'''
    if len(data) % 7:
        raise BCFWException('length of data to encode to sysex blob must be multiple of 7 but is 0x%x'%len(data))
    j = 0
    out = [0] * (len(data)/7*8)
    highbits = 0
    for byte in data:
        if byte & 0x80: highbits |= 1<<(6-(j%8))
        out[j] = byte & 0x7f
        j += 1
        if j%8 == 7:
            out[j] = highbits
            j += 1
            highbits = 0
    return out

_syx_cipher= [ 0x54, 0x5a, 0x27, 0x30, 0x33, 0x42, 0x43, 0x4f, 0x4e, 0x54, 0x52, 0x4f, 0x4c ]
def syx_decode(data):
    '''return deciphered data; as it is xor it works both ways'''
    out = [0] * len(data)
    for i in range(len(data)):
        out[i] = data[i] ^ _syx_cipher[i%len(_syx_cipher)]
    return out

def syx_checksum_update(byte, checksum):
    '''return updated checksum for this byte'''
    for i in range(8):
        if not ((byte>>i)^checksum)&1: checksum ^= 0x19
        if checksum&1: checksum |= 0x100
        checksum >>= 1
    return checksum

def syx_decode_write(data, dmagic):
    '''return (de)ciphered data that happens for writing only'''
    out = []
    if len(data)%2:
        raise BCFWException("syx_decode_write: length must be divisible by two")
    if not dmagic: dmagic = 0x545a
    for i in range(0,len(data),2):
        if dmagic & 1: dmagic ^= 0x8005
        dmagic >>= 1
        out.append(data[i] ^ (dmagic&0xff))
        out.append(data[i+1] ^ ((dmagic>>8)&0xff))
    return out

## Behringer firmware sysex message
#
#    | Manu ID  | Dev+Mod | Cmd | Data               |
# F0 | 00 20 32 | 00 15   |  34 | 00 01 02 03 04 ... |  F7  (hex)
#  0 |  1  2  3 |  4  5   |   6 | 7..303             | 304  (dec)
#
# Data is decoded with 7to8 shuffling and cipher
# Then the resulting data is interpreted as follows:
#
# Address | Checksum | Firmware page
#  xx xx  |  y       | f0 f1 f2 f3 ...  (hex)
#   0  1  |  2       | 3..258           (dec)
#
# checksum is computed over firmware page (3..258)

_offs=0
def syx_parse_packet(idata, lastaddr):
    '''process a single chunk of firmware packet data.
       If the argument doFlashDecipher is True, then also do the deciphering
       that happens only when writing but not when reading from the device.'''
    global _offs # hack
    if len(idata) != 296:
        raise BCFWException("wrong length: 0x%x should be 0x%x"%(len(idata),296))
    odata = syx_decode(syx_implode(idata))
    address = ( (odata[0]<<7) + odata[1] ) * 0x100
    origsum = odata[2]
    odata = odata[3:]
    # make sure address is right
    if lastaddr and address!=lastaddr+0x100:
        raise BCFWException("No jump in firmware addresses allowed: 0x%05x->0x%05x"%(lastaddr,address))
        #sys.stderr.write('New address 0x%05x at offset 0x%06x\n'%(address<<8, _offs))
    _offs+=0x100
    # and verify checksum
    checksum = 0
    for b in odata: checksum = syx_checksum_update(b, checksum)
    if checksum != origsum:
        raise BCFWException("Checksum error: 0x%x should be 0x%x"%(checksum,odata[2]))
    return odata, address

def syx2dump(idata):
    '''convert a sysex file to a memory dump'''
    odata = []
    sysex = []
    insysex = False
    foundnonsysex = False
    addr = [None, None]
    command = None
    for byte in idata:
        if insysex or byte == 0xf0:
            sysex.append(byte)
        # handle sysex start
        if byte == 0xf0:
            insysex = True
            continue
        # handle and process sysex
        elif byte == 0xf7:
            insysex = False
            # need behringer packet, firmware command
            if sysex[1:4] == [0x00, 0x20, 0x32] and sysex[6] in [0x34, 0x74]:
                # make sure we have one packet type: firmware image (0x34) or flash dump (0x74)
                if not command: command = sysex[6]
                if sysex[6] != command:
                    raise BCFWException('Cannot parse both firmware image and flash dump packets at once')
                # parse packet
                data, addr[1] = syx_parse_packet(sysex[7:-1], addr[1])
                odata.extend(data)
                if addr[0] == None:
                    addr[0] = addr[1]
                    sys.stderr.write('Starting address: 0x%05x\n'%(addr[0]))
                sysex = []
                continue
            sysex = []
        # sysex data
        elif insysex:
            continue
        # non-firmware packet, warn once
        if not foundnonsysex:
            sys.stderr.write("warning: non-firmware data present in input (mentioning once) 0x%2x\n"%byte)
            foundnonsysex = True
    # now do extra deciphering if it is a firmware dump to be written to device
    if command == 0x34:
        # TODO also handle non-4k-aligned
        for i in range(0, len(odata), 0x1000):
            odata[i:i+0x1000] = syx_decode_write(odata[i:i+0x1000], (i+addr[0])/0x1000)
    return odata


def dump2syx(idata, base, model):
    '''convert a memory dump to a sysex file'''
    if base & 0xfff:
        raise BCFWException("base must be a multiple of 0x1000")
    odata = []
    header = [0xf0, 0x00, 0x20, 0x32, 0x7f, model, 0x34 ]
    footer = [0xf7]
    if base < 0x2000:
        raise BCFWException("base address must be 0x2000 or more, or it may brick the device")
    # make length a multiple of 4k
    idata = idata + [0] * ((0x1000 - (len(idata)%0x1000))%0x1000)
    # flash in 0x1000=4k byte sectors
    for page in range(0, len(idata), 0x1000):
        sector = syx_decode_write(idata[page:page+0x1000], (base+page)/0x1000)
        # packet size of 0x100
        for subpage in range(0, 0x1000, 0x100):
            # construct argument to firmware upload command
            arg = [0] * 0x103
            arg[0] = ((base+page+subpage)/0x100) >> 8
            arg[1] = ((base+page+subpage)/0x100) & 0xff
            arg[3:0x103] = sector[subpage:subpage+0x100]
            # compute checksum
            for b in arg[3:]: arg[2] = syx_checksum_update(b, arg[2])
            # and output sysex packet
            odata.extend(header + syx_explode(syx_decode(arg)) + footer)
    return odata

##############################################################################
## OS image handling

_oscipher1 = [ 0x2726534c, 0x3971212d, 0x71167b24, 0x69272171, 0x3b652f24,
               0x30293644, 0x541a183f, 0x2c3f7c31, 0x29287d28, 0x5648553d,
               0x4c4f1257, 0x31677518, 0x2e2e186a, 0x00554400, 0x44554d4d ]

_oscipher2 = [ 0x75697361, 0x77386664, 0x33363765, 0x20756934, 0x6920686a,
               0x74667564, 0x7437387a, 0x756f3372, 0x616f347a, 0x667a7569,
               0x616f2067, 0x74203738, 0x747a3738, 0x00756920 ]

def os_decodeword(wordin, offset):
    '''encode/decode a 32bit word of data with cipher offset'''
    return wordin \
        ^ _oscipher1[offset % len(_oscipher1)] \
        ^ _oscipher2[offset % len(_oscipher2)]

def dump2os(idata):
    '''convert a dump of the os flash to an os image'''
    # first two words are special
    size = os_decodeword(wunpack(idata[0:4]), 0)
    #size = len(idata)-8
    origsum = os_decodeword(wunpack(idata[4:8]), 1)
    #sys.stderr.write("header: size=0x%x, checksum=0x%x\n"%(size, origsum))
    # make sure size matches
    if size <= 0 or ((size+3)/4)*4+0x2008 > 0x7ffff:
        raise BCFWException("Bad size field: 0x%x must be between 0 and 0x%x"%(size, 0x7ffff-0x2008));
    # and process the data
    odata = [0] * size
    dmagic = 0x42474552
    checksum = 0
    for offset in range(8, size+8, 4):
        # deobfuscate
        word = wunpack(idata[offset:offset+4])
        word = os_decodeword(word, offset/4)
        odata[offset-8:offset-8+4]=wpack(word)
        # and update checksum
        if dmagic & 1: dmagic |= 1<<32
        dmagic >>= 1
        checksum += dmagic ^ word
    # verify checksum
    checksum &= 0xffffffff
    if checksum != origsum:
        raise BCFWException("Corrupt image: checksum mismatch 0x%x should be 0x%x"%(checksum, origsum))
    return odata

def os2dump(idata):
    '''convert an os image to a flashdump portion'''
    size = len(idata)
    # length validation and checksum
    if size <= 0 or ((size+3)/4)*4+0x2008 > 0x7ffff:
        raise BCFWException("Bad size: 0x%x must be between 0 and 0x%x"%(size, 0x7ffff-0x2008));
    # fill 4k page with 0xff as official firmware does
    #idata = idata + [0] * (4-(len(idata)%4))
    idata = idata + [0xff] * ((0x1000 - ((size+8)%0x1000))%0x1000)
    odata = [0] * (size+8)
    odata[0:4] = wpack(os_decodeword(size, 0))
    # and process the data
    dmagic = 0x42474552
    checksum = 0
    for offset in range(0, len(idata), 4):
        # obfuscate
        word = wunpack(idata[offset:offset+4])
        newword = os_decodeword(word, offset/4+2)
        odata[offset+8:offset+8+4]=wpack(newword)
        # and compute checksum (but not for filler bytes)
        if offset < size:
            if dmagic & 1: dmagic |= 1<<32
            dmagic >>= 1
            checksum += dmagic ^ word
    # store checksum
    checksum &= 0xffffffff
    odata[4:8] = wpack(os_decodeword(checksum, 1))
    return odata


##############################################################################
## Main program

if __name__ == "__main__":
  try:
    #
    # parse options
    #
    try:
        opts, args = getopt.getopt(sys.argv[1:], "i:o:I:O:s:b:m:hf")
    except getopt.GetoptError:
        sys.stderr.write(_usage)
        sys.exit(1)

    inf             = sys.stdin
    outf            = sys.stdout
    infile          = None
    outfile         = None
    informat        = None
    outformat       = None
    offset          = None
    baseaddress     = None
    model           = 0x7f
    force_overwrite = False
    param_given     = False

    for o, a in opts:
        param_given = True
        if o == "-i":
            infile = a
        if o == "-o":
            outfile = a
        if o == "-I":
            informat = a
        if o == "-O":
            outformat = a
        if o == "-s":
            offset = int(a, 0)
        if o == "-b":
            baseaddress = int(a, 0)
        if o == "-m":
            if a == "any": model = 0x7f
            elif a.lower() == "bcf2000": model = 0x14
            elif a.lower() == "bcr2000": model = 0x15
            else: model = int(a, 0)
        if o == "-h":
            sys.stderr.write(_usage)
            sys.exit(0)
        if o == "-f":
            force_overwrite = True

    #
    # validate options
    #
    if not param_given:
        sys.stderr.write(_usage)
        sys.exit(1)

    if not informat and not outformat:
        sys.stderr.write("Please specify an input or output file format or both\n")
        sys.exit(1)

    # smart outformat default
    if informat=="syx" and not outformat: outformat = "os"
    if informat=="os" and not outformat: outformat = "syx"
    if outformat=="syx" and not informat: informat = "os"
    if outformat=="os" and not informat: informat = "syx"
    
    if not informat in ["syx","dump","os"]:
        sys.stderr.write("Unrecognised input file format: %s\n"%(informat))
        sys.exit(1)

    if not outformat in ["syx","dump","os"]:
        sys.stderr.write("Unrecognised output file format: %s\n"%(outformat))
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

    #
    # do conversion
    #
    data = str2array(inf.read())
    if informat == "os" and outformat == "dump":
        if offset: data = data[offset:]
        data = os2dump(data)
        sys.stderr.write("note that the output file has base address 0x2000\n");

    elif informat == "dump" and outformat == "os":
        if offset: data = data[offset:]
        data = dump2os(data)

    elif informat == "syx" and outformat == "dump":
        if not offset == None:
            sys.stderr.write("warning: offset is ignored for this conversion\n");
        data = syx2dump(data)

    elif informat == "syx" and outformat == "os":
        data = syx2dump(data)
        if offset: data = data[offset:]
        data = dump2os(data)

    elif informat == "dump" and outformat == "syx":
        if offset: data = data[offset:]
        if not baseaddress:
            sys.stderr.write("need to specify base address\n")
            sys.exit(1)
        data = dump2syx(data, baseaddress, model)

    elif informat == "os" and outformat == "syx":
        if offset: data = data[offset:]
        if baseaddress == None: baseaddress = 0x2000
        data = os2dump(data)
        data = dump2syx(data, baseaddress, model)

    else:
        raise BCFWException("unimplemented conversion: %s to %s"%(informat,outformat))

    outf.write(array2str(data))

  except BCFWException, e:
    sys.stderr.write(str(e)+'\n')
    sys.exit(1)

# vim:et:sw=4:ts=4:ai:
