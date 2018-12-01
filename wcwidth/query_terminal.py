import sys
from time import sleep

import os
from termios import TCSANOW, TCSADRAIN, TCSAFLUSH, tcsetattr, tcgetattr
from functools import partial
from select import poll, POLLIN, select
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

def _kbhit():
    poll_obj = poll()
    def wrapped(fd=sys.stdin.fileno(), timeout=0):
        poll_obj.register(fd, POLLIN)
        with cbreak_terminal(fd, when_exit=TCSADRAIN):
            for i in poll_obj.poll(timeout):
                if i[0] == fd and i[1] & POLLIN:
                    return 1
        return 0
    return wrapped

kbhit = _kbhit()

def kbhit_select(fd=sys.stdin.fileno(), timeout=0):
    with cbreak_terminal(fd, when_exit=TCSADRAIN):
        rds, _, _ = select([fd], [], [], timeout)
        if rds:
            return 1
        return 0

def getch(fd=sys.stdin.fileno()):
    with cbreak_terminal(fd, when_exit=TCSADRAIN) as rterm:
        return os.read(rterm, 1)

def getwch(fd=sys.stdin.fileno(), encoding=sys.stdin.encoding):
    raw_str = ""
    for i in xrange(4):
        if raw_str:
            if kbhit():
                raw_str += getch(fd)
            else: break
        else:
            raw_str = getch(fd)
        try:
            return unicode(raw_str, encoding)
        except UnicodeDecodeError: continue
    return unicode(raw_str, encoding)

def width_from_terminal(start, end):
    s = ''
    try:
      mode = tcgetattr(sys.stdin.fileno())
      mode[LFLAG] &= ~ECHO
      tcsetattr(sys.stdin.fileno(), TCSADRAIN, mode)
      print
      for i in range(start, end):
          sys.stdout.write(unichr(i) + '\x1b[6n')
          sys.stdout.flush()
          # wait for CPR on stdin
          while not kbhit_select():
            sleep(.01)
          resp = ''
          while kbhit_select():
              resp += os.read(sys.stdin.fileno(), 1024)
          row, col = resp[2:-1].split(';')
          width = int(col)
          s += str(width - 1)
          print '\x1b[1K\x1b[Gcodepoint:', i, 'width:', width - 1
    finally:
        mode[LFLAG] |= ECHO
        tcsetattr(sys.stdin.fileno(), TCSADRAIN, mode)
    return s


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print "error, usage: query_terminal.py <start> <end> <file>"
        sys.exit(1)
    with open(sys.argv[3], 'w') as f:
        start = int(sys.argv[1], 16 if sys.argv[1].startswith('0x') else 10)
        end = int(sys.argv[2], 16 if sys.argv[2].startswith('0x') else 10)
        f.write(width_from_terminal(start, end))
