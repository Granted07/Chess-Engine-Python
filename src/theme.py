from colour import Colour


class Theme:

    def __init__(self, light_bg, dark_bg,
                 light_trace, dark_trace,
                 light_moves, dark_moves):
        self.bg = Colour(light_bg, dark_bg)
        self.trace = Colour(light_trace, dark_trace)
        self.moves = Colour(light_moves, dark_moves)
