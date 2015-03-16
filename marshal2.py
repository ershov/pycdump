"""Custom unmarshal for PYC
"""

import sys
import time
import struct
from opcode import *
import new
import dis2 as dis

#sys.setrecursionlimit(5000)

class TYPE:
    NULL              = '0'
    NONE              = 'N'
    FALSE             = 'F'
    TRUE              = 'T'
    STOPITER          = 'S'
    ELLIPSIS          = '.'
    INT               = 'i'
    INT64             = 'I'
    FLOAT             = 'f'
    BINARY_FLOAT      = 'g'
    COMPLEX           = 'x'
    BINARY_COMPLEX    = 'y'
    LONG              = 'l'
    STRING            = 's'
    INTERNED          = 't'
    STRINGREF         = 'R'
    TUPLE             = '('
    LIST              = '['
    DICT              = '{'
    CODE              = 'c'
    UNICODE           = 'u'
    UNKNOWN           = '?'
    SET               = '<'
    FROZENSET         = '>'

# do like in opcode.py
typemap = {}
typename = {} # [''] * 256
#for ty in range(256): opname[ty] = '<type %r>' % (ty,)
#del ty

def def_type(name, ty):
    typename[ty] = name
    typemap[name] = ty

# copy-paste from marshal.c
def_type('NULL'           , '0')
def_type('NONE'           , 'N')
def_type('FALSE'          , 'F')
def_type('TRUE'           , 'T')
def_type('STOPITER'       , 'S')
def_type('ELLIPSIS'       , '.')
def_type('INT'            , 'i')
def_type('INT64'          , 'I')
def_type('FLOAT'          , 'f')
def_type('BINARY_FLOAT'   , 'g')
def_type('COMPLEX'        , 'x')
def_type('BINARY_COMPLEX' , 'y')
def_type('LONG'           , 'l')
def_type('STRING'         , 's')
def_type('INTERNED'       , 't')
def_type('STRINGREF'      , 'R')
def_type('TUPLE'          , '(')
def_type('LIST'           , '[')
def_type('DICT'           , '{')
def_type('CODE'           , 'c')
def_type('UNICODE'        , 'u')
def_type('UNKNOWN'        , '?')
def_type('SET'            , '<')
def_type('FROZENSET'      , '>')

del def_type

class Null(object): pass

SIZE32_MAX = 0x7FFFFFFF
PyLong_SHIFT = 15
MAX_MARSHAL_STACK_DEPTH = 2000
MAXSIZE = 100000

def stringdump(text):
    return " ".join("%02X" % ord(c) for c in text)

def hexdump(text, fileoffset = 0):
    import itertools
    i = fileoffset - (fileoffset % 16)
    print "            0  1  2  3  4  5  6  7   8  9  A  B  C  D  E  F",
    for c in itertools.chain( ('  ' for c in range(fileoffset - i)) ,  ("%02X" % ord(c) for c in text) ):
        if ((i % 16) == 0): print "\n  %06X: " % (i),
        if ((i % 16) == 8): print "",
        i = i+1
        print c,
    print
    print "            0  1  2  3  4  5  6  7   8  9  A  B  C  D  E  F"


# dumb port of marshal.c
class dump_pyc:
    f = None
    depth = 0
    strings = []

    def __init__(self, filename):
        self.f = open(filename, "rb")

    def r_string(self, n):
        assert n < MAXSIZE
        return self.f.read(n)

    def r_PyString(self):
        return self.r_string(self.r_long())

    # unsigned
    def r_byte(self):
        return struct.unpack("<B", self.f.read(1))[0]
    def r_char(self):
        return self.f.read(1)

    def r_short(self):
        return struct.unpack("<h", self.f.read(2))[0]

    def r_long(self):
        return struct.unpack("<l", self.f.read(4))[0]

    def r_long64(self):
        return struct.unpack("<q", self.f.read(8))[0]

    def r_double(self):
        return struct.unpack("<d", self.f.read(8))[0]

    def r_PyLong(self):
        n = self.r_long();
        if (n == 0): return 0

        size = abs(n)
        shorts_in_top_digit = size

        raise NotImplementedError("r_PyLong unimplemented")

    def r_object(self):
        pos1 = self.f.tell()
        t = typename.get(self.r_char())
        if (t == None):
            print "type code error:", repr(t), "at 0x%08X" % pos1
            raise Exception("type code error")
        self._on_obj_start(t, pos1)
        self.depth += 1
        retval = None
        def _r_NULL(self): return Null
        def _r_NONE(self): return None
        def _r_STOPITER(self): raise NotImplementedError("STOPITER unsupported")
        def _r_ELLIPSIS(self): raise NotImplementedError("ELLIPSIS unsupported")
        def _r_FALSE(self): return False
        def _r_TRUE(self): return True
        def _r_INT(self): return self.r_long()
        def _r_INT64(self): return self.r_long64()
        def _r_LONG(self): return self.r_PyLong()
        def _r_FLOAT(self): return float(self.r_string(self.r_byte()))
        def _r_BINARY_FLOAT(self): return self.r_double()
        def _r_STRING(self): return self.r_PyString()
        def _r_INTERNED(self): ret = self.r_PyString(); self.strings.append(ret); return ret
        def _r_STRINGREF(self): return self.strings[self.r_long()]
        def _r_LIST(self): return [self.r_object() for i in range(self.r_long())]
        def _r_TUPLE(self): return tuple([self.r_object() for i in range(self.r_long())])
        def _r_DICT(self):
            ret = {}
            while True:
                key = self.r_object()
                if (key is Null): break
                val = self.r_object()
                if (val is Null): continue
                ret[key] = val
            return ret
        def _r_SET(self): return {self.r_object() for i in range(self.r_long())}
        def _r_FROZENSET(self): return frozenset({self.r_object() for i in range(self.r_long())})
        def _r_CODE(self):
            argcount = self.r_long()
            nlocals = self.r_long()
            stacksize = self.r_long()
            flags = self.r_long()
            code = self.r_object()
            posCode = self.f.tell() - len(code)
            consts = self.r_object()
            names = self.r_object()
            varnames = self.r_object()
            freevars = self.r_object()
            cellvars = self.r_object()
            filename = self.r_object()
            name = self.r_object()
            firstlineno = self.r_long()
            lnotab = self.r_object()

            ret = new.code(argcount, nlocals, stacksize, flags,
                    code, consts, names, varnames,
                    filename, name, firstlineno, lnotab)

            print "Disassemble of "+name+" at "+filename+":"+repr(firstlineno)
            #hexdump(code, posCode)
            #dis.disassemble_string(code, -1, varnames, names, consts)

            dis.disassemble(ret, -1, posCode)

            return ret

        retval = locals()["_r_"+t](self)

        pos2 = self.f.tell()
        self._on_obj_beforeend(t, retval, pos1, pos2)
        self.depth -= 1
        self._on_obj_afterend(t, retval, pos1, pos2)
        return retval

    #
    def _indents(self): return "  " * self.depth
    def _indent(self): print self._indents(),
    def _on_obj_start(self, name, pos1):
        self._indent()
        print "%s start at 0x%08X (%d) {" % (name, pos1, pos1)

    def _on_obj_beforeend(self, name, obj, pos1, pos2):
        self._indent()
        print "= %s" % repr(obj)

    def _on_obj_afterend(self, name, obj, pos1, pos2):
        self._indent()
        print "} %s range: 0x%08X : 0x%08X (%d : %d) = 0x%X (%d)" % (name, pos1, pos2, pos1, pos2, pos2-pos1, pos2-pos1)

    #
    def __enter__(self): return self
    def __exit__(self, type, value, traceback):
        if (self.f): self.f.close()

if __name__ == "__main__":
    print sys.argv[1]
    with dump_pyc(sys.argv[1]) as pyc:
        print "Magic: %d %02X %02X" % (struct.unpack("<H", pyc.f.read(2))[0], pyc.r_byte(), pyc.r_byte())
        print "Timestamp:", time.asctime(time.localtime(pyc.r_long()))
        print pyc.r_object()


