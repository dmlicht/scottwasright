"""Language for describing events that in terminal"""
class Event(object):
    pass

class WindowChangeEvent(Event):
    def __init__(self, rows, columns):
        self.rows = rows
        self.columns = columns
    x = width = property(lambda self: self.columns)
    y = height = property(lambda self: self.rows)
    def __repr__(self):
        return "<WindowChangeEvent (%d, %d)>" % (self.rows, self.columns)

class Keypress(Event):
    def __init__(self, seq):
        self.seq = seq
    def __repr__(self, seq):
        return "<Key %r>" % self.seq
