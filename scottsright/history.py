"""implementations of readline control sequences to do with history

Implementing these similar to how they're done in bpython:
    * never modifying previous history entries
    * always appending the executed line
in the order of description at http://www.bigsmoke.us/readline/shortcuts
"""

import logging

CHAR_SEQUENCES = {}

def on(seq):
    def add_to_seq_handler(func):
        CHAR_SEQUENCES[seq] = func.__name__
        return func
    return add_to_seq_handler

line_with_cursor_at_end = lambda line: (len(line), line)

class History(object):
    def __init__(self):
        self._history_lines = [] # this is what we use for history - later
                                # it might remember previous sessions
        self.history_index = 0
        self.filter_line = ''
        self.char_sequences = {seq: getattr(self, handler)
                               for seq, handler in CHAR_SEQUENCES.items()}
        self.just_rewound = ''

    @property
    def history_lines(self):
        logging.debug('self.rewound: %r', self.just_rewound)
        if self.just_rewound:
            return self._history_lines + [self.just_rewound]
        else:
            return self._history_lines

    def use_history_index(self):
        current_line = self.history_lines[-self.history_index]
        return line_with_cursor_at_end(current_line)


    @on('')
    @on('[A')
    def prev_line_in_history(self, cursor_offset, current_line):
        logging.debug('contents of self.history_lines: %r', self.history_lines)
        if cursor_offset != len(current_line):
            return line_with_cursor_at_end(current_line)
        else:
            if self.history_index == 0:
                self.filter_line = current_line
            if len(self.history_lines) == 0:
                return cursor_offset, current_line
            #TODO do actual filtering here
            self.history_index = (self.history_index % len(self.history_lines)) + 1
            return self.use_history_index()

    @on('')
    @on('[B')
    def next_line_in_history(self, cursor_offset, current_line):
        if self.history_index == 0:
            return cursor_offset, current_line
        else:
            self.history_index -= 1
            if self.history_index == 0:
                return line_with_cursor_at_end(self.filter_line)
            return self.use_history_index()

    @on('.')
    def back_to_current_line_in_history(self, cursor_offset, current_line):
        raise NotImplementedError()

    def on_enter(self, line):
        self.history_index = 0
        if line:
            self._history_lines.append(line)
        self.just_rewound = ''

    def clear_history_before_rewind(self):
        self._history_lines = []

    def set_just_rewound(self, line):
        self.just_rewound = line

