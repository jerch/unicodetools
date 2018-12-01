import sys
from time import sleep

import os
from termios import TCSANOW, TCSADRAIN, TCSAFLUSH, tcsetattr, tcgetattr
from functools import partial
from select import select
from tty import setcbreak, setraw
from termios import *

IFLAG = 0
OFLAG = 1
CFLAG = 2
LFLAG = 3
ISPEED = 4
OSPEED = 5

def setcooked(fd, when=TCSAFLUSH):
    """Put terminal into cooked mode."""
    mode = tcgetattr(fd)
    mode[IFLAG] = BRKINT | ICRNL | INPCK | ISTRIP | IXON | IGNPAR
    mode[OFLAG] = OPOST | ONLCR
    mode[CFLAG] = mode[CFLAG] | CS8
    mode[LFLAG] = ECHOKE | ECHOCTL | ECHOK | ECHOE | ECHO | ICANON | IEXTEN | ISIG
    tcsetattr(fd, when, mode)

TERM_MODES = {'cooked': setcooked, 'cbreak': setcbreak, 'raw': setraw}

class TerminalHandler(object):
    _cooked_settings = {}
    def __new__(cls, *args, **kwargs):
        instance = object.__new__(cls)
        instance.cooked_settings = cls._cooked_settings
        return instance

    def __init__(self,
                 mode='cbreak',
                 fd=sys.stdin.fileno(),
                 when=TCSADRAIN,
                 when_exit=TCSAFLUSH):
        self.mode = mode
        self.fd = fd
        self.when = when
        self.when_exit = when_exit
        self.old_settings = tcgetattr(self.fd)
        self.cooked_settings.setdefault(self.fd, self.old_settings)

    def __enter__(self):
        TERM_MODES[self.mode](self.fd, self.when)
        return self.fd

    def __exit__(self, type_, value, traceback):
        tcsetattr(self.fd, self.when_exit, self.old_settings)

    @classmethod
    def reset(cls, fd=sys.stdin.fileno()):
        if cls._cooked_settings.get(fd):
            tcsetattr(fd, TCSAFLUSH, cls._cooked_settings[fd])

cooked_terminal = partial(TerminalHandler, 'cooked')
cbreak_terminal = partial(TerminalHandler, 'cbreak')
rare_terminal = cbreak_terminal
raw_terminal = partial(TerminalHandler, 'raw')
reset_terminal = TerminalHandler.reset

def kbhit(fd=sys.stdin.fileno(), timeout=0):
    with cbreak_terminal(fd, when_exit=TCSADRAIN):
        rds, _, _ = select([fd], [], [], timeout)
        if rds:
            return 1
        return 0

def width_from_terminal(start, end):
    s = ''
    print
    for i in range(start, end):
        # we have to use 'unicode-escape' since narrow build cannot use
        # codepoints > 65535
        sys.stdout.write(('\\U%08x' % i).decode('unicode-escape') + '\x1b[6n')
        sys.stdout.flush()
        # wait for CPR on stdin
        while not kbhit():
          sleep(.01)
        resp = ''
        while kbhit():
            resp += os.read(sys.stdin.fileno(), 1024)
        row, col = resp[2:-1].split(';')
        width = int(col)
        s += str(width - 1)
        print '\x1b[1K\x1b[Gcodepoint:', i, 'width:', width - 1
    return s


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print "error, usage: query_terminal.py <start> <end> <file>"
        sys.exit(1)
    start = int(sys.argv[1], 16 if sys.argv[1].startswith('0x') else 10)
    end = int(sys.argv[2], 16 if sys.argv[2].startswith('0x') else 10)
    result = ''
    # set terminal into cbreak mode to avoid echoing CPR
    with cbreak_terminal():
        result = width_from_terminal(start, end)
    with open(sys.argv[3], 'w') as f:
        f.write(result)
