"""Terminal Wrapper which renders 2d arrays of characters to terminal"""

import sys
import os
import logging

import numpy

import termformat
import terminalcontrol
import termformatconstants
import events

logging.basicConfig(filename='terminal.log',level=logging.DEBUG)


class Terminal(object):
    """ Renders 2D arrays of characters and cursor position """
    #TODO: when less than whole screen owned, deal with that:
    #    -render the top of the screen at the first clear row
    #    -scroll down before rendering as necessary
    def __init__(self, tc):
        """
        tc expected to have must have methods:
            get_cursor_position()
            get_screen_size() -> (row, col)
            set_screen_position((row, column))
            write(msg)
            scroll_down()
            erase_line()
            down, up, left, back()
            get_event() -> 'c' | events.WindowChangeEvent(rows, columns)
        """
        logging.debug('-------initializing Terminal object %r------' % self)
        self.tc = tc

    def __enter__(self):
        self.top_usable_row, _ = self.tc.get_cursor_position()
        logging.debug('initial top_usable_row: %d' % self.top_usable_row)
        return self

    def __exit__(self, type, value, traceback):
        # We may have been killed by stderr being closed, so we
        # might not be able to query the cursor position.
        self.tc.scroll_down()
        row, _ = self.tc.get_cursor_position()
        for i in range(1000):
            self.tc.erase_line()
            self.tc.down()
            self.tc.up()
        self.tc.set_screen_position((row, 1))
        self.tc.erase_rest_of_line()

    def render_to_terminal(self, array, cursor_pos=(0,0), farray=None):
        """Renders array to terminal, returns the number of lines
            scrolled offscreen
        outputs:
         -number of times scrolled

        If array received is of width too small, render it anyway
        if array received is of width too large, render it anyway
        if array received is of height too small, render it anyway
        if array received is of height too large, render it, scroll down,
            and render the rest of it, then return how much we scrolled down
        """
        #TODO add cool render-on-change caching
        #TODO take a formatting array with same dimensions as array

        if farray is None:
            farray = numpy.zeros((array.shape[0], array.shape[1], 3), dtype=int)
            farray[:, :, 0] = termformatconstants.GREEN
            farray[:, :, 1] = 0 #termformatconstants.ON_GREEN
            farray[:, :, 2] = termformatconstants.BOLD

        height, width = self.tc.get_screen_size()
        rows_for_use = range(self.top_usable_row, height + 1)
        shared = min(len(array), len(rows_for_use))
        for row, line, fline in zip(rows_for_use[:shared], array[:shared], farray[:shared]):
            self.tc.set_screen_position((row, 1))
            self.tc.write(termformat.formatted_text(line, fline))
            self.tc.erase_rest_of_line()
        rest_of_lines = array[shared:]
        rest_of_flines = farray[shared:]
        rest_of_rows = rows_for_use[shared:]
        for row in rest_of_rows: # if array too small
            self.tc.set_screen_position((row, 1))
            self.tc.erase_line()
        offscreen_scrolls = 0
        for line, fline in zip(rest_of_lines, rest_of_flines): # if array too big
            logging.debug('sending scroll down message')
            self.tc.scroll_down()
            if self.top_usable_row > 1:
                self.top_usable_row -= 1
            else:
                offscreen_scrolls += 1
            logging.debug('new top_usable_row: %d' % self.top_usable_row)
            self.tc.set_screen_position((height, 1)) # since scrolling moves the cursor
            self.tc.write(termformat.formatted_text(line, fline))

        self.tc.set_screen_position((cursor_pos[0]-offscreen_scrolls+self.top_usable_row, cursor_pos[1]+1))
        return offscreen_scrolls

    def array_from_text(self, msg):
        rows, columns = self.tc.get_screen_size()
        a = numpy.array([[' ' for _ in range(columns)] for _ in range(rows)])
        i = 0
        for c in msg:
            if i >= a.size:
                return a
            elif c in '\r\n':
                i = ((i / columns) + 1) * columns
            else:
                a.flat[i] = c
            i += 1
        for r in reversed(range(rows)):
            if all(a[r] == [' ' for _ in range(columns)]):
                a = a[:r]
        return a

def test():
    with terminalcontrol.TCPartialler(sys.stdin, sys.stdout) as tc:
        with Terminal(tc) as t:
            rows, columns = t.tc.get_screen_size()
            while True:
                c = t.tc.get_event()
                if c == "":
                    sys.exit() # same as raise SystemExit()
                elif c == "h":
                    a = t.array_from_text("a for small array")
                elif c == "a":
                    a = numpy.array([[c] * columns for _ in range(rows)])
                elif c == "s":
                    a = numpy.array([[c] * columns for _ in range(rows-1)])
                elif c == "d":
                    a = numpy.array([[c] * columns for _ in range(rows+1)])
                elif c == "f":
                    a = numpy.array([[c] * columns for _ in range(rows-2)])
                elif c == "q":
                    a = numpy.array([[c] * columns for _ in range(1)])
                elif c == "w":
                    a = numpy.array([[c] * columns for _ in range(1)])
                elif c == "e":
                    a = numpy.array([[c] * columns for _ in range(1)])
                elif isinstance(c, events.WindowChangeEvent):
                    a = t.array_from_text("window just changed to %d rows and %d columns" % (c.rows, c.columns))
                elif c == "":
                    [t.tc.write('\n') for _ in range(rows)]
                    continue
                else:
                    a = t.array_from_text("unknown command")
                t.render_to_terminal(a)

def main():
    t = Terminal(sys.stdin, sys.stdout)
    rows, columns = t.tc.get_screen_size()
    import random
    goop = lambda l: [random.choice('aaabcddeeeefghiiijklmnooprssttuv        ') for _ in range(l)]
    a = numpy.array([goop(columns) for _ in range(rows)])
    t.render_to_terminal(a)
    while True:
        c = t.tc.get_event()
        if c == "":
            t.cleanup()
            sys.exit()
        t.render_to_terminal(numpy.array([[c] * columns for _ in range(rows)]))

def test_array_from_text():
    t = Terminal(sys.stdin, sys.stdout)
    a = t.array_from_text('\n\nhey there\nyo')
    os.system('reset')
    for line in a:
        print ''.join(line)
    raw_input()

if __name__ == '__main__':
    #test_array_from_text()
    test()
