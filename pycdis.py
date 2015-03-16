#!/usr/bin/env python

import sys
import time
import struct
from marshal2 import dump_pyc

if __name__ == "__main__":
    print sys.argv[1]
    with dump_pyc(sys.argv[1]) as pyc:
        print "Look here for ocodes description: https://docs.python.org/2/library/dis.html"
        print "opcode.py for opcode numbers: http://svn.python.org/projects/python/trunk/Lib/opcode.py"
        print "Magic: %d %02X %02X" % (struct.unpack("<H", pyc.f.read(2))[0], pyc.r_byte(), pyc.r_byte())
        print "Timestamp:", time.asctime(time.localtime(pyc.r_long()))
        print pyc.r_object()


