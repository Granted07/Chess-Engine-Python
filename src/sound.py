import os
import sys
import pygame


def asset_path(rel_path):
    base = getattr(sys, '_MEIPASS', os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    return os.path.join(base, rel_path)


class Sound:

    def __init__(self, path):
        self.path = asset_path(path)
        self.sound = None
        if self._ensure_mixer():
            try:
                self.sound = pygame.mixer.Sound(self.path)
            except pygame.error as exc:
                print(f"Warning: failed to load sound '{path}': {exc}")

    @staticmethod
    def _ensure_mixer():
        """Ensure the mixer is ready before attempting to load sounds."""
        if pygame.mixer.get_init():
            return True
        try:
            pygame.mixer.init()
        except pygame.error as exc:
            print(f"Warning: pygame.mixer.init() failed: {exc}")
            return False
        return True

    def play(self):
        if self.sound:
            self.sound.play()
