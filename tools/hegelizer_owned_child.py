"""Exec an owned trial subprocess that exits if its supervising parent disappears."""
import ctypes
import os
import signal
import sys


def main() -> None:
    if len(sys.argv)<3:
        raise SystemExit('usage: trial_child.py PARENT_PID ABSOLUTE_EXECUTABLE [ARGS...]')
    parent=int(sys.argv[1])
    argv=sys.argv[2:]
    if parent <= 1 or not os.path.isabs(argv[0]):
        raise SystemExit('invalid parent or executable')
    libc=ctypes.CDLL(None,use_errno=True)
    libc.prctl.argtypes=[ctypes.c_int,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong]
    libc.prctl.restype=ctypes.c_int
    if libc.prctl(1,signal.SIGTERM,0,0,0) != 0:
        raise OSError(ctypes.get_errno(),'PR_SET_PDEATHSIG failed')
    if os.getppid()!=parent:
        raise SystemExit('supervisor already absent')
    os.execve(argv[0],argv,os.environ)


if __name__=='__main__':
    main()
