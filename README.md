# pycdump
Dump/disassemble python PYC files

### Usage:
pycdump module.pyc > module.dis

The output is suitable for hexedit the source file

### Credits:
* Python opcodes description: https://docs.python.org/2/library/dis.html
* PYC file layout: http://nedbatchelder.com/blog/200804/the_structure_of_pyc_files.html
* Python marshal/unmarshal source code: http://svn.python.org/projects/python/trunk/Python/marshal.c
* Patch to make uncompyle2 work almost perfectly: https://github.com/Mysterie/uncompyle2/pull/24/files
