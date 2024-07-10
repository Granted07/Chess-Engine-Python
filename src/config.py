import os

from sound import Sound
from theme import Theme


class Config:

    def __init__(self):
        self.themes = []
        self._add_themes()
        self.index = 0
        self.theme = self.themes[self.index]
        self.move_sound = Sound(
            os.path.join('assets/sounds/move.wav')
        )
        self.capture_sound = Sound(
            os.path.join('assets/sounds/capture.wav')
        )

    def change_theme(self):
        self.index += 1
        self.index = self.index % len(self.themes)
        self.theme = self.themes[self.index]

    def _add_themes(self):
        blue = Theme((31, 165, 209), (167, 216, 232),
                     (123, 187, 227), (43, 119, 191),
                     'C86464', '#c84646')

        green = Theme((234, 235, 200), (119, 154, 88),
                      (244, 247, 116), (172, 195, 51),
                      'C86464', '#c84646')

        grey = Theme((120, 119, 118), (86, 85, 84),
                     (99, 126, 143), (82,102, 128),
                     'C86464', '#c84646')

        self.themes = [blue, green, grey]
