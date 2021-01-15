#!/usr/bin/env python
# 
#  Unofficial Behringer Control Development Kit - firmware flash tool
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
# This program works only on systems that have a midi device in /dev
# so I guess that means Linux/Unix only
#

import sys, getopt, os, glob, select

__AUTHOR__  = "Willem van Engen <dev-bc2000@willem.engen.nl>"
__VERSION__ = "2010.08.27"
__LICENSE__ = "GPL version 2 or higher"

_usage = r"""
bc firmware flash tool version %s by %s
Usage: bcfwflash -u [-i in_file] [-d midi_device] [-h] [-r]
       bcfwflash -g [-s range] [-o out_file] [-d midi_device] [-f] [-h] [-r]
       bcfwflash -p <string> [-h]
       bcfwflash -r [-h]
       bcfwflash -l [-h]

    -u    upload firmware to the device
    -i    name of sysex input file (default: standard input)
    -d    midi device to work on (default: auto-detect)

    -r    reboot device after everything else

    -g    retrieve a dump from the device
    -s    address range to retrieve (default: 0x0000-0x2000)
    -o    name of sysex output file (default: standard output)
    -f    force overwriting of the output file

    -p    put a 4-character string on the device's display

    -l    list auto-detected midi devices
    -h    show this help
"""[1:] % (__VERSION__, __AUTHOR__)


##############################################################################
## General helper functions

class BCFWException(Exception):
    pass

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

def midi_receive_sysex(f, timeout=0.2):
    '''return next sysex message from device, or None if timeout'''
    sysex = []
    insysex = False
    while len(sysex)==0 or insysex:
        if not f.fileno() in select.select([f.fileno()],[],[],timeout)[0]:
            return None
        byte = f.read(1)
        c = ord(byte)
        if c == 0xf0:
            sysex = [c]
            insysex = True
        elif c == 0xf7:
            sysex += [c]
            insysex = False
        else:
            if insysex: sysex.append(c)
    return sysex

def midi_check_sysex(sysex, cmds, exceptions = True):
    '''check if the response was a valid sysex blob message and return command'''
    try:
        if not sysex:
            raise BCFWException("timeout waiting for flash blob from device")
        if not sysex[1:4] == [0x00, 0x20, 0x32]:
            raise BCFWException("unexpected sysex manufacturer received: 0x%02x,0x%02x,0x%02x"%(sysex[1],sysex[2],sysex[3]))
        if not sysex[6] in cmds:
            raise BCFWException("unexpected sysex response command received: 0x%02x"%sysex[6])
        return sysex[6]
    except BCFWException, e:
        if not exceptions: return None
        raise e

def midi_detect(verbose=False, findall=False):
    '''detect midi devices that have a Behringer Control device attached'''
    if os.path.isdir("/dev/snd"):
        devices = glob.glob("/dev/snd/midi*")
    else:
        devices = glob.glob("/dev/midi*")
    if not devices:
        raise BCFWException("No midi devices found")
    # find matching id responses on each device
    founddevnames = []
    for devname in devices:
        try:
            devf = open(devname, 'r+b', 0)
        except:
            if verbose: sys.stderr.write("warning: could not open midi device %s\n"%devname)
            continue
        data = [0xf0, 0x00, 0x20, 0x32, 0x7f, 0x7f, 0x01, 0xf7]
        devf.write(array2str(data))
        devf.flush()
        recvd = midi_receive_sysex(devf,1)
        devf.close()
        if recvd and recvd[0:4] == [0xf0, 0x00, 0x20, 0x32]:
            if verbose: sys.stderr.write("%s:\t%s\n"%(devname, array2str(recvd[7:-1])))
            if not findall: return devname
            founddevnames.append(devname)
    if not findall: return None
    return founddevnames


##############################################################################
## Flash upload functions

def flash_upload(f, data):
    '''Upload sysex firmware data to the device'''
    offset = 0
    nonsysexwarned = False
    while offset < len(data):
        # start of current message
        curoffset = offset
        if data[offset] != 0xf0:
            if not nonsysexwarned:
                sys.stderr.write('warning: found non-sysex data (mentioning only once)\n')
                nonsysexwarned = True
            offset += data[offset:].index(0xf0)
        # end of current message
        offset += data[offset:].index(0xf7) + 1
        # now send current message
        f.write(array2str(data[curoffset:offset]))
        f.flush()
        # wait for response if on 4k boundary
        argstart = syx_decode(syx_implode(data[curoffset+7:curoffset+7+8]))
        address = (argstart[0]<<8) + argstart[1]
        if address % 0x10 == 0x0f:
            # and parse response, if any; handle loopback too
            sysex = midi_receive_sysex(f,4)
            while midi_check_sysex(sysex, [0x34, 0x35], False) == 0x34:
                sysex = midi_receive_sysex(f,4)
            # parse response packet
            midi_check_sysex(sysex, [0x35])
            address = ((sysex[7]<<7) + sysex[8])*0x100
            status = 'ok\r'
            if sysex[9] == 1: status = 'sector incomplete\n'
            if sysex[9] == 2: status = 'erase failure\n'
            if sysex[9] == 3: status = 'write failure\n'
            sys.stderr.write('0x%06x-0x%06x: %s'%(address-0xf00,address+0x100,status))

##############################################################################
## Flash retrieval functions

def flash_get_blob(f, page):
    '''request flash blob from midi device by page'''
    # sysex message to request flash
    data = [0xf0, 0x00, 0x20, 0x32, 0x7f, 0x7f, 0x74, page>>7, page&0x7f, 0xf7]
    f.write(array2str(data))
    f.flush()
    # receive dump, but allow for sending the packet back
    sysex = midi_receive_sysex(f)
    while midi_check_sysex(sysex, [0x34, 0x74], False) == 0x74:
        sysex = midi_receive_sysex(f)
    midi_check_sysex(sysex, [0x34])
    # change command to avoid bricking device when writing it back accidentally
    sysex[6] = 0x74
    return sysex

def flash_get(f, addr, count):
    '''request flash address range from midi device.'''
    if addr&0xff: raise BCFWException('Start address must be a multiple of 0x100')
    if count&0xff: raise BCFWException('Count must be a multiple of 0x100')
    data = []
    # first get all blobs required
    for curaddr in range(addr, addr+count, 0x100):
        sys.stderr.write('0x%06x-0x%06x\r'%(curaddr,curaddr+0x100))
        data += flash_get_blob(f, curaddr/0x100)
    return data

##############################################################################
## Special feature functions

# sorry for the code duplication from bcfwconvert; but this makes it easy
# to just take the script as it is without caring for dependencies

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

def send_display(f, s):
    '''Send a 4-character string to the display. If the string is "boot" the
    device will reboot.'''
    # construct packet argument
    arg  = [0xff, 0x00]             # special address
    arg += [0x00]                   # checksum (compute later)
    arg += str2array(s[0:4])        # string
    arg += [0]*(0x100-4)            # padding
    for i in arg[3:]: arg[2] = syx_checksum_update(i, arg[2])
    # construct packet
    data  = [0xf0, 0x00, 0x20, 0x32, 0x7f, 0x7f, 0x34] # firmware send packet
    data += syx_explode(syx_decode(arg))
    data += [0xf7]                  # end of sysex
    # checksum
    f.write(array2str(data))
    f.flush()


##############################################################################
## Main program

if __name__ == "__main__":
  try:
    #
    # parse options
    #
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ugli:o:d:s:p:hrf")
    except getopt.GetoptError:
        sys.stderr.write(_usage)
        sys.exit(1)

    inf             = sys.stdin
    outf            = sys.stdout
    midif           = None
    infile          = None
    outfile         = None
    midifile        = None
    arange          = [0, 0x2000]
    actions         = []
    force_overwrite = False
    param_given     = False
    display         = None

    for o, a in opts:
        param_given = True
        if o == "-i":
            infile = a
        if o == "-o":
            outfile = a
        if o == "-d":
            midifile = a
        if o == "-s":
            arange = map(lambda x: int(x,0), a.split('-'))
        if o == "-u":
            actions.append('upload')
        if o == "-g":
            actions.append('retrieve')
        if o == "-l":
            actions.append('list')
        if o == "-p":
            display = a
            actions.append('put')
        if o == "-r":
            display = "boot"
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

    if len(actions) == 0 and display == 'boot':
        actions = ['put']

    if len(actions) != 1:
        sys.stderr.write("please choose either upload (-u), retrieve (-g) or list (-l)\n")
        sys.exit(1)

    if 'list' in actions:
        midi_detect(True, True)
        sys.exit(0)


    #
    # detect midi device when required, and open it
    #
    if not midifile:
        midifile = midi_detect()
        if not midifile:
            raise BCFWException("No Behringer Control found attached\n")

    try:
        midif = open(midifile, 'r+b', 0)
    except:
        raise BCFWException("Unable to open midi device %s.\n" % midifile)

    #
    # execute action
    #
    if 'retrieve' in actions:
        if outfile:
            if os.path.exists(outfile) and not force_overwrite:
                raise BCFWException("Output file %s exists.\n" % outfile)
            try:
                outf = open(outfile, 'w')
            except:
                raise BCFWException("Unable to open %s.\n" % outfile)
        data = flash_get(midif, arange[0], arange[1]-arange[0])
        outf.write(array2str(data))
        outf.close()

    elif 'upload' in actions:
        if infile:
            try:
                inf = open(infile, 'rb')
            except:
                raise BCFWException("Unable to open %s.\n" % infile)
        data = str2array(inf.read())
        inf.close()
        flash_upload(midif, data)

    if display:
        while len(display) < 4: display += ' '
        send_display(midif, display)

  except BCFWException, e:
    sys.stderr.write(str(e)+'\n')
    sys.exit(1)

# vim:et:sw=4:ts=4:ai:
