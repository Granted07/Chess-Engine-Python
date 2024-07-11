import math


class Move:

    def __init__(self, initial, final):
        self.initial = initial
        self.final = final

    def __str__(self):
        s = ''
        s += f'{chr(ord('A') + self.initial.col)}{int(math.fabs(self.initial.row-8))}'
        s += f'; {chr(ord('A') + self.final.col)}{int(math.fabs(self.final.row-8))}'
        return s

    def __eq__(self, other):
        return self.initial == other.initial and self.final == other.final
